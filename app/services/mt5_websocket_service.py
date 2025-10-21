# # app/services/mt5_websocket_service.py
# import asyncio
# import json
# import logging
# import websockets
# from typing import Dict, Set, Callable
# from datetime import datetime
# import aiohttp

# logger = logging.getLogger(__name__)

# class MT5WebSocketService:
#     def __init__(self):
#         self.ws_url = "ws://13.53.42.25:78/ws"
#         self.http_url = "http://13.53.42.25:78"
#         self.connected = False
#         self.websocket = None
#         self.subscribed_symbols: Set[str] = set()
#         self.message_handlers: Set[Callable] = set()
#         self.reconnect_delay = 5
#         self.max_reconnect_delay = 60
        
#     async def connect(self):
#         """Connect to MT5 WebSocket with reconnection logic"""
#         while True:
#             try:
#                 logger.info(f"🔗 Connecting to MT5 WebSocket at {self.ws_url}")
#                 self.websocket = await websockets.connect(self.ws_url, ping_interval=30)
#                 self.connected = True
#                 logger.info("✅ Connected to MT5 WebSocket")
                
#                 # Resubscribe to symbols
#                 if self.subscribed_symbols:
#                     await self._resubscribe_symbols()
                
#                 # Start listening for messages
#                 await self._listen()
                
#             except Exception as e:
#                 logger.error(f"❌ MT5 WebSocket connection failed: {e}")
#                 self.connected = False
#                 await self._handle_reconnect()
    
#     async def _listen(self):
#         """Listen for incoming messages"""
#         try:
#             async for message in self.websocket:
#                 await self._handle_message(message)
#         except Exception as e:
#             logger.error(f"❌ Error in MT5 WebSocket listener: {e}")
#             self.connected = False
    
#     async def _handle_message(self, message: str):
#         """Process incoming WebSocket messages"""
#         try:
#             data = json.loads(message)
#             symbol = data.get('symbol')
            
#             # Only process our target symbols
#             if symbol in ['BTCUSD', 'ETHUSD', 'AUDUSD']:
#                 # Add timestamp and calculate latency
#                 receive_time = datetime.utcnow().timestamp()
#                 data['receive_timestamp'] = receive_time
                
#                 if 'timestamp' in data:
#                     server_time = data['timestamp']
#                     data['latency_ms'] = (receive_time - server_time) * 1000
#                 else:
#                     data['latency_ms'] = 0
                
#                 # Notify all handlers
#                 for handler in self.message_handlers:
#                     try:
#                         await handler(data)
#                     except Exception as e:
#                         logger.error(f"Error in message handler: {e}")
                        
#         except json.JSONDecodeError as e:
#             logger.error(f"❌ JSON decode error: {e}")
    
#     async def subscribe(self, symbols: list):
#         """Subscribe to symbols"""
#         if not self.connected or not self.websocket:
#             logger.warning("❌ WebSocket not connected, caching symbols for later subscription")
#             self.subscribed_symbols.update(symbols)
#             return
        
#         for symbol in symbols:
#             if symbol not in self.subscribed_symbols:
#                 subscribe_msg = {
#                     'action': 'subscribe',
#                     'symbol': symbol
#                 }
#                 try:
#                     await self.websocket.send(json.dumps(subscribe_msg))
#                     self.subscribed_symbols.add(symbol)
#                     logger.info(f"✅ Subscribed to {symbol}")
#                 except Exception as e:
#                     logger.error(f"❌ Failed to subscribe to {symbol}: {e}")
    
#     async def unsubscribe(self, symbols: list):
#         """Unsubscribe from symbols"""
#         if not self.connected or not self.websocket:
#             return
        
#         for symbol in symbols:
#             if symbol in self.subscribed_symbols:
#                 unsubscribe_msg = {
#                     'action': 'unsubscribe',
#                     'symbol': symbol
#                 }
#                 try:
#                     await self.websocket.send(json.dumps(unsubscribe_msg))
#                     self.subscribed_symbols.remove(symbol)
#                     logger.info(f"✅ Unsubscribed from {symbol}")
#                 except Exception as e:
#                     logger.error(f"❌ Failed to unsubscribe from {symbol}: {e}")
    
#     async def _resubscribe_symbols(self):
#         """Resubscribe to all symbols after reconnection"""
#         if self.subscribed_symbols:
#             await self.subscribe(list(self.subscribed_symbols))
    
#     async def _handle_reconnect(self):
#         """Handle reconnection with exponential backoff"""
#         logger.info(f"🔄 Reconnecting in {self.reconnect_delay} seconds...")
#         await asyncio.sleep(self.reconnect_delay)
#         self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
    
#     def add_message_handler(self, handler: Callable):
#         """Add a message handler"""
#         self.message_handlers.add(handler)
    
#     def remove_message_handler(self, handler: Callable):
#         """Remove a message handler"""
#         self.message_handlers.discard(handler)
    
#     async def check_connection(self):
#         """Check if MT5 service is available"""
#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.get(f"{self.http_url}/symbols", timeout=5) as response:
#                     return response.status == 200
#         except:
#             return False

# # Global instance
# mt5_websocket_service = MT5WebSocketService()






























# # mt5_websocket_service.py
# import asyncio
# import json
# import logging
# import socket
# import threading
# import time
# import random
# from datetime import datetime
# from typing import Dict, Set, Callable
# from dataclasses import dataclass

# logger = logging.getLogger(__name__)

# @dataclass
# class MT5SymbolData:
#     symbol: str
#     bid: float
#     ask: float
#     last_price: float
#     timestamp: float
#     latency_ms: float

# class MT5WebSocketService:
#     def __init__(self, host='13.53.42.25', command_port=85, data_port=86):
#         self.host = host
#         self.command_port = command_port
#         self.data_port = data_port
#         self.buffer_size = 326582
        
#         # MT5 connection state
#         self.s_cmd = None
#         self.s_data = None
#         self.is_connected = False
#         self.should_stop = False
#         self.simulation_mode = False
        
#         # Symbol management
#         self.subscribed_symbols: Set[str] = set()
#         self.symbol_data: Dict[str, MT5SymbolData] = {}
#         self.data_callbacks: Set[Callable] = set()
        
#         # Threading
#         self.data_thread = None
#         self.reconnect_thread = None
        
#         # Statistics
#         self.message_count = 0
#         self.start_time = None
        
#     def check_connection(self) -> bool:
#         """Check if MTSocketAPI is running"""
#         try:
#             # Test command port
#             test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             test_socket.settimeout(2)
#             result = test_socket.connect_ex((self.host, self.command_port))
#             test_socket.close()
            
#             if result == 0:
#                 # Test data port
#                 test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#                 test_socket.settimeout(2)
#                 result = test_socket.connect_ex((self.host, self.data_port))
#                 test_socket.close()
#                 return result == 0
#             return False
#         except:
#             return False

#     def start_simulation(self):
#         """Start simulation mode for MT5 symbols"""
#         logger.info("🔧 Starting MT5 SIMULATION MODE for watchlist...")
#         self.simulation_mode = True
#         self.start_time = time.time()
        
#         # Realistic initial prices for MT5 symbols (Forex & Crypto)
#         base_prices = {
#             'BTCUSD': 45000.0,
#             'ETHUSD': 2500.0, 
#             'AUDUSD': 0.6650,
#             'EURUSD': 1.0850,
#             'GBPUSD': 1.2650,
#             'USDJPY': 147.50,
#             'XAUUSD': 1980.0  # Gold
#         }
        
#         volatility = {
#             'BTCUSD': 0.005,  # 0.5% volatility
#             'ETHUSD': 0.006,  # 0.6% volatility
#             'AUDUSD': 0.0005, # 0.05% volatility
#             'EURUSD': 0.0003,
#             'GBPUSD': 0.0004,
#             'USDJPY': 0.0006,
#             'XAUUSD': 0.002   # 0.2% volatility for gold
#         }
        
#         spreads = {
#             'BTCUSD': 5.0,
#             'ETHUSD': 0.5,
#             'AUDUSD': 0.0001,
#             'EURUSD': 0.00008,
#             'GBPUSD': 0.0001,
#             'USDJPY': 0.008,
#             'XAUUSD': 0.30
#         }
        
#         def simulation_loop():
#             current_prices = base_prices.copy()
            
#             while not self.should_stop:
#                 for symbol in list(self.subscribed_symbols):
#                     if self.should_stop:
#                         break
                    
#                     if symbol not in current_prices:
#                         # Add new symbol with realistic price
#                         if 'BTC' in symbol:
#                             current_prices[symbol] = 45000.0
#                         elif 'ETH' in symbol:
#                             current_prices[symbol] = 2500.0
#                         elif 'XAU' in symbol:
#                             current_prices[symbol] = 1980.0
#                         else:
#                             current_prices[symbol] = 1.0  # Default
                    
#                     current_price = current_prices[symbol]
#                     symbol_volatility = volatility.get(symbol, 0.001)
                    
#                     # Realistic price movement
#                     change_percent = random.uniform(-symbol_volatility, symbol_volatility)
#                     new_price = current_price * (1 + change_percent)
#                     current_prices[symbol] = new_price
                    
#                     # Apply spreads
#                     spread = spreads.get(symbol, 0.0001)
#                     bid = round(new_price, 6)
#                     ask = round(bid + spread, 6)
                    
#                     # Simulate latency (1-10ms for simulation)
#                     latency_ms = random.uniform(1, 10)
                    
#                     # Create symbol data
#                     symbol_data = MT5SymbolData(
#                         symbol=symbol,
#                         bid=bid,
#                         ask=ask,
#                         last_price=(bid + ask) / 2,
#                         timestamp=time.time(),
#                         latency_ms=latency_ms
#                     )
                    
#                     # Update data and notify callbacks
#                     self.symbol_data[symbol] = symbol_data
#                     self._notify_callbacks(symbol_data)
                    
#                     self.message_count += 1
                
#                 time.sleep(0.05)  # 50ms between updates
        
#         sim_thread = threading.Thread(target=simulation_loop)
#         sim_thread.daemon = True
#         sim_thread.start()

#     def connect_to_mt5(self):
#         """Connect to real MT5 MTSocketAPI"""
#         if not self.check_connection():
#             logger.warning("❌ MTSocketAPI not available. Starting simulation...")
#             self.start_simulation()
#             return False
            
#         try:
#             self.start_time = time.time()
            
#             # Connect to command port
#             self.s_cmd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             self.s_cmd.settimeout(3)
#             self.s_cmd.connect((self.host, self.command_port))
            
#             # Connect to data port
#             self.s_data = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             self.s_data.connect((self.host, self.data_port))
            
#             # Subscribe to existing symbols
#             if self.subscribed_symbols:
#                 subscribe_msg = {
#                     "MSG": "TRACK_PRICES", 
#                     "SYMBOLS": list(self.subscribed_symbols)
#                 }
#                 cmd_message = json.dumps(subscribe_msg) + '\r\n'
#                 self.s_cmd.sendall(cmd_message.encode('ascii'))
                
#                 # Get initial response
#                 response = self.s_cmd.recv(self.buffer_size).decode('ascii')
#                 logger.info(f"✅ MT5 Command response: {response.strip()}")
            
#             self.is_connected = True
#             logger.info("✅ Connected to MTSocketAPI for watchlist data")
            
#             # Start data receiving thread
#             self.data_thread = threading.Thread(target=self._receive_data_loop)
#             self.data_thread.daemon = True
#             self.data_thread.start()
            
#             return True
                
#         except Exception as e:
#             logger.error(f"❌ MT5 Connection failed: {e}")
#             logger.info("🔄 Switching to simulation mode...")
#             self.start_simulation()
#             return False

#     def _receive_data_loop(self):
#         """Receive data from MTSocketAPI"""
#         while not self.should_stop and self.is_connected:
#             try:
#                 data = self.s_data.recv(self.buffer_size).decode('ascii').strip()
#                 if data:
#                     self._process_real_data(data)
#             except socket.timeout:
#                 continue
#             except Exception as e:
#                 if not self.should_stop:
#                     logger.error(f"❌ MT5 Data receive error: {e}")
#                     self.is_connected = False
#                     break

#     def _process_real_data(self, raw_data):
#         """Process real MT5 data"""
#         receive_time = time.time()
        
#         try:
#             for line in raw_data.split('\n'):
#                 if line.strip():
#                     data = json.loads(line.strip())
                    
#                     # Check if this is a price update for our symbols
#                     if 'SYMBOL' in data and 'BID' in data:
#                         symbol = data['SYMBOL']
                        
#                         if symbol in self.subscribed_symbols:
#                             # Calculate latency
#                             if 'TIMESTAMP' in data:
#                                 server_time = data['TIMESTAMP'] / 1000.0
#                                 latency = (receive_time - server_time) * 1000
#                             else:
#                                 latency = (receive_time - self.start_time) * 1000
                            
#                             # Create symbol data
#                             symbol_data = MT5SymbolData(
#                                 symbol=symbol,
#                                 bid=data['BID'],
#                                 ask=data['ASK'],
#                                 last_price=(data['BID'] + data['ASK']) / 2,
#                                 timestamp=receive_time,
#                                 latency_ms=latency
#                             )
                            
#                             # Update data and notify callbacks
#                             self.symbol_data[symbol] = symbol_data
#                             self._notify_callbacks(symbol_data)
                            
#                             self.message_count += 1
                            
#                             # Log every 50 messages
#                             if self.message_count % 50 == 0:
#                                 logger.info(f"📊 MT5 WS: {self.message_count} messages, {len(self.subscribed_symbols)} symbols")
                                
#         except json.JSONDecodeError as e:
#             logger.error(f"❌ MT5 JSON decode error: {e}")
#         except Exception as e:
#             logger.error(f"❌ Error processing MT5 data: {e}")

#     def _notify_callbacks(self, symbol_data: MT5SymbolData):
#         """Notify all registered callbacks of new data"""
#         for callback in self.data_callbacks:
#             try:
#                 callback(symbol_data)
#             except Exception as e:
#                 logger.error(f"Error in MT5 data callback: {e}")

#     def subscribe_symbol(self, symbol: str):
#         """Subscribe to a symbol for MT5 data"""
#         symbol = symbol.upper()
        
#         if symbol in self.subscribed_symbols:
#             return True
            
#         self.subscribed_symbols.add(symbol)
#         logger.info(f"✅ MT5 Subscribed to: {symbol}")
        
#         # If connected to real MT5, send subscription command
#         if self.is_connected and not self.simulation_mode:
#             try:
#                 subscribe_msg = {
#                     "MSG": "TRACK_PRICES", 
#                     "SYMBOLS": [symbol]
#                 }
#                 cmd_message = json.dumps(subscribe_msg) + '\r\n'
#                 self.s_cmd.sendall(cmd_message.encode('ascii'))
#             except Exception as e:
#                 logger.error(f"Failed to subscribe {symbol} to MT5: {e}")
        
#         return True

#     def unsubscribe_symbol(self, symbol: str):
#         """Unsubscribe from a symbol"""
#         symbol = symbol.upper()
        
#         if symbol in self.subscribed_symbols:
#             self.subscribed_symbols.remove(symbol)
#             if symbol in self.symbol_data:
#                 del self.symbol_data[symbol]
#             logger.info(f"✅ MT5 Unsubscribed from: {symbol}")
#             return True
#         return False

#     def get_symbol_data(self, symbol: str) -> MT5SymbolData:
#         """Get current data for a symbol"""
#         symbol = symbol.upper()
#         return self.symbol_data.get(symbol)

#     def register_callback(self, callback: Callable):
#         """Register callback for MT5 data updates"""
#         self.data_callbacks.add(callback)

#     def unregister_callback(self, callback: Callable):
#         """Unregister callback"""
#         self.data_callbacks.discard(callback)

#     def start(self):
#         """Start the MT5 WebSocket service"""
#         logger.info("🚀 Starting MT5 WebSocket Service for watchlist...")
#         self.connect_to_mt5()

#     def stop(self):
#         """Stop the MT5 WebSocket service"""
#         self.should_stop = True
#         if self.s_cmd:
#             self.s_cmd.close()
#         if self.s_data:
#             self.s_data.close()
#         logger.info("🛑 MT5 WebSocket Service stopped")

#     def get_stats(self):
#         """Get service statistics"""
#         return {
#             "is_connected": self.is_connected,
#             "simulation_mode": self.simulation_mode,
#             "subscribed_symbols_count": len(self.subscribed_symbols),
#             "message_count": self.message_count,
#             "symbols": list(self.subscribed_symbols)
#         }


# # Global instance
# mt5_websocket_service = MT5WebSocketService()




# mt5_websocket_service.py
import asyncio
import json
import logging
import os
import socket
import threading
import time
import random
from datetime import datetime
from typing import Dict, Set, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MT5SymbolData:
    symbol: str
    bid: float
    ask: float
    last_price: float
    timestamp: float
    latency_ms: float

class MT5WebSocketService:
    def __init__(self, host=None, command_port=None, data_port=None):
        # Get configuration from environment variables with fallbacks
        self.host = host or os.getenv('MT5_HOST', '13.53.42.25')
        self.command_port = command_port or int(os.getenv('MT5_COMMAND_PORT', '85'))
        self.data_port = data_port or int(os.getenv('MT5_DATA_PORT', '86'))
        self.buffer_size = 326582
        
        # MT5 connection state
        self.s_cmd = None
        self.s_data = None
        self.is_connected = False
        self.should_stop = False
        self.simulation_mode = False
        
        # Symbol management
        self.subscribed_symbols: Set[str] = set()
        self.symbol_data: Dict[str, MT5SymbolData] = {}
        self.data_callbacks: Set[Callable] = set()
        
        # Threading
        self.data_thread = None
        self.reconnect_thread = None
        
        # Statistics
        self.message_count = 0
        self.start_time = None
        
        logger.info(f"🔧 MT5 WebSocket Service configured - Host: {self.host}, Command Port: {self.command_port}, Data Port: {self.data_port}")
        
    def check_connection(self) -> bool:
        """Check if MTSocketAPI is running"""
        try:
            # Test command port
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(2)
            result = test_socket.connect_ex((self.host, self.command_port))
            test_socket.close()
            
            if result == 0:
                # Test data port
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.settimeout(2)
                result = test_socket.connect_ex((self.host, self.data_port))
                test_socket.close()
                return result == 0
            return False
        except:
            return False

    def start_simulation(self):
        """Start simulation mode for MT5 symbols"""
        logger.info("🔧 Starting MT5 SIMULATION MODE for watchlist...")
        self.simulation_mode = True
        self.start_time = time.time()
        
        # Realistic initial prices for MT5 symbols (Forex & Crypto)
        base_prices = {
            'BTCUSD': 45000.0,
            'ETHUSD': 2500.0, 
            'AUDUSD': 0.6650,
            'EURUSD': 1.0850,
            'GBPUSD': 1.2650,
            'USDJPY': 147.50,
            'XAUUSD': 1980.0  # Gold
        }
        
        volatility = {
            'BTCUSD': 0.005,  # 0.5% volatility
            'ETHUSD': 0.006,  # 0.6% volatility
            'AUDUSD': 0.0005, # 0.05% volatility
            'EURUSD': 0.0003,
            'GBPUSD': 0.0004,
            'USDJPY': 0.0006,
            'XAUUSD': 0.002   # 0.2% volatility for gold
        }
        
        spreads = {
            'BTCUSD': 5.0,
            'ETHUSD': 0.5,
            'AUDUSD': 0.0001,
            'EURUSD': 0.00008,
            'GBPUSD': 0.0001,
            'USDJPY': 0.008,
            'XAUUSD': 0.30
        }
        
        def simulation_loop():
            current_prices = base_prices.copy()
            
            while not self.should_stop:
                for symbol in list(self.subscribed_symbols):
                    if self.should_stop:
                        break
                    
                    if symbol not in current_prices:
                        # Add new symbol with realistic price
                        if 'BTC' in symbol:
                            current_prices[symbol] = 45000.0
                        elif 'ETH' in symbol:
                            current_prices[symbol] = 2500.0
                        elif 'XAU' in symbol:
                            current_prices[symbol] = 1980.0
                        else:
                            current_prices[symbol] = 1.0  # Default
                    
                    current_price = current_prices[symbol]
                    symbol_volatility = volatility.get(symbol, 0.001)
                    
                    # Realistic price movement
                    change_percent = random.uniform(-symbol_volatility, symbol_volatility)
                    new_price = current_price * (1 + change_percent)
                    current_prices[symbol] = new_price
                    
                    # Apply spreads
                    spread = spreads.get(symbol, 0.0001)
                    bid = round(new_price, 6)
                    ask = round(bid + spread, 6)
                    
                    # Simulate latency (1-10ms for simulation)
                    latency_ms = random.uniform(1, 10)
                    
                    # Create symbol data
                    symbol_data = MT5SymbolData(
                        symbol=symbol,
                        bid=bid,
                        ask=ask,
                        last_price=(bid + ask) / 2,
                        timestamp=time.time(),
                        latency_ms=latency_ms
                    )
                    
                    # Update data and notify callbacks
                    self.symbol_data[symbol] = symbol_data
                    self._notify_callbacks(symbol_data)
                    
                    self.message_count += 1
                
                time.sleep(0.05)  # 50ms between updates
        
        sim_thread = threading.Thread(target=simulation_loop)
        sim_thread.daemon = True
        sim_thread.start()

    def connect_to_mt5(self):
        """Connect to real MT5 MTSocketAPI"""
        if not self.check_connection():
            logger.warning(f"❌ MTSocketAPI not available at {self.host}:{self.command_port}/{self.data_port}. Starting simulation...")
            self.start_simulation()
            return False
            
        try:
            self.start_time = time.time()
            
            # Connect to command port
            self.s_cmd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s_cmd.settimeout(3)
            self.s_cmd.connect((self.host, self.command_port))
            
            # Connect to data port
            self.s_data = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s_data.connect((self.host, self.data_port))
            
            # Subscribe to existing symbols
            if self.subscribed_symbols:
                subscribe_msg = {
                    "MSG": "TRACK_PRICES", 
                    "SYMBOLS": list(self.subscribed_symbols)
                }
                cmd_message = json.dumps(subscribe_msg) + '\r\n'
                self.s_cmd.sendall(cmd_message.encode('ascii'))
                
                # Get initial response
                response = self.s_cmd.recv(self.buffer_size).decode('ascii')
                logger.info(f"✅ MT5 Command response: {response.strip()}")
            
            self.is_connected = True
            logger.info(f"✅ Connected to MTSocketAPI at {self.host}:{self.command_port}/{self.data_port} for watchlist data")
            
            # Start data receiving thread
            self.data_thread = threading.Thread(target=self._receive_data_loop)
            self.data_thread.daemon = True
            self.data_thread.start()
            
            return True
                
        except Exception as e:
            logger.error(f"❌ MT5 Connection failed to {self.host}:{self.command_port}: {e}")
            logger.info("🔄 Switching to simulation mode...")
            self.start_simulation()
            return False

    def _receive_data_loop(self):
        """Receive data from MTSocketAPI"""
        while not self.should_stop and self.is_connected:
            try:
                data = self.s_data.recv(self.buffer_size).decode('ascii').strip()
                if data:
                    self._process_real_data(data)
            except socket.timeout:
                continue
            except Exception as e:
                if not self.should_stop:
                    logger.error(f"❌ MT5 Data receive error: {e}")
                    self.is_connected = False
                    break

    def _process_real_data(self, raw_data):
        """Process real MT5 data"""
        receive_time = time.time()
        
        try:
            for line in raw_data.split('\n'):
                if line.strip():
                    data = json.loads(line.strip())
                    
                    # Check if this is a price update for our symbols
                    if 'SYMBOL' in data and 'BID' in data:
                        symbol = data['SYMBOL']
                        
                        if symbol in self.subscribed_symbols:
                            # Calculate latency
                            if 'TIMESTAMP' in data:
                                server_time = data['TIMESTAMP'] / 1000.0
                                latency = (receive_time - server_time) * 1000
                            else:
                                latency = (receive_time - self.start_time) * 1000
                            
                            # Create symbol data
                            symbol_data = MT5SymbolData(
                                symbol=symbol,
                                bid=data['BID'],
                                ask=data['ASK'],
                                last_price=(data['BID'] + data['ASK']) / 2,
                                timestamp=receive_time,
                                latency_ms=latency
                            )
                            
                            # Update data and notify callbacks
                            self.symbol_data[symbol] = symbol_data
                            self._notify_callbacks(symbol_data)
                            
                            self.message_count += 1
                            
                            # Log every 50 messages
                            if self.message_count % 50 == 0:
                                logger.info(f"📊 MT5 WS: {self.message_count} messages, {len(self.subscribed_symbols)} symbols")
                                
        except json.JSONDecodeError as e:
            logger.error(f"❌ MT5 JSON decode error: {e}")
        except Exception as e:
            logger.error(f"❌ Error processing MT5 data: {e}")

    def _notify_callbacks(self, symbol_data: MT5SymbolData):
        """Notify all registered callbacks of new data"""
        for callback in self.data_callbacks:
            try:
                callback(symbol_data)
            except Exception as e:
                logger.error(f"Error in MT5 data callback: {e}")

    def subscribe_symbol(self, symbol: str):
        """Subscribe to a symbol for MT5 data"""
        symbol = symbol.upper()
        
        if symbol in self.subscribed_symbols:
            return True
            
        self.subscribed_symbols.add(symbol)
        logger.info(f"✅ MT5 Subscribed to: {symbol}")
        
        # If connected to real MT5, send subscription command
        if self.is_connected and not self.simulation_mode:
            try:
                subscribe_msg = {
                    "MSG": "TRACK_PRICES", 
                    "SYMBOLS": [symbol]
                }
                cmd_message = json.dumps(subscribe_msg) + '\r\n'
                self.s_cmd.sendall(cmd_message.encode('ascii'))
            except Exception as e:
                logger.error(f"Failed to subscribe {symbol} to MT5: {e}")
        
        return True

    def unsubscribe_symbol(self, symbol: str):
        """Unsubscribe from a symbol"""
        symbol = symbol.upper()
        
        if symbol in self.subscribed_symbols:
            self.subscribed_symbols.remove(symbol)
            if symbol in self.symbol_data:
                del self.symbol_data[symbol]
            logger.info(f"✅ MT5 Unsubscribed from: {symbol}")
            return True
        return False

    def get_symbol_data(self, symbol: str) -> MT5SymbolData:
        """Get current data for a symbol"""
        symbol = symbol.upper()
        return self.symbol_data.get(symbol)

    def register_callback(self, callback: Callable):
        """Register callback for MT5 data updates"""
        self.data_callbacks.add(callback)

    def unregister_callback(self, callback: Callable):
        """Unregister callback"""
        self.data_callbacks.discard(callback)

    def start(self):
        """Start the MT5 WebSocket service"""
        logger.info("🚀 Starting MT5 WebSocket Service for watchlist...")
        self.connect_to_mt5()

    def stop(self):
        """Stop the MT5 WebSocket service"""
        self.should_stop = True
        if self.s_cmd:
            self.s_cmd.close()
        if self.s_data:
            self.s_data.close()
        logger.info("🛑 MT5 WebSocket Service stopped")

    def get_stats(self):
        """Get service statistics"""
        return {
            "is_connected": self.is_connected,
            "simulation_mode": self.simulation_mode,
            "subscribed_symbols_count": len(self.subscribed_symbols),
            "message_count": self.message_count,
            "symbols": list(self.subscribed_symbols),
            "host": self.host,
            "command_port": self.command_port,
            "data_port": self.data_port
        }


# Global instance
mt5_websocket_service = MT5WebSocketService()