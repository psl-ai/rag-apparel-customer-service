from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)


class AddressCreate(BaseModel):
    recipient_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=6, max_length=32)
    province: str = Field(min_length=1, max_length=64)
    city: str = Field(min_length=1, max_length=64)
    district: str = Field(min_length=1, max_length=64)
    detail: str = Field(min_length=1, max_length=255)
    is_default: bool = False


class PreferenceUpdate(BaseModel):
    body_data: dict[str, object] | None = None
    style_preferences: list[str] | None = None
