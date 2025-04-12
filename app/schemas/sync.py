from pydantic import BaseModel, Field, RootModel
from typing import List, Dict, Any, Optional
from datetime import datetime # Import datetime
from app.schemas.submission import SubmissionInDB # Import other doc types if syncing them

# Represents a document coming from PouchDB in _bulk_docs
# It will have _id, _rev, and potentially _deleted flag
class PouchDocument(BaseModel):
    id: str = Field(..., alias="_id")
    rev: str = Field(..., alias="_rev")
    deleted: Optional[bool] = Field(None, alias="_deleted")
    # Include fields common to *all* synced document types, or use Any
    # Alternatively, use discriminated unions if doc_type is reliable
    doc_type: Optional[str] = None # Useful for routing logic
    last_updated_at: Optional[datetime] = None # Crucial for LWW

    # Allow extra fields as documents have varying structures
    model_config = {
        "extra": "allow",
        "populate_by_name": True
    }


class BulkDocsRequest(BaseModel):
    docs: List[Dict[str, Any]] # Use Dict initially, validate specific types later
    new_edits: bool = True # PouchDB usually sends true

class BulkDocsResponseItem(BaseModel):
    ok: bool = True
    id: str
    rev: str # The new revision ID after successful save/update
    error: Optional[str] = None
    reason: Optional[str] = None

# Update RevsDiffRequest to use RootModel
class RevsDiffRequest(RootModel):
    # Structure: { "doc_id": ["rev1", "rev2", ...] }
    root: Dict[str, List[str]]

class RevsDiffResponseItemMissing(BaseModel):
    missing: List[str]

# Update RevsDiffResponse to use RootModel
class RevsDiffResponse(RootModel):
     # Structure: { "doc_id": { "missing": ["rev3", "rev4"], "possible_ancestors": [...] } }
     # Simplified: just return missing revs PouchDB needs to send
    root: Dict[str, RevsDiffResponseItemMissing]


# Simplified structure for _changes feed
class ChangeItem(BaseModel):
    seq: Any # Sequence ID (can be int or string based on implementation)
    id: str
    changes: List[Dict[str, str]] # List of [{"rev": "revision_id"}]
    deleted: Optional[bool] = None
    doc: Optional[Dict[str, Any]] = None # Include doc if include_docs=true

class ChangesResponse(BaseModel):
    results: List[ChangeItem]
    last_seq: Any
    pending: Optional[int] = None