import sys
import os

# Add the b-tcrimer directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'b-tcrimer')))

from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional

from .auth import get_api_key, get_password_hash
from .rate_limiter import rate_limit
from .database import create_db_and_tables, get_db, User, APIKey
from .signals import get_signals
from .backtest import run_backtest
from .portfolio import analyze_portfolio
from .stripe_integration import create_checkout_session, handle_webhook

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
async def read_root():
    return {"message": "Welcome to B-tcrimer API"}

# Endpoint to create a test user and API key (for initial setup only)
@app.post("/create_test_user")
async def create_test_user(username: str, password: str, is_paid_user: bool = False, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(password)
    user = User(username=username, hashed_password=hashed_password, is_paid_user=is_paid_user)
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate a simple API key for now. In production, use a more robust method.
    api_key_str = f"test_key_{username}"
    api_key = APIKey(api_key=api_key_str, user_id=user.id, is_active=True)
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return {"message": "Test user and API key created", "username": username, "api_key": api_key_str}

@app.get("/signals/{symbol}")
async def get_trading_signals(symbol: str, api_key: APIKey = Depends(get_api_key), request: Request = Depends(rate_limit)):
    # The rate_limit dependency will raise HTTPException if rate limit is exceeded
    # The get_api_key dependency will raise HTTPException if API key is invalid
    
    # Call the signals logic from signals.py
    signals_data = get_signals(symbol)
    return signals_data

@app.post("/backtest")
async def perform_backtest(strategy: str, symbol: str, start_date: str, end_date: str, api_key: APIKey = Depends(get_api_key), request: Request = Depends(rate_limit)):
    backtest_results = run_backtest(strategy, symbol, start_date, end_date)
    return backtest_results

@app.get("/portfolio_analysis")
async def get_portfolio_analysis(api_key: APIKey = Depends(get_api_key), request: Request = Depends(rate_limit)):
    # Assuming user_id can be derived from the API key for portfolio analysis
    user_id = api_key.user_id
    analysis_results = analyze_portfolio(user_id)
    return analysis_results

@app.post("/create-checkout-session")
async def create_stripe_checkout_session(product_id: str, api_key: APIKey = Depends(get_api_key)):
    # In a real application, you'd get success_url and cancel_url from config or request
    success_url = "https://your-domain.com/success"
    cancel_url = "https://your-domain.com/cancel"
    
    # Use the user_id from the API key for Stripe's client_reference_id
    user_id = str(api_key.user_id)
    
    session_info = create_checkout_session(user_id, product_id, success_url, cancel_url)
    if "error" in session_info:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=session_info["error"])
    return session_info

@app.post("/stripe-webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not sig_header:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stripe-Signature header missing")

    result = handle_webhook(payload, sig_header)
    if "error" in result:
        raise HTTPException(status_code=result["status_code"], detail=result["error"])
    return result
