from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import yfinance as yf

# Import our new database modules
import models
from db import engine
from routers import trade, user, auth

# Automatically create all SQL tables if PostgreSQL is connected
if engine:
    try:
        models.Base.metadata.create_all(bind=engine)
        print("Database tables verified/created successfully!")
    except Exception as e:
        print(f"Could not initialize tables: {e}")

app = FastAPI(title="Trade Spark Engine")

# Plug in our new endpoints!
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(trade.router)

# Allow the frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Trading engine is online!"}

# Simple cache to avoid hitting rate limits
price_cache = {}

async def fetch_real_price(symbol: str):
    """Fetches real price from Yahoo Finance without blocking the server."""
    try:
        def get_price():
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                return data['Close'].iloc[-1]
            return None
            
        price = await asyncio.to_thread(get_price)
        if price is not None:
            price_cache[symbol] = price
            
        return price_cache.get(symbol, 150.00) # Fallback to cached or default
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return price_cache.get(symbol, 150.00)

@app.websocket("/ws/price_stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("A client connected to the real market data stream!")
    
    symbol = "AAPL"
    
    try:
        while True:
            # Fetch the actual real price of Apple stock from the market
            current_price = await fetch_real_price(symbol)
            
            await websocket.send_json({
                "symbol": symbol,
                "price": round(current_price, 2)
            })
            
            # Wait 3 seconds before next tick (yfinance will rate-limit us if we do 1 second)
            await asyncio.sleep(3)
            
    except Exception as e:
        print(f"Client disconnected: {e}")
