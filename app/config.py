import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "micro_routine_db")

JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

BACKEND_ROOT_URL = os.getenv("BACKEND_ROOT_URL", "http://localhost:8000")
FRONTEND_ROOT_URL = os.getenv("FRONTEND_ROOT_URL", "http://localhost:5713")

# Google
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_BACKEND_CALLBACK = os.getenv(
    "GOOGLE_BACKEND_CALLBACK", f"{BACKEND_ROOT_URL}/permissions/google/callback"
)
GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/calendar.events.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.location.read",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]

# Jira (Atlassian 3LO)
JIRA_CLIENT_ID = os.getenv("JIRA_CLIENT_ID")
JIRA_CLIENT_SECRET = os.getenv("JIRA_CLIENT_SECRET")
JIRA_BACKEND_CALLBACK = os.getenv("JIRA_BACKEND_CALLBACK", f"{BACKEND_ROOT_URL}/permissions/jira/callback")
JIRA_SCOPES = "read:jira-user read:jira-work write:jira-work offline_access"
