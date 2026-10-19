from decimal import Decimal
import hashlib
import json
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.catalog import Product, ProductSku
from app.models.idempotency import IdempotencyRecord
from app.models.commerce import Cart, CartItem, Coupon, Inventory, InventoryTransaction, Order, OrderItem, Payment, Shipment
from app.schemas.orders import CartResponse, OrderResponse


class OrderService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _cart(self, user_id: UUID) -> Cart:
        cart = self.session.scalar(select(Cart).where(Cart.user_id == user_id))
        if cart is None:
            cart = Cart(user_id=user_id)
            self.session.add(cart)
            self.session.flush()
        return cart

    def add_to_cart(self, user_id: UUID, sku_id: UUID, quantity: int) -> CartResponse:
        sku = self.session.get(ProductSku, sku_id)
        if sku is None or sku.status != "active":
            raise AppError("SKU_NOT_FOUND", "SKU 不存在或不可售", 404)
        product = self.session.get(Product, sku.product_id)
        if product is None or product.status != "published":
            raise AppError("PRODUCT_NOT_AVAILABLE", "商品当前不可售", 409)
        inventory = self.session.scalar(select(Inventory).where(Inventory.sku_id == sku_id))
        if inventory is None or inventory.available_quantity < quantity:
            raise AppError("INVENTORY_INSUFFICIENT", "库存不足", 409)
        cart = self._cart(user_id)
        item = self.session.scalar(select(CartItem).where(CartItem.cart_id == cart.id, CartItem.sku_id == sku_id))
        next_quantity = quantity + (item.quantity if item else 0)
        if next_quantity > inventory.available_quantity:
            raise AppError("INVENTORY_INSUFFICIENT", "库存不足", 409)
        if item is None:
            item = CartItem(cart_id=cart.id, sku_id=sku_id, quantity=quantity)
            self.session.add(item)
        else:
            item.quantity = next_quantity
        self.session.commit()
        self.session.refresh(cart)
        return self.get_cart(user_id)

    def get_cart(self, user_id: UUID) -> CartResponse:
        cart = self._cart(user_id)
        items = self.session.scalars(select(CartItem).where(CartItem.cart_id == cart.id)).all()
        return CartResponse(id=cart.id, user_id=user_id, items=[{"id": i.id, "sku_id": i.sku_id, "quantity": i.quantity} for i in items])

    def get_cart_items(self, user_id: UUID) -> list[CartItem]:
        cart = self._cart(user_id)
        return list(self.session.scalars(select(CartItem).where(CartItem.cart_id == cart.id)))

    def update_cart_item(self, user_id: UUID, item_id: UUID, quantity: int) -> CartResponse:
        item = self.session.scalar(select(CartItem).join(Cart).where(CartItem.id == item_id, Cart.user_id == user_id))
        if item is None:
            raise AppError("CART_ITEM_NOT_FOUND", "购物车商品不存在", 404)
        inventory = self.session.scalar(select(Inventory).where(Inventory.sku_id == item.sku_id))
        if inventory is None or quantity > inventory.available_quantity:
            raise AppError("INVENTORY_INSUFFICIENT", "库存不足", 409)
        item.quantity = quantity
        self.session.commit()
        return self.get_cart(user_id)

    def remove_cart_item(self, user_id: UUID, item_id: UUID) -> CartResponse:
        item = self.session.scalar(select(CartItem).join(Cart).where(CartItem.id == item_id, Cart.user_id == user_id))
        if item is None:
            raise AppError("CART_ITEM_NOT_FOUND", "购物车商品不存在", 404)
        self.session.delete(item); self.session.commit()
        return self.get_cart(user_id)

    def checkout(self, user_id: UUID, address_snapshot: str, coupon_code: str | None = None, idempotency_key: str | None = None) -> OrderResponse:
        request_hash = hashlib.sha256(json.dumps({"address_snapshot": address_snapshot, "coupon_code": coupon_code}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if idempotency_key:
            if len(idempotency_key) > 128:
                raise AppError("IDEMPOTENCY_KEY_INVALID", "幂等键长度不能超过 128", 422)
            previous = self.session.scalar(select(IdempotencyRecord).where(IdempotencyRecord.user_id == user_id, IdempotencyRecord.key == idempotency_key, IdempotencyRecord.endpoint == "POST /orders"))
            if previous is not None:
                if previous.request_hash != request_hash:
                    raise AppError("IDEMPOTENCY_CONFLICT", "幂等键已用于其他请求", 409)
                if previous.order_id is not None:
                    original = self.session.get(Order, previous.order_id)
                    if original is not None:
                        return OrderResponse.model_validate(original)
        cart = self._cart(user_id)
        items = self.session.scalars(select(CartItem).where(CartItem.cart_id == cart.id)).all()
        if not items:
            raise AppError("CART_EMPTY", "购物车为空", 409)
        order_items: list[OrderItem] = []
        total = Decimal("0.00")
        for item in items:
            sku = self.session.get(ProductSku, item.sku_id)
            inventory = self.session.scalar(select(Inventory).where(Inventory.sku_id == item.sku_id).with_for_update())
            if sku is None or inventory is None or inventory.available_quantity < item.quantity:
                raise AppError("INVENTORY_INSUFFICIENT", "库存不足", 409)
            product = self.session.get(Product, sku.product_id)
            if product is None or product.status != "published":
                raise AppError("PRODUCT_NOT_AVAILABLE", "商品当前不可售", 409)
            inventory.quantity -= item.quantity
            inventory.available_quantity -= item.quantity
            self.session.add(InventoryTransaction(inventory_id=inventory.id, change_quantity=-item.quantity, reason="checkout"))
            line_total = sku.sale_price * item.quantity
            total += line_total
            order_items.append(OrderItem(sku_id=sku.id, product_name=product.name, quantity=item.quantity, unit_price=sku.sale_price))
        discount = Decimal("0.00")
        if coupon_code:
            coupon = self.session.scalar(select(Coupon).where(Coupon.code == coupon_code, Coupon.active.is_(True)))
            if coupon is None:
                raise AppError("COUPON_INVALID", "优惠券无效或已过期", 409)
            discount = (total * coupon.discount_value / Decimal("100")) if coupon.discount_type == "percentage" else min(total, coupon.discount_value)
            total -= discount
        order = Order(
            order_number=f"FR{uuid4().hex[:18].upper()}",
            user_id=user_id,
            status="paid",
            total_amount=total,
            address_snapshot=address_snapshot,
        )
        self.session.add(order)
        self.session.flush()
        for order_item in order_items:
            order_item.order_id = order.id
            self.session.add(order_item)
        self.session.add(Payment(order_id=order.id, provider="mock", status="paid", amount=total, provider_reference=f"mock-{uuid4().hex}"))
        for item in items:
            self.session.delete(item)
        self.session.commit()
        self.session.refresh(order)
        if idempotency_key:
            self.session.add(IdempotencyRecord(user_id=user_id, key=idempotency_key, endpoint="POST /orders", request_hash=request_hash, order_id=order.id))
            self.session.commit()
        return OrderResponse.model_validate(order)

    def list_orders(self, user_id: UUID) -> list[OrderResponse]:
        orders = self.session.scalars(
            select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
        ).all()
        return [OrderResponse.model_validate(order) for order in orders]

    def get_order(self, user_id: UUID, order_id: UUID) -> OrderResponse:
        order = self.session.scalar(select(Order).where(Order.id == order_id, Order.user_id == user_id))
        if order is None:
            raise AppError("ORDER_NOT_FOUND", "订单不存在", 404)
        return OrderResponse.model_validate(order)

    def cancel_order(self, user_id: UUID, order_id: UUID) -> OrderResponse:
        order = self.session.scalar(select(Order).where(Order.id == order_id, Order.user_id == user_id))
        if order is None:
            raise AppError("ORDER_NOT_FOUND", "订单不存在", 404)
        if order.status not in {"paid", "pending_payment"}:
            raise AppError("ORDER_CANNOT_CANCEL", "当前订单状态不可取消", 409)
        for item in self.session.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all():
            inventory = self.session.scalar(select(Inventory).where(Inventory.sku_id == item.sku_id))
            if inventory:
                inventory.quantity += item.quantity; inventory.available_quantity += item.quantity
                self.session.add(InventoryTransaction(inventory_id=inventory.id, change_quantity=item.quantity, reason="order_cancel", reference_id=order.id))
        order.status = "canceled"
        payment = self.session.scalar(select(Payment).where(Payment.order_id == order.id))
        if payment: payment.status = "refunded"
        self.session.commit(); self.session.refresh(order)
        return OrderResponse.model_validate(order)

    def refund_order(self, user_id: UUID, order_id: UUID) -> OrderResponse:
        order = self.session.scalar(select(Order).where(Order.id == order_id, Order.user_id == user_id))
        if order is None:
            raise AppError("ORDER_NOT_FOUND", "订单不存在", 404)
        if order.status not in {"paid", "shipped", "delivered"}:
            raise AppError("ORDER_CANNOT_REFUND", "当前订单状态不可申请退款", 409)
        order.status = "refund_requested"
        self.session.commit(); self.session.refresh(order)
        return OrderResponse.model_validate(order)

    def shipping(self, user_id: UUID, order_id: UUID) -> dict[str, object]:
        self.get_order(user_id, order_id)
        shipment = self.session.scalar(select(Shipment).where(Shipment.order_id == order_id))
        return {"status": shipment.status if shipment else "pending", "carrier": shipment.carrier if shipment else None, "tracking_number": shipment.tracking_number if shipment else None}
