# Micro Routine Agent - Backend (FastAPI)

## Setup

1. copy `.env.example` to `.env` and fill values.
2. Install dependencies:
   pip install -r requirements.txt

3. Start the server:
   python -m uvicorn app.main:app --reload

## Flow (frontend-driven)

1. User signs up / logs in via `/auth/signup` and `/auth/login` → receives `access_token`.
2. Frontend calls protected endpoint to get provider auth URL:

   - GET /permissions/google/connect (Authorization: Bearer <token>)
   - GET /permissions/jira/connect

   Response: `{ "auth_url": "<provider-oauth-url>" }`

3. Frontend redirects the browser to `auth_url`. Provider completes consent and redirects to backend callback:

   - Google redirects to `/permissions/google/callback?code=...&state=<user_id>`
   - Jira redirects to `/permissions/jira/callback?code=...&state=<user_id>`

4. Backend exchanges the code, saves tokens in Mongo (`user_tokens`), and redirects user to:
   `FRONTEND_ROOT_URL/oauth-success?provider=<provider>`

## Notes

- `state` holds the `user_id` (internal) so the backend knows which user to associate tokens with.
- Tokens are saved in MongoDB per user & provider.
- You should protect the callback endpoints from CSRF in production (validate `state` more strictly).
- For production:
  - Use HTTPS
  - Store secrets securely
  - Rotate client secrets and secure tokens encryption at rest
