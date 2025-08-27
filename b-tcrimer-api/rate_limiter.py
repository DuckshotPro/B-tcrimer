import time
from collections import defaultdict
from fastapi import HTTPException, Request, Depends
from starlette.status import HTTP_429_TOO_MANY_REQUESTS, HTTP_403_FORBIDDEN
from sqlalchemy.orm import Session

from .database import get_db, User

# In-memory storage for demonstration purposes
# In a real application, use Redis or a similar distributed cache
rate_limits = defaultdict(lambda: {'count': 0, 'last_reset': time.time()})

async def rate_limit(request: Request, api_key_record: dict, db: Session = Depends(get_db), calls_per_day: int = 100):
    user_id = api_key_record.user_id
    current_time = time.time()
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="User not found for API Key")

    # Reset count if a new day has started (for simplicity, using 24-hour window)
    if current_time - rate_limits[user_id]['last_reset'] > 24 * 60 * 60:
        rate_limits[user_id]['count'] = 0
        rate_limits[user_id]['last_reset'] = current_time

    if not api_key_record.is_active:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="API Key is inactive")

    # Paid users have unlimited calls
    if user.is_paid_user:
        return

    if rate_limits[user_id]['count'] >= calls_per_day:
        raise HTTPException(status_code=HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    
    rate_limits[user_id]['count'] += 1
