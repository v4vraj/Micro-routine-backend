import warnings
from google_auth_oauthlib.flow import Flow
from app.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_BACKEND_CALLBACK,
    GOOGLE_SCOPES,
    FRONTEND_ROOT_URL
)
from app.services.token_store import save_token


def _make_client_config():
    """Google OAuth client config."""
    return {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [GOOGLE_BACKEND_CALLBACK],
        }
    }


def get_google_auth_url_for_user(user_id: str) -> str:
    """Generate Google OAuth URL for frontend; state=user_id."""
    # Sort scopes to prevent 'ScopeChangedError' due to ordering differences
    flow = Flow.from_client_config(
        _make_client_config(),
        scopes=sorted(GOOGLE_SCOPES)
    )
    flow.redirect_uri = GOOGLE_BACKEND_CALLBACK

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=user_id
    )
    return auth_url


def handle_google_callback(code: str, state: str) -> dict:
    """Exchange code for tokens and save them."""
    user_id = state
    flow = Flow.from_client_config(
        _make_client_config(),
        scopes=sorted(GOOGLE_SCOPES)  # Keep ordering consistent
    )
    flow.redirect_uri = GOOGLE_BACKEND_CALLBACK

    # Ignore "Scope has changed" warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        flow.fetch_token(code=code)  # Do NOT pass client_id/client_secret

    creds = flow.credentials
    token_dict = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
        "expiry": creds.expiry.isoformat() if creds.expiry else None
    }

    save_token(user_id, "google", token_dict)
    return token_dict

def make_frontend_redirect_after_success(provider: str, status: str = "success", msg: str = None, user_id: str = None):
    """Redirect user back to frontend Permissions page after OAuth."""
    url = f"{FRONTEND_ROOT_URL}/permissions?connected={provider}&status={status}"
    if user_id:
        url += f"&user_id={user_id}"
    if msg:
        url += f"&msg={msg}"
    return url



