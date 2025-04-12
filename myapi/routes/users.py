from fastapi import APIRouter
from db import db
from models import User

router = APIRouter()

@router.post("/users")
async def create_user(user: User):
    result = await db.users.insert_one(user.dict())
    return {"id": str(result.inserted_id)}
