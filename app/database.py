from pymongo import MongoClient
from app.config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users_collection = db["users"]
tokens_collection = db["user_tokens"]
wellness_collection = db["wellness_scores"]
