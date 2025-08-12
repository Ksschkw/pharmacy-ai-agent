from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import pytz
from app.services.database import get_db
import logging
import os

logger = logging.getLogger("pharmacy_module.auth")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")  # Set in .env
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def create_access_token(pharmacy_id: str) -> str:
    """Generate a JWT for the given pharmacy_id."""
    to_encode = {
        "sub": pharmacy_id,
        "exp": datetime.now(pytz.UTC) + timedelta(hours=24)
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

async def get_current_pharmacy_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT and return pharmacy_id."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        pharmacy_id: str = payload.get("sub")
        if not pharmacy_id:
            raise HTTPException(status_code=401, detail="Invalid token: pharmacy_id missing")
        
        db = get_db()
        pharmacy = db.pharmacies.find_one({"pharmacy_id": pharmacy_id})
        if not pharmacy:
            raise HTTPException(status_code=401, detail="Pharmacy not found")
        return pharmacy_id
    except JWTError as e:
        logger.error(f"JWT validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")