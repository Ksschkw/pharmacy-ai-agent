from bson import ObjectId
from fastapi import APIRouter, UploadFile, Form, HTTPException, File, BackgroundTasks
from ..models.prescription import Prescription
from ..models.patient import Patient
from ..services.database import get_db
from ..services.ocr_service import OCRService
from ..services.ai_service import parse_prescription
import shutil
import os
import logging
import asyncio

router = APIRouter()
ocr_service = OCRService()
logger = logging.getLogger("pharmacy_module.prescriptions")

async def process_ocr(file_path: str, prescription_data: dict):
    logger.info(f"Processing OCR for file: {file_path}")
    try:
        result = await asyncio.to_thread(ocr_service.process_image, file_path)
        if "error" in result["parsed_data"]:
            raise ValueError(result["parsed_data"]["error"])
        prescription_data.update({
            "ocr_raw": result["ocr_raw"],
            "parsed_data": result["parsed_data"],
            "image_path": result["image_path"]
        })
        db = get_db()
        prescription = Prescription(**prescription_data)
        result = db.prescriptions.insert_one(prescription.dict(by_alias=True, exclude_none=True))
        prescription_id = str(result.inserted_id)
        db.patients.update_one(
            {"patient_id": prescription_data["patient_id"]},
            {"$push": {"prescription_ids": prescription_id}},
            upsert=True
        )
        logger.info(f"Prescription processed successfully, ID: {prescription_id}")
    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        raise

@router.post("/prescriptions/upload", response_model=dict)
async def upload_prescription(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    patient_id: str = Form(...),
    physician_id: str = Form(...),
    prescription_number: str = Form(...),
    priority: str = Form(...),
    notes: str = Form(None)
):
    try:
        upload_dir = os.path.join("static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{patient_id}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        prescription_data = {
            "patient_id": patient_id,
            "physician_id": physician_id,
            "prescription_number": prescription_number,
            "priority": priority,
            "notes": notes,
            "source": "file"
        }
        background_tasks.add_task(process_ocr, file_path, prescription_data)
        return {"message": "Prescription upload initiated", "status": "processing"}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prescriptions/manual", response_model=dict)
async def add_manual_prescription(
    patient_id: str = Form(...),
    physician_id: str = Form(...),
    prescription_number: str = Form(...),
    priority: str = Form(...),
    notes: str = Form(None),
    text: str = Form(...)
):
    try:
        logger.info(f"Processing manual prescription for patient_id: {patient_id}")
        parsed_data = parse_prescription(text, os.getenv("API_KEY"))
        if "error" in parsed_data:
            raise ValueError(parsed_data["error"])
        
        prescription_data = {
            "patient_id": patient_id,
            "physician_id": physician_id,
            "prescription_number": prescription_number,
            "priority": priority,
            "notes": notes,
            "ocr_raw": text,
            "parsed_data": parsed_data,
            "source": "manual"
        }
        db = get_db()
        prescription = Prescription(**prescription_data)
        result = db.prescriptions.insert_one(prescription.dict(by_alias=True, exclude_none=True))
        prescription_id = str(result.inserted_id)
        db.patients.update_one(
            {"patient_id": patient_id},
            {"$push": {"prescription_ids": prescription_id}},
            upsert=True
        )
        return {"message": "Prescription added", "prescription_id": prescription_id}
    except Exception as e:
        logger.error(f"Manual prescription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prescriptions/{patient_id}", response_model=dict)
async def get_prescriptions(patient_id: str):
    try:
        logger.info(f"Fetching prescriptions for patient_id: {patient_id}")
        db = get_db()
        patient = db.patients.find_one({"patient_id": patient_id})
        if not patient or "prescription_ids" not in patient:
            return {"prescriptions": [], "message": "No prescriptions found"}
        
        prescription_ids = [ObjectId(pid) for pid in patient["prescription_ids"]]
        prescriptions = list(db.prescriptions.find({"_id": {"$in": prescription_ids}}))
        for p in prescriptions:
            p["_id"] = str(p["_id"])
        return {"prescriptions": prescriptions}
    except Exception as e:
        logger.error(f"Error fetching prescriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))