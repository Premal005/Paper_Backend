import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # MT5 Configuration
    MT5_PATH = os.getenv("MT5_PATH", "C:\Program Files\Pepperstone MetaTrader 5\terminal64.exe")
    MT5_LOGIN = int(os.getenv("MT5_LOGIN", 12345678))
    MT5_PASSWORD = "hMwdfpob0("
    MT5_SERVER = os.getenv("MT5_SERVER", "YourBrokerServer")
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8080))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

settings = Settings()