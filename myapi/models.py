from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class User(BaseModel):
    name: str
    email: EmailStr
    role: str  # "student", "teacher", "admin"

class Team(BaseModel):
    name: str
    createdBy: str  # teacher _id

class Assignment(BaseModel):
    title: str
    description: str
    teamId: str
    createdBy: str
    deadline: datetime

class Submission(BaseModel):
    assignmentId: str
    studentId: str
    content: str
