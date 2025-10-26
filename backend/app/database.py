import motor.motor_asyncio
from .config import MONGODB_URL

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
database = client.get_database("polymarket") # You can change the DB name here if needed

def get_database():
    return database
