from pydantic import BaseModel


class BaseCategory(BaseModel):
    name: str
    is_last: bool = False


class CategoryInDB(BaseCategory):
    id: int
    parrent_id: int | None
    author_id: int | None
    created_at: int
    updated_at: int


class ToJsonCategory(BaseCategory):
    id: int


class CategoryCreate(BaseCategory):
    pass


class SubcategoryCreate(BaseCategory):
    pass


class CategoryUpdate(BaseCategory):
    pass


class CategoryInfo(BaseModel):
    detail: str


class CategoryError(CategoryInfo):
    pass
