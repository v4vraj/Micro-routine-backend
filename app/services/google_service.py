import warnings
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import logging
import pytz

from app.config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_BACKEND_CALLBACK,
    GOOGLE_SCOPES,
    FRONTEND_ROOT_URL,
)
from app.services.token_store import save_token, get_token_for_user


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
    flow = Flow.from_client_config(_make_client_config(), scopes=sorted(GOOGLE_SCOPES))
    flow.redirect_uri = GOOGLE_BACKEND_CALLBACK

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=user_id,
    )
    return auth_url


def handle_google_callback(code: str, state: str) -> dict:
    """Exchange code for tokens and save them."""
    user_id = state
    flow = Flow.from_client_config(_make_client_config(), scopes=sorted(GOOGLE_SCOPES))
    flow.redirect_uri = GOOGLE_BACKEND_CALLBACK

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        flow.fetch_token(code=code)

    creds = flow.credentials
    token_dict = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
    }

    save_token(user_id, "google", token_dict)
    return token_dict


def make_frontend_redirect_after_success(
    provider: str, status: str = "success", msg: str = None, user_id: str = None
):
    """Redirect user back to frontend Permissions page after OAuth."""
    url = f"{FRONTEND_ROOT_URL}/permissions?connected={provider}&status={status}"
    if user_id:
        url += f"&user_id={user_id}"
    if msg:
        url += f"&msg={msg}"
    return url


# ✅ --- GOOGLE CALENDAR API ACCESS ---


def _build_google_calendar_service(user_id: str):
    """Create Google Calendar service using saved user tokens."""
    token_doc = get_token_for_user(user_id, "google")
    if not token_doc:
        raise Exception("Google account not connected")

    creds = Credentials(
        token=token_doc["token"],
        refresh_token=token_doc.get("refresh_token"),
        token_uri=token_doc.get("token_uri"),
        client_id=token_doc.get("client_id"),
        client_secret=token_doc.get("client_secret"),
        scopes=token_doc.get("scopes"),
    )

    # Refresh expired token if needed
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_token(
            user_id,
            "google",
            {
                **token_doc,
                "token": creds.token,
                "expiry": creds.expiry.isoformat() if creds.expiry else None,
            },
        )

    return build("calendar", "v3", credentials=creds)


def get_month_events(user_id: str):
    """Fetch events for the current month for a given user."""
    try:
        service = _build_google_calendar_service(user_id)
        now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1)

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_of_month.isoformat(),
                timeMax=end_of_month.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])
        formatted_events = [
            {
                "id": e["id"],
                "title": e.get("summary", "No Title"),
                "start": e["start"].get("dateTime", e["start"].get("date")),
                "end": e["end"].get("dateTime", e["end"].get("date")),
                "calendar": e.get("organizer", {}).get("email", "primary"),
            }
            for e in events
        ]

        return formatted_events

    except Exception as e:
        logging.error(f"Error fetching events: {e}")
        raise e


def _build_google_fitness_service(user_id: str):
    """Create Google Fitness service using saved user tokens."""
    token_doc = get_token_for_user(user_id, "google")
    if not token_doc:
        raise Exception("Google account not connected")

    creds = Credentials(
        token=token_doc["token"],
        refresh_token=token_doc.get("refresh_token"),
        token_uri=token_doc.get("token_uri"),
        client_id=token_doc.get("client_id"),
        client_secret=token_doc.get("client_secret"),
        scopes=token_doc.get("scopes"),
    )

    # Refresh expired token if needed
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_token(
            user_id,
            "google",
            {
                **token_doc,
                "token": creds.token,
                "expiry": creds.expiry.isoformat() if creds.expiry else None,
            },
        )

    return build("fitness", "v1", credentials=creds)


def _get_daily_aggregate_data(
    user_id: str, 
    data_source_id: str, 
    value_field: str = "intVal"
) -> float: # Return float to handle both int and float values
    """
    Generic helper to fetch daily aggregate data from Google Fit.
    
    Args:
        user_id: The user's ID.
        data_source_id: The Google Fit data source to query (e.g., "derived:com.google.step_count.delta:...")
        value_field: The field to extract the value from ("intVal" or "fpVal").
    """
    try:
        service = _build_google_fitness_service(user_id)

        # Define time range (start of day → now) in UTC
        now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Google Fit API uses nanoseconds
        dataset_id = f"{int(start_of_day.timestamp() * 1e9)}-{int(now.timestamp() * 1e9)}"

        dataset = (
            service.users()
            .dataSources()
            .datasets()
            .get(
                userId="me",
                dataSourceId=data_source_id,
                datasetId=dataset_id,
            )
            .execute()
        )

        total_value = 0.0
        for point in dataset.get("point", []):
            for field in point.get("value", []):
                total_value += field.get(value_field, 0)

        return total_value

    except Exception as e:
        logging.error(f"Error getting Google Fit data for {data_source_id}: {e}")
        # Re-raise to be handled by the route
        raise e

# --- NEW GOOGLE FIT SERVICE METHODS ---

def get_daily_steps_from_google(user_id: str) -> int:
    """Fetches daily step count from Google Fit."""
    steps = _get_daily_aggregate_data(
        user_id,
        "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps",
        "intVal"
    )
    return int(steps)

def get_daily_calories_from_google(user_id: str) -> float:
    """Fetches daily calories burned from Google Fit."""
    calories = _get_daily_aggregate_data(
        user_id,
        "derived:com.google.calories.expended:com.google.android.gms:merge_calories_expended",
        "fpVal"
    )
    return calories

def get_daily_active_minutes_from_google(user_id: str) -> int:
    """Fetches daily active minutes from Google Fit."""
    minutes = _get_daily_aggregate_data(
        user_id,
        "derived:com.google.active_minutes:com.google.android.gms:merge_active_minutes",
        "intVal"
    )
    return int(minutes)
