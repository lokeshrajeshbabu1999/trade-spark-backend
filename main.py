import asyncio
from datetime import datetime, time

import yfinance as yf
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

# Import our new database modules
import models
import schemas
from db import engine, SessionLocal
from routers import auth, trade, user

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
    allow_origins=[
        "http://localhost:8080", 
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://trade-spark-frontend-lokesh.s3-website.ap-south-1.amazonaws.com",
        "https://tradespark.vercel.app", 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Trading engine is online!"}

# Simple cache to avoid hitting rate limits
price_cache = {}


def is_trading_open() -> bool:
    now = datetime.now().time()
    return time(9, 15) <= now < time(15, 20)


def is_after_square_off_time() -> bool:
    return datetime.now().time() >= time(15, 20)

async def fetch_real_price(symbol: str):
    """Fetches real price from Yahoo Finance without blocking the server."""
    try:
        def get_price():
            return trade.get_market_price(symbol)
            
        price = await asyncio.to_thread(get_price)
        if price is not None:
            price_cache[symbol] = price
            print(f"[YFinance Log] Live price of {trade.normalize_market_symbol(symbol)} is: Rs {price:.2f}")
            
        return price_cache.get(symbol, 150.00) # Fallback to cached or default
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return price_cache.get(symbol, 150.00)

@app.websocket("/ws/price_stream/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    await websocket.accept()
    print(f"A client connected to the real market data stream for {symbol}!")
    
    try:
        while True:
            # Fetch the actual real price of the stock from the market
            current_price = await fetch_real_price(symbol)
            
            await websocket.send_json({
                "symbol": trade.normalize_market_symbol(symbol).replace(".NS", "").replace(".BO", ""),
                "price": round(current_price, 2),
                "currency": "INR",
                "formatted_price": f"Rs {current_price:.2f}",
            })
            
            # Wait 3 seconds before next tick (yfinance will rate-limit
            # us if we do 1 second)
            await asyncio.sleep(3)
            
    except Exception as e:
        print(f"Client disconnected: {e}")

async def background_order_processor():
    while True:
        try:
            db = SessionLocal()
            try:
                if is_after_square_off_time():
                    intraday_positions = db.query(models.Position).filter(
                        models.Position.product_type == "INTRADAY",
                        models.Position.quantity != 0
                    ).all()

                    for position in intraday_positions:
                        current_price = await fetch_real_price(position.symbol)
                        square_off_order = schemas.OrderCreate(
                            symbol=position.symbol,
                            side="SELL" if position.quantity > 0 else "BUY",
                            quantity=abs(position.quantity),
                            product_type="INTRADAY",
                            order_type="MARKET"
                        )
                        trade.process_trade_execution(
                            db,
                            position.owner,
                            square_off_order,
                            current_price,
                            current_price * abs(position.quantity),
                        )

                pending_limit_orders = db.query(models.Order).filter(models.Order.status == "PENDING").all()
                
                gtt_orders = db.query(models.Order).filter(
                    models.Order.status == "EXECUTED",
                    (models.Order.gtt_sl.isnot(None)) | (models.Order.gtt_target.isnot(None))
                ).all()
                
                symbols_to_check = set([o.symbol for o in pending_limit_orders] + [o.symbol for o in gtt_orders])
                
                prices = {}
                for sym in symbols_to_check:
                    prices[sym] = await fetch_real_price(sym)
                    
                for order in pending_limit_orders:
                    current_price = prices.get(order.symbol)
                    if not current_price: continue
                    
                    execute = False
                    if order.side == "BUY" and current_price <= order.limit_price:
                        execute = True
                    elif order.side == "SELL" and current_price >= order.limit_price:
                        execute = True
                        
                    if execute:
                        current_user = order.owner
                        total_cost = current_price * order.quantity
                        trade.process_trade_execution(db, current_user, order, current_price, total_cost)
                        
                for order in gtt_orders:
                    current_price = prices.get(order.symbol)
                    if not current_price: continue
                    
                    hit_sl = False
                    hit_target = False
                    
                    if order.side == "BUY":
                        sl_price = order.price - (order.price * (order.gtt_sl or 0) / 100)
                        target_price = order.price + (order.price * (order.gtt_target or 0) / 100)
                        
                        if order.gtt_sl and current_price <= sl_price:
                            hit_sl = True
                        if order.gtt_target and current_price >= target_price:
                            hit_target = True
                            
                        if hit_sl or hit_target:
                            position = db.query(models.Position).filter(
                                models.Position.owner_id == order.owner_id,
                                models.Position.symbol == order.symbol,
                                models.Position.product_type == order.product_type
                            ).first()
                            
                            if position and position.quantity > 0:
                                current_user = order.owner
                                sell_qty = min(position.quantity, order.quantity)
                                total_cost = current_price * sell_qty
                                
                                sell_order = schemas.OrderCreate(
                                    symbol=order.symbol, side="SELL", quantity=sell_qty,
                                    product_type=order.product_type, order_type="MARKET"
                                )
                                order.gtt_sl = None
                                order.gtt_target = None
                                trade.process_trade_execution(db, current_user, sell_order, current_price, total_cost)
                            else:
                                order.gtt_sl = None
                                order.gtt_target = None
                                db.commit()
                                
                    elif order.side == "SELL":
                        sl_price = order.price + (order.price * (order.gtt_sl or 0) / 100)
                        target_price = order.price - (order.price * (order.gtt_target or 0) / 100)
                        
                        if order.gtt_sl and current_price >= sl_price:
                            hit_sl = True
                        if order.gtt_target and current_price <= target_price:
                            hit_target = True
                            
                        if hit_sl or hit_target:
                            position = db.query(models.Position).filter(
                                models.Position.owner_id == order.owner_id,
                                models.Position.symbol == order.symbol,
                                models.Position.product_type == order.product_type
                            ).first()
                            
                            if position and position.quantity < 0:
                                current_user = order.owner
                                buy_qty = min(abs(position.quantity), order.quantity)
                                total_cost = current_price * buy_qty
                                
                                buy_order = schemas.OrderCreate(
                                    symbol=order.symbol, side="BUY", quantity=buy_qty,
                                    product_type=order.product_type, order_type="MARKET"
                                )
                                order.gtt_sl = None
                                order.gtt_target = None
                                trade.process_trade_execution(db, current_user, buy_order, current_price, total_cost)
                            else:
                                order.gtt_sl = None
                                order.gtt_target = None
                                db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"Error in background processor: {e}")
            
        await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_order_processor())
