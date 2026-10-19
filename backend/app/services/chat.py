from __future__ import annotations

import json
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.policy import compose_answer
from app.agents.tools import (
    HandoffInput,
    InventoryQueryInput,
    KnowledgeQueryInput,
    create_human_handoff,
    query_inventory,
    recommend_size,
    retrieve_knowledge,
)
from app.core.errors import AppError
from app.models.conversation import AgentTrace, Conversation, Message, ToolCall
from app.schemas.chat import ChatRequest, ChatResult


class ChatService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _conversation(self, user_id: UUID | None, conversation_id: UUID | None) -> Conversation:
        if conversation_id:
            conversation = self.session.get(Conversation, conversation_id)
            if conversation is None or conversation.user_id != user_id:
                raise AppError("CONVERSATION_NOT_FOUND", "会话不存在", 404)
            return conversation
        conversation = Conversation(user_id=user_id, status="open")
        self.session.add(conversation)
        self.session.flush()
        return conversation

    def handle(self, user_id: UUID | None, request: ChatRequest) -> ChatResult:
        conversation = self._conversation(user_id, request.conversation_id)
        self.session.add(Message(conversation_id=conversation.id, role="user", content=request.message))
        intent = self._intent(request.message)
        trace = AgentTrace(conversation_id=conversation.id, intent=intent, model_name="deterministic-mock")
        self.session.add(trace)
        self.session.flush()
        citations = []
        handoff = False
        answer: str
        if intent == "inventory":
            if request.sku_id is None:
                answer = "请提供具体 SKU 或先选择颜色和尺码，我才能查询实时库存。"
            else:
                result = query_inventory(self.session, InventoryQueryInput(sku_id=request.sku_id))
                answer = compose_answer(intent, request.message, [], live_value=str(result.available_quantity))
                self._record_tool(trace, "query_inventory", request.model_dump(mode="json"), result.model_dump(mode="json"))
        elif intent == "size":
            rows = recommend_size(self.session, request.product_id) if request.product_id else []
            evidence = [row["measurements"] for row in rows]
            answer = compose_answer(intent, request.message, evidence)
            self._record_tool(trace, "recommend_size", request.model_dump(mode="json"), rows)
            if not evidence:
                handoff = True
        elif intent == "return_policy":
            results = retrieve_knowledge(self.session, KnowledgeQueryInput(query=request.message, document_type="policy"))
            citations = [item for item in results]
            evidence = [f"{item.title} § {item.section or '正文'} ({item.source_locator or '来源未标注'}): {item.snippet}" for item in results]
            answer = compose_answer(intent, request.message, evidence)
            self._record_tool(trace, "retrieve_knowledge", request.model_dump(mode="json"), [item.model_dump(mode="json") for item in results])
            handoff = not bool(results)
        else:
            answer = "我可以帮你查询商品、尺码、实时库存和退换货政策。请告诉我你想了解哪一项。"
            handoff = True
        if handoff and conversation.status != "handoff":
            create_human_handoff(self.session, HandoffInput(conversation_id=conversation.id, reason="缺少可靠证据或需要人工确认"))
        assistant = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            citations_json=json.dumps([item.model_dump(mode="json") for item in citations], ensure_ascii=False),
        )
        self.session.add(assistant)
        trace.retrieved_context = json.dumps([item.model_dump(mode="json") for item in citations], ensure_ascii=False)
        self.session.commit()
        self.session.refresh(assistant)
        return ChatResult(conversation_id=conversation.id, message_id=assistant.id, answer=answer, intent=intent, citations=citations, handoff=handoff)

    @staticmethod
    def _intent(message: str) -> str:
        if any(word in message for word in ("库存", "有货", "现货")):
            return "inventory"
        if any(word in message for word in ("尺码", "大小", "穿多大")):
            return "size"
        if any(word in message for word in ("退货", "换货", "售后", "政策")):
            return "return_policy"
        return "general"

    def _record_tool(self, trace: AgentTrace, name: str, arguments: object, result: object) -> None:
        self.session.add(ToolCall(trace_id=trace.id, tool_name=name, arguments_json=json.dumps(arguments, ensure_ascii=False, default=str), result_json=json.dumps(result, ensure_ascii=False, default=str), success=True))
