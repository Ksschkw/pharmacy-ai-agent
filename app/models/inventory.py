from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class InventoryItem(BaseModel):
    name: str
    description: Optional[str] = None
    quantity: int
    unit_cost: float
    selling_price: float
    batch_number: str
    expiration_date: datetime
    storage_location: str
    reorder_level: int = Field(default=10, gt=0)  # Add validation
    daily_usage_rate: float = Field(default=0.0)  # Track actual usage
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}