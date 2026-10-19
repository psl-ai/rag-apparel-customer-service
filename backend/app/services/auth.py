from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.models.user import Role, User, user_roles
from app.schemas.auth import TokenResponse, UserResponse


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def register(self, email: str, password: str, display_name: str) -> UserResponse:
        normalized_email = email.strip().lower()
        existing = self.session.scalar(select(User).where(User.email == normalized_email))
        if existing is not None:
            raise AppError("AUTH_EMAIL_EXISTS", "邮箱已注册", 409)
        user = User(
            email=normalized_email,
            password_hash=hash_password(password),
            display_name=display_name.strip(),
        )
        self.session.add(user)
        self.session.commit()
        try:
            customer_role = self.session.scalar(select(Role).where(Role.name == "customer"))
            if customer_role is not None:
                self.session.execute(user_roles.insert().values(user_id=user.id, role_id=customer_role.id))
                self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
        self.session.refresh(user)
        return UserResponse.model_validate(user)

    def login(self, email: str, password: str) -> TokenResponse:
        normalized_email = email.strip().lower()
        user = self.session.scalar(select(User).where(User.email == normalized_email))
        if user is None or not verify_password(password, user.password_hash):
            raise AppError("AUTH_INVALID_CREDENTIALS", "邮箱或密码错误", 401)
        if not user.is_active:
            raise AppError("AUTH_INACTIVE", "账户已停用", 403)
        role = self._role_for_user(user.id)
        return TokenResponse(
            access_token=create_access_token(str(user.id), role),
            refresh_token=create_refresh_token(str(user.id), role),
            user=UserResponse.model_validate(user),
        )

    def _role_for_user(self, user_id) -> str:
        priority = {"super_admin": 4, "admin": 3, "operator": 2, "customer": 1}
        try:
            roles = list(self.session.scalars(select(Role.name).join(user_roles, Role.id == user_roles.c.role_id).where(user_roles.c.user_id == user_id)))
        except SQLAlchemyError:
            self.session.rollback()
            return "customer"
        return max(roles, key=lambda item: priority.get(item, 0), default="customer")

    def refresh(self, refresh_token: str) -> TokenResponse:
        claims = decode_token(refresh_token)
        if claims.get("type") != "refresh":
            raise AppError("AUTH_INVALID_REFRESH", "刷新令牌无效", 401)
        user = self.session.get(User, claims.get("sub"))
        if user is None or not user.is_active:
            raise AppError("AUTH_INVALID_REFRESH", "刷新令牌无效", 401)
        role = self._role_for_user(user.id)
        return TokenResponse(
            access_token=create_access_token(str(user.id), role),
            refresh_token=create_refresh_token(str(user.id), role),
            user=UserResponse.model_validate(user),
        )
