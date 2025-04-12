from fastapi import APIRouter
from db import db
from models import Submission
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.post("/submissions")
async def submit_assignment(sub: Submission):
    assignment = await db.assignments.find_one({"_id": ObjectId(sub.assignmentId)})
    if not assignment:
        return {"error": "Assignment not found"}
    
    if datetime.utcnow() > assignment["deadline"]:
        return {"error": "Deadline has passed"}

    # Find version count
    version = await db.submissions.count_documents({
        "assignmentId": ObjectId(sub.assignmentId),
        "studentId": ObjectId(sub.studentId)
    }) + 1

    submission_data = {
        "assignmentId": ObjectId(sub.assignmentId),
        "studentId": ObjectId(sub.studentId),
        "content": sub.content,
        "version": version,
        "submittedAt": datetime.utcnow()
    }

    result = await db.submissions.insert_one(submission_data)
    return {"id": str(result.inserted_id), "version": version}
