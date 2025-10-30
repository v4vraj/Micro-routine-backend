from datetime import datetime
from app.database import tokens_collection

def save_token(user_id: str, provider: str, token_data: dict):
    """Upserts the OAuth token for the given user and provider."""
    tokens_collection.update_one(
        {"user_id": user_id, "provider": provider},
        {
            "$set": {
                "token": token_data,
                "updated_at": datetime.utcnow(),
            }
        },
        upsert=True
    )

def get_token(user_id: str, provider: str):
    """Retrieve stored token for user/provider if it exists."""
    record = tokens_collection.find_one({"user_id": user_id, "provider": provider})
    return record.get("token") if record else None


def get_token_for_user(user_id: str, provider: str):
    """Retrieve stored token for a specific user and provider."""
    record = tokens_collection.find_one({"user_id": user_id, "provider": provider})
    return record.get("token") if record else None
