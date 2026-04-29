import sys
import json
from db import SessionLocal
import models
import yfinance as yf

db = SessionLocal()
user = db.query(models.User).first()
if user:
    all_orders = db.query(models.Order).filter(models.Order.owner_id == user.id, models.Order.status == 'EXECUTED').all()
    from collections import defaultdict
    grouped = defaultdict(list)
    for o in all_orders:
        grouped[(o.symbol, o.product_type)].append(o)
    dynamic_positions = []
    for (symbol, product_type), stock_orders in grouped.items():
        qty = sum(o.quantity if o.side == 'BUY' else -o.quantity for o in stock_orders)
        if qty <= 0: continue
        buys = [o for o in stock_orders if o.side == 'BUY']
        total_qty = sum(o.quantity for o in buys)
        avg_price = sum(o.quantity * o.price for o in buys) / total_qty if total_qty > 0 else 0
        dynamic_positions.append({'symbol': symbol, 'qty': qty, 'avg_price': avg_price})

    current_holdings_value = 0.0
    for pos in dynamic_positions:
        ticker = yf.Ticker(pos['symbol'])
        price = getattr(ticker.fast_info, 'lastPrice', None)
        if price is None:
            data = ticker.history(period='1d')
            if not data.empty:
                price = float(data['Close'].iloc[-1])
        market_value = price * pos['qty']
        print(f"{pos['symbol']}: Qty={pos['qty']}, Price={price}, MarketValue={market_value}")
        current_holdings_value += market_value
        
    print(f'Total Holdings Value: {current_holdings_value}')
