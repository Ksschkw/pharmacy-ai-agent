import logging
from app.services.database import get_db
from datetime import datetime, timedelta

logger = logging.getLogger("pharmacy_module.forecasting")

def generate_forecast_report():
    try:
        logger.info("Starting demand forecasting report generation")
        db = get_db()
        
        # Get all inventory items
        items = list(db.inventory.find())
        
        for item in items:
            # Get actual usage from history if available
            usage_rate = item.get("daily_usage_rate", 0)
            
            # Fallback calculation if no usage data
            if usage_rate <= 0:
                # Calculate based on current stock and default period
                usage_rate = item.get("quantity", 10) / 30  # Default to 10 if missing
            
            # Calculate days until reorder needed
            current_stock = item.get("quantity", 0)
            reorder_level = item.get("reorder_level", 10)  # Default reorder level
            
            if usage_rate > 0:
                days_until_reorder = max(0, (current_stock - reorder_level) / usage_rate)
            else:
                days_until_reorder = 0
            
            # Update forecast in database
            db.inventory.update_one(
                {"_id": item["_id"]},
                {"$set": {
                    "forecast": {
                        "usage_rate": usage_rate,
                        "days_until_reorder": days_until_reorder,
                        "last_forecast_date": datetime.utcnow()
                    }
                }}
            )
        
        logger.info("Demand forecasting completed")
        return True
    except Exception as e:
        logger.error(f"Forecasting failed: {e}")
        return False