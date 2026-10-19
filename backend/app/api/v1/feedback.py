from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.rbac import current_claims, require_roles
from app.db.session import get_sync_db_session
from app.models.conversation import Conversation, CustomerFeedback, HumanHandoff
from app.schemas.common import ApiResponse
from app.schemas.feedback import FeedbackRequest

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=ApiResponse[dict[str, object]])
def feedback(payload: FeedbackRequest, request: Request, claims: dict[str, object] = Depends(current_claims), session: Session = Depends(get_sync_db_session)) -> ApiResponse[dict[str, object]]:
    user_id = UUID(str(claims["sub"]))
    conversation = session.get(Conversation, payload.conversation_id)
    if conversation is None or conversation.user_id != user_id:
        raise AppError("CONVERSATION_NOT_FOUND", "会话不存在", 404)
    row = CustomerFeedback(**payload.model_dump())
    session.add(row); session.commit(); session.refresh(row)
    return ApiResponse.ok(request_id=request.state.request_id, data={"id": row.id, "rating": row.rating})


@router.post("/admin/handoffs/{handoff_id}/takeover", response_model=ApiResponse[dict[str, object]], dependencies=[Depends(require_roles("operator", "admin", "super_admin"))])
def takeover(handoff_id: UUID, request: Request, claims: dict[str, object] = Depends(current_claims), session: Session = Depends(get_sync_db_session)) -> ApiResponse[dict[str, object]]:
    handoff = session.get(HumanHandoff, handoff_id)
    if handoff is None:
        raise AppError("HANDOFF_NOT_FOUND", "转人工记录不存在", 404)
    handoff.status = "in_progress"; handoff.assigned_to_user_id = UUID(str(claims["sub"]))
    session.commit()
    return ApiResponse.ok(request_id=request.state.request_id, data={"id": handoff.id, "status": handoff.status})
