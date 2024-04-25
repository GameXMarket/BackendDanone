from enum import Enum

from pydantic import Field, BaseModel


# Предварительные версии для тестов


class OfferStatusEnum(str, Enum):
    active: str = "active"
    hidden: str = "hidden"
    deleted: str = "deleted"


class CategoryValueIdsBase(BaseModel):
    category_value_ids: list[int] | None = None


class OfferMiniBase(BaseModel):
    name: str = Field(examples=["Offer name"])
    description: str = Field(examples=["Offer description"])


class OfferMini(OfferMiniBase):
    id: int


class OfferBase(OfferMiniBase):
    price: int = Field(examples=[1000], gt=0, lt=100000)
    count: int | None = Field(examples=[None], gt=-1, lt=100000)
    category_value_ids: list[int] | None = None


class OfferPreDB(OfferBase):
    id: int
    user_id: int
    status: OfferStatusEnum = OfferStatusEnum.active.value
    created_at: int
    updated_at: int
    upped_at: int


class CreateOffer(OfferBase):
    category_value_ids: list[int]


class UpdateOffer(OfferBase):
    pass


class OfferInfo(BaseModel):
    detail: str


class OfferError(OfferInfo):
    pass
