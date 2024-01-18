from typing import List, Optional
from pydantic import BaseModel, validator

class ReceiveData(BaseModel):
    subscribers: Optional[List[int]] = None
    unsubscribers: Optional[List[int]] = None

