from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.rbac import current_claims
from app.db.session import get_sync_db_session
from app.schemas.common import ApiResponse
from app.schemas.auth import UserResponse
from app.schemas.profile import AddressCreate, PreferenceUpdate, ProfileUpdate
from app.models.user import User
from app.services.profile import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


def uid(claims: dict[str, object]) -> UUID:
    return UUID(str(claims["sub"]))


@router.get("", response_model=ApiResponse[UserResponse])
def profile(request: Request, claims: dict[str, object] = Depends(current_claims), session: Session = Depends(get_sync_db_session)) -> ApiResponse[UserResponse]:
    user = session.get(User, uid(claims))
    if user is None:
        from app.core.errors import AppError
        raise AppError("USER_NOT_FOUND", "用户不存在", 404)
    return ApiResponse.ok(request_id=request.state.request_id, data=UserResponse.model_validate(user))


@router.patch("", response_model=ApiResponse[UserResponse])
def update_profile(payload: ProfileUpdate, request: Request, claims: dict[str, object] = Depends(current_claims), session: Session = Depends(get_sync_db_session)) -> ApiResponse[UserResponse]:
    user = ProfileService(session).update_user(uid(claims), payload.model_dump())
    return ApiResponse.ok(request_id=request.state.request_id, data=UserResponse.model_validate(user))


@router.get("/addresses", response_model=ApiResponse[list[dict[str, object]]])
def list_addresses(request: Request, claims: dict[str, object] = Depends(current_claims), session: Session = Depends(get_sync_db_session)) -> ApiResponse[list[dict[str, object]]]:
    rows = ProfileService(session).list_addresses(uid(claims))
    return ApiResponse.ok(request_id=request.state.request_id, data=[{"id": row.id, "recipient_name": row.recipient_name, "phone": row.phone, "province": row.province, "city": row.city, "district": row.district, "detail": row.detail, "is_default": row.is_default} for row in rows])


@router.post("/addresses", response_model=ApiResponse[dict[str, object]], status_code=201)
def create_address(payload: AddressCreate, request: Request, claims: dict[str, object] = Depends(current_claims), session: Session = Depends(get_sync_db_session)) -> ApiResponse[dict[str, object]]:
    row = ProfileService(session).create_address(uid(claims), payload.model_dump())
    return ApiResponse.ok(request_id=request.state.request_id, data={"id": row.id, "detail": row.detail, "is_default": row.is_default})


@router.delete("/addresses/{address_id}", response_model=ApiResponse[dict[str, str]])
def delete_address(address_id: UUID, request: Request, claims: dict[str, object] = Depends(current_claims), session: Session = Depends(get_sync_db_session)) -> ApiResponse[dict[str, str]]:
    ProfileService(session).delete_address(uid(claims), address_id)
    return ApiResponse.ok(request_id=request.state.request_id, data={"id": str(address_id), "status": "deleted"})


@router.put("/preferences", response_model=ApiResponse[dict[str, object]])
def update_preferences(payload: PreferenceUpdate, request: Request, claims: dict[str, object] = Depends(current_claims), session: Session = Depends(get_sync_db_session)) -> ApiResponse[dict[str, object]]:
    data = ProfileService(session).upsert_preferences(uid(claims), payload.model_dump(exclude_none=True))
    return ApiResponse.ok(request_id=request.state.request_id, data=data)
