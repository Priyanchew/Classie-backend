from pydantic import EmailStr, Field, BaseModel
from typing import List, Optional
from app.schemas.base import BaseSchema

# Base properties
class UserBase(BaseModel):
    email: EmailStr = Field(...)
    full_name: str | None = None
    is_active: bool = True
    is_admin: bool = False # Or role-based system

# Properties stored in DB
class UserInDBBase(UserBase, BaseSchema):
    hashed_password: str | None = None # Can be null for OAuth users initially
    google_id: str | None = None       # Store Google unique ID
    team_ids: List[str] = []           # IDs of teams the user is part of

# For creating a new user via email/password
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

# For creating user via Google OAuth
class UserCreateGoogle(UserBase):
    google_id: str

# For updating user data
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None # Handle password update carefully

# Properties to return to client (exclude sensitive info)
class UserPublic(UserBase, BaseSchema):
    pass # Inherits necessary fields, excludes hashed_password, google_id etc. by default

# Full User representation in DB (used internally)
class UserInDB(UserInDBBase):
    pass