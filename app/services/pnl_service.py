# services/pnl_service.py
from datetime import datetime, timedelta
from bson import ObjectId
from app.models.userModel import User
from app.models.orderModel import Order

class PnLService:
    
    @staticmethod
    async def calculate_margin_used(entry_price: float, quantity: int, leverage: int = 20) -> float:
        """Calculate margin used: (price * quantity) / leverage"""
        if leverage == 0:
            leverage = 20
        return (entry_price * quantity) / leverage
    
    @staticmethod
    async def calculate_active_pnl(user_id: str) -> float:
        """Calculate sum of all PnL of active trades only"""
        active_trades = await Order.get_active_trades(user_id)
        total_pnl = 0
        
        for trade in active_trades:
            if trade.get("currentPrice") and trade.get("executedPrice"):
                quantity = trade.get("quantity", 0)
                entry_price = trade.get("executedPrice", 0)
                current_price = trade.get("currentPrice", 0)
                
                if trade.get("side") == "buy":
                    pnl = (current_price - entry_price) * quantity
                else:  # sell/short
                    pnl = (entry_price - current_price) * quantity
                
                total_pnl += pnl
                
                # Update the trade's current PnL
                await Order.update_pnl(str(trade["_id"]), pnl, current_price)
        
        return total_pnl
    
    @staticmethod
    async def calculate_today_pnl(user_id: str) -> float:
        """Calculate today's PnL"""
        return await Order.get_today_pnl(user_id)
    
    
    @staticmethod
    async def calculate_margin_level(user_id: str) -> float:
        """Calculate margin level: (available margin / used margin) * 100%"""
        user = await User.get_full_user(user_id)
        if not user:
            return 0
        
        margin_available = user.get("marginAvailable", 0)
        margin_used = user.get("marginUsed", 0)
        
        if margin_used == 0:
            return 0
            
        return (margin_available / margin_used) * 100
    
    @staticmethod
    async def update_trade_prices(symbol: str, exchange: str, current_price: float):
        """Update current prices for all active trades of a symbol"""
        # Find all active trades for this symbol
        cursor = Order.collection.find({
            "symbol": symbol,
            "exchange": exchange,
            "isClosed": False,
            "status": "active"
        })
        
        active_trades = await cursor.to_list(length=None)
        
        for trade in active_trades:
            quantity = trade.get("quantity", 0)
            entry_price = trade.get("executedPrice", 0)
            
            if trade.get("side") == "buy":
                pnl = (current_price - entry_price) * quantity
            else:  # sell/short
                pnl = (entry_price - current_price) * quantity
            
            await Order.update_pnl(str(trade["_id"]), pnl, current_price)
    
    @staticmethod
    async def calculate_net_pnl(user_id: str) -> float:
        """Calculate net PnL: ledger balance minus initial investment"""
        user = await User.get_full_user(user_id)
        if not user:
            return 0
        
        ledger_balance = user.get("ledgerBalance", 0)
        initial_investment = user.get("initialInvestment", 100000)  # Default to 100k
        
        return ledger_balance - initial_investment