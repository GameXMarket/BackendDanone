from pydantic import BaseModel, ConfigDict


# я хз вообще как разбить схемы для деливери, модель мелкая
class Delivery(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    offer_id: int
    value: int

