from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
import pytz

class Pharmacy(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    pharmacy_id: str = Field(min_length=1)  # Unique identifier
    name: str = Field(min_length=1)
    email: str
    address: str
    password_hash: str = Field(min_length=1)  # Hashed password for auth
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}