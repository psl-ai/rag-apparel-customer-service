from uuid import UUID

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    content: str | None = Field(default=None, max_length=2000)


class FavoriteResponse(BaseModel):
    product_id: UUID
    favorited: bool
