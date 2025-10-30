import os
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv

load_dotenv()

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]

def get_google_flow():
    return Flow.from_client_secrets_file(
        os.getenv("GOOGLE_CLIENT_SECRET_FILE"),
        scopes=GOOGLE_SCOPES,
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI") 
    )

# Atlassian Jira OAuth setup (OAuth 2.0)
JIRA_CLIENT_ID = os.getenv("JIRA_CLIENT_ID")
JIRA_CLIENT_SECRET = os.getenv("JIRA_CLIENT_SECRET")
JIRA_REDIRECT_URI = os.getenv("JIRA_REDIRECT_URI")
JIRA_AUTH_URL = "https://auth.atlassian.com/authorize"
JIRA_TOKEN_URL = "https://auth.atlassian.com/oauth/token"
JIRA_SCOPES = [
    "read:jira-user",
    "read:jira-work",
    "write:jira-work",
]
