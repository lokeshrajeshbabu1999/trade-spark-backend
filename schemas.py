from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- USER SCHEMAS (Validation for Authentication) ---
class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    balance: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- POSITION SCHEMAS (Data sent to the frontend Portfolio) ---
class PositionResponse(BaseModel):
    id: int
    symbol: str
    quantity: float
    avg_price: float
    
    class Config:
        from_attributes = True

# --- ORDER SCHEMAS (Validation for executing trades) ---
class OrderCreate(BaseModel):
    symbol: str
    side: str # Expects 'BUY' or 'SELL'
    quantity: float
    # We don't ask the user for 'price' because the server fetches the real market price to prevent cheating!

class OrderResponse(BaseModel):
    id: int
    symbol: str
    side: str
    quantity: float
    price: float
    status: str
    timestamp: datetime
    
    class Config:
        from_attributes = True
