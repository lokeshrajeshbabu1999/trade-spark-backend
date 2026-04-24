from datetime import datetime
from typing import List
from pydantic import BaseModel


# --- USER SCHEMAS (Validation for Authentication) ---
class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    cash_balance: float = 1000000.0
    balance: float = 1000000.0
    total_invested_value: float = 0.0
    realized_pnl: float = 0.0
    deposited_capital: float = 1000000.0
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
    # We don't ask the user for 'price' because the server fetches the real 
    # market price to prevent cheating!

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

class PortfolioSummary(BaseModel):
    cash_balance: float
    total_invested_value: float # Cost basis of open positions
    current_holdings_value: float # Market value of open positions
    total_portfolio_value: float # Cash + Market Value
    unrealized_pnl: float
    realized_pnl: float
    pnl_percentage: float
    win_rate: float
    positions: List[PositionResponse]
    orders: List[OrderResponse]
