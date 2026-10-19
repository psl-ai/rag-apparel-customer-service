from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.catalog import Product, ProductSku
from app.schemas.catalog import ProductResponse, ProductUpdate


class CatalogService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_product(self, **values: object) -> ProductResponse:
        product = Product(**values)
        self.session.add(product)
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        self.session.refresh(product)
        return ProductResponse.model_validate(product)

    def list_products(self, *, search: str | None = None, skip: int = 0, limit: int = 20) -> list[ProductResponse]:
        statement = select(Product).where(Product.status == "published")
        if search:
            term = f"%{search.strip()}%"
            statement = statement.where(or_(Product.name.ilike(term), Product.description.ilike(term)))
        products = self.session.scalars(statement.order_by(Product.created_at.desc()).offset(skip).limit(limit)).all()
        return [ProductResponse.model_validate(product) for product in products]

    def get_product(self, product_id: UUID, *, include_unpublished: bool = False) -> ProductResponse:
        product = self.session.get(Product, product_id)
        if product is None or (not include_unpublished and product.status != "published"):
            raise AppError("PRODUCT_NOT_FOUND", "商品不存在", 404)
        return ProductResponse.model_validate(product)

    def update_product(self, product_id: UUID, payload: ProductUpdate) -> ProductResponse:
        product = self.session.get(Product, product_id)
        if product is None:
            raise AppError("PRODUCT_NOT_FOUND", "商品不存在", 404)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        self.session.commit()
        self.session.refresh(product)
        return ProductResponse.model_validate(product)

    def publish_product(self, product_id: UUID) -> ProductResponse:
        product = self.session.get(Product, product_id)
        if product is None:
            raise AppError("PRODUCT_NOT_FOUND", "商品不存在", 404)
        product.status = "published"
        self.session.commit()
        self.session.refresh(product)
        return ProductResponse.model_validate(product)

    def create_sku(self, product_id: UUID, **values: object) -> ProductSku:
        product = self.session.get(Product, product_id)
        if product is None:
            raise AppError("PRODUCT_NOT_FOUND", "商品不存在", 404)
        sku = ProductSku(product_id=product_id, **values)
        self.session.add(sku)
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise AppError("SKU_CODE_EXISTS", "SKU 编码已存在", 409)
        self.session.refresh(sku)
        return sku

    def list_skus(self, product_id: UUID) -> list[ProductSku]:
        return list(self.session.scalars(select(ProductSku).where(ProductSku.product_id == product_id)))

    def count_published(self) -> int:
        return int(self.session.scalar(select(func.count()).select_from(Product).where(Product.status == "published")) or 0)
