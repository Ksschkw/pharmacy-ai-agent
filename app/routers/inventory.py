from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.services.database import get_db
from app.services.forecasting import generate_forecast_report
from app.models.inventory import InventoryItem as InventoryItemModel  # Renamed import
import csv
import io
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger("pharmacy_module.inventory")

@router.post("/inventory", response_model=dict)
async def add_inventory_item(item: InventoryItemModel):  # Use renamed model
    try:
        db = get_db()
        # Add created_at timestamp
        item_dict = item.dict()
        item_dict["created_at"] = datetime.utcnow()
        
        result = db.inventory.insert_one(item_dict)
        return {"message": "Inventory item added", "item_id": str(result.inserted_id)}
    except Exception as e:
        logger.error(f"Error adding inventory item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory", response_model=list)
async def get_inventory():
    try:
        db = get_db()
        items = list(db.inventory.find())
        for item in items:
            item["_id"] = str(item["_id"])
        return items
    except Exception as e:
        logger.error(f"Error fetching inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inventory/report", response_model=dict)
async def generate_inventory_report(background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(generate_forecast_report)
        return {"message": "Report generation started", "status": "processing"}
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory/export", response_model=dict)
async def export_inventory():
    try:
        db = get_db()
        items = list(db.inventory.find({}, {
            "_id": 0,  # Exclude MongoDB ID
            "forecast": 0  # Exclude forecast data
        }))
        
        # Create CSV in memory
        output = io.StringIO()
        fieldnames = [
            "name", "description", "quantity", "unit_cost", "selling_price", 
            "batch_number", "expiration_date", "storage_location", "reorder_level", "created_at"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for item in items:
            # Format dates properly
            if "expiration_date" in item and item["expiration_date"]:
                item["expiration_date"] = item["expiration_date"].strftime("%Y-%m-%d")
            if "created_at" in item and item["created_at"]:
                item["created_at"] = item["created_at"].strftime("%Y-%m-%d")
                
            writer.writerow(item)
        
        return {
            "filename": "inventory_report.csv",
            "content": output.getvalue(),
            "media_type": "text/csv"
        }
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))