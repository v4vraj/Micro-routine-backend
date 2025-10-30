from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from app.utils.auth_utils import get_current_user
from app.services.google_service import (
    get_google_auth_url_for_user,
    handle_google_callback,
    make_frontend_redirect_after_success as google_frontend_redirect
)
from app.services.jira_service import (
    get_jira_auth_url_for_user,
    handle_jira_callback,
    make_frontend_redirect_after_success as jira_frontend_redirect
)
from app.database import tokens_collection  # ✅ NEW IMPORT

router = APIRouter(prefix="/permissions", tags=["Permissions"])


# --- FRONTEND INITIATES GOOGLE AUTH ---
@router.get("/google/connect")
def google_connect(current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    url = get_google_auth_url_for_user(user_id)
    return {"auth_url": url}


# --- FRONTEND INITIATES JIRA AUTH ---
@router.get("/jira/connect")
def jira_connect(current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    url = get_jira_auth_url_for_user(user_id)
    return {"auth_url": url}


# --- GOOGLE CALLBACK (REDIRECTS TO FRONTEND) ---
@router.get("/google/callback")
def google_callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    # ✅ --- ADD DEBUGGING ---
    print("--- GOOGLE CALLBACK RECEIVED ---")
    print(f"Code: {code}")
    print(f"State (user_id): {state}")
    print(f"Error (if any): {error}")
    # ✅ -----------------------

    if error:
        print(f"OAuth Error from Google: {error}") # ✅ DEBUG
        return RedirectResponse(
            url=google_frontend_redirect("google", status="error", msg=error, user_id=state)
        )

    if not code or not state:
        print("Error: Missing code or state") # ✅ DEBUG
        return RedirectResponse(
            url=google_frontend_redirect("google", status="error", msg="Missing code/state")
        )

    try:
        print("Attempting to handle_google_callback...") # ✅ DEBUG
        handle_google_callback(code, state)
        print("Callback successful, token saved.") # ✅ DEBUG
    except Exception as e:
        # ✅ --- THIS IS THE MOST IMPORTANT PART ---
        print(f"--- !!! ERROR DURING TOKEN EXCHANGE !!! ---")
        print(str(e))
        import traceback
        traceback.print_exc() # This will print the full error
        # ✅ ---------------------------------------
        return RedirectResponse(
            url=google_frontend_redirect("google", status="error", msg=str(e), user_id=state)
        )

    print("Redirecting to frontend (success)...") # ✅ DEBUG
    return RedirectResponse(
        url=google_frontend_redirect("google", status="success", user_id=state)
    )


# --- JIRA CALLBACK (REDIRECTS TO FRONTEND) ---
@router.get("/jira/callback")
def jira_callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        return RedirectResponse(
            url=jira_frontend_redirect("jira", status="error", msg=error, user_id=state)
        )

    if not code or not state:
        return RedirectResponse(
            url=jira_frontend_redirect("jira", status="error", msg="Missing code/state")
        )

    try:
        handle_jira_callback(code, state)
    except Exception as e:
        return RedirectResponse(
            url=jira_frontend_redirect("jira", status="error", msg=str(e), user_id=state)
        )

    return RedirectResponse(
        url=jira_frontend_redirect("jira", status="success", user_id=state)
    )


# --- ✅ NEW: CONNECTION STATUS ENDPOINT ---
@router.get("/status")
def get_connection_status(current_user=Depends(get_current_user)):
    """
    Returns whether Google and Jira are connected for the current user.
    Looks up tokens in the `tokens_collection`.
    """
    user_id = str(current_user["_id"])

    google_connected = tokens_collection.find_one({
        "user_id": user_id,
        "provider": "google"
    }) is not None

    jira_connected = tokens_collection.find_one({
        "user_id": user_id,
        "provider": "jira"
    }) is not None

    return {"google": google_connected, "jira": jira_connected}
