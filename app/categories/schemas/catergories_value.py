from pydantic import BaseModel


class BaseValue(BaseModel):
    value: str


class ValueInDB(BaseValue):
    id: int
    author_id: int    
    carcass_id: int
    created_at: int
    updated_at: int
        

class ValueCreate(BaseValue):
    pass


class ValueRead(BaseValue):
    pass


class ValueUpdate(BaseValue):
    pass
