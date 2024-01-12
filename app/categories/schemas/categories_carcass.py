from pydantic import BaseModel


class BaseCategoryCarcass(BaseModel):
    name: str
    is_last: bool = False


class CategoryCarcassInDB(BaseCategoryCarcass):
    id: int
    parrent_id: int | None
    author_id: int | None
    created_at: int
    updated_at: int


class ToJsonCategoryCarcass(BaseCategoryCarcass):
    id: int


class CategoryCarcassCreate(BaseCategoryCarcass):
    pass


class SubcategoryCarcassCreate(BaseCategoryCarcass):
    pass


class CategoryCarcassUpdate(BaseCategoryCarcass):
    pass


class CategoryCarcassInfo(BaseModel):
    detail: str


class CategoryCarcassError(CategoryCarcassInfo):
    pass
