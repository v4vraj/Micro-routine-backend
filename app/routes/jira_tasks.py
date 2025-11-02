import requests
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import RedirectResponse 
from app.services.token_store import get_token
from datetime import datetime

# Import the functions you need from the service
from app.services.jira_service import (
    get_high_priority_tickets_for_user,
    handle_jira_callback,
    make_frontend_redirect_after_success
)

router = APIRouter(prefix="/api/jira", tags=["Jira"])

@router.get("/tickets/high-priority")
def get_high_priority_tickets(user_id: str = Query(...)):
    return get_high_priority_tickets_for_user(user_id)


@router.get("/callback")
def jira_oauth_callback(code: str, state: str):
    try:
        user_id = state
        handle_jira_callback(code, user_id)
        redirect_url = make_frontend_redirect_after_success(
            provider="jira", 
            status="success", 
            user_id=user_id
        )
        return RedirectResponse(url=redirect_url)
    except Exception as e:
        print(f"Error during Jira callback: {e}")
        redirect_url = make_frontend_redirect_after_success(
            provider="jira", 
            status="error", 
            msg=str(e)
        )
        return RedirectResponse(url=redirect_url)