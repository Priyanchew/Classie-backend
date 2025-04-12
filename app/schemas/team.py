from pydantic import Field, BaseModel
from typing import List
from app.schemas.base import BaseSchema

class TeamBase(BaseModel):
    name: str = Field(..., min_length=3)
    description: str | None = None

class TeamCreate(TeamBase):
    admin_id: str # Set automatically on creation

class TeamUpdate(TeamBase):
    name: str | None = None # Allow partial updates

class TeamJoin(BaseModel):
    join_code: str

class TeamInDB(TeamBase, BaseSchema):
    admin_id: str
    member_ids: List[str] = []
    join_code: str | None = None # Unique code to join

class TeamPublic(TeamBase, BaseSchema):
    admin_id: str
    member_count: int # Calculated field for public view

# schemas/team.py continued
from app.schemas.user import UserPublic # Ensure UserPublic is importable

class TeamWithMembers(TeamPublic):
     members: List[UserPublic] = [] # Now UserPublic is defined