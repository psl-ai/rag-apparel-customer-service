from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.commerce import Order
from app.models.commerce import Shipment
from app.models.catalog import Product
from app.core.errors import AppError
from app.models.conversation import Conversation, CustomerFeedback, HumanHandoff
from app.models.user import User


class AdminAnalyticsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def dashboard(self) -> dict[str, object]:
        users = int(self.session.scalar(select(func.count()).select_from(User)) or 0)
        orders = int(self.session.scalar(select(func.count()).select_from(Order)) or 0)
        sales = self.session.scalar(select(func.coalesce(func.sum(Order.total_amount), 0)).where(Order.status.not_in(["canceled", "refund_requested"]))) or Decimal("0")
        consultations = int(self.session.scalar(select(func.count()).select_from(Conversation)) or 0)
        handoffs = int(self.session.scalar(select(func.count()).select_from(HumanHandoff)) or 0)
        feedback_count = int(self.session.scalar(select(func.count()).select_from(CustomerFeedback)) or 0)
        rating = self.session.scalar(select(func.avg(CustomerFeedback.rating)))
        return {
            "users": users,
            "orders": orders,
            "sales_amount": Decimal(str(sales)),
            "consultations": consultations,
            "handoffs": handoffs,
            "satisfaction": round(float(rating or 0), 2),
            "feedback_count": feedback_count,
        }


class AdminOperationsService:
    _allowed: dict[str, set[str]] = {
        "pending_payment": {"paid", "canceled"},
        "paid": {"processing", "shipped", "canceled", "refund_requested"},
        "processing": {"shipped", "canceled"},
        "shipped": {"delivered", "refund_requested"},
        "delivered": {"refund_requested"},
        "refund_requested": {"refunded"},
    }

    def __init__(self, session: Session) -> None:
        self.session = session

    def product_listing(self) -> list[dict[str, object]]:
        rows = self.session.scalars(select(Product).order_by(Product.created_at.desc()).limit(200)).all()
        return [{"id": row.id, "name": row.name, "slug": row.slug, "status": row.status, "category_id": row.category_id, "description": row.description, "fabric_info": row.fabric_info, "care_instructions": row.care_instructions} for row in rows]

    def set_product_status(self, product_id, status: str) -> Product:
        if status not in {"draft", "published", "archived"}:
            raise AppError("PRODUCT_INVALID_STATUS", "商品状态无效", 422)
        product = self.session.get(Product, product_id)
        if product is None:
            raise AppError("PRODUCT_NOT_FOUND", "商品不存在", 404)
        product.status = status
        self.session.commit(); self.session.refresh(product)
        return product

    def update_order_status(self, order_id, status: str, *, carrier: str | None = None, tracking_number: str | None = None) -> Order:
        order = self.session.get(Order, order_id)
        if order is None:
            raise AppError("ORDER_NOT_FOUND", "订单不存在", 404)
        if status not in self._allowed.get(order.status, set()):
            raise AppError("ORDER_INVALID_TRANSITION", f"订单不能从 {order.status} 变更为 {status}", 409)
        if status == "shipped" and not tracking_number:
            raise AppError("SHIPMENT_TRACKING_REQUIRED", "发货必须填写物流单号", 422)
        order.status = status
        if status == "shipped":
            shipment = self.session.scalar(select(Shipment).where(Shipment.order_id == order.id))
            if shipment is None:
                shipment = Shipment(order_id=order.id)
                self.session.add(shipment)
            shipment.status = "in_transit"; shipment.carrier = carrier; shipment.tracking_number = tracking_number
        if status == "delivered":
            shipment = self.session.scalar(select(Shipment).where(Shipment.order_id == order.id))
            if shipment: shipment.status = "delivered"
        self.session.commit(); self.session.refresh(order)
        return order
