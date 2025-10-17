# import asyncio
# import logging
# from typing import Dict, Set
# from fastapi import WebSocket

# logger = logging.getLogger(__name__)

# class WatchlistWebSocketManager:
#     def __init__(self):
#         self.active_connections: Dict[str, WebSocket] = {}
#         self.user_watchlists: Dict[str, Set[str]] = {}
        
#     async def connect(self, websocket: WebSocket, user_id: str):
#         await websocket.accept()
#         self.active_connections[user_id] = websocket
#         logger.info(f"🟢 Watchlist WS connected for user {user_id}")
        
#     def disconnect(self, user_id: str):
#         if user_id in self.active_connections:
#             del self.active_connections[user_id]
#             logger.info(f"🔴 Watchlist WS disconnected for user {user_id}")
            
#     async def send_personal_message(self, message: dict, user_id: str):
#         if user_id in self.active_connections:
#             try:
#                 await self.active_connections[user_id].send_json(message)
#             except Exception as e:
#                 logger.error(f"Failed to send message to user {user_id}: {e}")
#                 self.disconnect(user_id)

# watchlist_ws_manager = WatchlistWebSocketManager()



import asyncio
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class WatchlistWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_watchlists: Dict[str, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"🟢 Watchlist WS connected for user {user_id}")
        
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"🔴 Watchlist WS disconnected for user {user_id}")
            
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_symbol_update(self, symbol: str, exchange: str, data: dict):
        """Broadcast symbol update to all users watching this symbol"""
        tasks = []
        for user_id, websocket in self.active_connections.items():
            task = websocket.send_json({
                "type": "symbol_update",
                "symbol": symbol,
                "exchange": exchange,
                "data": data
            })
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

watchlist_ws_manager = WatchlistWebSocketManager()