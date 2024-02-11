from pydantic import BaseModel


class BaseCategoryCarcass(BaseModel):
    select_name: str
    in_offer_name: str
    admin_comment: str
    is_root: bool = False
    is_last: bool = False


class CategoryCarcassInDB(BaseCategoryCarcass):
    id: int
    author_id: int | None
    created_at: int
    updated_at: int


class ToJsonCategoryCarcass(BaseCategoryCarcass):
    id: int


class CategoryCarcassCreate(BaseCategoryCarcass):
    pass


class SubcategoryCarcassCreate(BaseCategoryCarcass):
    pass


class CategoryCarcassUpdate(BaseModel):
    select_name: str
    admin_comment: str
    in_offer_name: str


class CategoryCarcassInfo(BaseModel):
    detail: str


class CategoryCarcassError(CategoryCarcassInfo):
    pass
