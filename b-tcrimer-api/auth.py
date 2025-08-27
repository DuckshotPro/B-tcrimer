from fastapi import Security, HTTPException, Depends
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from passlib.context import CryptContext

from .database import get_db, APIKey

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_api_key(api_key_header: str = Security(api_key_header), db = Depends(get_db)):
    if api_key_header:
        api_key_record = db.query(APIKey).filter(APIKey.api_key == api_key_header, APIKey.is_active == True).first()
        if api_key_record:
            return api_key_record
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Could not validate API Key"
    )
