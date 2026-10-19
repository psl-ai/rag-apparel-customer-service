from __future__ import annotations

import json
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.catalog import Product, ProductSku, SizeChart
from app.models.commerce import Inventory, Order, Shipment
from app.models.conversation import Conversation, HumanHandoff
from app.models.user import UserPreference
from app.rag.retriever import get_knowledge_retriever
from app.schemas.catalog import ProductResponse
from app.schemas.rag import RetrievedChunk


class ProductSearchInput(BaseModel):
    query: str = Field(default="", max_length=100)
    limit: int = Field(default=5, ge=1, le=5)


class ProductSearchOutput(BaseModel):
    items: list[ProductResponse]


class InventoryQueryInput(BaseModel):
    sku_id: UUID


class InventoryQueryOutput(BaseModel):
    sku_id: UUID
    available_quantity: int
    sellable: bool


class KnowledgeQueryInput(BaseModel):
    query: str
    document_type: str | None = None
    product_id: UUID | None = None
    top_k: int = Field(default=5, ge=1, le=5)


class HandoffInput(BaseModel):
    conversation_id: UUID
    reason: str = Field(min_length=1, max_length=500)


def search_products(session: Session, payload: ProductSearchInput) -> ProductSearchOutput:
    statement = select(Product).where(Product.status == "published")
    if payload.query.strip():
        term = f"%{payload.query.strip()}%"
        statement = statement.where(or_(Product.name.ilike(term), Product.description.ilike(term)))
    products = session.scalars(statement.order_by(Product.created_at.desc()).limit(payload.limit)).all()
    return ProductSearchOutput(items=[ProductResponse.model_validate(product) for product in products])


def get_product_detail(session: Session, product_id: UUID) -> ProductResponse:
    product = session.get(Product, product_id)
    if product is None or product.status != "published":
        raise AppError("PRODUCT_NOT_FOUND", "商品不存在", 404)
    return ProductResponse.model_validate(product)


def query_inventory(session: Session, payload: InventoryQueryInput) -> InventoryQueryOutput:
    inventory = session.scalar(select(Inventory).where(Inventory.sku_id == payload.sku_id))
    if inventory is None:
        raise AppError("INVENTORY_NOT_FOUND", "库存不存在", 404)
    return InventoryQueryOutput(sku_id=payload.sku_id, available_quantity=inventory.available_quantity, sellable=inventory.available_quantity > 0)


def recommend_size(session: Session, product_id: UUID, *, size_name: str | None = None) -> list[dict[str, str]]:
    statement = select(SizeChart).where(SizeChart.product_id == product_id)
    rows = session.scalars(statement).all()
    if size_name:
        rows = [row for row in rows if size_name.lower() in row.measurements.lower()]
    return [{"size_id": str(row.size_id), "measurements": row.measurements} for row in rows]


def retrieve_knowledge(session: Session, payload: KnowledgeQueryInput) -> list[RetrievedChunk]:
    return get_knowledge_retriever(session).search(payload.query, document_type=payload.document_type, product_id=payload.product_id, top_k=payload.top_k)


def compare_products(session: Session, product_ids: list[UUID]) -> list[ProductResponse]:
    products = session.scalars(select(Product).where(Product.id.in_(product_ids), Product.status == "published")).all()
    return [ProductResponse.model_validate(product) for product in products]


def get_user_preferences(session: Session, user_id: UUID) -> dict[str, object]:
    preference = session.scalar(select(UserPreference).where(UserPreference.user_id == user_id))
    if preference is None:
        return {}
    return {"body_data": preference.body_data, "style_preferences": preference.style_preferences}


def save_user_preference(session: Session, user_id: UUID, values: dict[str, object]) -> dict[str, object]:
    preference = session.scalar(select(UserPreference).where(UserPreference.user_id == user_id))
    if preference is None:
        preference = UserPreference(user_id=user_id)
        session.add(preference)
    for key in ("body_data", "style_preferences"):
        if key in values:
            setattr(preference, key, json.dumps(values[key], ensure_ascii=False) if isinstance(values[key], (dict, list)) else str(values[key]))
    session.commit()
    return get_user_preferences(session, user_id)


def get_order_status(session: Session, user_id: UUID, order_id: UUID) -> dict[str, str]:
    order = session.scalar(select(Order).where(Order.id == order_id, Order.user_id == user_id))
    if order is None:
        raise AppError("ORDER_NOT_FOUND", "订单不存在", 404)
    return {"order_id": str(order.id), "order_number": order.order_number, "status": order.status}


def get_shipping_status(session: Session, user_id: UUID, order_id: UUID) -> dict[str, str | None]:
    get_order_status(session, user_id, order_id)
    shipment = session.scalar(select(Shipment).where(Shipment.order_id == order_id))
    if shipment is None:
        return {"status": "pending", "carrier": None, "tracking_number": None}
    return {"status": shipment.status, "carrier": shipment.carrier, "tracking_number": shipment.tracking_number}


def check_return_policy(session: Session, query: str = "退换货") -> list[RetrievedChunk]:
    return retrieve_knowledge(session, KnowledgeQueryInput(query=query, document_type="policy"))


def create_human_handoff(session: Session, payload: HandoffInput) -> HumanHandoff:
    conversation = session.get(Conversation, payload.conversation_id)
    if conversation is None:
        raise AppError("CONVERSATION_NOT_FOUND", "会话不存在", 404)
    handoff = HumanHandoff(conversation_id=payload.conversation_id, reason=payload.reason, status="pending")
    conversation.status = "handoff"
    session.add(handoff)
    session.commit()
    session.refresh(handoff)
    return handoff
