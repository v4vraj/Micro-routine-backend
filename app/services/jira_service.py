import requests
from urllib.parse import urlencode
from app.config import JIRA_CLIENT_ID, JIRA_CLIENT_SECRET, JIRA_BACKEND_CALLBACK, JIRA_SCOPES, FRONTEND_ROOT_URL
from app.services.token_store import save_token

def get_jira_auth_url_for_user(user_id: str):
    params = {
        "audience": "api.atlassian.com",
        "client_id": JIRA_CLIENT_ID,
        "scope": JIRA_SCOPES,
        "redirect_uri": JIRA_BACKEND_CALLBACK,
        "response_type": "code",
        "prompt": "consent",
        "state": user_id
    }
    return f"https://auth.atlassian.com/authorize?{urlencode(params)}"

def handle_jira_callback(code: str, state: str):
    user_id = state
    token_url = "https://auth.atlassian.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": JIRA_CLIENT_ID,
        "client_secret": JIRA_CLIENT_SECRET,
        "code": code,
        "redirect_uri": JIRA_BACKEND_CALLBACK
    }
    resp = requests.post(token_url, json=payload)
    resp.raise_for_status()
    token_data = resp.json()
    # token_data typically includes access_token, refresh_token, expires_in, etc.
    save_token(user_id, "jira", token_data)
    return token_data

def make_frontend_redirect_after_success(provider: str):
    return f"{FRONTEND_ROOT_URL}/oauth-success?provider={provider}"
