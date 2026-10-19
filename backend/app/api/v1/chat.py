from __future__ import annotations

import json
from collections.abc import Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rbac import current_claims
from app.db.session import get_sync_db_session
from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatRequest, ChatResult
from app.schemas.common import ApiResponse
from app.services.chat import ChatService

router = APIRouter(tags=["chat"])


def _user_id(claims: dict[str, object]) -> UUID:
    return UUID(str(claims["sub"]))


@router.post("/chat", response_model=ApiResponse[ChatResult])
def chat(payload: ChatRequest, request: Request, claims: dict[str, object] = Depends(current_claims), session: Session = Depends(get_sync_db_session)) -> ApiResponse[ChatResult]:
    result = ChatService(session).handle(_user_id(claims), payload)
    return ApiResponse.ok(request_id=request.state.request_id, data=result)


@router.post("/chat/stream")
def chat_stream(payload: ChatRequest, request: Request, claims: dict[str, object] = Depends(current_claims), session: Session = Depends(get_sync_db_session)) -> StreamingResponse:
    result = ChatService(session).handle(_user_id(claims), payload)

    def events() -> Iterator[str]:
        base = {"conversation_id": str(result.conversation_id), "message_id": str(result.message_id)}
        yield f"event: message_start\ndata: {json.dumps(base, ensure_ascii=False)}\n\n"
        yield f"event: tool_call\ndata: {json.dumps({**base, 'intent': result.intent}, ensure_ascii=False)}\n\n"
        for citation in result.citations:
            yield f"event: citation\ndata: {json.dumps({**base, 'citation': citation.model_dump(mode='json')}, ensure_ascii=False)}\n\n"
        yield f"event: token\ndata: {json.dumps({**base, 'text': result.answer}, ensure_ascii=False)}\n\n"
        yield f"event: message_end\ndata: {json.dumps({**base, 'handoff': result.handoff}, ensure_ascii=False)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


@router.get("/conversations", response_model=ApiResponse[list[dict[str, object]]])
def conversations(request: Request, claims: dict[str, object] = Depends(current_claims), session: Session = Depends(get_sync_db_session)) -> ApiResponse[list[dict[str, object]]]:
    rows = session.scalars(select(Conversation).where(Conversation.user_id == _user_id(claims)).order_by(Conversation.created_at.desc())).all()
    data = [{"id": row.id, "status": row.status, "title": row.title} for row in rows]
    return ApiResponse.ok(request_id=request.state.request_id, data=data)


@router.get("/conversations/{conversation_id}", response_model=ApiResponse[dict[str, object]])
def conversation_detail(conversation_id: UUID, request: Request, claims: dict[str, object] = Depends(current_claims), session: Session = Depends(get_sync_db_session)) -> ApiResponse[dict[str, object]]:
    conversation = session.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != _user_id(claims):
        from app.core.errors import AppError
        raise AppError("CONVERSATION_NOT_FOUND", "会话不存在", 404)
    messages = session.scalars(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)).all()
    return ApiResponse.ok(request_id=request.state.request_id, data={"id": conversation.id, "status": conversation.status, "messages": [{"id": m.id, "role": m.role, "content": m.content, "citations_json": m.citations_json} for m in messages]})
