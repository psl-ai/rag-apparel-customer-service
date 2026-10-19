from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.rbac import require_roles
from app.db.session import get_sync_db_session
from app.schemas.common import ApiResponse
from app.schemas.inventory import InventoryAdjustRequest, InventoryResponse
from app.services.inventory import InventoryService


router = APIRouter(prefix="/inventory", tags=["inventory"])
get_inventory_session = get_sync_db_session
session_dependency = Depends(get_inventory_session)
inventory_write_dependency = Depends(require_roles("operator", "admin", "super_admin"))


@router.get("", response_model=ApiResponse[list[InventoryResponse]], dependencies=[inventory_write_dependency])
def list_inventory(request: Request, session: Session = session_dependency) -> ApiResponse[list[InventoryResponse]]:
    from app.models.commerce import Inventory

    rows = session.query(Inventory).order_by(Inventory.available_quantity).all()
    return ApiResponse.ok(
        request_id=request.state.request_id,
        data=[InventoryResponse.model_validate(row) for row in rows],
    )


@router.patch(
    "/{sku_id}",
    response_model=ApiResponse[InventoryResponse],
    dependencies=[inventory_write_dependency],
)
def adjust_inventory(
    sku_id: UUID,
    payload: InventoryAdjustRequest,
    request: Request,
    session: Session = session_dependency,
) -> ApiResponse[InventoryResponse]:
    inventory = InventoryService(session).adjust(sku_id, payload.delta, reason=payload.reason)
    return ApiResponse.ok(request_id=request.state.request_id, data=inventory)
