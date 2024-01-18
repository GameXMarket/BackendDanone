from typing import List, Optional
from pydantic import BaseModel, model_validator


class ReceiveData(BaseModel):
    subscribers: Optional[List[int]] = []
    unsubscribers: Optional[List[int]] = []

    @model_validator(mode='after')
    def check_not_all_none(self) -> 'ReceiveData':
        if not self.subscribers and not self.unsubscribers:
            raise ValueError("Empty model (not subscribers and not unsubscribers)")
    
        return self
