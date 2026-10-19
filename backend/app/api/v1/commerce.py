from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.rbac import current_claims
from app.db.session import get_sync_db_session
from app.schemas.common import ApiResponse
from app.schemas.orders import CartItemRequest, CartResponse, CheckoutRequest, OrderResponse
from app.services.orders import OrderService


router = APIRouter(tags=["commerce"])
get_commerce_session = get_sync_db_session
session_dependency = Depends(get_commerce_session)
claims_dependency = Depends(current_claims)


def user_id_from_claims(claims: dict[str, object]) -> UUID:
    return UUID(str(claims["sub"]))


@router.get("/cart", response_model=ApiResponse[CartResponse])
def get_cart(
    request: Request,
    claims: dict[str, object] = claims_dependency,
    session: Session = session_dependency,
) -> ApiResponse[CartResponse]:
    return ApiResponse.ok(
        request_id=request.state.request_id,
        data=OrderService(session).get_cart(user_id_from_claims(claims)),
    )


@router.post("/cart/items", response_model=ApiResponse[CartResponse])
def add_cart_item(
    payload: CartItemRequest,
    request: Request,
    claims: dict[str, object] = claims_dependency,
    session: Session = session_dependency,
) -> ApiResponse[CartResponse]:
    cart = OrderService(session).add_to_cart(user_id_from_claims(claims), payload.sku_id, payload.quantity)
    return ApiResponse.ok(request_id=request.state.request_id, data=cart)


@router.patch("/cart/items/{item_id}", response_model=ApiResponse[CartResponse])
def update_cart_item(item_id: UUID, payload: CartItemRequest, request: Request, claims: dict[str, object] = claims_dependency, session: Session = session_dependency) -> ApiResponse[CartResponse]:
    cart = OrderService(session).update_cart_item(user_id_from_claims(claims), item_id, payload.quantity)
    return ApiResponse.ok(request_id=request.state.request_id, data=cart)


@router.delete("/cart/items/{item_id}", response_model=ApiResponse[CartResponse])
def delete_cart_item(item_id: UUID, request: Request, claims: dict[str, object] = claims_dependency, session: Session = session_dependency) -> ApiResponse[CartResponse]:
    cart = OrderService(session).remove_cart_item(user_id_from_claims(claims), item_id)
    return ApiResponse.ok(request_id=request.state.request_id, data=cart)


@router.post("/orders", response_model=ApiResponse[OrderResponse], status_code=201)
def create_order(
    payload: CheckoutRequest,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=128),
    claims: dict[str, object] = claims_dependency,
    session: Session = session_dependency,
) -> ApiResponse[OrderResponse]:
    order = OrderService(session).checkout(user_id_from_claims(claims), payload.address_snapshot, payload.coupon_code, idempotency_key=idempotency_key)
    return ApiResponse.ok(request_id=request.state.request_id, data=order)


@router.get("/orders", response_model=ApiResponse[list[OrderResponse]])
def list_orders(
    request: Request,
    claims: dict[str, object] = claims_dependency,
    session: Session = session_dependency,
) -> ApiResponse[list[OrderResponse]]:
    orders = OrderService(session).list_orders(user_id_from_claims(claims))
    return ApiResponse.ok(request_id=request.state.request_id, data=orders)


@router.get("/orders/{order_id}", response_model=ApiResponse[OrderResponse])
def get_order(order_id: UUID, request: Request, claims: dict[str, object] = claims_dependency, session: Session = session_dependency) -> ApiResponse[OrderResponse]:
    return ApiResponse.ok(request_id=request.state.request_id, data=OrderService(session).get_order(user_id_from_claims(claims), order_id))


@router.post("/orders/{order_id}/cancel", response_model=ApiResponse[OrderResponse])
def cancel_order(order_id: UUID, request: Request, claims: dict[str, object] = claims_dependency, session: Session = session_dependency) -> ApiResponse[OrderResponse]:
    return ApiResponse.ok(request_id=request.state.request_id, data=OrderService(session).cancel_order(user_id_from_claims(claims), order_id))


@router.post("/orders/{order_id}/refund", response_model=ApiResponse[OrderResponse])
def refund_order(order_id: UUID, request: Request, claims: dict[str, object] = claims_dependency, session: Session = session_dependency) -> ApiResponse[OrderResponse]:
    return ApiResponse.ok(request_id=request.state.request_id, data=OrderService(session).refund_order(user_id_from_claims(claims), order_id))


@router.get("/orders/{order_id}/shipping", response_model=ApiResponse[dict[str, object]])
def get_shipping(order_id: UUID, request: Request, claims: dict[str, object] = claims_dependency, session: Session = session_dependency) -> ApiResponse[dict[str, object]]:
    return ApiResponse.ok(request_id=request.state.request_id, data=OrderService(session).shipping(user_id_from_claims(claims), order_id))
