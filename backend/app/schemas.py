from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Helper to allow conversion from ObjectId to string
class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, info):
        if not isinstance(v, (str, bytes)) and not hasattr(v, 'is_valid'):
            raise TypeError('ObjectId required')
        return str(v)

class Pricing(BaseModel):
    outcomeYesPrice: Optional[float] = 0
    outcomeNoPrice: Optional[float] = 0
    volume: Optional[float] = 0
    liquidity: Optional[float] = 0
    spread: Optional[float] = 0
    # Add other pricing fields as needed

class Market(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    marketId: str
    question: str
    slug: str
    category: Optional[str] = None
    active: bool
    pricing: Pricing

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        populate_by_name = True
