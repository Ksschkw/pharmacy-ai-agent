from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class InventoryItem(BaseModel):
    name: str = Field(min_length=1)  # Ensure non-empty name
    description: Optional[str] = None
    quantity: int = Field(ge=0)  # Non-negative stock
    unit_cost: float = Field(gt=0)  # Positive cost
    selling_price: float = Field(gt=0)  # Positive price
    batch_number: str = Field(min_length=1)
    expiration_date: datetime  # Remove gt constraint; validate in endpoint
    storage_location: str = Field(min_length=1)
    reorder_level: int = Field(default=10, gt=0)  # Positive reorder level
    daily_usage_rate: float = Field(default=0.0, ge=0)  # Track usage
    pharmacy_id: Optional[str] = None  # Multi-tenancy support
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}