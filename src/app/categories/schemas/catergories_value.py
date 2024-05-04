from pydantic import BaseModel


class BaseValue(BaseModel):
    value: str
    next_carcass_id: int | None = None
    is_offer_with_delivery: bool = False

class ValueInDB(BaseValue):
    id: int
    carcass_id: int
    author_id: int
    created_at: int
    updated_at: int
        

class ValueCreate(BaseValue):
    pass


class ValueRead(BaseValue):
    pass


class ValueUpdate(BaseValue):
    pass
