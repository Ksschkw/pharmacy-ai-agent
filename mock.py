from app.services.database import get_db
from app.services.auth import hash_password
from datetime import datetime
import pytz

db = get_db()
# Seed pharmacy
pharmacy = {
    "pharmacy_id": "pharmacy_001",
    "name": "Test Pharmacy",
    "email": "test@pharmacy.com",
    "address": "123 Lagos St",
    "password_hash": hash_password("securepassword123"),
    "created_at": datetime.now(pytz.UTC)
}
db.pharmacies.insert_one(pharmacy)
print("Inserted pharmacy ID: pharmacy_001")

# Seed inventory item
item = {
    "name": "Paracetamol 500mg",
    "description": "Pain reliever",
    "quantity": 100,
    "unit_cost": 0.1,
    "selling_price": 0.2,
    "batch_number": "BATCH123",
    "expiration_date": datetime(2026, 12, 31, tzinfo=pytz.UTC),
    "storage_location": "Shelf A1",
    "reorder_level": 20,
    "daily_usage_rate": 5.0,
    "pharmacy_id": "pharmacy_001",
    "created_at": datetime.now(pytz.UTC)
}
result = db.inventory.insert_one(item)
print(f"Inserted item ID: {str(result.inserted_id)}")