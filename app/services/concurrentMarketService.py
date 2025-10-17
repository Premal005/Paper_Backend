# import asyncio
# import logging
# from datetime import datetime, timedelta
# from typing import Dict, List, Set
# from collections import defaultdict

# logger = logging.getLogger(__name__)

# class ConcurrentMarketDataService:
#     def __init__(self):
#         self.cache = {}
#         self.cache_ttl = 5  # 5 seconds cache
#         self.symbol_exchange_map = defaultdict(set)  # symbol_exchange -> user_ids
#         self.user_symbols_map = defaultdict(set)    # user_id -> symbol_exchange_keys
        
    
    
    
#     async def update_single_watchlist(self, user_id: str):
#         """Update a single user's watchlist immediately"""
#         try:
#             from app.models.watchlistModel import Watchlist
            
#             watchlist = await Watchlist.find_by_user(user_id)
#             if not watchlist:
#                 return
                
#             # Use the existing batch update logic for this single user
#             users_watchlists = [watchlist]
            
#             # Collect all unique symbols
#             all_symbols_map = defaultdict(list)
#             user_watchlist_map = {user_id: watchlist}
            
#             for symbol_data in watchlist.get("symbols", []):
#                 symbol = symbol_data["symbol"].upper()
#                 exchange = symbol_data["exchange"].upper()
#                 all_symbols_map[exchange].append(symbol)
            
#             # Fetch data and update
#             updated_data = await self._fetch_all_symbols_concurrently(all_symbols_map)
#             await self._update_user_watchlist(user_id, watchlist, updated_data)
            
#             logger.debug(f"✅ Immediately updated watchlist for user {user_id}")
            
#         except Exception as e:
#             logger.error(f"Error in immediate update for user {user_id}: {e}")
    
    
#     async def update_all_watchlists_concurrently(self):
#         """Update all watchlists concurrently with batch processing"""
#         try:
#             from app.models.watchlistModel import Watchlist
#             from app.services.watchlistWebSocket import watchlist_ws_manager
            
#             # Get all watchlists
#             users_watchlists = await Watchlist.get_all()
#             if not users_watchlists:
#                 return
                
#             logger.info(f"🔄 Concurrently updating {len(users_watchlists)} watchlists...")
            
#             # Collect all unique symbols across all watchlists
#             all_symbols_map = defaultdict(list)  # exchange -> [symbols]
#             user_watchlist_map = {}  # user_id -> watchlist_data
            
#             for watchlist in users_watchlists:
#                 user_id = str(watchlist["userId"])
#                 user_watchlist_map[user_id] = watchlist
                
#                 for symbol_data in watchlist.get("symbols", []):
#                     symbol = symbol_data["symbol"].upper()
#                     exchange = symbol_data["exchange"].upper()
#                     all_symbols_map[exchange].append(symbol)
            
#             # Fetch data for all symbols concurrently by exchange
#             updated_data = await self._fetch_all_symbols_concurrently(all_symbols_map)
            
#             # Update each user's watchlist and send WS updates
#             update_tasks = []
#             for user_id, watchlist in user_watchlist_map.items():
#                 task = self._update_user_watchlist(user_id, watchlist, updated_data)
#                 update_tasks.append(task)
            
#             # Run all user updates concurrently
#             await asyncio.gather(*update_tasks, return_exceptions=True)
            
#             logger.info("✅ All watchlists updated concurrently")
            
#         except Exception as e:
#             logger.error(f"❌ Error in concurrent watchlist update: {e}")
    
#     async def _fetch_all_symbols_concurrently(self, symbols_map: Dict[str, List[str]]):
#         """Fetch all symbols concurrently organized by exchange"""
#         from app.routers.market import get_quote_alpaca, get_quote_fyers, get_quote_mt5
        
#         all_results = {}
        
#         # Create tasks for each exchange batch
#         tasks = []
#         for exchange, symbols in symbols_map.items():
#             unique_symbols = list(set(symbols))  # Remove duplicates
#             if exchange == "ALPACA":
#                 tasks.append(self._fetch_alpaca_symbols(unique_symbols))
#             elif exchange == "FYERS":
#                 tasks.append(self._fetch_fyers_symbols(unique_symbols))
#             elif exchange == "MT5":
#                 tasks.append(self._fetch_mt5_symbols(unique_symbols))
#             else:
#                 # Try all sources for unknown exchanges
#                 tasks.append(self._fetch_mixed_symbols(unique_symbols))
        
#         # Run all exchange fetches concurrently
#         results = await asyncio.gather(*tasks, return_exceptions=True)
        
#         # Combine all results
#         for result in results:
#             if isinstance(result, dict):
#                 all_results.update(result)
                
#         return all_results
    
#     async def _fetch_alpaca_symbols(self, symbols: List[str]):
#         """Fetch multiple Alpaca symbols concurrently"""
#         from app.routers.market import get_quote_alpaca
        
#         tasks = [get_quote_alpaca(symbol) for symbol in symbols]
#         results = await asyncio.gather(*tasks, return_exceptions=True)
        
#         return {f"{symbol}_ALPACA": result for symbol, result in zip(symbols, results) 
#                 if not isinstance(result, Exception) and result}
    
#     async def _fetch_fyers_symbols(self, symbols: List[str]):
#         """Fetch multiple FYERS symbols concurrently"""
#         from app.routers.market import get_quote_fyers
        
#         tasks = [get_quote_fyers(symbol) for symbol in symbols]
#         results = await asyncio.gather(*tasks, return_exceptions=True)
        
#         return {f"{symbol}_FYERS": result for symbol, result in zip(symbols, results) 
#                 if not isinstance(result, Exception) and result}
    
#     async def _fetch_mt5_symbols(self, symbols: List[str]):
#         """Fetch multiple MT5 symbols concurrently"""
#         from app.routers.market import get_quote_mt5
        
#         tasks = [get_quote_mt5(symbol) for symbol in symbols]
#         results = await asyncio.gather(*tasks, return_exceptions=True)
        
#         return {f"{symbol}_MT5": result for symbol, result in zip(symbols, results) 
#                 if not isinstance(result, Exception) and result}
    
#     async def _fetch_mixed_symbols(self, symbols: List[str]):
#         """Try all sources for symbols with unknown exchange"""
#         results = {}
#         for symbol in symbols:
#             # Try all sources and take the first successful one
#             from app.routers.market import get_quote_alpaca, get_quote_fyers, get_quote_mt5
            
#             alpaca_data = await get_quote_alpaca(symbol)
#             if alpaca_data:
#                 results[f"{symbol}_ALPACA"] = alpaca_data
#                 continue
                
#             fyers_data = await get_quote_fyers(symbol)
#             if fyers_data:
#                 results[f"{symbol}_FYERS"] = fyers_data
#                 continue
                
#             mt5_data = await get_quote_mt5(symbol)
#             if mt5_data:
#                 results[f"{symbol}_MT5"] = mt5_data
                
#         return results
    
#     async def _update_user_watchlist(self, user_id: str, watchlist: dict, updated_data: dict):
#         """Update a single user's watchlist and send WS update"""
#         from app.models.watchlistModel import Watchlist
#         from app.services.watchlistWebSocket import watchlist_ws_manager
        
#         try:
#             updated_symbols = []
#             needs_update = False
#             individual_updates = []
            
#             for symbol_data in watchlist.get("symbols", []):
#                 symbol = symbol_data["symbol"].upper()
#                 exchange = symbol_data["exchange"].upper()
#                 cache_key = f"{symbol}_{exchange}"
                
#                 if cache_key in updated_data and updated_data[cache_key]:
#                     result = updated_data[cache_key]
#                     # Update symbol data
#                     updated_symbol = {
#                         **symbol_data,  # Keep existing data
#                         "current_price": round(result.get("last_price", 0.0), 2),
#                         "day_change": result.get("day_change", 0.0),
#                         "day_change_percentage": result.get("day_change_percentage", 0.0),
#                         "last_updated": datetime.now().isoformat()
#                     }
                    
#                     # Remove note if we have fresh data
#                     if "note" in updated_symbol and updated_symbol.get("note") == "No market data available":
#                         del updated_symbol["note"]
                        
#                     updated_symbols.append(updated_symbol)
#                     needs_update = True
                    
#                     # Also prepare individual update for more reliability
#                     individual_updates.append({
#                         "symbol": symbol,
#                         "exchange": exchange,
#                         "data": {
#                             "current_price": round(result.get("last_price", 0.0), 2),
#                             "day_change": result.get("day_change", 0.0),
#                             "day_change_percentage": result.get("day_change_percentage", 0.0),
#                             "last_updated": datetime.now().isoformat()
#                         }
#                     })
#                 else:
#                     # Keep existing data if no update available
#                     updated_symbols.append(symbol_data)
            
#             if needs_update:
#                 # METHOD 1: Update entire watchlist (more reliable)
#                 update_result = await Watchlist.update_symbols(user_id, updated_symbols)
                
#                 # METHOD 2: Also update symbols individually for extra reliability
#                 individual_tasks = []
#                 for update in individual_updates:
#                     task = Watchlist.update_symbol_data(
#                         user_id, 
#                         update["symbol"], 
#                         update["exchange"], 
#                         update["data"]
#                     )
#                     individual_tasks.append(task)
                
#                 # Run individual updates concurrently
#                 await asyncio.gather(*individual_tasks, return_exceptions=True)
                
#                 logger.debug(f"✅ Updated watchlist for user {user_id}: {len(individual_updates)} symbols")
                
#                 # Send WebSocket update
#                 await watchlist_ws_manager.send_personal_message({
#                     "type": "watchlist_update",
#                     "data": updated_symbols,
#                     "timestamp": datetime.now().isoformat()
#                 }, user_id)
                    
#         except Exception as e:
#             logger.error(f"Error updating watchlist for user {user_id}: {e}")

    

#     async def get_symbol_data(self, symbol: str, exchange: str):
#         """Get single symbol data for immediate use (e.g., when adding to watchlist)"""
#         try:
#             from app.routers.market import get_quote_alpaca, get_quote_fyers, get_quote_mt5
            
#             symbol = symbol.upper()
#             exchange = exchange.upper()
            
#             # Fetch based on exchange
#             if exchange == "ALPACA":
#                 result = await get_quote_alpaca(symbol)
#             elif exchange == "FYERS":
#                 result = await get_quote_fyers(symbol)
#             elif exchange == "MT5":
#                 result = await get_quote_mt5(symbol)
#             else:
#                 # Try all sources for unknown exchange
#                 result = await get_quote_alpaca(symbol)
#                 if not result:
#                     result = await get_quote_fyers(symbol)
#                 if not result:
#                     result = await get_quote_mt5(symbol)
            
#             if result:
#                 return {
#                     "current_price": round(result.get("last_price", 0.0), 2),
#                     "day_change": result.get("day_change", 0.0),
#                     "day_change_percentage": result.get("day_change_percentage", 0.0)
#                 }
#             else:
#                 return None
                
#         except Exception as e:
#             logger.error(f"Error fetching single symbol data for {symbol} ({exchange}): {e}")
#             return None

# # Global instance
# concurrent_market_service = ConcurrentMarketDataService()




import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set
from collections import defaultdict

logger = logging.getLogger(__name__)

class ConcurrentMarketDataService:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 5  # 5 seconds cache
        self.symbol_exchange_map = defaultdict(set)  # symbol_exchange -> user_ids
        self.user_symbols_map = defaultdict(set)    # user_id -> symbol_exchange_keys
        self.last_symbol_update = {}  # Track last update time per symbol
        
    async def update_single_symbol(self, symbol: str, exchange: str):
        """Update a single symbol across all watchlists that contain it"""
        try:
            from app.models.watchlistModel import Watchlist
            from app.services.watchlistWebSocket import watchlist_ws_manager
            
            # Get fresh market data for this symbol
            market_data = await self.get_symbol_data(symbol, exchange)
            if not market_data:
                logger.warning(f"No market data for {symbol} ({exchange})")
                return
            
            # Add timestamp
            market_data["last_updated"] = datetime.utcnow().isoformat() + "Z"
            
            # Find all watchlists containing this symbol
            watchlists = await Watchlist.get_watchlists_by_symbol(symbol, exchange)
            
            if not watchlists:
                return
            
            # Update each watchlist concurrently
            update_tasks = []
            ws_tasks = []
            
            for watchlist in watchlists:
                user_id = str(watchlist["userId"])
                
                # Update database
                update_task = Watchlist.update_single_symbol_data(
                    user_id, symbol, exchange, market_data
                )
                update_tasks.append(update_task)
                
                # Send WebSocket update
                ws_task = watchlist_ws_manager.send_personal_message({
                    "type": "symbol_update",
                    "symbol": symbol,
                    "exchange": exchange,
                    "data": market_data,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }, user_id)
                ws_tasks.append(ws_task)
            
            # Execute all updates concurrently
            if update_tasks:
                results = await asyncio.gather(*update_tasks, return_exceptions=True)
                successful_updates = sum(1 for r in results if not isinstance(r, Exception))
                logger.debug(f"✅ Updated {symbol} for {successful_updates}/{len(watchlists)} users")
            
            if ws_tasks:
                await asyncio.gather(*ws_tasks, return_exceptions=True)
                
            # Update last update time
            self.last_symbol_update[f"{exchange}:{symbol}"] = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"❌ Error updating single symbol {symbol} ({exchange}): {e}")
    
    async def update_all_watchlists_concurrently(self):
        """Per-symbol concurrent updates - much more efficient"""
        try:
            from app.models.watchlistModel import Watchlist
            
            # Get all unique symbols across all watchlists
            symbols_to_track = await Watchlist.get_all_symbols_to_track()
            
            if not symbols_to_track:
                logger.debug("No symbols to track")
                return
            
            logger.info(f"🔄 Updating {len(symbols_to_track)} unique symbols per-second...")
            
            # Create update tasks for each symbol with rate limiting
            semaphore = asyncio.Semaphore(20)  # Limit concurrent symbol updates
            
            async def bounded_symbol_update(symbol_info):
                async with semaphore:
                    await self.update_single_symbol(
                        symbol_info["symbol"], 
                        symbol_info["exchange"]
                    )
            
            # Execute all symbol updates concurrently
            tasks = [bounded_symbol_update(symbol_info) for symbol_info in symbols_to_track]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            errors = [r for r in results if isinstance(r, Exception)]
            if errors:
                logger.warning(f"Completed with {len(errors)} errors out of {len(tasks)} symbols")
            else:
                logger.info(f"✅ Successfully updated {len(symbols_to_track)} symbols")
                
        except Exception as e:
            logger.error(f"❌ Error in per-symbol watchlist update: {e}")
    
    async def update_single_watchlist(self, user_id: str):
        """Update all symbols in a single user's watchlist"""
        try:
            from app.models.watchlistModel import Watchlist
            
            watchlist = await Watchlist.find_by_user(user_id)
            if not watchlist or not watchlist.get("symbols"):
                return
            
            symbols = watchlist["symbols"]
            
            # Update each symbol in the watchlist
            update_tasks = []
            for symbol_data in symbols:
                symbol = symbol_data["symbol"]
                exchange = symbol_data["exchange"]
                task = self.update_single_symbol(symbol, exchange)
                update_tasks.append(task)
            
            if update_tasks:
                await asyncio.gather(*update_tasks, return_exceptions=True)
                
            logger.debug(f"✅ Updated all symbols for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error updating watchlist for user {user_id}: {e}")
    
    # Add to concurrentMarketService.py (modifications)

    async def get_symbol_data(self, symbol: str, exchange: str):
        """Get single symbol data with caching - UPDATED FOR MT5 WS"""
        cache_key = f"{exchange}:{symbol}"
        current_time = datetime.utcnow()
        
        # Check cache first
        if cache_key in self.cache:
            cached_data, cache_time = self.cache[cache_key]
            if (current_time - cache_time).total_seconds() < self.cache_ttl:
                return cached_data
        
        try:
            from app.routers.market import get_quote_alpaca, get_quote_fyers, get_quote_mt5
            from app.services.mt5_websocket_service import mt5_websocket_service
            
            symbol = symbol.upper()
            exchange = exchange.upper()
            
            # 🆕 USE MT5 WEBSOCKET FOR MT5 SYMBOLS INSTEAD OF HTTP REQUESTS
            if exchange == "MT5":
                # Subscribe to symbol in MT5 WebSocket
                mt5_websocket_service.subscribe_symbol(symbol)
                
                # Get data from WebSocket (real-time)
                mt5_data = mt5_websocket_service.get_symbol_data(symbol)
                if mt5_data:
                    # logger.info(f"{mt5_data}")
                    market_data = {
                        "current_price": round(mt5_data.last_price, 6),
                        "day_change": 0.0,  # MT5 WS doesn't provide day change
                        "day_change_percentage": 0.0,
                        "bid": mt5_data.bid,
                        "ask": mt5_data.ask,
                        "latency_ms": mt5_data.latency_ms,
                        "source": "MT5_WS"
                    }
                    
                    # Cache the result
                    self.cache[cache_key] = (market_data, current_time)
                    return market_data
            
            # Fallback to original methods for other exchanges
            if exchange == "ALPACA":
                result = await get_quote_alpaca(symbol)
            elif exchange == "FYERS":
                result = await get_quote_fyers(symbol)
            else:
                # Try MT5 HTTP as fallback
                result = await get_quote_mt5(symbol)
            
            if result:
                market_data = {
                    "current_price": round(result.get("last_price", 0.0), 2),
                    "day_change": result.get("day_change", 0.0),
                    "day_change_percentage": result.get("day_change_percentage", 0.0)
                }
                
                # Cache the result
                self.cache[cache_key] = (market_data, current_time)
                return market_data
            else:
                # Return fallback data
                fallback_data = {
                    "current_price": 0.0,
                    "day_change": 0.0,
                    "day_change_percentage": 0.0
                }
                self.cache[cache_key] = (fallback_data, current_time)
                return fallback_data
                
        except Exception as e:
            logger.error(f"Error fetching symbol data for {symbol} ({exchange}): {e}")
            # Return cached data if available, otherwise fallback
            if cache_key in self.cache:
                return self.cache[cache_key][0]
            return {
                "current_price": 0.0,
                "day_change": 0.0,
                "day_change_percentage": 0.0
            }
   
    # Legacy methods for backward compatibility
    async def _fetch_all_symbols_concurrently(self, symbols_map: Dict[str, List[str]]):
        """Legacy batch method - kept for compatibility"""
        from app.routers.market import get_quote_alpaca, get_quote_fyers, get_quote_mt5
        
        all_results = {}
        
        # Create tasks for each exchange batch
        tasks = []
        for exchange, symbols in symbols_map.items():
            unique_symbols = list(set(symbols))  # Remove duplicates
            if exchange == "ALPACA":
                tasks.append(self._fetch_alpaca_symbols(unique_symbols))
            elif exchange == "FYERS":
                tasks.append(self._fetch_fyers_symbols(unique_symbols))
            elif exchange == "MT5":
                tasks.append(self._fetch_mt5_symbols(unique_symbols))
            else:
                # Try all sources for unknown exchanges
                tasks.append(self._fetch_mixed_symbols(unique_symbols))
        
        # Run all exchange fetches concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all results
        for result in results:
            if isinstance(result, dict):
                all_results.update(result)
                
        return all_results
    
    async def _fetch_alpaca_symbols(self, symbols: List[str]):
        """Fetch multiple Alpaca symbols concurrently"""
        from app.routers.market import get_quote_alpaca
        
        tasks = [get_quote_alpaca(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {f"{symbol}_ALPACA": result for symbol, result in zip(symbols, results) 
                if not isinstance(result, Exception) and result}
    
    async def _fetch_fyers_symbols(self, symbols: List[str]):
        """Fetch multiple FYERS symbols concurrently"""
        from app.routers.market import get_quote_fyers
        
        tasks = [get_quote_fyers(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {f"{symbol}_FYERS": result for symbol, result in zip(symbols, results) 
                if not isinstance(result, Exception) and result}
    
    async def _fetch_mt5_symbols(self, symbols: List[str]):
        """Fetch multiple MT5 symbols concurrently"""
        from app.routers.market import get_quote_mt5
        
        tasks = [get_quote_mt5(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {f"{symbol}_MT5": result for symbol, result in zip(symbols, results) 
                if not isinstance(result, Exception) and result}
    
    async def _fetch_mixed_symbols(self, symbols: List[str]):
        """Try all sources for symbols with unknown exchange"""
        results = {}
        for symbol in symbols:
            # Try all sources and take the first successful one
            from app.routers.market import get_quote_alpaca, get_quote_fyers, get_quote_mt5
            
            alpaca_data = await get_quote_alpaca(symbol)
            if alpaca_data:
                results[f"{symbol}_ALPACA"] = alpaca_data
                continue
                
            fyers_data = await get_quote_fyers(symbol)
            if fyers_data:
                results[f"{symbol}_FYERS"] = fyers_data
                continue
                
            mt5_data = await get_quote_mt5(symbol)
            if mt5_data:
                results[f"{symbol}_MT5"] = mt5_data
                
        return results
    
    async def _update_user_watchlist(self, user_id: str, watchlist: dict, updated_data: dict):
        """Legacy batch update method - kept for compatibility"""
        from app.models.watchlistModel import Watchlist
        from app.services.watchlistWebSocket import watchlist_ws_manager
        
        try:
            updated_symbols = []
            needs_update = False
            individual_updates = []
            
            for symbol_data in watchlist.get("symbols", []):
                symbol = symbol_data["symbol"].upper()
                exchange = symbol_data["exchange"].upper()
                cache_key = f"{symbol}_{exchange}"
                
                if cache_key in updated_data and updated_data[cache_key]:
                    result = updated_data[cache_key]
                    # Update symbol data
                    updated_symbol = {
                        **symbol_data,  # Keep existing data
                        "current_price": round(result.get("last_price", 0.0), 2),
                        "day_change": result.get("day_change", 0.0),
                        "day_change_percentage": result.get("day_change_percentage", 0.0),
                        "last_updated": datetime.now().isoformat()
                    }
                    
                    # Remove note if we have fresh data
                    if "note" in updated_symbol and updated_symbol.get("note") == "No market data available":
                        del updated_symbol["note"]
                        
                    updated_symbols.append(updated_symbol)
                    needs_update = True
                    
                    # Also prepare individual update for more reliability
                    individual_updates.append({
                        "symbol": symbol,
                        "exchange": exchange,
                        "data": {
                            "current_price": round(result.get("last_price", 0.0), 2),
                            "day_change": result.get("day_change", 0.0),
                            "day_change_percentage": result.get("day_change_percentage", 0.0),
                            "last_updated": datetime.now().isoformat()
                        }
                    })
                else:
                    # Keep existing data if no update available
                    updated_symbols.append(symbol_data)
            
            if needs_update:
                # METHOD 1: Update entire watchlist (more reliable)
                update_result = await Watchlist.update_symbols(user_id, updated_symbols)
                
                # METHOD 2: Also update symbols individually for extra reliability
                individual_tasks = []
                for update in individual_updates:
                    task = Watchlist.update_symbol_data(
                        user_id, 
                        update["symbol"], 
                        update["exchange"], 
                        update["data"]
                    )
                    individual_tasks.append(task)
                
                # Run individual updates concurrently
                await asyncio.gather(*individual_tasks, return_exceptions=True)
                
                logger.debug(f"✅ Updated watchlist for user {user_id}: {len(individual_updates)} symbols")
                
                # Send WebSocket update
                await watchlist_ws_manager.send_personal_message({
                    "type": "watchlist_update",
                    "data": updated_symbols,
                    "timestamp": datetime.now().isoformat()
                }, user_id)
                    
        except Exception as e:
            logger.error(f"Error updating watchlist for user {user_id}: {e}")

    def get_update_stats(self):
        """Get statistics about symbol updates"""
        current_time = datetime.utcnow()
        recently_updated = 0
        for symbol_key, last_update in self.last_symbol_update.items():
            if (current_time - last_update).total_seconds() < 60:  # Last minute
                recently_updated += 1
        
        return {
            "total_symbols_tracked": len(self.last_symbol_update),
            "recently_updated": recently_updated,
            "cache_size": len(self.cache),
            "update_method": "per_symbol_individual"
        }

# Global instance
concurrent_market_service = ConcurrentMarketDataService()