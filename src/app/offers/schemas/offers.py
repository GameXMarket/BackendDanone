from enum import Enum

from pydantic import Field, BaseModel


# Предварительные версии для тестов


class OfferStatusEnum(str, Enum):
    active: str = "active"
    hidden: str = "hidden"
    deleted: str = "deleted"


class OfferMiniBase(BaseModel):
    attachment_id: int | None = None
    name: str = Field(examples=["Offer name"])
    description: str = Field(examples=["Offer description"])


class OfferMini(OfferMiniBase):
    id: int


class OfferBase(OfferMiniBase):
    price: int = Field(examples=[1000], gt=0, lt=100000)
    category_id: int | None = None
    count: int = Field(examples=[1], gt=0, lt=100000)


class OfferPreDB(OfferBase):
    id: int
    user_id: int
    status: OfferStatusEnum = OfferStatusEnum.active.value
    created_at: int
    updated_at: int
    upped_at: int


class CreateOffer(OfferBase):
    pass


class UpdateOffer(OfferBase):
    pass


class OfferInfo(BaseModel):
    detail: str


class OfferError(OfferInfo):
    pass
