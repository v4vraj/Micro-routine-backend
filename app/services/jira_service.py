import requests
from urllib.parse import urlencode
from app.config import JIRA_CLIENT_ID, JIRA_CLIENT_SECRET, JIRA_BACKEND_CALLBACK, JIRA_SCOPES, FRONTEND_ROOT_URL
from app.services.token_store import save_token, get_token
import requests
from datetime import date
from fastapi import HTTPException

# ... get_jira_auth_url_for_user (no changes) ...
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

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token from Jira.")

    # Get accessible resources to extract cloud_id
    resources_url = "https://api.atlassian.com/oauth/token/accessible-resources"
    headers = {"Authorization": f"Bearer {access_token}"}
    resources_resp = requests.get(resources_url, headers=headers)
    resources_resp.raise_for_status()
    resources_data = resources_resp.json()

    if not resources_data:
        raise HTTPException(status_code=400, detail="No accessible Jira resources found for this user.")

    cloud_id = resources_data[0].get("id")
    if not cloud_id:
        raise HTTPException(status_code=400, detail="Could not determine Jira Cloud ID.")

    token_data["cloud_id"] = cloud_id

    # ✅ Add user_id into token_data before saving
    token_data["user_id"] = user_id

    save_token(user_id, "jira", token_data)

    # ✅ Redirect back to frontend including user_id in query params
    redirect_url = make_frontend_redirect_after_success(
        provider="jira",
        status="success",
        user_id=user_id
    )
    print(f"Redirecting to: {redirect_url}") 
    return redirect_url



def get_high_priority_tickets_for_user(user_id: str):
    """
    Fetches high-priority Jira tickets assigned to the authenticated user
    using the new /rest/api/3/search/jql endpoint (required as of 2024).
    """
    token_data = get_token(user_id, "jira")
    if not token_data:
        raise HTTPException(status_code=401, detail="No Jira token found. Please authenticate Jira first.")

    access_token = token_data.get("access_token")
    cloud_id = token_data.get("cloud_id")

    if not cloud_id:
        raise HTTPException(status_code=400, detail="Missing Jira Cloud ID in stored token data. Please re-authenticate.")

    # ✅ Correct new Jira Search JQL endpoint
    url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/search/jql"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # ✅ Proper payload format — no "queries" array
    payload = {
        "jql": "assignee = currentUser() AND status != Done ORDER BY priority DESC",
        "maxResults": 5,
        "fields": ["summary", "priority", "status"]
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Jira API error: {response.text}"
        )

    data = response.json()

    issues = data.get("issues", [])
    ticket_list = []

    for issue in issues:
        fields = issue.get("fields", {})
        ticket_list.append({
            "key": issue.get("key"),
            "summary": fields.get("summary"),
            "priority": fields.get("priority", {}).get("name", "No Priority"),
            "status": fields.get("status", {}).get("name", "Unknown")
        })

    return {"tickets": ticket_list}


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