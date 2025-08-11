import os
import logging
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI
from app.routers.prescriptions import router as prescriptions_router
from app.routers.inventory import router as inventory_router

# Configure logging
logger = logging.getLogger("pharmacy_module")
logger.setLevel(logging.getLevelName(os.getenv("LOG_LEVEL", "INFO")))
handler = RotatingFileHandler("pharmacy.log", maxBytes=1000000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = FastAPI(title="Pharmacy Module API", description="API for managing prescriptions", version="1.0.0")

# Routers for prescriptions
app.include_router(prescriptions_router, prefix="/api/v1", tags=["Prescriptions"])
#Router for inventory heh
app.include_router(inventory_router, prefix="/api/v1", tags=["Inventory"])

@app.on_event("startup")
async def startup_event():
    logger.info("Pharmacy Module API started at 2025-08-07 06:30 WAT")

@app.get("/", response_model=dict)
async def root():
    return {"message": "Pharmacy Module API is live", "status": "running"}