from fastapi import APIRouter
from db import db
from models import Team
from bson import ObjectId

router = APIRouter()

@router.post("/teams")
async def create_team(team: Team):
    team_dict = team.dict()
    team_dict["students"] = []
    result = await db.teams.insert_one(team_dict)
    return {"id": str(result.inserted_id)}

@router.post("/teams/{team_id}/add_student/{student_id}")
async def add_student(team_id: str, student_id: str):
    await db.teams.update_one(
        {"_id": ObjectId(team_id)},
        {"$addToSet": {"students": ObjectId(student_id)}}
    )
    return {"status": "student added"}
