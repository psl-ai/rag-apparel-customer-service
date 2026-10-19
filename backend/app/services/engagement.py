from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.catalog import Product
from app.models.commerce import ProductFavorite, ProductReview


class EngagementService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def toggle_favorite(self, user_id: UUID, product_id: UUID) -> bool:
        product = self.session.scalar(select(Product).where(Product.id == product_id, Product.status == "published"))
        if product is None:
            raise AppError("PRODUCT_NOT_FOUND", "商品不存在", 404)
        favorite = self.session.scalar(select(ProductFavorite).where(ProductFavorite.user_id == user_id, ProductFavorite.product_id == product_id))
        if favorite:
            self.session.delete(favorite); self.session.commit(); return False
        self.session.add(ProductFavorite(user_id=user_id, product_id=product_id)); self.session.commit(); return True

    def list_favorites(self, user_id: UUID) -> list[Product]:
        return list(self.session.scalars(select(Product).join(ProductFavorite, ProductFavorite.product_id == Product.id).where(ProductFavorite.user_id == user_id, Product.status == "published")))

    def create_review(self, user_id: UUID, product_id: UUID, rating: int, content: str | None = None) -> ProductReview:
        product = self.session.scalar(select(Product).where(Product.id == product_id, Product.status == "published"))
        if product is None:
            raise AppError("PRODUCT_NOT_FOUND", "商品不存在", 404)
        review = ProductReview(user_id=user_id, product_id=product_id, rating=rating, content=content)
        self.session.add(review); self.session.commit(); self.session.refresh(review)
        return review

    def list_reviews(self, product_id: UUID) -> list[ProductReview]:
        return list(self.session.scalars(select(ProductReview).where(ProductReview.product_id == product_id).order_by(ProductReview.created_at.desc())))
