from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import yfinance as yf

from db import get_db
import models
import schemas
import security

router = APIRouter(
    prefix="/trade",
    tags=["Trading"]
)

@router.post("/execute", response_model=schemas.OrderResponse)
def execute_trade(order: schemas.OrderCreate, current_user: models.User = Depends(security.get_current_user), db: Session = Depends(get_db)):
    """Executes a real paper trade securely linked to the authenticated user's JWT token"""
    
    ticker = yf.Ticker(order.symbol)
    data = ticker.history(period="1d", interval="1m")
    if data.empty:
        raise HTTPException(status_code=400, detail="Invalid stock symbol or no data available")
    
    execution_price = float(data['Close'].iloc[-1])
    total_cost = execution_price * order.quantity
    
    if order.side == "BUY" and current_user.balance < total_cost:
        raise HTTPException(status_code=400, detail="Insufficient virtual funds")
        
    position = db.query(models.Position).filter(
        models.Position.owner_id == current_user.id, 
        models.Position.symbol == order.symbol
    ).first()
    
    if order.side == "BUY":
        current_user.balance -= total_cost
        if position:
            total_value = (position.quantity * position.avg_price) + total_cost
            position.quantity += order.quantity
            position.avg_price = total_value / position.quantity
        else:
            new_position = models.Position(
                symbol=order.symbol, quantity=order.quantity, avg_price=execution_price, owner_id=current_user.id
            )
            db.add(new_position)
            
    elif order.side == "SELL":
        if not position or position.quantity < order.quantity:
            raise HTTPException(status_code=400, detail="Insufficient shares to sell")
        current_user.balance += total_cost
        position.quantity -= order.quantity
        if position.quantity == 0:
            db.delete(position)
            
    new_order = models.Order(
        symbol=order.symbol,
        side=order.side,
        quantity=order.quantity,
        price=execution_price,
        status="FILLED",
        owner_id=current_user.id
    )
    db.add(new_order)
    
    db.commit()
    db.refresh(new_order)
    
    return new_order

@router.get("/portfolio")
def get_portfolio(current_user: models.User = Depends(security.get_current_user), db: Session = Depends(get_db)):
    """Returns holdings and order history securely for the authenticated JWT user"""
    positions = db.query(models.Position).filter(models.Position.owner_id == current_user.id).all()
    orders = db.query(models.Order).filter(models.Order.owner_id == current_user.id).order_by(models.Order.timestamp.desc()).limit(50).all()
    
    return {
        "balance": current_user.balance,
        "positions": positions,
        "orders": orders
    }
