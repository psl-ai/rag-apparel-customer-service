from fastapi import APIRouter, Request

from app.schemas.common import ApiResponse, HealthStatus


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=ApiResponse[HealthStatus])
async def live_health(request: Request) -> ApiResponse[HealthStatus]:
    return ApiResponse.ok(
        request_id=request.state.request_id,
        data=HealthStatus(status="ok"),
    )
