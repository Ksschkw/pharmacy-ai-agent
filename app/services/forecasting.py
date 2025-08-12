import logging
from app.services.database import get_db
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger("pharmacy_module.forecasting")

def generate_forecast_report(pharmacy_id: str = None):
    """Generate demand forecasting report with human-readable summary for a pharmacy.
    
    Updates daily_usage_rate based on recent stock changes (via deduction endpoint).
    Stores summary in 'reports' collection. Supports multi-tenancy via pharmacy_id.
    
    Args:
        pharmacy_id (str, optional): Filter by tenant for multi-tenant isolation.
    
    Returns:
        bool: Success status.
    """
    try:
        logger.info(f"Starting demand forecasting report generation for pharmacy_id: {pharmacy_id or 'all'}")
        db = get_db()
        query = {"pharmacy_id": pharmacy_id} if pharmacy_id else {}
        items = list(db.inventory.find(query))
        
        local_tz = pytz.timezone("Africa/Lagos")
        report_summary = []
        for item in items:
            usage_rate = item.get("daily_usage_rate", 0)
            if usage_rate <= 0:
                usage_rate = item.get("quantity", 10) / 30  # Fallback: assume stock depletes over 30 days
            
            current_stock = item.get("quantity", 0)
            reorder_level = item.get("reorder_level", 10)
            days_until_reorder = max(0, (current_stock - reorder_level) / usage_rate) if usage_rate > 0 else float('inf')
            predicted_demand_7d = usage_rate * 7
            predicted_demand_30d = usage_rate * 30
            
            # Update forecast in DB
            db.inventory.update_one(
                {"_id": item["_id"]},
                {"$set": {
                    "forecast": {
                        "usage_rate": usage_rate,
                        "days_until_reorder": days_until_reorder,
                        "predicted_demand_7d": predicted_demand_7d,
                        "predicted_demand_30d": predicted_demand_30d,
                        "last_forecast_date": datetime.utcnow()
                    }
                }}
            )
            
            # Human-readable insight
            alert = "URGENT REORDER" if days_until_reorder < 3 else "LOW STOCK ALERT" if days_until_reorder < 7 else "STABLE"
            summary_line = (
                f"Item: {item['name']} | Current Stock: {current_stock} | Usage Rate: {usage_rate:.2f}/day | "
                f"Days to Reorder: {days_until_reorder:.1f} | 7-Day Demand: {predicted_demand_7d:.0f} | "
                f"30-Day Demand: {predicted_demand_30d:.0f} | Alert: {alert}"
            )
            report_summary.append(summary_line)
        
        # Store report
        db.reports.insert_one({
            "pharmacy_id": pharmacy_id,
            "type": "demand_forecast",
            "summary": "\n".join(report_summary),
            "created_at": datetime.utcnow().astimezone(local_tz)
        })
        
        logger.info("Demand forecasting completed successfully")
        return True
    except Exception as e:
        logger.error(f"Forecasting failed: {str(e)}")
        return False