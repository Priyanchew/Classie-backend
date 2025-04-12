from motor.motor_asyncio import AsyncIOMotorCollection
from app.db.database import get_submission_collection
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionInDB,
    SubmissionVersion,
    SubmissionUploadNewVersion
)
# Import PouchDocument from sync schema
from app.schemas.sync import PouchDocument
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pymongo.results import UpdateResult


submission_collection: AsyncIOMotorCollection = get_submission_collection()

# Generate ID for submission document (consistent per student per assignment)
def generate_submission_doc_id(assignment_id: str, student_id: str) -> str:
     # Using a predictable ID helps PouchDB manage the same logical submission
     return f"sub_{assignment_id}_{student_id}"

async def get_submission_by_doc_id(doc_id: str) -> SubmissionInDB | None:
    submission = await submission_collection.find_one({"_id": doc_id})
    # Manually handle potential alias if needed during retrieval if model validation fails
    if submission and '_id' in submission:
         submission['id'] = submission['_id']
    if submission and '_rev' in submission:
         submission['rev'] = submission['_rev']
    return SubmissionInDB.model_validate(submission) if submission else None # Use model_validate in Pydantic v2

async def create_submission(submission_in: SubmissionCreate, student_id: str) -> SubmissionInDB:
    doc_id = generate_submission_doc_id(submission_in.assignment_id, student_id)
    now = datetime.now(timezone.utc)

    # Check if submission already exists (e.g., due to sync race condition)
    existing_submission = await get_submission_by_doc_id(doc_id)
    if existing_submission:
        # This shouldn't happen if UI prevents creating twice, but handle defensively
        # Maybe update instead? Or raise error? For now, let's raise.
        raise ValueError(f"Submission document {doc_id} already exists.")

    first_version = SubmissionVersion(
        version=1,
        file_url=submission_in.file_url,
        submitted_at=now,
        content_hash=submission_in.content_hash,
        notes=submission_in.notes
    )

    # NOTE: The initial _rev is typically set by CouchDB/PouchDB.
    # When creating directly in MongoDB, we don't usually set it,
    # but for sync compatibility, we might need a strategy.
    # For simplicity here, we'll let the sync logic handle revisions.
    # A placeholder 'rev' might be needed if Pouch expects it immediately.
    submission_db = SubmissionInDB(
        _id=doc_id, # Set _id explicitly
        rev=None, # Let sync process handle initial rev? Or generate "1-hash"?
        assignment_id=submission_in.assignment_id,
        student_id=student_id,
        team_id=submission_in.team_id,
        current_version=1,
        versions=[first_version],
        last_updated_at=now
    )

    # Use model_dump to get dict, respecting aliases
    submission_dict = submission_db.model_dump(by_alias=True)

    await submission_collection.insert_one(submission_dict)
    created_submission = await get_submission_by_doc_id(doc_id)
    if not created_submission:
        raise Exception("Failed to retrieve created submission")
    return created_submission

async def add_new_submission_version(
    doc_id: str,
    version_data: SubmissionUploadNewVersion,
    expected_current_version: int # Optimistic locking
) -> SubmissionInDB | None:
    now = datetime.now(timezone.utc)
    new_version_number = expected_current_version + 1

    new_version = SubmissionVersion(
        version=new_version_number,
        file_url=version_data.file_url,
        submitted_at=now,
        content_hash=version_data.content_hash,
        notes=version_data.notes
    )

    # Use optimistic locking: only update if current_version matches expected
    result: UpdateResult = await submission_collection.update_one(
        {"_id": doc_id, "current_version": expected_current_version},
        {
            "$push": {"versions": new_version.model_dump()},
            "$set": {
                "current_version": new_version_number,
                "last_updated_at": now
                # IMPORTANT: The _rev field should be updated by the sync logic
                # when this change is processed via _bulk_docs, not here directly.
            }
        }
    )

    if result.matched_count == 0:
        # Either doc not found OR current_version didn't match (concurrency issue)
        existing = await get_submission_by_doc_id(doc_id)
        if existing:
            print(f"Optimistic lock failed for {doc_id}. Expected version {expected_current_version}, found {existing.current_version}")
        return None

    # Fetch the updated document
    updated_submission = await get_submission_by_doc_id(doc_id)
    return updated_submission


# --- Functions for Sync Endpoint ---

async def get_docs_by_ids(doc_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """ Fetches multiple documents by their _ids, returning raw dicts. """
    docs_cursor = submission_collection.find({"_id": {"$in": doc_ids}})
    docs_list = await docs_cursor.to_list(length=None)
    return {doc["_id"]: doc for doc in docs_list}

async def save_bulk_docs(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Basic bulk save/update logic for the sync endpoint.
    Implements a simplified Last-Write-Wins based on 'last_updated_at'.
    THIS IS A SIMPLIFIED EXAMPLE. Real CouchDB sync is more complex.
    """
    results = []
    now = datetime.now(timezone.utc)

    # Fetch existing documents matching the incoming IDs
    incoming_ids = [doc.get("_id") for doc in docs if doc.get("_id")]
    existing_docs_dict = await get_docs_by_ids(incoming_ids)

    for doc in docs:
        doc_id = doc.get("_id")
        incoming_rev = doc.get("_rev") # Revision from PouchDB

        if not doc_id or not incoming_rev:
            results.append({"id": doc_id, "error": "bad_request", "reason": "Missing _id or _rev"})
            continue

        # Generate a 'winning' revision ID (e.g., incrementing prefix + hash of content)
        # This needs a proper strategy matching CouchDB's revision handling.
        # Simplified: Use timestamp for LWW, generate a fake new rev string
        new_rev_prefix = int(now.timestamp()) # Example prefix
        new_rev = f"{new_rev_prefix}-{uuid.uuid4().hex[:8]}" # Example new revision

        existing_doc = existing_docs_dict.get(doc_id)

        # --- Conflict Detection and Resolution (Simplified LWW) ---
        should_write = False
        if not existing_doc:
             # Document doesn't exist in MongoDB, definitely write
             should_write = True
        elif doc.get("_deleted", False):
             # Incoming doc is a deletion. Check if it's newer.
             # A proper system checks revision tree; simplified: check timestamp
             existing_ts = existing_doc.get("last_updated_at")
             incoming_ts_str = doc.get("last_updated_at") # PouchDB might send ISO string
             incoming_ts = datetime.fromisoformat(incoming_ts_str) if incoming_ts_str else None

             if not existing_ts or (incoming_ts and incoming_ts > existing_ts):
                 should_write = True # Incoming deletion wins
        else:
             # Incoming doc is an update. Check if it's newer than existing.
             existing_ts = existing_doc.get("last_updated_at")
             incoming_ts_str = doc.get("last_updated_at")
             incoming_ts = datetime.fromisoformat(incoming_ts_str) if incoming_ts_str else now # Default to now if missing

             if not existing_ts or incoming_ts > existing_ts:
                  should_write = True # Incoming update wins
             # ELSE: Existing document in MongoDB is newer or same age, ignore incoming doc

        # --- Perform Write/Delete if Necessary ---
        if should_write:
            try:
                doc_to_write = doc.copy()
                doc_to_write["_rev"] = new_rev # Assign the winning revision
                doc_to_write["last_updated_at"] = now # Ensure consistent timestamp

                if doc.get("_deleted", False):
                    # Delete the document in MongoDB
                    delete_result = await submission_collection.delete_one({"_id": doc_id})
                    if delete_result.deleted_count > 0:
                         results.append({"ok": True, "id": doc_id, "rev": new_rev})
                    else:
                         # Maybe it was already deleted? Still return ok for sync.
                         results.append({"ok": True, "id": doc_id, "rev": new_rev})

                else:
                    # Update or Insert (Upsert)
                    update_result = await submission_collection.replace_one(
                        {"_id": doc_id},
                        doc_to_write,
                        upsert=True
                    )
                    results.append({"ok": True, "id": doc_id, "rev": new_rev})

            except Exception as e:
                print(f"Error processing doc {doc_id} in bulk_docs: {e}")
                results.append({"id": doc_id, "error": "internal_error", "reason": str(e)})
        else:
             # Incoming change was older/conflicting and lost LWW
             # We need to inform PouchDB there was a conflict it needs to resolve locally
             # Returning an error might trigger PouchDB's conflict handling
             # Or just don't include it in success results? Sync protocol specifics matter here.
             # For simplicity, we just don't add it to results, PouchDB might retry/resolve.
             print(f"Doc {doc_id} conflict detected, incoming revision {incoming_rev} ignored (LWW).")
             # PouchDB expects *some* result for each doc sent. Maybe an error status?
             results.append({
                 "id": doc_id,
                 "error": "conflict",
                 "reason": "Document update conflict - server version is newer (LWW)"
                 # "rev": existing_doc.get("_rev") # Optionally return existing rev
                 })


    return results


async def get_doc_revisions(doc_id: str) -> List[str]:
    """ Simplified: Fetch current revision. Real diff needs history. """
    doc = await submission_collection.find_one({"_id": doc_id}, {"_rev": 1})
    return [doc["_rev"]] if doc and "_rev" in doc else []


# Add functions for _changes feed if implementing it
# async def get_changes_since(sequence_id, limit=100, include_docs=False): ...