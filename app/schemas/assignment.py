from pydantic import Field, BaseModel
from typing import List, Optional
from datetime import datetime
from app.schemas.base import BaseSchema

class AssignmentBase(BaseModel):
    title: str = Field(..., min_length=3)
    description: str | None = None
    due_date: datetime | None = None

class AssignmentCreate(AssignmentBase):
    team_id: str
    creator_id: str # Should be the admin

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class AssignmentInDB(AssignmentBase, BaseSchema):
    team_id: str
    creator_id: str

class AssignmentPublic(AssignmentBase, BaseSchema):
    team_id: str