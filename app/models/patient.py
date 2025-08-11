from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

class Patient(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    patient_id: str
    first_name: str
    last_name: str
    dob: str
    phone: str
    email: str
    address: str
    prescription_ids: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        validate_by_name = True