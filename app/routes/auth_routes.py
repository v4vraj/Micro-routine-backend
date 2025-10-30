from fastapi import APIRouter, HTTPException, status
from app.schemas.user_schema import UserSignup, UserLogin
from app.utils.auth_utils import hash_password, verify_password, create_access_token
from app.database import users_collection
from app.models.user_model import user_entity

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/signup")
def signup(user: UserSignup):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)
    user_data = {
        "username": user.username,
        "email": user.email,
        "password": hashed_pw
    }
    users_collection.insert_one(user_data)
    return {"message": "User registered successfully"}

@router.post("/login")
def login(user: UserLogin):
    existing_user = users_collection.find_one({"email": user.email})
    if not existing_user or not verify_password(user.password, existing_user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"user_id": str(existing_user["_id"])})
    return {"access_token": token, "user": user_entity(existing_user)}
