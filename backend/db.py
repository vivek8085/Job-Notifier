# db.py
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

from urllib.parse import quote_plus

username = "s8994680"
password = quote_plus("**********")  # encodes special characters

MONGO_URL = f"mongodb+srv://{username}:{password}@cluster0.ojmuisw.mongodb.net/job?retryWrites=true&w=majority&appName=Cluster0"


client = AsyncIOMotorClient(MONGO_URL)
db = client["job"]   # your DB name
opportunities_collection = db["opportunities"]
if not MONGO_URL:
    raise RuntimeError("MONGO_URL missing in environment (.env)")

MONGO_DB_NAME = os.getenv("MONGO_DB", "job")

async def ensure_indexes():
    # unique index on hash to avoid duplicates
    await opportunities_collection.create_index("hash", unique=True, sparse=True)
    await opportunities_collection.create_index("discovered_at")

