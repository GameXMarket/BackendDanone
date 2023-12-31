from pydantic import BaseModel


class BaseCategory(BaseModel):
    name: str


class CategoryInDB(BaseCategory):
    parrent_id: int | None
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
