from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

class BaseSchema(BaseModel):
    # Use Field to provide default factory for UUIDs
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=datetime.now(timezone.utc))

    class Config:
        populate_by_name = True # Allow using alias _id
        json_encoders = {datetime: lambda dt: dt.isoformat()}
        from_attributes = True # For orm_mode compatibility if needed later