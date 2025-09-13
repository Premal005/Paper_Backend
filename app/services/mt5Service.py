import asyncio
import json
import logging
from datetime import datetime
from typing import Callable, Any
import redis.asyncio as redis
from config import Config
from models.marketModel import MarketData

logger = logging.getLogger(__name__)

async def start_mt5_feed(broadcast: Callable[[Any], None]):
    redis_url = Config.REDIS_URL
    channel = Config.MT5_REDIS_CHANNEL
    
    if not redis_url:
        logger.warning("REDIS_URL missing; skipping MT5 feed")
        return
        
    try:
        r = await redis.from_url(redis_url)
        pubsub = r.pubsub()
        await pubsub.subscribe(channel)
        logger.info("✅ Subscribed to MT5 Redis channel")
        
        while True:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message is not None and message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        tick = {
                            "symbol": data.get("symbol"),
                            "exchange": "MT5",
                            "brokerSymbol": data.get("symbol"),
                            "instrumentType": data.get("instrumentType") or "Forex",
                            "ltp": data.get("ltp") or ((data.get("bid", 0) + data.get("ask", 0)) / 2),
                            "bid": data.get("bid"),
                            "ask": data.get("ask"),
                            "volume": data.get("volume"),
                            "timestamp": data.get("timestamp") or datetime.now().timestamp() * 1000
                        }

                        await MarketData.update_one(
                            {"symbol": tick["symbol"], "exchange": "MT5"},
                            {
                                "$set": {
                                    "brokerSymbol": tick["brokerSymbol"],
                                    "instrumentType": tick["instrumentType"],
                                    "ltp": tick["ltp"],
                                    "bid": tick["bid"],
                                    "ask": tick["ask"],
                                    "volume": tick["volume"],
                                    "updatedAt": datetime.now()
                                }
                            },
                            upsert=True
                        )

                        broadcast({**tick, "source": "MT5"})
                    except Exception as e:
                        logger.error(f"Error processing MT5 message: {e}")
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in MT5 feed: {e}")
                await asyncio.sleep(5)
                
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        await asyncio.sleep(5)