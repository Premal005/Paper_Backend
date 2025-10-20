from fyers_apiv3.FyersWebsocket import data_ws
import json
import time
from datetime import datetime
import logging
import threading

# Suppress the deprecation warning
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

class BulkFyersLiveData:
    def __init__(self, access_token, log_path="", litemode=False, batch_size=50):
        self.access_token = access_token
        self.fyers = None
        self.connected = False
        self.symbol_data = {}
        self.batch_size = batch_size
        self.current_batch = 0
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Create FyersDataSocket instance
        self.fyers = data_ws.FyersDataSocket(
            access_token=access_token,
            log_path=log_path,
            litemode=litemode,
            write_to_file=False,
            reconnect=True,
            on_connect=self.onopen,
            on_close=self.onclose,
            on_error=self.onerror,
            on_message=self.onmessage
        )
    
    def get_symbols_batches(self):
        """Divide symbols into batches to avoid overwhelming the connection"""
        symbols = [
            # --- Top NSE 200 Stocks (Valid EQ suffix) ---
            "NSE:RELIANCE-EQ", "NSE:TCS-EQ", "NSE:HDFCBANK-EQ", "NSE:ICICIBANK-EQ",
            "NSE:INFY-EQ", "NSE:ITC-EQ", "NSE:SBIN-EQ", "NSE:HINDUNILVR-EQ",
            "NSE:BHARTIARTL-EQ", "NSE:BAJFINANCE-EQ", "NSE:LT-EQ", "NSE:ASIANPAINT-EQ",
            "NSE:AXISBANK-EQ", "NSE:HCLTECH-EQ", "NSE:MARUTI-EQ", "NSE:KOTAKBANK-EQ",
            "NSE:WIPRO-EQ", "NSE:TITAN-EQ",
            # Index Futures
            "NSE:RELIANCE25DECFUT", "NSE:BANKNIFTY25DECFUT", "NSE:NIFTY25DECFUT", 
            "NSE:FINNIFTY25DECFUT", "NSE:MIDCPNIFTY25DECFUT",
            "NSE:TCS25DECFUT", "NSE:HDFCBANK25DECFUT", "NSE:ICICIBANK25DECFUT",
            "NSE:INFY25DECFUT","NSE:TATASTEEL25DECFUT", "NSE:HINDALCO25DECFUT", "NSE:JSWSTEEL25DECFUT",
            
            # Options
            "NSE:BANKNIFTY25OCT49000CE", "NSE:BANKNIFTY25OCT49500CE", "NSE:BANKNIFTY25OCT50000CE",
            "NSE:BANKNIFTY25OCT50500CE", "NSE:BANKNIFTY25OCT51000CE", "NSE:BANKNIFTY25OCT51500CE",
            "NSE:BANKNIFTY25OCT52000CE", "NSE:BANKNIFTY25OCT49000PE", "NSE:BANKNIFTY25OCT49500PE",
            "NSE:BANKNIFTY25OCT50000PE", "NSE:BANKNIFTY25OCT50500PE", "NSE:BANKNIFTY25OCT51000PE",
            "NSE:BANKNIFTY25OCT51500PE", "NSE:BANKNIFTY25OCT52000PE",
            
            "NSE:NIFTY25OCT22000CE", "NSE:NIFTY25OCT22500CE", "NSE:NIFTY25OCT23000CE",
            "NSE:NIFTY25OCT23500CE", "NSE:NIFTY25OCT24000CE", "NSE:NIFTY25OCT22000PE",
            "NSE:NIFTY25OCT22500PE", "NSE:NIFTY25OCT23000PE", "NSE:NIFTY25OCT23500PE",
            "NSE:NIFTY25OCT24000PE",
            
            # MCX Commodities
            "MCX:GOLD25DECFUT", "MCX:GOLDM25DECFUT", "MCX:SILVER25DECFUT",
            "MCX:COPPER25DECFUT", "MCX:ZINC25DECFUT", "MCX:LEAD25DECFUT",
            "MCX:NICKEL25DECFUT", "MCX:ALUMINIUM25DECFUT", "MCX:CRUDEOIL25DECFUT",
            "MCX:NATURALGAS25DECFUT",
            
            # MCX Options
            "MCX:GOLD25DEC130000CE", "MCX:GOLD25DEC132000CE", "MCX:GOLD25DEC131000CE",
            "MCX:GOLD25DEC134000CE", "MCX:GOLD25DEC129000CE", "MCX:GOLD25DEC128000CE",
            "MCX:GOLD25DEC120000PE", "MCX:GOLD25DEC125000PE", "MCX:GOLD25DEC130000PE",
            "MCX:GOLD25DEC129000PE", "MCX:GOLD25DEC128000PE", "MCX:GOLD25DEC123000PE",
            
            "MCX:CRUDEOIL25DEC6000CE", "MCX:CRUDEOIL25DEC6200CE", "MCX:CRUDEOIL25DEC6400CE",
            "MCX:CRUDEOIL25DEC6600CE", "MCX:CRUDEOIL25DEC6800CE", "MCX:CRUDEOIL25DEC7000CE",
            "MCX:CRUDEOIL25DEC6000PE", "MCX:CRUDEOIL25DEC6200PE", "MCX:CRUDEOIL25DEC6400PE",
            "MCX:CRUDEOIL25DEC6600PE", "MCX:CRUDEOIL25DEC6800PE", "MCX:CRUDEOIL25DEC7000PE",
        ]
        
        # Split into batches
        batches = []
        for i in range(0, len(symbols), self.batch_size):
            batches.append(symbols[i:i + self.batch_size])
        
        return batches
    
    def onmessage(self, message):
        """
        Callback function to handle incoming messages from the WebSocket.
        """
        try:
            if isinstance(message, dict):
                message_type = message.get('type', '')
                
                if message_type == 'sf':  # Symbol feed data
                    symbol = message.get('symbol', 'Unknown')
                    self.symbol_data[symbol] = message
                    self.display_symbol_data(message)
                elif message_type in ['cn', 'ful', 'sub']:
                    self.logger.info(f"📡 {message.get('message', '')}")
                elif message_type == 'unsub':
                    self.logger.info(f"📡 Unsubscribed: {message.get('message', '')}")
                else:
                    self.logger.debug(f"Other message: {json.dumps(message, indent=2)}")
                    
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def display_symbol_data(self, data):
        """
        Display formatted symbol data in a readable format.
        """
        symbol = data.get('symbol', 'N/A')
        ltp = data.get('ltp', 'N/A')
        change = data.get('ch', 0)
        change_percent = data.get('chp', 0)
        
        # Determine color based on price change
        color_code = ""
        reset_code = ""
        if change > 0:
            color_code = "\033[92m"  # Green
        elif change < 0:
            color_code = "\033[91m"  # Red
        
        symbol_type = "EQ" if "-EQ" in symbol else "FUT" if "FUT" in symbol else "OPT" if "CE" in symbol or "PE" in symbol else "MCX"
        
        print(f"\n{color_code}{'='*60}{reset_code}")
        print(f"{color_code}📊 {symbol_type} | {symbol} | {datetime.now().strftime('%H:%M:%S')}{reset_code}")
        print(f"{color_code}{'='*60}{reset_code}")
        
        print(f"LTP: {color_code}{ltp}{reset_code}")
        print(f"Change: {color_code}{change} ({change_percent}%){reset_code}")
        print("-" * 40)
        
        if "-EQ" in symbol or "FUT" in symbol:
            open_price = data.get('open_price', 'N/A')
            high_price = data.get('high_price', 'N/A')
            low_price = data.get('low_price', 'N/A')
            prev_close = data.get('prev_close_price', 'N/A')
            volume = data.get('vol_traded_today', 'N/A')
            
            # Format volume with commas only if it's a number
            if isinstance(volume, (int, float)):
                volume = f"{volume:,}"
            
            print(f"Open: {open_price} | High: {high_price} | Low: {low_price}")
            print(f"Prev Close: {prev_close} | Volume: {volume}")
        
        bid_price = data.get('bid_price', 0)
        ask_price = data.get('ask_price', 0)
        bid_size = data.get('bid_size', 0)
        ask_size = data.get('ask_size', 0)
        
        print(f"Bid: {bid_price} (Qty: {bid_size}) | Ask: {ask_price} (Qty: {ask_size})")
        
        if "CE" in symbol or "PE" in symbol:
            oi = data.get('oi', 'N/A')
            volume = data.get('vol_traded_today', 'N/A')
            
            # Format OI and volume with commas only if they're numbers
            if isinstance(oi, (int, float)):
                oi = f"{oi:,}"
            if isinstance(volume, (int, float)):
                volume = f"{volume:,}"
                
            print(f"OI: {oi} | Volume: {volume}")
        
        print(f"Last Trade: {data.get('last_traded_qty', 'N/A')} @ {self.format_timestamp(data.get('last_traded_time', 'N/A'))}")



    def format_timestamp(self, timestamp):
        """
        Convert UNIX timestamp to readable format.
        """
        if timestamp in ['N/A', 0] or not timestamp:
            return 'N/A'
        try:
            return datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
        except:
            return str(timestamp)
    
    def onerror(self, message):
        """
        Callback function to handle WebSocket errors.
        """
        self.logger.error(f"❌ WebSocket Error: {message}")
    
    def onclose(self, message):
        """
        Callback function to handle WebSocket connection close events.
        """
        self.logger.info(f"🔌 Connection closed: {message}")
        self.connected = False
    
    def onopen(self):
        """
        Callback function to subscribe to data upon WebSocket connection.
        """
        self.logger.info("✅ WebSocket connection established successfully!")
        self.connected = True
        
        batches = self.get_symbols_batches()
        self.logger.info(f"📦 Total symbols: {sum(len(batch) for batch in batches)} in {len(batches)} batches")
        
        # Subscribe to first batch
        if batches:
            self.current_batch = 0
            self.subscribe_batch(batches[self.current_batch])
        
        self.fyers.keep_running()
    
    def subscribe_batch(self, symbols_batch):
        """
        Subscribe to a batch of symbols.
        """
        if self.connected and symbols_batch:
            data_type = "SymbolUpdate"
            self.logger.info(f"📡 Subscribing to batch {self.current_batch + 1}: {len(symbols_batch)} symbols")
            self.fyers.subscribe(symbols=symbols_batch, data_type=data_type)
    
    def rotate_batch(self):
        """
        Rotate to next batch of symbols (for demonstration).
        """
        batches = self.get_symbols_batches()
        if len(batches) > 1:
            # Unsubscribe current batch
            if self.current_batch < len(batches):
                current_symbols = batches[self.current_batch]
                self.fyers.unsubscribe(symbols=current_symbols)
            
            # Move to next batch
            self.current_batch = (self.current_batch + 1) % len(batches)
            self.subscribe_batch(batches[self.current_batch])
    
    def connect(self):
        """
        Establish connection to FYERS WebSocket.
        """
        self.logger.info("🔗 Connecting to FYERS WebSocket...")
        self.fyers.connect()
    
    def get_latest_data(self, symbol):
        """
        Get the latest stored data for a specific symbol.
        """
        return self.symbol_data.get(symbol, None)
    
    def get_all_symbols_data(self):
        """
        Get latest data for all subscribed symbols.
        """
        return self.symbol_data
    
    def disconnect(self):
        """
        Disconnect from WebSocket.
        """
        self.logger.info("🔌 Disconnecting from WebSocket...")
        self.fyers.close_connection()
        self.connected = False

# Main execution
if __name__ == "__main__":
    # Replace with your actual access token
    ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIl0sImF0X2hhc2giOiJnQUFBQUFCbzlHMW1BaHpCSG0ya2VrQkhib2pqcDZlaDdPekRGakRSaDNfbnR2cDU5MjBtQzRLN2xRTUdHN2haMGpVdU5palBQM1U4MHBISHlyYWhmdk5mVG5wc0JlaV9hejJaWnI3c1AzazJmb3IyRWpSajZOdz0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJlN2ZhZmU2OTdmNTQ4MGNjZjk3M2RjZDVmNzJmYTAwNDgxNjNkNTBiMWJiMTBlM2I2NzgxN2U4YyIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiRkFENDE5MTIiLCJhcHBUeXBlIjoxMDAsImV4cCI6MTc2MDkyMDIwMCwiaWF0IjoxNzYwODQ5MjU0LCJpc3MiOiJhcGkuZnllcnMuaW4iLCJuYmYiOjE3NjA4NDkyNTQsInN1YiI6ImFjY2Vzc190b2tlbiJ9.qzR3t35Nql7e1FESIWMIbDyLpHTocL48I47GATk48u8"  # Format: "appid:accesstoken"
    
    print("🚀 FYERS Comprehensive Live Market Data Feed")
    print("=" * 60)
    print("📊 Coverage: NSE EQ | Futures | Options | MCX Commodities")
    print("=" * 60)
    
    # Create live data instance with larger batch size
    live_data = BulkFyersLiveData(
        access_token=ACCESS_TOKEN,
        log_path="",
        litemode=False,
        batch_size=100  # Increased batch size
    )
    
    try:
        # Connect to WebSocket
        live_data.connect()
        
        print("\n✅ Live data feed started. Press Ctrl+C to stop.")
        print("🎯 You'll see colored updates: Green = Up, Red = Down")
        print("💡 Symbols: EQ (Stocks) | FUT (Futures) | OPT (Options) | MCX (Commodities)")
        
        # Keep the script running
        batch_rotation_time = 300  # 5 minutes
        last_rotation = time.time()
        
        while True:
            time.sleep(1)
            
            # Optional: Rotate batches every X seconds (comment out if not needed)
            # if time.time() - last_rotation > batch_rotation_time:
            #     live_data.rotate_batch()
            #     last_rotation = time.time()
            #     print(f"\n🔄 Rotated to batch {live_data.current_batch + 1}")
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping live data feed...")
        live_data.disconnect()
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        live_data.disconnect()