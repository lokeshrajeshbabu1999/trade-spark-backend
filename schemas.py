from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# --- USER SCHEMAS (Validation for Authentication) ---
class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    cash_balance: float
    balance: float
    total_invested_value: float
    realized_pnl: float
    deposited_capital: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- POSITION SCHEMAS (Data sent to the frontend Portfolio) ---
class PositionResponse(BaseModel):
    id: int
    symbol: str
    quantity: float
    avg_price: float
    product_type: str
    live_price: float = 0.0
    market_value: float = 0.0
    weight_percentage: float = 0.0
    unrealized_pnl: float = 0.0
    
    class Config:
        from_attributes = True

# --- ORDER SCHEMAS (Validation for executing trades) ---
class OrderCreate(BaseModel):
    symbol: str
    side: str # Expects 'BUY' or 'SELL'
    quantity: float
    product_type: str = "NORMAL" # "NORMAL" or "INTRADAY"
    order_type: str = "MARKET"
    limit_price: Optional[float] = None
    gtt_sl: Optional[float] = None
    gtt_target: Optional[float] = None

class OrderResponse(BaseModel):
    id: int
    symbol: str
    side: str
    quantity: float
    price: float
    profit: float = 0.0
    status: str
    product_type: str
    order_type: str
    limit_price: Optional[float] = None
    gtt_sl: Optional[float] = None
    gtt_target: Optional[float] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True

class GTTUpdate(BaseModel):
    sl: Optional[float] = None
    target: Optional[float] = None
    
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
