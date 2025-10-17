# from fastapi import FastAPI, HTTPException, Depends
# from fastapi.middleware.cors import CORSMiddleware
# import MetaTrader5 as mt5
# from typing import List, Optional, Dict, Any
# from pydantic import BaseModel
# import datetime
# import pandas as pd
# from config import settings

# app = FastAPI(
#     title="MT5 FastAPI Service",
#     description="REST API for MetaTrader 5 operations",
#     version="1.0.0"
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Pydantic models
# class SymbolInfo(BaseModel):
#     symbol: str
#     bid: float
#     ask: float
#     spread: float
#     digits: int
#     point: float

# class OrderRequest(BaseModel):
#     symbol: str
#     volume: float
#     order_type: str  # "buy" or "sell"
#     price: Optional[float] = None
#     slippage: int = 2
#     magic: int = 1000
#     comment: str = "From FastAPI"

# class OrderResponse(BaseModel):
#     order_id: int
#     symbol: str
#     volume: float
#     price: float
#     type: str
#     comment: str

# class AccountInfo(BaseModel):
#     login: int
#     balance: float
#     equity: float
#     margin: float
#     free_margin: float
#     leverage: int

# # MT5 Connection management
# class MT5Connection:
#     def __init__(self):
#         self.connected = False
    
#     def connect(self) -> bool:
#         """Initialize and connect to MT5"""
#         if not mt5.initialize(
#             path=settings.MT5_PATH,
#             login=settings.MT5_LOGIN,
#             password=settings.MT5_PASSWORD,
#             server=settings.MT5_SERVER
#         ):
#             print(f"Initialize failed, error code: {mt5.last_error()}")
#             return False
        
#         self.connected = True
#         print("Connected to MT5 successfully")
#         return True
    
#     def disconnect(self):
#         """Shutdown MT5 connection"""
#         if self.connected:
#             mt5.shutdown()
#             self.connected = False
#             print("Disconnected from MT5")

# # Global connection instance
# mt5_conn = MT5Connection()

# # Dependency to ensure MT5 is connected
# def get_mt5_connection():
#     if not mt5_conn.connected:
#         if not mt5_conn.connect():
#             raise HTTPException(status_code=500, detail="Failed to connect to MT5")
#     return mt5_conn

# # Startup and shutdown events
# @app.on_event("startup")
# async def startup_event():
#     """Connect to MT5 on startup"""
#     mt5_conn.connect()

# @app.on_event("shutdown")
# async def shutdown_event():
#     """Disconnect from MT5 on shutdown"""
#     mt5_conn.disconnect()

# # API Endpoints
# @app.get("/")
# async def root():
#     return {"message": "MT5 FastAPI Service is running"}

# @app.get("/health")
# async def health_check(connection: MT5Connection = Depends(get_mt5_connection)):
#     return {
#         "status": "healthy",
#         "mt5_connected": connection.connected,
#         "mt5_version": mt5.version()
#     }

# @app.get("/account", response_model=AccountInfo)
# async def get_account_info(connection: MT5Connection = Depends(get_mt5_connection)):
#     """Get account information"""
#     account_info = mt5.account_info()
#     if account_info is None:
#         raise HTTPException(status_code=500, detail="Failed to get account info")
    
#     return AccountInfo(
#         login=account_info.login,
#         balance=account_info.balance,
#         equity=account_info.equity,
#         margin=account_info.margin,
#         free_margin=account_info.margin_free,
#         leverage=account_info.leverage
#     )

# @app.get("/symbols", response_model=List[str])
# async def get_symbols(connection: MT5Connection = Depends(get_mt5_connection)):
#     """Get all available symbols"""
#     symbols = mt5.symbols_get()
#     if symbols is None:
#         raise HTTPException(status_code=500, detail="Failed to get symbols")
    
#     return [s.name for s in symbols]

# @app.get("/symbol/{symbol_name}", response_model=SymbolInfo)
# async def get_symbol_info(symbol_name: str, connection: MT5Connection = Depends(get_mt5_connection)):
#     """Get information for a specific symbol"""
#     symbol_info = mt5.symbol_info(symbol_name)
#     if symbol_info is None:
#         raise HTTPException(status_code=404, detail=f"Symbol {symbol_name} not found")
    
#     return SymbolInfo(
#         symbol=symbol_info.name,
#         bid=symbol_info.bid,
#         ask=symbol_info.ask,
#         spread=symbol_info.spread,
#         digits=symbol_info.digits,
#         point=symbol_info.point
#     )

# @app.get("/rates/{symbol}")
# async def get_rates(
#     symbol: str, 
#     timeframe: int = mt5.TIMEFRAME_M1,
#     count: int = 100,
#     connection: MT5Connection = Depends(get_mt5_connection)
# ):
#     """Get historical rates for a symbol"""
#     rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
#     if rates is None:
#         raise HTTPException(status_code=500, detail=f"Failed to get rates for {symbol}")
    
#     df = pd.DataFrame(rates)
#     df['time'] = pd.to_datetime(df['time'], unit='s')
    
#     return df.to_dict(orient='records')

# @app.post("/order", response_model=OrderResponse)
# async def place_order(order_request: OrderRequest, connection: MT5Connection = Depends(get_mt5_connection)):
#     """Place a new order"""
#     symbol_info = mt5.symbol_info(order_request.symbol)
#     if symbol_info is None:
#         raise HTTPException(status_code=404, detail=f"Symbol {order_request.symbol} not found")
    
#     if not symbol_info.visible:
#         raise HTTPException(status_code=400, detail=f"Symbol {order_request.symbol} is not visible")
    
#     # Prepare order request
#     order_type = mt5.ORDER_TYPE_BUY if order_request.order_type.lower() == "buy" else mt5.ORDER_TYPE_SELL
#     price = order_request.price or (symbol_info.ask if order_type == mt5.ORDER_TYPE_BUY else symbol_info.bid)
    
#     request = {
#         "action": mt5.TRADE_ACTION_DEAL,
#         "symbol": order_request.symbol,
#         "volume": order_request.volume,
#         "type": order_type,
#         "price": price,
#         "slippage": order_request.slippage,
#         "magic": order_request.magic,
#         "comment": order_request.comment,
#         "type_time": mt5.ORDER_TIME_GTC,
#         "type_filling": mt5.ORDER_FILLING_FOK,
#     }
    
#     # Send order
#     result = mt5.order_send(request)
#     if result.retcode != mt5.TRADE_RETCODE_DONE:
#         raise HTTPException(
#             status_code=400, 
#             detail=f"Order failed: {result.comment} (error code: {result.retcode})"
#         )
    
#     return OrderResponse(
#         order_id=result.order,
#         symbol=order_request.symbol,
#         volume=order_request.volume,
#         price=result.price,
#         type=order_request.order_type,
#         comment=order_request.comment
#     )

# @app.get("/orders")
# async def get_orders(connection: MT5Connection = Depends(get_mt5_connection)):
#     """Get all open orders"""
#     orders = mt5.orders_get()
#     if orders is None:
#         return []
    
#     orders_list = []
#     for order in orders:
#         orders_list.append({
#             "ticket": order.ticket,
#             "symbol": order.symbol,
#             "type": "buy" if order.type == mt5.ORDER_TYPE_BUY else "sell",
#             "volume": order.volume_current,
#             "price_open": order.price_open,
#             "sl": order.sl,
#             "tp": order.tp,
#             "profit": order.profit,
#             "comment": order.comment
#         })
    
#     return orders_list

# @app.delete("/order/{order_id}")
# async def close_order(order_id: int, connection: MT5Connection = Depends(get_mt5_connection)):
#     """Close an open order"""
#     order = mt5.orders_get(ticket=order_id)
#     if not order:
#         raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    
#     order = order[0]
#     close_type = mt5.ORDER_TYPE_SELL if order.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
#     price = mt5.symbol_info_tick(order.symbol).ask if close_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(order.symbol).bid
    
#     request = {
#         "action": mt5.TRADE_ACTION_DEAL,
#         "symbol": order.symbol,
#         "volume": order.volume_current,
#         "type": close_type,
#         "position": order.ticket,
#         "price": price,
#         "magic": order.magic,
#         "comment": f"Closed by API",
#         "type_time": mt5.ORDER_TIME_GTC,
#         "type_filling": mt5.ORDER_FILLING_FOK,
#     }
    
#     result = mt5.order_send(request)
#     if result.retcode != mt5.TRADE_RETCODE_DONE:
#         raise HTTPException(
#             status_code=400, 
#             detail=f"Close order failed: {result.comment} (error code: {result.retcode})"
#         )
    
#     return {"message": f"Order {order_id} closed successfully"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "main:app",
#         host=settings.API_HOST,
#         port=settings.API_PORT,
#         reload=settings.DEBUG
#     )



from fastapi import FastAPI, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import MetaTrader5 as mt5
from typing import List, Optional
from pydantic import BaseModel
import pandas as pd
import asyncio
from config import settings


import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="MT5 FastAPI Service",
    description="REST + WebSocket API for MetaTrader 5 operations",
    version="1.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Pydantic Models
# -------------------------------
class SymbolInfo(BaseModel):
    symbol: str
    bid: float
    ask: float
    spread: float
    digits: int
    point: float
    change: float
    day_change_percentage: float

class OrderRequest(BaseModel):
    symbol: str
    volume: float
    order_type: str  # "buy" or "sell"
    price: Optional[float] = None
    slippage: int = 2
    magic: int = 1000
    comment: str = "From FastAPI"

class OrderResponse(BaseModel):
    order_id: int
    symbol: str
    volume: float
    price: float
    type: str
    comment: str

class AccountInfo(BaseModel):
    login: int
    balance: float
    equity: float
    margin: float
    free_margin: float
    leverage: int

# -------------------------------
# MT5 Connection Management
# -------------------------------
class MT5Connection:
    def __init__(self):
        self.connected = False
    
    def connect(self) -> bool:
        """Initialize and connect to MT5"""
        if not mt5.initialize(
            path=settings.MT5_PATH,
            login=settings.MT5_LOGIN,
            password=settings.MT5_PASSWORD,
            server=settings.MT5_SERVER
        ):
            print(f"Initialize failed, error code: {mt5.last_error()}")
            return False
        
        self.connected = True
        print("✅ Connected to MT5 successfully")
        return True
    
    def disconnect(self):
        """Shutdown MT5 connection"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("❌ Disconnected from MT5")

# Global connection instance
mt5_conn = MT5Connection()

# Dependency
def get_mt5_connection():
    if not mt5_conn.connected:
        if not mt5_conn.connect():
            raise HTTPException(status_code=500, detail="Failed to connect to MT5")
    return mt5_conn

# -------------------------------
# WebSocket Setup
# -------------------------------
connected_clients = set()

@app.websocket("/ws/mt5")
async def mt5_ws(ws: WebSocket):
    """WebSocket for streaming MT5 market data"""
    await ws.accept()
    await ws.send_text("✅ Connected to MT5 WebSocket")
    connected_clients.add(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive
    except Exception:
        connected_clients.remove(ws)
        await ws.close()

from fastapi import WebSocket
import json

# ---- WebSocket Endpoint for Live Prices ----
# @app.websocket("/ws/ticks/{symbol}")
# async def ticks_ws(websocket: WebSocket, symbol: str):
#     await websocket.accept()
#     if not mt5_conn.connected:
#         mt5_conn.connect()

#     try:
#         # Subscribe to symbol
#         if not mt5.symbol_select(symbol, True):
#             await websocket.send_text(json.dumps({"error": f"Symbol {symbol} not found"}))
#             await websocket.close()
#             return

#         await websocket.send_text(json.dumps({"msg": f"✅ Connected to {symbol} ticks"}))

#         last_time = None
#         while True:
#             tick = mt5.symbol_info_tick(symbol)
#             if tick and (last_time is None or tick.time != last_time):
#                 # Send only if new tick
#                 data = {
#                     "symbol": symbol,
#                     "time": tick.time,
#                     "bid": tick.bid,
#                     "ask": tick.ask,
#                     "last": tick.last,
#                     "volume": tick.volume
#                 }
#                 await websocket.send_text(json.dumps(data))
#                 last_time = tick.time

#             # Small sleep to avoid hammering CPU
#             await asyncio.sleep(0.5)

#     except Exception as e:
#         await websocket.send_text(json.dumps({"error": str(e)}))
#     finally:
#         await websocket.close()
@app.websocket("/ws/ticks/{symbol}")
async def ticks_ws(websocket: WebSocket, symbol: str):
    # Accept connection immediately (no extra headers)
    await websocket.accept()

    if not mt5_conn.connected:
        mt5_conn.connect()
    try:
        # Select symbol
        if not mt5.symbol_select(symbol, True):
            await websocket.send_text(json.dumps({"error": f"Symbol {symbol} not found"}))
            await websocket.close()
            return

        await websocket.send_text(json.dumps({"msg": f"✅ Connected to {symbol} ticks"}))

        last_time = None
        while True:
            tick = mt5.symbol_info_tick(symbol)
            # logger.info(f"{tick}")
            if tick and (last_time is None or tick.time != last_time):
                data = {
                    "symbol": symbol,
                    "time": tick.time,
                    "bid": tick.bid,
                    "ask": tick.ask,
                    "last": tick.last,
                    "volume": tick.volume,
                    "open": tick.open,
                    "change": tick.price_change
                }
                logger.info(f"🟢 Client connected: {data}")
                await websocket.send_text(json.dumps(data))
                last_time = tick.time

            # Avoid hammering CPU
            await asyncio.sleep(0.5)

    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e)}))
    finally:
        await websocket.close()

async def broadcast(message: dict):
    """Send JSON to all connected WS clients"""
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_json(message)
        except:
            dead.append(ws)
    for ws in dead:
        connected_clients.remove(ws)

# -------------------------------
# Startup & Shutdown
# -------------------------------
@app.on_event("startup")
async def startup_event():
    """Connect to MT5 and start streaming"""
    mt5_conn.connect()

    async def tick_stream():
        while True:
            tick = mt5.symbol_info_tick("EURUSD")  # default symbol
            if tick:
                await broadcast({
                    "symbol": "EURUSD",
                    "bid": tick.bid,
                    "ask": tick.ask,
                    "time": tick.time,
                })
            await asyncio.sleep(1)  # adjust frequency as needed

    asyncio.create_task(tick_stream())

@app.on_event("shutdown")
async def shutdown_event():
    """Disconnect from MT5 on shutdown"""
    mt5_conn.disconnect()

# -------------------------------
# API Endpoints
# -------------------------------
@app.get("/")
async def root():
    return {"message": "MT5 FastAPI Service is running"}

@app.get("/health")
async def health_check(connection: MT5Connection = Depends(get_mt5_connection)):
    return {
        "status": "healthy",
        "mt5_connected": connection.connected,
        "mt5_version": mt5.version()
    }

@app.get("/account", response_model=AccountInfo)
async def get_account_info(connection: MT5Connection = Depends(get_mt5_connection)):
    account_info = mt5.account_info()
    if account_info is None:
        raise HTTPException(status_code=500, detail="Failed to get account info")
    
    return AccountInfo(
        login=account_info.login,
        balance=account_info.balance,
        equity=account_info.equity,
        margin=account_info.margin,
        free_margin=account_info.margin_free,
        leverage=account_info.leverage
    )

@app.get("/symbols", response_model=List[str])
async def get_symbols(connection: MT5Connection = Depends(get_mt5_connection)):
    symbols = mt5.symbols_get()
    if symbols is None:
        raise HTTPException(status_code=500, detail="Failed to get symbols")
    return [s.name for s in symbols]

@app.get("/symbol/{symbol_name}", response_model=SymbolInfo)
async def get_symbol_info(symbol_name: str, connection: MT5Connection = Depends(get_mt5_connection)):
    symbol_info = mt5.symbol_info(symbol_name)
    if symbol_info is None:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol_name} not found")
    # logger.info(f"{symbol_info}")
    return SymbolInfo(
        symbol=symbol_info.name,
        bid=symbol_info.bid,
        ask=symbol_info.ask,
        spread=symbol_info.spread,
        digits=symbol_info.digits,
        point=symbol_info.point,
        change=symbol_info.price_change,
        day_change_percentage= (symbol_info.price_change/(symbol_info.bid-symbol_info.price_change)*100)
    )

@app.get("/rates/{symbol}")
async def get_rates(
    symbol: str, 
    timeframe: int = mt5.TIMEFRAME_M1,
    count: int = 100,
    connection: MT5Connection = Depends(get_mt5_connection)
):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None:
        raise HTTPException(status_code=500, detail=f"Failed to get rates for {symbol}")
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df.to_dict(orient='records')

@app.post("/order", response_model=OrderResponse)
async def place_order(order_request: OrderRequest, connection: MT5Connection = Depends(get_mt5_connection)):
    symbol_info = mt5.symbol_info(order_request.symbol)
    if symbol_info is None:
        raise HTTPException(status_code=404, detail=f"Symbol {order_request.symbol} not found")
    
    if not symbol_info.visible:
        raise HTTPException(status_code=400, detail=f"Symbol {order_request.symbol} is not visible")
    
    order_type = mt5.ORDER_TYPE_BUY if order_request.order_type.lower() == "buy" else mt5.ORDER_TYPE_SELL
    price = order_request.price or (symbol_info.ask if order_type == mt5.ORDER_TYPE_BUY else symbol_info.bid)
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": order_request.symbol,
        "volume": order_request.volume,
        "type": order_type,
        "price": price,
        "slippage": order_request.slippage,
        "magic": order_request.magic,
        "comment": order_request.comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        raise HTTPException(
            status_code=400, 
            detail=f"Order failed: {result.comment} (error code: {result.retcode})"
        )
    
    return OrderResponse(
        order_id=result.order,
        symbol=order_request.symbol,
        volume=order_request.volume,
        price=result.price,
        type=order_request.order_type,
        comment=order_request.comment
    )

@app.get("/orders")
async def get_orders(connection: MT5Connection = Depends(get_mt5_connection)):
    orders = mt5.orders_get()
    if orders is None:
        return []
    
    return [
        {
            "ticket": order.ticket,
            "symbol": order.symbol,
            "type": "buy" if order.type == mt5.ORDER_TYPE_BUY else "sell",
            "volume": order.volume_current,
            "price_open": order.price_open,
            "sl": order.sl,
            "tp": order.tp,
            "profit": order.profit,
            "comment": order.comment
        }
        for order in orders
    ]

@app.delete("/order/{order_id}")
async def close_order(order_id: int, connection: MT5Connection = Depends(get_mt5_connection)):
    order = mt5.orders_get(ticket=order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    
    order = order[0]
    close_type = mt5.ORDER_TYPE_SELL if order.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    price = mt5.symbol_info_tick(order.symbol).ask if close_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(order.symbol).bid
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": order.symbol,
        "volume": order.volume_current,
        "type": close_type,
        "position": order.ticket,
        "price": price,
        "magic": order.magic,
        "comment": "Closed by API",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        raise HTTPException(
            status_code=400, 
            detail=f"Close order failed: {result.comment} (error code: {result.retcode})"
        )
    
    return {"message": f"Order {order_id} closed successfully"}

# -------------------------------
# Entrypoint
# -------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
