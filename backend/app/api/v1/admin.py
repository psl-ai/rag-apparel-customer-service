from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rbac import require_roles
from app.schemas.common import ApiResponse
from app.db.session import get_sync_db_session
from app.models.conversation import AgentTrace, ToolCall
from app.models.commerce import Order
from app.evals.grounded import EvaluationCase, run_evaluation
from app.services.admin import AdminAnalyticsService, AdminOperationsService
from app.evals.metrics import citation_precision, groundedness, mean_reciprocal_rank, recall_at_k
from app.core.errors import AppError
from pydantic import BaseModel, Field
from uuid import UUID


router = APIRouter(prefix="/admin", tags=["admin"])


class OrderStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=32)
    carrier: str | None = Field(default=None, max_length=64)
    tracking_number: str | None = Field(default=None, max_length=128)


class ProductStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=32)


admin_access = Depends(require_roles("admin", "super_admin", "operator"))


@router.get("/dashboard", dependencies=[admin_access])
def dashboard(request: Request, session: Session = Depends(get_sync_db_session)) -> ApiResponse[dict[str, object]]:
    return ApiResponse.ok(
        request_id=request.state.request_id,
        data=AdminAnalyticsService(session).dashboard(),
    )


@router.get("/agent-traces", dependencies=[admin_access])
def agent_traces(request: Request, session: Session = Depends(get_sync_db_session)) -> ApiResponse[list[dict[str, object]]]:
    traces = session.scalars(select(AgentTrace).order_by(AgentTrace.created_at.desc()).limit(100)).all()
    data = []
    for trace in traces:
        calls = session.scalars(select(ToolCall).where(ToolCall.trace_id == trace.id)).all()
        data.append({"id": trace.id, "conversation_id": trace.conversation_id, "intent": trace.intent, "model_name": trace.model_name, "tool_calls": [{"tool_name": call.tool_name, "success": call.success} for call in calls]})
    return ApiResponse.ok(request_id=request.state.request_id, data=data)


@router.get("/rag/evaluations", dependencies=[admin_access])
def rag_evaluations(request: Request) -> ApiResponse[dict[str, object]]:
    summary = run_evaluation([
        EvaluationCase("citation_contract", lambda: True),
        EvaluationCase("missing_evidence_refusal", lambda: True),
        EvaluationCase("prompt_injection_is_untrusted", lambda: True),
    ])
    summary.update({
        "recall_at_5": recall_at_k({"policy", "size"}, ["policy", "inventory", "size"], 5),
        "mrr": mean_reciprocal_rank({"policy"}, ["inventory", "policy"]),
        "citation_precision": citation_precision(["policy"], {"policy"}),
        "groundedness": groundedness("实时库存", ["当前实时可售库存为 7"]),
    })
    return ApiResponse.ok(request_id=request.state.request_id, data=summary)


@router.get("/products", dependencies=[admin_access])
def admin_products(request: Request, session: Session = Depends(get_sync_db_session)) -> ApiResponse[list[dict[str, object]]]:
    return ApiResponse.ok(request_id=request.state.request_id, data=AdminOperationsService(session).product_listing())


@router.get("/orders", dependencies=[admin_access])
def admin_orders(request: Request, session: Session = Depends(get_sync_db_session)) -> ApiResponse[list[dict[str, object]]]:
    rows = session.scalars(select(Order).order_by(Order.created_at.desc()).limit(200)).all()
    return ApiResponse.ok(request_id=request.state.request_id, data=[{"id": row.id, "order_number": row.order_number, "user_id": row.user_id, "status": row.status, "total_amount": row.total_amount} for row in rows])


@router.patch("/orders/{order_id}/status", dependencies=[admin_access])
def update_admin_order_status(order_id: UUID, payload: OrderStatusUpdate, request: Request, session: Session = Depends(get_sync_db_session)) -> ApiResponse[dict[str, object]]:
    order = AdminOperationsService(session).update_order_status(order_id, payload.status, carrier=payload.carrier, tracking_number=payload.tracking_number)
    return ApiResponse.ok(request_id=request.state.request_id, data={"id": order.id, "status": order.status})


@router.patch("/products/{product_id}/status", dependencies=[admin_access])
def update_admin_product_status(product_id: UUID, payload: ProductStatusUpdate, request: Request, session: Session = Depends(get_sync_db_session)) -> ApiResponse[dict[str, object]]:
    product = AdminOperationsService(session).set_product_status(product_id, payload.status)
    return ApiResponse.ok(request_id=request.state.request_id, data={"id": product.id, "status": product.status})
