import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
import security
from db import get_db

router = APIRouter(
    prefix="/trade",
    tags=["Trading"]
)

INTRADAY_SHORT_MARGIN_RATE = 0.20


def normalize_market_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if normalized.endswith((".NS", ".BO")):
        return normalized
    return f"{normalized}.NS"


def get_market_price(symbol: str) -> float | None:
    market_symbol = normalize_market_symbol(symbol)
    ticker = yf.Ticker(market_symbol)
    price = getattr(ticker.fast_info, 'lastPrice', None)

    if price is None:
        data = ticker.history(period="1d")
        if not data.empty:
            price = float(data['Close'].iloc[-1])

    return float(price) if price is not None else None


@router.post("/execute", response_model=schemas.OrderResponse)
def execute_trade(
    order: schemas.OrderCreate, 
    current_user: models.User = Depends(security.get_current_user), 
    db: Session = Depends(get_db)
):
    """Executes a real paper trade securely linked to the authenticated user's JWT token"""

    market_price = get_market_price(order.symbol)

    if market_price is None:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid stock symbol or no data available for {order.symbol}"
        )

    execution_price = order.limit_price if order.order_type == "LIMIT" and order.limit_price else market_price
    total_cost = execution_price * order.quantity
    
    # Delegate to core logic
    return process_trade_execution(db, current_user, order, execution_price, total_cost, market_price)

def process_trade_execution(db: Session, current_user: models.User, order: schemas.OrderCreate | models.Order, execution_price: float, total_cost: float, market_price: float | None = None):
    profit = 0.0
    status = "EXECUTED"
    market_price = market_price if market_price is not None else execution_price

    # Handle LIMIT orders
    if order.order_type == "LIMIT" and order.limit_price is not None:
        if order.side == "BUY" and market_price > order.limit_price:
            status = "PENDING"
        elif order.side == "SELL" and market_price < order.limit_price:
            status = "PENDING"

    if status == "PENDING":
        new_order = models.Order(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=order.limit_price, # Store limit price
            profit=0.0,
            status="PENDING",
            product_type=order.product_type,
            order_type=order.order_type,
            limit_price=order.limit_price,
            gtt_sl=order.gtt_sl,
            gtt_target=order.gtt_target,
            owner_id=current_user.id
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        return new_order
    
    margin_required = total_cost * INTRADAY_SHORT_MARGIN_RATE
        
    position = db.query(models.Position).filter(
        models.Position.owner_id == current_user.id, 
        models.Position.symbol == order.symbol,
        models.Position.product_type == order.product_type
    ).first()
    
    if order.side == "BUY":
        if order.product_type == "NORMAL":
            if current_user.cash_balance < total_cost:
                raise HTTPException(status_code=400, detail="Insufficient virtual funds")
            current_user.cash_balance -= total_cost
            current_user.total_invested_value += total_cost
            
            if position:
                total_value = (position.quantity * position.avg_price) + total_cost
                position.quantity += order.quantity
                position.avg_price = total_value / position.quantity
            else:
                new_position = models.Position(
                    symbol=order.symbol, quantity=order.quantity, avg_price=execution_price, 
                    product_type=order.product_type, owner_id=current_user.id
                )
                db.add(new_position)
        else: # INTRADAY BUY
            if position and position.quantity < 0: # Squaring off short
                buy_qty = min(abs(position.quantity), order.quantity)
                cost_basis = position.avg_price * buy_qty
                profit = cost_basis - (execution_price * buy_qty)
                margin_released = cost_basis * INTRADAY_SHORT_MARGIN_RATE
                current_user.cash_balance += (margin_released + profit)
                current_user.realized_pnl += profit
                
                position.quantity += buy_qty
                if position.quantity == 0:
                    db.delete(position)
                if order.quantity > buy_qty:
                    raise HTTPException(status_code=400, detail="Cannot square off and go long in one order")
            else: # Opening LONG INTRADAY
                if current_user.cash_balance < total_cost:
                    raise HTTPException(status_code=400, detail="Insufficient virtual funds")
                current_user.cash_balance -= total_cost
                
                if position:
                    total_value = (position.quantity * position.avg_price) + total_cost
                    position.quantity += order.quantity
                    position.avg_price = total_value / position.quantity
                else:
                    new_position = models.Position(
                        symbol=order.symbol, quantity=order.quantity, avg_price=execution_price, 
                        product_type=order.product_type, owner_id=current_user.id
                    )
                    db.add(new_position)
            
    elif order.side == "SELL":
        if order.product_type == "NORMAL":
            if not position or position.quantity < order.quantity:
                raise HTTPException(status_code=400, detail="Insufficient shares to sell")
            
            proceeds = execution_price * order.quantity
            cost_basis_of_sold_shares = position.avg_price * order.quantity
            profit = proceeds - cost_basis_of_sold_shares
            
            current_user.cash_balance += proceeds
            current_user.total_invested_value -= cost_basis_of_sold_shares
            current_user.realized_pnl += profit
            
            position.quantity -= order.quantity
            if position.quantity <= 0:
                db.delete(position)
        else: # INTRADAY SELL
            if position and position.quantity > 0: # Squaring off LONG
                sell_qty = min(position.quantity, order.quantity)
                cost_basis = position.avg_price * sell_qty
                proceeds = execution_price * sell_qty
                profit = proceeds - cost_basis
                
                current_user.cash_balance += proceeds
                current_user.realized_pnl += profit
                
                position.quantity -= sell_qty
                if position.quantity == 0:
                    db.delete(position)
                if order.quantity > sell_qty:
                    raise HTTPException(status_code=400, detail="Cannot square off and short in one order")
            else: # Opening SHORT INTRADAY
                if current_user.cash_balance < margin_required:
                    raise HTTPException(status_code=400, detail="Insufficient virtual funds")
                current_user.cash_balance -= margin_required
                
                if position: # already short
                    total_value = (abs(position.quantity) * position.avg_price) + total_cost
                    position.quantity -= order.quantity
                    position.avg_price = total_value / abs(position.quantity)
                else:
                    new_position = models.Position(
                        symbol=order.symbol, quantity=-order.quantity, avg_price=execution_price, 
                        product_type=order.product_type, owner_id=current_user.id
                    )
                    db.add(new_position)
            
    if isinstance(order, schemas.OrderCreate):
        new_order = models.Order(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=execution_price,
            profit=profit,
            status="EXECUTED",
            product_type=order.product_type,
            order_type=order.order_type,
            limit_price=order.limit_price,
            gtt_sl=order.gtt_sl,
            gtt_target=order.gtt_target,
            owner_id=current_user.id
        )
        db.add(new_order)
    else:
        # It's an existing PENDING order being executed
        order.status = "EXECUTED"
        order.price = execution_price
        order.profit = profit
        new_order = order
    
    db.commit()
    db.refresh(new_order)
    
    return new_order

@router.get("/portfolio", response_model=schemas.PortfolioSummary)
def get_portfolio(
    current_user: models.User = Depends(security.get_current_user), 
    db: Session = Depends(get_db)
):
    """Returns holdings and detailed financial summary securely for the authenticated user"""
    all_orders = db.query(models.Order).filter(
        models.Order.owner_id == current_user.id
    ).all()
    executed_orders = [order for order in all_orders if order.status == "EXECUTED"]

    open_positions = db.query(models.Position).filter(
        models.Position.owner_id == current_user.id,
        models.Position.quantity != 0
    ).all()

    current_holdings_value = 0.0
    dynamic_invested_value = 0.0
    unrealized_pnl = 0.0
    position_data = []

    for pos in open_positions:
        price = None
        try:
            price = get_market_price(pos.symbol)
        except Exception:
            pass

        if price is None:
            price = pos.avg_price

        abs_qty = abs(pos.quantity)
        exposure_value = price * abs_qty
        invested_value = pos.avg_price * abs_qty
        position_unrealized_pnl = (
            (price - pos.avg_price) * pos.quantity
            if pos.quantity > 0
            else (pos.avg_price - price) * abs_qty
        )

        current_holdings_value += exposure_value
        dynamic_invested_value += invested_value
        unrealized_pnl += position_unrealized_pnl

        position_data.append({
            "id": pos.id,
            "symbol": pos.symbol.replace(".NS", "").replace(".BO", ""),
            "quantity": pos.quantity,
            "avg_price": round(pos.avg_price, 2),
            "product_type": pos.product_type,
            "live_price": round(price, 2),
            "market_value": round(exposure_value, 2),
            "unrealized_pnl": round(position_unrealized_pnl, 2)
        })

    # Add weight percentage
    for p_data in position_data:
        if current_holdings_value > 0:
            p_data["weight_percentage"] = round((p_data["market_value"] / current_holdings_value) * 100, 1)
        else:
            p_data["weight_percentage"] = 0.0

    total_portfolio_value = current_user.cash_balance + current_holdings_value
    
    pnl_percentage = 0.0
    if dynamic_invested_value > 0:
        pnl_percentage = (unrealized_pnl / dynamic_invested_value) * 100

    # 5. Win Rate Calculation (Percentage of profitable SELL orders)
    sell_orders = [o for o in executed_orders if o.side == "SELL"]
    win_rate = 0.0
    if sell_orders:
        winning_trades = len([o for o in sell_orders if o.profit > 0])
        win_rate = (winning_trades / len(sell_orders)) * 100

    # 6. Recent Orders, including pending limit orders (limit to 50)
    recent_orders = sorted(all_orders, key=lambda x: x.timestamp, reverse=True)[:50]
    
    return {
        "cash_balance": round(current_user.cash_balance, 2),
        "total_invested_value": round(dynamic_invested_value, 2),
        "current_holdings_value": round(current_holdings_value, 2),
        "total_portfolio_value": round(total_portfolio_value, 2),
        "unrealized_pnl": round(unrealized_pnl, 2),
        "realized_pnl": round(current_user.realized_pnl, 2),
        "pnl_percentage": round(pnl_percentage, 2),
        "win_rate": round(win_rate, 2),
        "positions": position_data,
        "orders": recent_orders
    }

@router.get("/price/{symbol}")
def get_live_price(symbol: str):
    """Fetches the real-time price of a symbol using yfinance"""
    try:
        market_symbol = normalize_market_symbol(symbol)
        ticker = yf.Ticker(market_symbol)
        price = getattr(ticker.fast_info, 'lastPrice', None)
        if price is None:
            data = ticker.history(period="1d")
            if not data.empty:
                price = float(data['Close'].iloc[-1])
        
        # Super Fallback: Simulate price if Yahoo Finance blocks the connection entirely
        if price is None:
            print(f"[YFinance Fallback] Simulating INR price for blocked symbol {market_symbol}")
            price = 1000.00
            
        if price is not None:
            print(f"[YFinance REST Log] Live price of {market_symbol} is: Rs {price:.2f}")
            return {
                "symbol": market_symbol,
                "live_price": price,
                "currency": "INR",
                "formatted_price": f"Rs {price:.2f}",
            }
        else:
            return {"error": f"Could not fetch price for {market_symbol}"}
    except Exception as e:
        return {"error": str(e)}

@router.get("/history/{symbol}")
def get_historical_data(symbol: str, period: str = "1mo", interval: str = "1d"):
    """
    Fetches historical data for rendering charts.
    Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    Valid intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    """
    try:
        market_symbol = normalize_market_symbol(symbol)
        ticker = yf.Ticker(market_symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            # Super Fallback: Generate mock history if Yahoo Finance is geoblocking us
            print(f"[YFinance Fallback] Generating mock INR history for blocked symbol {market_symbol}")
            import datetime
            import random
            history_list = []
            base_price = 1000.00
            for i in range(30, -1, -1):
                date = datetime.datetime.now() - datetime.timedelta(days=i)
                base_price = base_price + (random.random() - 0.48) * 20  # nosec
                history_list.append({
                    "time": date.isoformat(),
                    "open": round(base_price - 5, 2),
                    "high": round(base_price + 10, 2),
                    "low": round(base_price - 10, 2),
                    "close": round(base_price, 2),
                    "volume": int(random.uniform(1000000, 5000000))  # nosec
                })
            return {"symbol": market_symbol, "currency": "INR", "data": history_list}
            
        df.reset_index(inplace=True)
        time_col = 'Datetime' if 'Datetime' in df.columns else 'Date'
        
        history_list = []
        for _, row in df.iterrows():
            history_list.append({
                "time": row[time_col].isoformat(),
                "open": round(float(row['Open']), 2),
                "high": round(float(row['High']), 2),
                "low": round(float(row['Low']), 2),
                "close": round(float(row['Close']), 2),
                "volume": int(row['Volume'])
            })
            
        print(
            f"[YFinance REST Log] Fetched {len(history_list)} data points "
            f"for {market_symbol} in INR ({period}/{interval})"
        )
        return {"symbol": market_symbol, "currency": "INR", "data": history_list}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
