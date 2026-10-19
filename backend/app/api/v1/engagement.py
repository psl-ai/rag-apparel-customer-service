from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.rbac import current_claims
from app.db.session import get_sync_db_session
from app.schemas.common import ApiResponse
from app.schemas.engagement import FavoriteResponse, ReviewCreate
from app.services.engagement import EngagementService

router = APIRouter(tags=["engagement"])


def uid(claims: dict[str, object]) -> UUID:
    return UUID(str(claims["sub"]))


@router.post("/products/{product_id}/favorite", response_model=ApiResponse[FavoriteResponse])
def toggle_favorite(product_id: UUID, request: Request, claims: dict[str, object] = Depends(current_claims), session: Session = Depends(get_sync_db_session)) -> ApiResponse[FavoriteResponse]:
    state = EngagementService(session).toggle_favorite(uid(claims), product_id)
    return ApiResponse.ok(request_id=request.state.request_id, data=FavoriteResponse(product_id=product_id, favorited=state))


@router.get("/profile/favorites", response_model=ApiResponse[list[dict[str, object]]])
def favorites(request: Request, claims: dict[str, object] = Depends(current_claims), session: Session = Depends(get_sync_db_session)) -> ApiResponse[list[dict[str, object]]]:
    rows = EngagementService(session).list_favorites(uid(claims))
    return ApiResponse.ok(request_id=request.state.request_id, data=[{"id": row.id, "name": row.name, "slug": row.slug} for row in rows])


@router.post("/products/{product_id}/reviews", response_model=ApiResponse[dict[str, object]], status_code=201)
def create_review(product_id: UUID, payload: ReviewCreate, request: Request, claims: dict[str, object] = Depends(current_claims), session: Session = Depends(get_sync_db_session)) -> ApiResponse[dict[str, object]]:
    row = EngagementService(session).create_review(uid(claims), product_id, payload.rating, payload.content)
    return ApiResponse.ok(request_id=request.state.request_id, data={"id": row.id, "rating": row.rating, "content": row.content})


@router.get("/products/{product_id}/reviews", response_model=ApiResponse[list[dict[str, object]]])
def reviews(product_id: UUID, request: Request, session: Session = Depends(get_sync_db_session)) -> ApiResponse[list[dict[str, object]]]:
    rows = EngagementService(session).list_reviews(product_id)
    return ApiResponse.ok(request_id=request.state.request_id, data=[{"id": row.id, "rating": row.rating, "content": row.content, "created_at": row.created_at} for row in rows])
