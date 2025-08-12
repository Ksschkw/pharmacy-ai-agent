from fastapi import APIRouter, HTTPException, Form, Depends
from app.services.auth import create_access_token, verify_password
from app.services.database import get_db
import logging

router = APIRouter(tags=["Authentication"])
logger = logging.getLogger("pharmacy_module.auth")

@router.post("/auth/login", response_model=dict)
async def login(pharmacy_id: str = Form(...), password: str = Form(...), db=Depends(get_db)):
    """Authenticate a pharmacy and return a JWT."""
    try:
        pharmacy = db.pharmacies.find_one({"pharmacy_id": pharmacy_id})
        if not pharmacy or not verify_password(password, pharmacy["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token(pharmacy_id)
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))