# from datetime import datetime
# from typing import Optional
# from pydantic import BaseModel, Field

# class MarketData(BaseModel):
#     symbol: str = Field(..., description="Standardized display symbol")
#     exchange: str = Field(..., description='"FYERS", "ALPACA", "MT5", or "BROKER4"')
#     brokerSymbol: Optional[str] = Field(None, description="Raw broker symbol if different")
#     instrumentType: Optional[str] = Field(None, description='"Futures" | "Options" | "Forex" | "Crypto"')
#     ltp: float = Field(..., description="Last traded price")
#     bid: Optional[float] = None
#     ask: Optional[float] = None
#     volume: Optional[float] = None
#     oi: Optional[float] = None
#     updatedAt: datetime = Field(default_factory=datetime.utcnow)
from datetime import datetime
from app.database import db

class MarketData:
    collection = db.market_data

    @staticmethod
    async def save(data: dict):
        data.setdefault("updatedAt", datetime.utcnow())
        return await MarketData.collection.update_one(
            {"symbol": data["symbol"], "exchange": data["exchange"]},
            {"$set": data},
            upsert=True
        )

    @staticmethod
    async def find(symbol: str, exchange: str):
        return await MarketData.collection.find_one({"symbol": symbol, "exchange": exchange})
