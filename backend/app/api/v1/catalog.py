from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rbac import require_roles
from app.db.session import get_sync_db_session
from app.models.catalog import Color, ProductCategory, Size
from app.schemas.catalog import ProductCreate, ProductListResponse, ProductResponse, ProductUpdate, SkuCreate
from app.schemas.common import ApiResponse
from app.services.catalog import CatalogService


router = APIRouter(tags=["catalog"])
get_catalog_session = get_sync_db_session
session_dependency = Depends(get_catalog_session)
catalog_write_dependency = Depends(require_roles("operator", "admin", "super_admin"))


@router.get("/categories", response_model=ApiResponse[list[dict[str, str]]])
def categories(request: Request, session: Session = session_dependency) -> ApiResponse[list[dict[str, str]]]:
    rows = session.scalars(select(ProductCategory).order_by(ProductCategory.name)).all()
    data = [{"id": str(row.id), "name": row.name, "slug": row.slug} for row in rows]
    return ApiResponse.ok(request_id=request.state.request_id, data=data)


@router.get("/colors", response_model=ApiResponse[list[dict[str, str]]])
def colors(request: Request, session: Session = session_dependency) -> ApiResponse[list[dict[str, str]]]:
    rows = session.scalars(select(Color).order_by(Color.name)).all()
    data = [{"id": str(row.id), "name": row.name, "hex_value": row.hex_value} for row in rows]
    return ApiResponse.ok(request_id=request.state.request_id, data=data)


@router.get("/sizes", response_model=ApiResponse[list[dict[str, object]]])
def sizes(request: Request, session: Session = session_dependency) -> ApiResponse[list[dict[str, object]]]:
    rows = session.scalars(select(Size).order_by(Size.sort_order, Size.name)).all()
    data = [{"id": str(row.id), "name": row.name, "sort_order": row.sort_order} for row in rows]
    return ApiResponse.ok(request_id=request.state.request_id, data=data)


@router.get("/products", response_model=ApiResponse[ProductListResponse])
def list_products(
    request: Request,
    search: str | None = Query(default=None, max_length=100),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = session_dependency,
) -> ApiResponse[ProductListResponse]:
    service = CatalogService(session)
    items = service.list_products(search=search, skip=skip, limit=limit)
    return ApiResponse.ok(
        request_id=request.state.request_id,
        data=ProductListResponse(items=items, total=service.count_published(), skip=skip, limit=limit),
    )


@router.get("/products/{product_id}", response_model=ApiResponse[ProductResponse])
def get_product(product_id: UUID, request: Request, session: Session = session_dependency) -> ApiResponse[ProductResponse]:
    return ApiResponse.ok(
        request_id=request.state.request_id,
        data=CatalogService(session).get_product(product_id),
    )


@router.post(
    "/products",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiResponse[ProductResponse],
    dependencies=[catalog_write_dependency],
)
def create_product(
    payload: ProductCreate,
    request: Request,
    session: Session = session_dependency,
) -> ApiResponse[ProductResponse]:
    product = CatalogService(session).create_product(**payload.model_dump())
    return ApiResponse.ok(request_id=request.state.request_id, data=product)


@router.patch(
    "/products/{product_id}",
    response_model=ApiResponse[ProductResponse],
    dependencies=[catalog_write_dependency],
)
def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    request: Request,
    session: Session = session_dependency,
) -> ApiResponse[ProductResponse]:
    product = CatalogService(session).update_product(product_id, payload)
    return ApiResponse.ok(request_id=request.state.request_id, data=product)


@router.post(
    "/products/{product_id}/publish",
    response_model=ApiResponse[ProductResponse],
    dependencies=[catalog_write_dependency],
)
def publish_product(
    product_id: UUID,
    request: Request,
    session: Session = session_dependency,
) -> ApiResponse[ProductResponse]:
    product = CatalogService(session).publish_product(product_id)
    return ApiResponse.ok(request_id=request.state.request_id, data=product)


@router.get("/products/{product_id}/skus", response_model=ApiResponse[list[dict[str, object]]])
def list_skus(
    product_id: UUID,
    request: Request,
    session: Session = session_dependency,
) -> ApiResponse[list[dict[str, object]]]:
    skus = CatalogService(session).list_skus(product_id)
    data = [
        {
            "id": sku.id,
            "code": sku.code,
            "color_id": sku.color_id,
            "size_id": sku.size_id,
            "sale_price": sku.sale_price,
            "original_price": sku.original_price,
            "status": sku.status,
        }
        for sku in skus
    ]
    return ApiResponse.ok(request_id=request.state.request_id, data=data)


@router.post(
    "/products/{product_id}/skus",
    response_model=ApiResponse[dict[str, object]],
    status_code=status.HTTP_201_CREATED,
    dependencies=[catalog_write_dependency],
)
def create_sku(
    product_id: UUID,
    payload: SkuCreate,
    request: Request,
    session: Session = session_dependency,
) -> ApiResponse[dict[str, object]]:
    sku = CatalogService(session).create_sku(product_id, **payload.model_dump())
    data = {
        "id": sku.id,
        "product_id": sku.product_id,
        "code": sku.code,
        "sale_price": sku.sale_price,
        "status": sku.status,
    }
    return ApiResponse.ok(request_id=request.state.request_id, data=data)
