from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth_routes, permission_routes

app = FastAPI(title="Micro Routine AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(permission_routes.router)
@app.get("/")
def root():
    return {"message": "Welcome to Micro Routine AI Agent API 🚀"}
