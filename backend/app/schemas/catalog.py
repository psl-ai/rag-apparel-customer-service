from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    category_id: UUID
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    fabric_info: str | None = None
    care_instructions: str | None = None
    status: str = "draft"


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    fabric_info: str | None = None
    care_instructions: str | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category_id: UUID
    name: str
    slug: str
    description: str
    fabric_info: str | None
    care_instructions: str | None
    status: str


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    skip: int
    limit: int


class SkuCreate(BaseModel):
    color_id: UUID
    size_id: UUID
    code: str = Field(min_length=1, max_length=80)
    barcode: str | None = Field(default=None, max_length=80)
    sale_price: float = Field(gt=0)
    original_price: float | None = Field(default=None, gt=0)
    image_key: str | None = None
