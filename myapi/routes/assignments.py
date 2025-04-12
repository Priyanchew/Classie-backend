from fastapi import APIRouter
from db import db
from models import Assignment

router = APIRouter()

@router.post("/assignments")
async def create_assignment(assignment: Assignment):
    result = await db.assignments.insert_one(assignment.dict())
    return {"id": str(result.inserted_id)}
