from motor.motor_asyncio import AsyncIOMotorCollection
from app.db.database import get_assignment_collection
from app.schemas.assignment import AssignmentCreate, AssignmentInDB, AssignmentUpdate
import uuid
from typing import List, Optional

assignment_collection: AsyncIOMotorCollection = get_assignment_collection()

async def create_assignment(assignment_in: AssignmentCreate) -> AssignmentInDB:
    assignment_id = str(uuid.uuid4())
    assignment_db_data = assignment_in.model_dump()
    assignment_db_data["_id"] = assignment_id

    await assignment_collection.insert_one(assignment_db_data)
    created_assignment = await get_assignment_by_id(assignment_id)
    if not created_assignment:
        raise Exception("Failed to retrieve created assignment")
    return created_assignment

async def get_assignment_by_id(assignment_id: str) -> AssignmentInDB | None:
    assignment = await assignment_collection.find_one({"_id": assignment_id})
    return AssignmentInDB(**assignment) if assignment else None

async def get_assignments_for_team(team_id: str) -> List[AssignmentInDB]:
    assignments_cursor = assignment_collection.find({"team_id": team_id})
    assignments = await assignments_cursor.to_list(length=None)
    return [AssignmentInDB(**assignment) for assignment in assignments]

# Add update_assignment function if needed (check admin/creator permission)