from enum import StrEnum

from pydantic import BaseModel


class PurchaseStatus(StrEnum):
    completed = "completed"
    process = "process"
    refund = "refund"


class PurchaseInDB(BaseModel):
    id: int
    buyer_id: int
    offer_id: int
    name: str
    description: str
    price: int
    count: int
    status: PurchaseStatus
    created_at: int
    updated_at : int
