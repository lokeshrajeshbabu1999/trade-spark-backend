from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    # Everyone gets $100,000 in paper trading money!
    balance = Column(Float, default=100000.0) 
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships mapping to other tables
    positions = relationship("Position", back_populates="owner")
    orders = relationship("Order", back_populates="owner")

class Position(Base):
    """Tracks currently held stocks for a user"""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True) # e.g. 'AAPL'
    quantity = Column(Float, default=0.0)
    avg_price = Column(Float, default=0.0)
    owner_id = Column(String, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="positions")

class Order(Base):
    """A historical ledger of every trade a user has made"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    side = Column(String) # "BUY" or "SELL"
    quantity = Column(Float)
    price = Column(Float) # executed price
    status = Column(String) # "FILLED" or "REJECTED"
    timestamp = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(String, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="orders")
