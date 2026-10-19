from uuid import UUID

from sqlalchemy import Boolean, Column, ForeignKey, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampedUuidModel


user_roles = Table(
    "user_roles",
    TimestampedUuidModel.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    TimestampedUuidModel.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Role(TimestampedUuidModel):
    __tablename__ = "roles"
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)


class Permission(TimestampedUuidModel):
    __tablename__ = "permissions"
    code: Mapped[str] = mapped_column(String(128), unique=True, index=True)


class User(TimestampedUuidModel):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_blacklisted: Mapped[bool] = mapped_column(Boolean, default=False)


class UserAddress(TimestampedUuidModel):
    __tablename__ = "user_addresses"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    recipient_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(32))
    province: Mapped[str] = mapped_column(String(64))
    city: Mapped[str] = mapped_column(String(64))
    district: Mapped[str] = mapped_column(String(64))
    detail: Mapped[str] = mapped_column(String(255))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


class UserPreference(TimestampedUuidModel):
    __tablename__ = "user_preferences"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_preferences_user_id"),)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    body_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    style_preferences: Mapped[str | None] = mapped_column(Text, nullable=True)
