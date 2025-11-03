from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth_routes, permission_routes
from app.routes import google_calendar_route
from app.routes.google_fitness import router as google_fitness_router
from app.routes import jira_tasks,wellness_router

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
app.include_router(google_calendar_route.router)
app.include_router(google_fitness_router)
app.include_router(jira_tasks.router)
app.include_router(wellness_router.router)


@app.get("/")
def root():
    return {"message": "Welcome to Micro Routine AI Agent API 🚀"}
