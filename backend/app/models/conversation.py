from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampedUuidModel


class Conversation(TimestampedUuidModel):
    __tablename__ = "conversations"
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Message(TimestampedUuidModel):
    __tablename__ = "messages"
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(32), index=True)
    content: Mapped[str] = mapped_column(Text)
    citations_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class AgentTrace(TimestampedUuidModel):
    __tablename__ = "agent_traces"
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    message_id: Mapped[UUID | None] = mapped_column(ForeignKey("messages.id"), nullable=True)
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    retrieved_context: Mapped[str | None] = mapped_column(Text, nullable=True)


class ToolCall(TimestampedUuidModel):
    __tablename__ = "tool_calls"
    trace_id: Mapped[UUID] = mapped_column(ForeignKey("agent_traces.id", ondelete="CASCADE"), index=True)
    tool_name: Mapped[str] = mapped_column(String(100), index=True)
    arguments_json: Mapped[str] = mapped_column(Text)
    result_json: Mapped[str] = mapped_column(Text)
    success: Mapped[bool] = mapped_column(Boolean, default=True)


class CustomerFeedback(TimestampedUuidModel):
    __tablename__ = "customer_feedback"
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    message_id: Mapped[UUID | None] = mapped_column(ForeignKey("messages.id"), nullable=True)
    rating: Mapped[int] = mapped_column()
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)


class HumanHandoff(TimestampedUuidModel):
    __tablename__ = "human_handoffs"
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    reason: Mapped[str] = mapped_column(Text)
    assigned_to_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
