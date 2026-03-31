from fastapi import APIRouter, Depends
from typing import List
import uuid
from datetime import datetime, timezone

from database import db
from auth import get_current_user, require_admin, hash_password, verify_password, create_token
from models import UserCreate, UserLogin, UserResponse
from fastapi import HTTPException

router = APIRouter()


@router.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate):
    existing = await db.users.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username-ul există deja")

    user_doc = {
        "id": str(uuid.uuid4()),
        "username": user.username,
        "password": hash_password(user.password),
        "full_name": user.full_name,
        "role": user.role,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)

    return UserResponse(
        id=user_doc["id"],
        username=user_doc["username"],
        full_name=user_doc["full_name"],
        role=user_doc["role"],
        created_at=user_doc["created_at"]
    )


@router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"username": credentials.username}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credențiale invalide")

    token = create_token(user["id"], user["role"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"]
        }
    }


@router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        username=user["username"],
        full_name=user["full_name"],
        role=user["role"],
        created_at=user["created_at"]
    )


@router.get("/users", response_model=List[UserResponse])
async def get_users(user: dict = Depends(require_admin)):
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return [UserResponse(**u) for u in users]


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(require_admin)):
    if admin["id"] == user_id:
        raise HTTPException(status_code=400, detail="Nu vă puteți șterge propriu cont")
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Utilizator negăsit")
    return {"message": "Utilizator șters"}
