
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
    "NSE:AMBUJACEM-EQ", "NSE:DALBHARAT-EQ", "NSE:JKCEMENT-EQ", "NSE:RELIANCE25DECFUT","NSE:BANKNIFTY25DECFUT","NSE:NIFTY25DECFUT", "NSE:FINNIFTY25DECFUT", "NSE:MIDCPNIFTY25DECFUT",
    "NSE:TCS25DECFUT", "NSE:HDFCBANK25DECFUT", "NSE:ICICIBANK25DECFUT",
    "NSE:INFY25DECFUT", "NSE:ITC25DECFUT", "NSE:SBIN25DECFUT", "NSE:HINDUNILVR25DECFUT",
    "NSE:BHARTIARTL25DECFUT", "NSE:BAJFINANCE25DECFUT", "NSE:LT25DECFUT", "NSE:ASIANPAINT25DECFUT",
    "NSE:AXISBANK25DECFUT", "NSE:HCLTECH25DECFUT", "NSE:MARUTI25DECFUT", "NSE:KOTAKBANK25DECFUT",
    "NSE:WIPRO25DECFUT", "NSE:TITAN25DECFUT", "NSE:ULTRACEMCO25DECFUT", "NSE:POWERGRID25DECFUT",
    "NSE:ADANIENT25DECFUT", "NSE:ADANIGREEN25DECFUT", "NSE:ADANIPORTS25DECFUT",
    "NSE:ONGC25DECFUT", "NSE:COALINDIA25DECFUT", "NSE:NTPC25DECFUT", "NSE:BPCL25DECFUT", "NSE:IOC25DECFUT","NSE:GAIL25DECFUT", "NSE:VEDL25DECFUT", "NSE:TATASTEEL25DECFUT", "NSE:HINDALCO25DECFUT", "NSE:JSWSTEEL25DECFUT",
    "NSE:GRASIM25DECFUT", "NSE:TECHM25DECFUT", "NSE:M&M25DECFUT", "NSE:TATAMOTORS25DECFUT", "NSE:TATAPOWER25DECFUT",
    "NSE:TATACONSUM25DECFUT", "NSE:TATAELXSI25DECFUT", "NSE:PIDILITIND25DECFUT", "NSE:BRITANNIA25DECFUT",
    "NSE:HDFCLIFE25DECFUT", "NSE:SBILIFE25DECFUT", "NSE:ICICIPRULI25DECFUT", "NSE:ICICIGI25DECFUT",
    "NSE:BAJAJFINSV25DECFUT", "NSE:HEROMOTOCO25DECFUT", "NSE:EICHERMOT25DECFUT", "NSE:BAJAJ-AUTO25DECFUT",
    "NSE:DLF25DECFUT", "NSE:INDUSINDBK25DECFUT", "NSE:HAVELLS25DECFUT", "NSE:DIVISLAB25DECFUT",
    "NSE:CIPLA25DECFUT", "NSE:DRREDDY25DECFUT", "NSE:SUNPHARMA25DECFUT", "NSE:APOLLOHOSP25DECFUT",
    "NSE:TATATECH25DECFUT", "NSE:BANKBARODA25DECFUT", "NSE:PNB25DECFUT",
    "NSE:CANBK25DECFUT", "NSE:UNIONBANK25DECFUT", "NSE:IDFCFIRSTB25DECFUT", "NSE:INDIANB25DECFUT",
    
    # More Futures
    "NSE:MANAPPURAM25DECFUT", "NSE:MUTHOOTFIN25DECFUT", "NSE:CHOLAFIN25DECFUT", "NSE:LICHSGFIN25DECFUT",
    "NSE:GODREJCP25DECFUT", "NSE:COLPAL25DECFUT", "NSE:DABUR25DECFUT", "NSE:NESTLEIND25DECFUT",
     "NSE:MARICO25DECFUT", "NSE:PAGEIND25DECFUT", "NSE:LUPIN25DECFUT",
    "NSE:ABB25DECFUT", "NSE:BEL25DECFUT", "NSE:BHEL25DECFUT", "NSE:IRCTC25DECFUT", "NSE:HAL25DECFUT",
    "NSE:POLYCAB25DECFUT", "NSE:TVSMOTOR25DECFUT", "NSE:JUBLFOOD25DECFUT", "NSE:NYKAA25DECFUT",
    "NSE:PAYTM25DECFUT", "NSE:DMART25DECFUT", "NSE:DELHIVERY25DECFUT", "NSE:SBICARD25DECFUT",
    "NSE:POWERINDIA25DECFUT", "NSE:RECLTD25DECFUT", "NSE:PFC25DECFUT",
    "NSE:NAUKRI25DECFUT", "NSE:LTIM25DECFUT", "NSE:PERSISTENT25DECFUT", "NSE:KPITTECH25DECFUT",
    "NSE:COFORGE25DECFUT", "NSE:MPHASIS25DECFUT", "NSE:IRFC25DECFUT", "NSE:RVNL25DECFUT", "NSE:NBCC25DECFUT",
    "NSE:SAIL25DECFUT", "NSE:PETRONET25DECFUT",
    "NSE:GODREJPROP25DECFUT", "NSE:OBEROIRLTY25DECFUT", "NSE:LODHA25DECFUT",
    "NSE:PRESTIGE25DECFUT", "NSE:BOSCHLTD25DECFUT", "NSE:SIEMENS25DECFUT", "NSE:CUMMINSIND25DECFUT",
    "NSE:ASHOKLEY25DECFUT", "NSE:ALKEM25DECFUT",
    "NSE:AUBANK25DECFUT", "NSE:BANDHANBNK25DECFUT", "NSE:RBLBANK25DECFUT",
    "NSE:MFSL25DECFUT", "NSE:PIIND25DECFUT", "NSE:SRF25DECFUT", "NSE:INDHOTEL25DECFUT", "NSE:TRENT25DECFUT",
    "NSE:NHPC25DECFUT", "NSE:NMDC25DECFUT",
    "NSE:HINDZINC25DECFUT", "NSE:CONCOR25DECFUT",
    "NSE:VOLTAS25DECFUT", "NSE:INDIGO25DECFUT", "NSE:SUPREMEIND25DECFUT",
    "NSE:TORNTPHARM25DECFUT", "NSE:ZYDUSLIFE25DECFUT", "NSE:SHREECEM25DECFUT",
    "NSE:AMBUJACEM25DECFUT", "NSE:DALBHARAT25DECFUT","NSE:BANKNIFTY25OCT49000CE",


    "NSE:BANKNIFTY25OCT49500CE", "NSE:BANKNIFTY25OCT50000CE",
    "NSE:BANKNIFTY25OCT50500CE", "NSE:BANKNIFTY25OCT51000CE", "NSE:BANKNIFTY25OCT51500CE",
    "NSE:BANKNIFTY25OCT52000CE", "NSE:BANKNIFTY25OCT49000PE", "NSE:BANKNIFTY25OCT49500PE",
    "NSE:BANKNIFTY25OCT50000PE", "NSE:BANKNIFTY25OCT50500PE", "NSE:BANKNIFTY25OCT51000PE",
    "NSE:BANKNIFTY25OCT51500PE", "NSE:BANKNIFTY25OCT52000PE",
    
    "NSE:BANKNIFTY25NOV49000CE", "NSE:BANKNIFTY25NOV50000CE", "NSE:BANKNIFTY25NOV51000CE",
    "NSE:BANKNIFTY25NOV52000CE", "NSE:BANKNIFTY25NOV49000PE", "NSE:BANKNIFTY25NOV50000PE",
    "NSE:BANKNIFTY25NOV51000PE", "NSE:BANKNIFTY25NOV52000PE",
    
    # NIFTY Options
    "NSE:NIFTY25OCT22000CE", "NSE:NIFTY25OCT22500CE", "NSE:NIFTY25OCT23000CE",
    "NSE:NIFTY25OCT23500CE", "NSE:NIFTY25OCT24000CE", "NSE:NIFTY25OCT22000PE",
    "NSE:NIFTY25OCT22500PE", "NSE:NIFTY25OCT23000PE", "NSE:NIFTY25OCT23500PE",
    "NSE:NIFTY25OCT24000PE",
    
    "NSE:NIFTY25NOV22000CE", "NSE:NIFTY25NOV23000CE", "NSE:NIFTY25NOV24000CE",
    "NSE:NIFTY25NOV22000PE", "NSE:NIFTY25NOV23000PE", "NSE:NIFTY25NOV24000PE",
    
    # MIDCPNIFTY Options
    "NSE:MIDCPNIFTY25OCT11000CE", "NSE:MIDCPNIFTY25OCT11500CE", "NSE:MIDCPNIFTY25OCT12000CE",
    "NSE:MIDCPNIFTY25OCT11000PE", "NSE:MIDCPNIFTY25OCT11500PE", "NSE:MIDCPNIFTY25OCT12000PE",
    
    # Stock Options - RELIANCE
    
    # TCS Options
    "NSE:TCS25OCT3800CE", "NSE:TCS25OCT4000CE", "NSE:TCS25OCT4200CE",
    "NSE:TCS25OCT3800PE", "NSE:TCS25OCT4000PE", "NSE:TCS25OCT4200PE",
    
    # HDFCBANK Options
    
    # ICICIBANK Options
    "NSE:ICICIBANK25OCT1000CE", "NSE:ICICIBANK25OCT1050CE", "NSE:ICICIBANK25OCT1100CE",
    "NSE:ICICIBANK25OCT1000PE", "NSE:ICICIBANK25OCT1050PE", "NSE:ICICIBANK25OCT1100PE",
    
    # INFY Options
    "NSE:INFY25OCT1600CE", "NSE:INFY25OCT1700CE", "NSE:INFY25OCT1800CE",
    "NSE:INFY25OCT1600PE", "NSE:INFY25OCT1700PE", "NSE:INFY25OCT1800PE",
    
    # SBIN Options
    "NSE:SBIN25OCT600CE", "NSE:SBIN25OCT650CE", "NSE:SBIN25OCT700CE",
    "NSE:SBIN25OCT600PE", "NSE:SBIN25OCT650PE", "NSE:SBIN25OCT700PE",
    
    # HINDUNILVR Options
    "NSE:HINDUNILVR25OCT2400CE", "NSE:HINDUNILVR25OCT2500CE", "NSE:HINDUNILVR25OCT2600CE",
    "NSE:HINDUNILVR25OCT2400PE", "NSE:HINDUNILVR25OCT2500PE", "NSE:HINDUNILVR25OCT2600PE",
    
    # BHARTIARTL Options
    "NSE:BHARTIARTL25OCT1200CE", "NSE:BHARTIARTL25OCT1300CE", "NSE:BHARTIARTL25OCT1400CE",
    "NSE:BHARTIARTL25OCT1200PE", "NSE:BHARTIARTL25OCT1300PE", "NSE:BHARTIARTL25OCT1400PE",
    
    # BAJFINANCE Options
    
    # LT Options
    "NSE:LT25OCT3200CE", "NSE:LT25OCT3400CE", "NSE:LT25OCT3600CE",
    "NSE:LT25OCT3200PE", "NSE:LT25OCT3400PE", "NSE:LT25OCT3600PE",
    
    # AXISBANK Options
    "NSE:AXISBANK25OCT1100CE", "NSE:AXISBANK25OCT1150CE", "NSE:AXISBANK25OCT1200CE",
    "NSE:AXISBANK25OCT1100PE", "NSE:AXISBANK25OCT1150PE", "NSE:AXISBANK25OCT1200PE",
    
    # KOTAKBANK Options
    "NSE:KOTAKBANK25OCT1800CE", "NSE:KOTAKBANK25OCT1900CE", "NSE:KOTAKBANK25OCT2000CE",
    "NSE:KOTAKBANK25OCT1800PE", "NSE:KOTAKBANK25OCT1900PE", "NSE:KOTAKBANK25OCT2000PE",
    
    # ADANIENT Options
    "NSE:ADANIENT25OCT2500CE", "NSE:ADANIENT25OCT2700CE", "NSE:ADANIENT25OCT2900CE",
    "NSE:ADANIENT25OCT2500PE", "NSE:ADANIENT25OCT2700PE", "NSE:ADANIENT25OCT2900PE",
    
    # TATAMOTORS Options
    "NSE:TATAMOTORS25OCT600CE", "NSE:TATAMOTORS25OCT650CE", "NSE:TATAMOTORS25OCT700CE",
    "NSE:TATAMOTORS25OCT600PE", "NSE:TATAMOTORS25OCT650PE", "NSE:TATAMOTORS25OCT700PE",
    
    # MARUTI Options
    "NSE:MARUTI25OCT12000CE", "NSE:MARUTI25OCT12500CE", "NSE:MARUTI25OCT13000CE",
    "NSE:MARUTI25OCT12000PE", "NSE:MARUTI25OCT12500PE", "NSE:MARUTI25OCT13000PE",
    
    # TATASTEEL Options
    "NSE:TATASTEEL25OCT140CE", "NSE:TATASTEEL25OCT150CE", "NSE:TATASTEEL25OCT160CE",
    "NSE:TATASTEEL25OCT140PE", "NSE:TATASTEEL25OCT150PE", "NSE:TATASTEEL25OCT160PE",
    
    # More Stock Options for different expiries
    "NSE:TCS25NOV4000CE", "NSE:TCS25NOV4200CE", "NSE:TCS25NOV4000PE",
    
    # ITC Options
    "NSE:ITC25OCT400CE", "NSE:ITC25OCT450CE", "NSE:ITC25OCT500CE",
    "NSE:ITC25OCT400PE", "NSE:ITC25OCT450PE", "NSE:ITC25OCT500PE",
    
    # WIPRO Options

    # ONGC Options
    "NSE:ONGC25OCT200CE", "NSE:ONGC25OCT220CE", "NSE:ONGC25OCT240CE",
    "NSE:ONGC25OCT200PE", "NSE:ONGC25OCT220PE", "NSE:ONGC25OCT240PE",
    
    # COALINDIA Options
    "NSE:COALINDIA25OCT400CE", "NSE:COALINDIA25OCT450CE", "NSE:COALINDIA25OCT500CE",
    "NSE:COALINDIA25OCT400PE", "NSE:COALINDIA25OCT450PE", "NSE:COALINDIA25OCT500PE",
    
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

    from app.services.mt5_websocket_service import mt5_websocket_service
    mt5_websocket_service.start()


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
    await asyncio.sleep(5)
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