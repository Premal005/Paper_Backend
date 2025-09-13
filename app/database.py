import motor.motor_asyncio
from app.config import Config

# Initialize the MongoDB client (shared across all models)
client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URI)
db = client.get_database("paper_trading")

# Initialize indexes for collections that require uniqueness
async def init_indexes():
    await db.market_data.create_index(
        [("symbol", 1), ("exchange", 1)],
        unique=True
    )
    await db.users.create_index("email", unique=True)
    # Add more indexes here if needed
