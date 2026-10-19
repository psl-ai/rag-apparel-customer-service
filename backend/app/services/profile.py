from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
import json

from app.models.user import User, UserAddress, UserPreference


class ProfileService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_address(self, user_id: UUID, values: dict[str, object]) -> UserAddress:
        if values.get("is_default"):
            for address in self.session.scalars(select(UserAddress).where(UserAddress.user_id == user_id)).all():
                address.is_default = False
        address = UserAddress(user_id=user_id, **values)
        self.session.add(address); self.session.commit(); self.session.refresh(address)
        return address

    def update_user(self, user_id: UUID, values: dict[str, object]) -> User:
        user = self.session.get(User, user_id)
        if user is None:
            raise AppError("USER_NOT_FOUND", "用户不存在", 404)
        if "display_name" in values:
            user.display_name = str(values["display_name"]).strip()
        self.session.commit(); self.session.refresh(user)
        return user

    def upsert_preferences(self, user_id: UUID, values: dict[str, object]) -> dict[str, object]:
        preference = self.session.scalar(select(UserPreference).where(UserPreference.user_id == user_id))
        if preference is None:
            preference = UserPreference(user_id=user_id)
            self.session.add(preference)
        for key in ("body_data", "style_preferences"):
            if key in values:
                setattr(preference, key, json.dumps(values[key], ensure_ascii=False))
        self.session.commit(); self.session.refresh(preference)
        return {"body_data": json.loads(preference.body_data) if preference.body_data else {}, "style_preferences": json.loads(preference.style_preferences) if preference.style_preferences else []}

    def list_addresses(self, user_id: UUID) -> list[UserAddress]:
        return list(self.session.scalars(select(UserAddress).where(UserAddress.user_id == user_id).order_by(UserAddress.is_default.desc(), UserAddress.created_at.desc())))

    def get_address(self, user_id: UUID, address_id: UUID) -> UserAddress:
        address = self.session.scalar(select(UserAddress).where(UserAddress.id == address_id, UserAddress.user_id == user_id))
        if address is None:
            raise AppError("ADDRESS_NOT_FOUND", "收货地址不存在", 404)
        return address

    def delete_address(self, user_id: UUID, address_id: UUID) -> None:
        address = self.get_address(user_id, address_id)
        self.session.delete(address); self.session.commit()
