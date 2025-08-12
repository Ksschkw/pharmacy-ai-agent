from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Form, Query
from fastapi.responses import StreamingResponse
from bson import ObjectId
from app.services.database import get_db
from app.services.forecasting import generate_forecast_report
from app.models.inventory import InventoryItem as InventoryItemModel
import csv
import io
import logging
from datetime import datetime
import pytz
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

router = APIRouter(tags=["Inventory"])
logger = logging.getLogger("pharmacy_module.inventory")

async def get_current_pharmacy_id(
    pharmacy_id: str = Query(..., description="Pharmacy ID for multi-tenancy"),
    db=Depends(get_db)
):
    """Validate pharmacy_id against the pharmacies collection."""
    pharmacy = db.pharmacies.find_one({"pharmacy_id": pharmacy_id})
    if not pharmacy:
        raise HTTPException(status_code=403, detail="Invalid pharmacy_id")
    return pharmacy_id

@router.post("/inventory", response_model=dict)
async def add_inventory_item(
    item: InventoryItemModel,
    pharmacy_id: str = Depends(get_current_pharmacy_id),
    db=Depends(get_db)
):
    """Add a new inventory item with pharmacy_id for multi-tenancy.
    
    Validates expiration_date and assigns pharmacy_id.
    """
    try:
        item_dict = item.dict()
        if item_dict["expiration_date"] <= datetime.now(pytz.UTC):
            raise HTTPException(status_code=400, detail="Expiration date must be in the future")
        item_dict["pharmacy_id"] = pharmacy_id
        item_dict["created_at"] = datetime.now(pytz.UTC)
        result = db.inventory.insert_one(item_dict)
        return {"message": "Inventory item added", "item_id": str(result.inserted_id)}
    except Exception as e:
        logger.error(f"Error adding inventory item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory", response_model=list)
async def get_inventory(
    pharmacy_id: str = Depends(get_current_pharmacy_id),
    db=Depends(get_db)
):
    """Retrieve inventory items filtered by pharmacy_id."""
    try:
        items = list(db.inventory.find({"pharmacy_id": pharmacy_id}))
        for item in items:
            item["_id"] = str(item["_id"])
        return items
    except Exception as e:
        logger.error(f"Error fetching inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inventory/deduct", response_model=dict)
async def deduct_inventory(
    item_id: str = Form(...),
    quantity: float = Form(..., gt=0),
    pharmacy_id: str = Depends(get_current_pharmacy_id),
    db=Depends(get_db)
):
    """Deduct stock from inventory and update daily_usage_rate for forecasting.
    
    Ensures item belongs to the pharmacy.
    """
    try:
        item = db.inventory.find_one({"_id": ObjectId(item_id), "pharmacy_id": pharmacy_id})
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        new_quantity = item["quantity"] - quantity
        if new_quantity < 0:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        
        usage_rate = item.get("daily_usage_rate", 0)
        usage_rate = (usage_rate * 0.7 + (quantity / 7) * 0.3)
        db.inventory.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": {"quantity": new_quantity, "daily_usage_rate": usage_rate}}
        )
        return {"message": "Stock deducted", "item_id": item_id}
    except Exception as e:
        logger.error(f"Stock deduction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inventory/report", response_model=dict)
async def generate_inventory_report(
    background_tasks: BackgroundTasks,
    pharmacy_id: str = Depends(get_current_pharmacy_id)
):
    """Trigger inventory forecasting report generation asynchronously."""
    try:
        background_tasks.add_task(generate_forecast_report, pharmacy_id=pharmacy_id)
        return {"message": "Report generation started", "status": "processing"}
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory/report/latest", response_model=dict)
async def get_latest_report(
    pharmacy_id: str = Depends(get_current_pharmacy_id),
    db=Depends(get_db)
):
    """Retrieve the latest demand forecasting report for the pharmacy as JSON."""
    try:
        report = db.reports.find_one(
            {"pharmacy_id": pharmacy_id, "type": "demand_forecast"},
            sort=[("created_at", -1)]
        )
        if not report:
            raise HTTPException(status_code=404, detail="No report found")
        report["_id"] = str(report["_id"])
        report["created_at"] = report["created_at"].astimezone(pytz.timezone("Africa/Lagos")).strftime("%Y-%m-%d %H:%M:%S")
        return {"report": report}
    except Exception as e:
        logger.error(f"Error fetching report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory/report/download", response_model=None)
async def download_inventory_report(
    pharmacy_id: str = Depends(get_current_pharmacy_id),
    db=Depends(get_db)
):
    """Download the latest demand forecasting report as a PDF."""
    try:
        report = db.reports.find_one(
            {"pharmacy_id": pharmacy_id, "type": "demand_forecast"},
            sort=[("created_at", -1)]
        )
        if not report:
            raise HTTPException(status_code=404, detail="No report found")
        
        # Generate PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Add title and metadata
        elements.append(Paragraph(f"Demand Forecasting Report - {pharmacy_id}", styles['Title']))
        created_at = report["created_at"].astimezone(pytz.timezone("Africa/Lagos")).strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(f"Generated: {created_at}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Add report summary
        elements.append(Paragraph("Inventory Summary:", styles['Heading2']))
        for line in report["summary"].split("\n"):
            elements.append(Paragraph(line, styles['Normal']))
            elements.append(Spacer(1, 6))
        
        doc.build(elements)
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=forecast_report_{pharmacy_id}.pdf"}
        )
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory/export", response_model=dict)
async def export_inventory(
    pharmacy_id: str = Depends(get_current_pharmacy_id),
    db=Depends(get_db)
):
    """Export inventory data as CSV with Africa/Lagos timezone."""
    try:
        items = list(db.inventory.find(
            {"pharmacy_id": pharmacy_id},
            {"_id": 0, "forecast": 0, "pharmacy_id": 0}
        ))
        
        output = io.StringIO()
        fieldnames = [
            "name", "description", "quantity", "unit_cost", "selling_price",
            "batch_number", "expiration_date", "storage_location", "reorder_level",
            "daily_usage_rate", "created_at"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        local_tz = pytz.timezone("Africa/Lagos")
        for item in items:
            if "expiration_date" in item and item["expiration_date"]:
                item["expiration_date"] = item["expiration_date"].astimezone(local_tz).strftime("%Y-%m-%d")
            if "created_at" in item and item["created_at"]:
                item["created_at"] = item["created_at"].astimezone(local_tz).strftime("%Y-%m-%d")
            writer.writerow(item)
        
        return {
            "filename": f"inventory_report_{pharmacy_id}.csv",
            "content": output.getvalue(),
            "media_type": "text/csv"
        }
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))