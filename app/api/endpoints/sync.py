from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, Query
from typing import List, Dict, Any, Optional

from app.schemas import user as user_schema # For dependency
from app.schemas import sync as sync_schema
from app.schemas import submission as submission_schema # Import submission schema
from app.crud import crud_submission # Add other CRUD modules if syncing other doc types
from app.api import deps

router = APIRouter()

# NOTE: This implements a VERY basic version of CouchDB replication protocol endpoints
# focusing on _bulk_docs with LWW. Real implementation is far more complex.
# Assumes PouchDB points to /api/sync/{db_name}/... where db_name might be user-specific

@router.post("/{db_name}/_bulk_docs", response_model=List[sync_schema.BulkDocsResponseItem])
async def handle_bulk_docs(
    db_name: str, # Use db_name for potential multi-tenancy/filtering if needed
    payload: sync_schema.BulkDocsRequest,
    # current_user: user_schema.UserInDB = Depends(deps.get_current_active_user) # Auth needed!
):
    """
    Handles bulk document writes from PouchDB.
    Implements simplified LWW based on 'last_updated_at'.
    Needs Authentication. Needs to handle different doc types.
    """
    # TODO: Add authentication check (current_user dependency)
    # TODO: Check if current_user is allowed to write to this 'db_name'

    # Currently only handles 'submission' docs, needs extension for others (teams, assignments?)
    # Need robust parsing and validation based on 'doc_type' if present
    submission_docs = []
    other_docs = []
    parsed_docs = []

    for doc_dict in payload.docs:
        # Attempt to parse as known types, fallback to basic PouchDocument
        try:
            # Use discriminated unions in Pydantic v2 for better type handling based on 'doc_type'
             if doc_dict.get("doc_type") == "submission":
                 parsed_docs.append(submission_schema.SubmissionInDB.model_validate(doc_dict))
                 submission_docs.append(doc_dict) # Keep raw dict for CRUD for now
             else:
                 # Handle other types or treat as generic
                 parsed_docs.append(sync_schema.PouchDocument.model_validate(doc_dict))
                 other_docs.append(doc_dict) # Keep raw dict
        except Exception as e:
            # Handle validation errors for individual docs
             print(f"Failed to validate doc {doc_dict.get('_id')}: {e}")
             # Decide how to report this error in the response
             # For now, crud function will handle errors internally

    # Process submission documents (add logic for other types)
    submission_results = []
    if submission_docs:
        submission_results = await crud_submission.save_bulk_docs(submission_docs)

    # Combine results (add results for other_docs if processed)
    # Ensure the response format matches BulkDocsResponseItem schema
    all_results = submission_results # + other_results

    # Convert results to the response model structure if needed
    # final_response = [sync_schema.BulkDocsResponseItem(**res) for res in all_results]

    return all_results # Return the list of dicts directly if crud returns matching structure


@router.post("/{db_name}/_revs_diff", response_model=sync_schema.RevsDiffResponse)
async def handle_revs_diff(
    db_name: str,
    payload: Dict[str, List[str]], # Raw dict matches RevsDiffRequest.__root__
    # current_user: user_schema.UserInDB = Depends(deps.get_current_active_user) # Auth needed!
):
    """
    Checks which revisions the server is missing for given documents.
    Simplified: Assumes only latest revision exists on server for LWW.
    Real CouchDB checks revision history.
    """
    # TODO: Add authentication and authorization for db_name

    response_data: Dict[str, sync_schema.RevsDiffResponseItemMissing] = {}

    for doc_id, incoming_revs in payload.items():
        # Fetch current revision(s) from DB for this doc_id
        # Currently only supports submissions, extend as needed
        server_revs = await crud_submission.get_doc_revisions(doc_id) # Simplified

        missing_revs = [rev for rev in incoming_revs if rev not in server_revs]

        if missing_revs:
             response_data[doc_id] = sync_schema.RevsDiffResponseItemMissing(missing=missing_revs)

    return response_data


# --- Stubs for other potential sync endpoints ---

@router.get("/{db_name}/_changes")
async def handle_changes_feed(
    db_name: str,
    feed: str = Query("normal"),
    since: Any = Query("0"), # Sequence ID, can be int or string
    limit: int = Query(100),
    include_docs: bool = Query(False),
    style: str = Query("main_only"), # CouchDB option
    # current_user: user_schema.UserInDB = Depends(deps.get_current_active_user) # Auth needed!
):
    """
    (Stub) Provides a feed of changes to the database since a sequence ID.
    Requires implementing a sequence tracking mechanism in MongoDB. Complex.
    """
    # TODO: Implement changes feed logic using MongoDB change streams or a dedicated sequence collection.
    raise HTTPException(status_code=501, detail="_changes feed not implemented")


@router.get("/{db_name}/{doc_id}")
async def get_document(
    db_name: str,
    doc_id: str,
    rev: Optional[str] = Query(None), # Optional specific revision
    # current_user: user_schema.UserInDB = Depends(deps.get_current_active_user) # Auth needed!
):
    """
    (Stub) Fetch a specific document, potentially a specific revision.
    PouchDB uses this during replication.
    """
     # TODO: Implement document fetching, potentially specific revisions if stored
    submission = await crud_submission.get_submission_by_doc_id(doc_id)
    if submission:
        # Need to return as raw dict with _id, _rev etc.
        return submission.model_dump(by_alias=True)
    raise HTTPException(status_code=404, detail="Document not found")


# Add other endpoints PouchDB might call: PUT /{db_name}/{doc_id}, DELETE /{db_name}/{doc_id}, etc.
# if PouchDB is configured to use them directly (less common with replication protocol).