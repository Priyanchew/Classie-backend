from pydantic import Field, HttpUrl, BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from app.schemas.base import BaseSchema # Reusing BaseSchema is tricky for _rev handling

# PouchDB/CouchDB documents need _id and _rev
class PouchDocBase(BaseModel):
    id: str = Field(..., alias="_id")
    rev: Optional[str] = Field(None, alias="_rev") # Revision ID is crucial for sync/conflicts

class SubmissionVersion(BaseModel):
    version: int
    file_url: HttpUrl # URL to the uploaded file (S3, GCS, etc.)
    submitted_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    content_hash: Optional[str] = None # Optional hash to detect identical files
    notes: Optional[str] = None

# Represents the document stored in MongoDB and potentially synced via PouchDB
class SubmissionInDB(PouchDocBase): # Inherit _id, _rev structure
    doc_type: str = "submission" # Add a type field for easier querying/sync filtering
    assignment_id: str
    student_id: str
    team_id: str
    current_version: int = 0
    versions: List[SubmissionVersion] = []
    # Add updated_at specifically managed for LWW resolution if needed
    last_updated_at: datetime = Field(default_factory=datetime.now(timezone.utc))

    class Config:
        populate_by_name = True # Allow _id and _rev aliases
        json_encoders = {datetime: lambda dt: dt.isoformat()}

# Data needed to create the *first* version of a submission
class SubmissionCreate(BaseModel):
    assignment_id: str
    team_id: str
    file_url: HttpUrl # URL provided after successful upload elsewhere
    content_hash: Optional[str] = None
    notes: Optional[str] = None

# Data needed to upload a *new* version
class SubmissionUploadNewVersion(BaseModel):
    file_url: HttpUrl
    content_hash: Optional[str] = None
    notes: Optional[str] = None

# Public view of a submission (e.g., latest version)
class SubmissionPublic(BaseModel):
    id: str = Field(..., alias="_id")
    assignment_id: str
    student_id: str
    team_id: str
    current_version: int
    latest_version: SubmissionVersion | None = None # Show latest version details
    last_updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}
        from_attributes = True # Allow creation from SubmissionInDB model