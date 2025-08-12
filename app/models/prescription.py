from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

class MedicationItem(BaseModel):
    name: str
    dosage: str
    frequency: Optional[str] = None

class ParsedData(BaseModel):
    medications: List[MedicationItem]
    doctor: Optional[str] = None
    date_issued: Optional[str] = None
    patient_name: Optional[str] = None

class Prescription(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    patient_id: str
    physician_id: str
    prescription_number: str
    priority: str
    notes: Optional[str] = None
    image_path: Optional[str] = None
    ocr_raw: Optional[str] = None
    parsed_data: ParsedData
    status: str = "pending"
    pharmacy_id: Optional[str] = None  # Multi-tenancy support
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source: str

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        validate_by_name = True