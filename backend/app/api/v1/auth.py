from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_sync_db_session
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from app.schemas.common import ApiResponse
from app.services.auth import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])
get_auth_session = get_sync_db_session
session_dependency = Depends(get_auth_session)


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[UserResponse])
def register(
    payload: RegisterRequest,
    request: Request,
    session: Session = session_dependency,
) -> ApiResponse[UserResponse]:
    user = AuthService(session).register(payload.email, payload.password, payload.display_name)
    return ApiResponse.ok(request_id=request.state.request_id, data=user)


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(
    payload: LoginRequest,
    request: Request,
    session: Session = session_dependency,
) -> ApiResponse[TokenResponse]:
    tokens = AuthService(session).login(payload.email, payload.password)
    return ApiResponse.ok(request_id=request.state.request_id, data=tokens)


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
def refresh(
    payload: RefreshRequest,
    request: Request,
    session: Session = session_dependency,
) -> ApiResponse[TokenResponse]:
    tokens = AuthService(session).refresh(payload.refresh_token)
    return ApiResponse.ok(request_id=request.state.request_id, data=tokens)
