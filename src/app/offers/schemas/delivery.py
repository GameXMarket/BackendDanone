from pydantic import BaseModel


# я хз вообще как разбить схемы для деливери, модель мелкая
class Delivery(BaseModel):
    offer_id: int
    value: int
