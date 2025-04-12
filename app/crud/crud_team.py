import secrets
from motor.motor_asyncio import AsyncIOMotorCollection
from app.db.database import get_team_collection, get_user_collection
from app.schemas.team import TeamCreate, TeamInDB, TeamUpdate
from app.crud.crud_user import add_team_to_user
import uuid
from typing import List, Optional

team_collection: AsyncIOMotorCollection = get_team_collection()
user_collection: AsyncIOMotorCollection = get_user_collection()

# Generate a unique, hard-to-guess join code
async def generate_unique_join_code(length=8):
    while True:
        code = secrets.token_urlsafe(length)
        existing = await team_collection.find_one({"join_code": code})
        if not existing:
            return code

async def get_team_by_id(team_id: str) -> TeamInDB | None:
    team = await team_collection.find_one({"_id": team_id})
    return TeamInDB(**team) if team else None

async def get_team_by_join_code(code: str) -> TeamInDB | None:
    team = await team_collection.find_one({"join_code": code})
    return TeamInDB(**team) if team else None

async def get_teams_for_user(user_id: str) -> List[TeamInDB]:
    # Find teams where user is admin or member
    teams_cursor = team_collection.find({
        "$or": [
            {"admin_id": user_id},
            {"member_ids": user_id}
        ]
    })
    teams = await teams_cursor.to_list(length=None) # Get all matching teams
    return [TeamInDB(**team) for team in teams]


async def create_team(team_in: TeamCreate) -> TeamInDB:
    team_id = str(uuid.uuid4())
    join_code = await generate_unique_join_code()
    team_db_data = team_in.model_dump()
    team_db_data["_id"] = team_id
    team_db_data["join_code"] = join_code
    team_db_data["member_ids"] = [team_in.admin_id] # Admin is also a member

    await team_collection.insert_one(team_db_data)
    # Add team to admin's user document
    await add_team_to_user(user_id=team_in.admin_id, team_id=team_id)

    created_team = await get_team_by_id(team_id)
    if not created_team:
        raise Exception("Failed to retrieve created team")
    return created_team

async def add_member_to_team(team_id: str, user_id: str) -> bool:
    # Add user to team's member list
    result_team = await team_collection.update_one(
        {"_id": team_id},
        {"$addToSet": {"member_ids": user_id}}
    )
    # Add team to user's team list
    await add_team_to_user(user_id=user_id, team_id=team_id)

    return result_team.modified_count > 0


# Add update_team function if needed (check admin permission)