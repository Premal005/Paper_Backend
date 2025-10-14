
import asyncio
import json
import logging
import os
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from app.services import fyerService

# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- Import routers and services ----
from .routers import auth, market, portfolio, order, trade, watchlist, transactions
from .services import alpacaService

# ---- FastAPI App ----
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- MongoDB Connection ----
MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client["paper_trading"]

# ---- WebSocket Connections ----
connected_clients: set[WebSocket] = set()
subscribed_symbols: set[str] = {"AAPL", "RELI", "SPY"}  # default symbols
subscribed_symbols2 = [
    # --- Top NSE 200 Stocks (Valid EQ suffix) ---
    "NSE:RELIANCE-EQ", "NSE:TCS-EQ", "NSE:HDFCBANK-EQ", "NSE:ICICIBANK-EQ",
    "NSE:INFY-EQ", "NSE:ITC-EQ", "NSE:SBIN-EQ", "NSE:HINDUNILVR-EQ",
    "NSE:BHARTIARTL-EQ", "NSE:BAJFINANCE-EQ", "NSE:LT-EQ", "NSE:ASIANPAINT-EQ",
    "NSE:AXISBANK-EQ", "NSE:HCLTECH-EQ", "NSE:MARUTI-EQ", "NSE:KOTAKBANK-EQ",
    "NSE:WIPRO-EQ", "NSE:TITAN-EQ", "NSE:ULTRACEMCO-EQ", "NSE:POWERGRID-EQ",
    "NSE:ADANIENT-EQ", "NSE:ADANIGREEN-EQ", "NSE:ADANIPORTS-EQ", "NSE:ADANIPOWER-EQ",
    "NSE:ONGC-EQ", "NSE:COALINDIA-EQ", "NSE:NTPC-EQ", "NSE:BPCL-EQ", "NSE:IOC-EQ",
    "NSE:GAIL-EQ", "NSE:VEDL-EQ", "NSE:TATASTEEL-EQ", "NSE:HINDALCO-EQ", "NSE:JSWSTEEL-EQ",
    "NSE:GRASIM-EQ", "NSE:TECHM-EQ", "NSE:M&M-EQ", "NSE:TATAMOTORS-EQ", "NSE:TATAPOWER-EQ",
    "NSE:TATACONSUM-EQ", "NSE:TATAELXSI-EQ", "NSE:PIDILITIND-EQ", "NSE:BRITANNIA-EQ",
    "NSE:HDFCLIFE-EQ", "NSE:SBILIFE-EQ", "NSE:ICICIPRULI-EQ", "NSE:ICICIGI-EQ",
    "NSE:BAJAJFINSV-EQ", "NSE:HEROMOTOCO-EQ", "NSE:EICHERMOT-EQ", "NSE:BAJAJ-AUTO-EQ",
    "NSE:DLF-EQ", "NSE:INDUSINDBK-EQ", "NSE:HAVELLS-EQ", "NSE:DIVISLAB-EQ",
    "NSE:CIPLA-EQ", "NSE:DRREDDY-EQ", "NSE:SUNPHARMA-EQ", "NSE:APOLLOHOSP-EQ",
    "NSE:TATATECH-EQ", "NSE:TATACOMM-EQ", "NSE:BANKBARODA-EQ", "NSE:PNB-EQ",
    "NSE:CANBK-EQ", "NSE:UNIONBANK-EQ", "NSE:IDFCFIRSTB-EQ", "NSE:INDIANB-EQ",
    "NSE:MANAPPURAM-EQ", "NSE:MUTHOOTFIN-EQ", "NSE:CHOLAFIN-EQ", "NSE:LICHSGFIN-EQ",
    "NSE:UBL-EQ", "NSE:GODREJCP-EQ", "NSE:COLPAL-EQ", "NSE:DABUR-EQ", "NSE:NESTLEIND-EQ",
    "NSE:BERGEPAINT-EQ", "NSE:MARICO-EQ", "NSE:PAGEIND-EQ", "NSE:LUPIN-EQ",
    "NSE:ABB-EQ", "NSE:BEL-EQ", "NSE:BHEL-EQ", "NSE:IRCTC-EQ", "NSE:HAL-EQ",
    "NSE:POLYCAB-EQ", "NSE:TVSMOTOR-EQ", "NSE:JUBLFOOD-EQ", "NSE:NYKAA-EQ",
    "NSE:PAYTM-EQ", "NSE:DMART-EQ", "NSE:DELHIVERY-EQ", "NSE:SBICARD-EQ",
    "NSE:POWERINDIA-EQ", "NSE:RECLTD-EQ", "NSE:PFC-EQ", "NSE:ABBOTINDIA-EQ",
    "NSE:NAUKRI-EQ", "NSE:LTIM-EQ", "NSE:PERSISTENT-EQ", "NSE:KPITTECH-EQ",
    "NSE:COFORGE-EQ", "NSE:MPHASIS-EQ", "NSE:IRFC-EQ", "NSE:RVNL-EQ", "NSE:NBCC-EQ",
    "NSE:SAIL-EQ", "NSE:PETRONET-EQ", "NSE:GUJGASLTD-EQ", "NSE:IGL-EQ",
    "NSE:GODREJPROP-EQ", "NSE:SOBHA-EQ", "NSE:OBEROIRLTY-EQ", "NSE:LODHA-EQ",
    "NSE:PRESTIGE-EQ", "NSE:BOSCHLTD-EQ", "NSE:SIEMENS-EQ", "NSE:CUMMINSIND-EQ",
    "NSE:ASHOKLEY-EQ", "NSE:TATACHEM-EQ", "NSE:DEEPAKNTR-EQ", "NSE:ALKEM-EQ",
    "NSE:AUBANK-EQ", "NSE:BANDHANBNK-EQ", "NSE:RBLBANK-EQ", "NSE:CANFINHOME-EQ",
    "NSE:MFSL-EQ", "NSE:PIIND-EQ", "NSE:SRF-EQ", "NSE:INDHOTEL-EQ", "NSE:TRENT-EQ",
    "NSE:JSWINFRA-EQ", "NSE:IRB-EQ", "NSE:NHPC-EQ", "NSE:SJVN-EQ", "NSE:NMDC-EQ",
    "NSE:HINDZINC-EQ", "NSE:BLUEDART-EQ", "NSE:CONCOR-EQ", "NSE:ABFRL-EQ",
    "NSE:VOLTAS-EQ", "NSE:INDIGO-EQ", "NSE:FLUOROCHEM-EQ", "NSE:SUPREMEIND-EQ",
    "NSE:ESCORTS-EQ", "NSE:COROMANDEL-EQ", "NSE:ATUL-EQ", "NSE:GLAND-EQ",
    "NSE:TORNTPHARM-EQ", "NSE:ZYDUSLIFE-EQ", "NSE:METROPOLIS-EQ", "NSE:MEDANTA-EQ",
    "NSE:RAIN-EQ", "NSE:ASTERDM-EQ", "NSE:SUNTV-EQ", "NSE:ZEEL-EQ", "NSE:PVRINOX-EQ",
    "NSE:BALRAMCHIN-EQ", "NSE:RAJESHEXPO-EQ", "NSE:SHREECEM-EQ", "NSE:ACC-EQ",
    "NSE:AMBUJACEM-EQ", "NSE:DALBHARAT-EQ", "NSE:JKCEMENT-EQ", "NSE:SBIN28OCT900CE"
    
]

  # instead of "RELI", "ITC"

alpaca_ws = None  # will be set when Alpaca WS connects


async def broadcast(message: dict):
    """Send tick to all connected WebSocket clients"""
    if not connected_clients:
        return
    dead_clients = set()
    for ws in connected_clients:
        try:
            await ws.send_json(message)
        except Exception:
            dead_clients.add(ws)
    connected_clients.difference_update(dead_clients)


@app.websocket("/ws/market")
async def market_ws(ws: WebSocket):
    """WebSocket for streaming market ticks + dynamic symbol subscriptions"""
    global alpaca_ws

    await ws.accept()
    connected_clients.add(ws)
    logger.info(f"🟢 Client connected: {ws.client}")

    await ws.send_json({"msg": "✅ Connected to Market WS"})

    try:
        while True:
            data = await ws.receive_json()
            action = data.get("action")
            symbol = data.get("symbol")

            if action == "subscribe" and symbol:
                symbol = symbol.upper()
                if symbol not in subscribed_symbols:
                    subscribed_symbols.add(symbol)
                    await ws.send_json({"msg": f"🟢 Subscribing to {symbol}"})
                    # Tell Alpaca WS to subscribe live
                    if alpaca_ws:
                        try:
                            await alpaca_ws.send(json.dumps({
                                "action": "subscribe",
                                "quotes": [symbol]
                            }))
                            logger.info(f"✅ Live subscribed {symbol}")
                        except Exception as e:
                            logger.warning(f"⚠️ Failed live subscribe {symbol}: {e}")
            else:
                await ws.send_json({"msg": "❌ Invalid request"})

    except Exception:
        logger.info(f"🔴 Client disconnected: {ws.client}")
    finally:
        connected_clients.discard(ws)
        await ws.close()



# ---- Register Routers ----
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(market.router, prefix="/api/market", tags=["market"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(order.router, prefix="/api/orders", tags=["orders"])
app.include_router(trade.router, prefix="/api/trades", tags=["trades"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(alpacaService.router, prefix="/api/alpaca", tags=["alpaca"])


# ---- Root ----
@app.get("/")
@app.head("/")
async def root():
    return {"message": "Paper Trading Backend is running..."}



# ---- Startup ----
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Paper Trading Backend...")
    # watchlist.start_watchlist_updater(app)




    from app.routers.order import process_pending_orders
    asyncio.create_task(process_pending_orders())




    async def start_alpaca():
        # Pass globals so Alpaca WS can update
        await alpacaService.start_alpaca_feed(
            broadcast=broadcast,
            subscribed_symbols=subscribed_symbols,
            ws_ref=lambda ws: globals().__setitem__("alpaca_ws", ws)
        )

    # async def start_fyers():
    #     await fyerService.start_fyers_feed(
    #         broadcast=broadcast,
    #         subscribed_symbols=subscribed_symbols
    #     )

    asyncio.create_task(start_alpaca())
    # asyncio.create_task(start_fyers())
    loop = asyncio.get_running_loop()
    
    # Start Fyers WebSocket feed
    fyerService.start_fyers_feed(
        broadcast=broadcast,
        main_loop=loop,
        subscribed_symbols=subscribed_symbols2
    )

    # Start processing Fyers messages
    asyncio.create_task(fyerService.process_fyers_messages())

    from app.routers import watchlist
    watchlist.start_watchlist_updater(loop)
    
    logger.info("✅ Feeds launched")

    def handle_exception(loop, context):
        msg = context.get("exception", context["message"])
        logger.error(f"Unhandled exception: {msg}")

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)