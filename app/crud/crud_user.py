from motor.motor_asyncio import AsyncIOMotorCollection
from app.db.database import get_user_collection
from app.schemas.user import UserCreate, UserCreateGoogle, UserInDB, UserUpdate
from app.core.security import get_password_hash
from bson import ObjectId # Only if using ObjectId, prefer UUID strings
import uuid

user_collection: AsyncIOMotorCollection = get_user_collection()

async def get_user_by_email(email: str) -> UserInDB | None:
    user = await user_collection.find_one({"email": email})
    return UserInDB(**user) if user else None

async def get_user_by_id(user_id: str) -> UserInDB | None:
    # Use _id as the query key if using aliases, otherwise 'id' if not
    user = await user_collection.find_one({"_id": user_id})
    return UserInDB(**user) if user else None

async def get_user_by_google_id(google_id: str) -> UserInDB | None:
     user = await user_collection.find_one({"google_id": google_id})
     return UserInDB(**user) if user else None

async def create_user_email_pwd(user_in: UserCreate) -> UserInDB:
    hashed_password = get_password_hash(user_in.password)
    user_db_data = user_in.model_dump(exclude={"password"}) # Use model_dump in Pydantic v2
    user_db_data["hashed_password"] = hashed_password
    user_id = str(uuid.uuid4())
    user_db_data["_id"] = user_id # Explicitly set _id

    await user_collection.insert_one(user_db_data)
    # Fetch the created user to return the full UserInDB model
    created_user = await get_user_by_id(user_id)
    if not created_user: # Should not happen but good practice
        raise Exception("Failed to retrieve created user")
    return created_user


async def create_user_google(user_in: UserCreateGoogle) -> UserInDB:
    user_db_data = user_in.model_dump()
    user_id = str(uuid.uuid4())
    user_db_data["_id"] = user_id # Explicitly set _id
    user_db_data["hashed_password"] = None # No password initially for Google users
    user_db_data["is_active"] = True # Assume active on Google sign-up

    await user_collection.insert_one(user_db_data)
    created_user = await get_user_by_id(user_id)
    if not created_user:
        raise Exception("Failed to retrieve created Google user")
    return created_user

async def add_team_to_user(user_id: str, team_id: str):
    await user_collection.update_one(
        {"_id": user_id},
        {"$addToSet": {"team_ids": team_id}} # Use $addToSet to avoid duplicates
    )

# Add update_user function if needed