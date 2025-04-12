from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from app.schemas import submission as submission_schema
from app.schemas import user as user_schema # For dependency
from app.crud import crud_submission, crud_assignment, crud_team
from app.api import deps
from datetime import datetime, timezone # For validation

router = APIRouter()

# NOTE: Actual file upload logic (to S3 etc.) is NOT included here.
# This assumes you handle upload elsewhere and pass the resulting URL.
# If uploading directly to FastAPI, use UploadFile.

@router.post("", response_model=submission_schema.SubmissionPublic, status_code=status.HTTP_201_CREATED)
async def create_or_update_submission(
    assignment_id: str, # Usually from path
    submission_data: submission_schema.SubmissionCreate, # Contains file URL etc.
    current_user: user_schema.UserInDB = Depends(deps.get_current_active_user)
):
    """
    Submit the first version of an assignment OR upload a new version
    if a submission already exists for this user/assignment.
    Requires user to be a member of the assignment's team.
    Assumes assignment_id is part of the path, e.g., /api/assignments/{assignment_id}/submissions
    """
    # 1. Validate Assignment
    assignment = await crud_assignment.get_assignment_by_id(assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    # 2. Validate Team Membership
    team = await crud_team.get_team_by_id(assignment.team_id)
    if not team or current_user.id not in team.member_ids:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not a member of the team for this assignment")

    # 3. Validate Due Date (Optional)
    # if assignment.due_date and datetime.now(timezone.utc) > assignment.due_date:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignment due date has passed")

    # 4. Check if submission already exists
    doc_id = crud_submission.generate_submission_doc_id(assignment_id, current_user.id)
    existing_submission = await crud_submission.get_submission_by_doc_id(doc_id)

    if existing_submission:
        # --- Add new version ---
        new_version_data = submission_schema.SubmissionUploadNewVersion(
             file_url=submission_data.file_url, # Extract relevant fields
             content_hash=submission_data.content_hash,
             notes=submission_data.notes
        )
        updated_submission = await crud_submission.add_new_submission_version(
            doc_id=doc_id,
            version_data=new_version_data,
            expected_current_version=existing_submission.current_version
        )
        if not updated_submission:
             # This likely means a concurrent update happened (optimistic lock failed)
             raise HTTPException(
                 status_code=status.HTTP_409_CONFLICT,
                 detail="Submission updated concurrently. Please refresh and try again."
             )
        submission_to_return = updated_submission
    else:
        # --- Create first submission ---
        # Ensure team_id is correct in submission data (can override or validate)
        create_data = submission_schema.SubmissionCreate(
             assignment_id=assignment_id,
             team_id=assignment.team_id, # Use validated team_id
             file_url=submission_data.file_url,
             content_hash=submission_data.content_hash,
             notes=submission_data.notes
        )
        new_submission = await crud_submission.create_submission(
            submission_in=create_data,
            student_id=current_user.id
        )
        submission_to_return = new_submission

    # Prepare public response
    latest_version = next((v for v in reversed(submission_to_return.versions) if v.version == submission_to_return.current_version), None)
    return submission_schema.SubmissionPublic(
        **submission_to_return.model_dump(by_alias=True),
        latest_version=latest_version
    )


@router.get("/{student_id}", response_model=submission_schema.SubmissionPublic)
async def get_student_submission_for_assignment(
    assignment_id: str,
    student_id: str, # ID of the student whose submission to view
    current_user: user_schema.UserInDB = Depends(deps.get_current_active_user)
):
    """
    Get a specific student's latest submission for an assignment.
    Requires current user to be the student themselves OR the team admin.
    """
    # 1. Validate Assignment & Team
    assignment = await crud_assignment.get_assignment_by_id(assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    team = await crud_team.get_team_by_id(assignment.team_id)
    if not team:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found for assignment") # Should not happen

    # 2. Authorize: Allow student or team admin
    is_student = current_user.id == student_id
    is_admin = current_user.id == team.admin_id

    if not is_student and not is_admin:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this submission")

    # 3. Fetch submission
    doc_id = crud_submission.generate_submission_doc_id(assignment_id, student_id)
    submission = await crud_submission.get_submission_by_doc_id(doc_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found for this student")

    # Prepare public response
    latest_version = next((v for v in reversed(submission.versions) if v.version == submission.current_version), None)
    return submission_schema.SubmissionPublic(
        **submission.model_dump(by_alias=True),
        latest_version=latest_version
    )


@router.get("/{student_id}/versions", response_model=List[submission_schema.SubmissionVersion])
async def get_submission_versions(
     assignment_id: str,
     student_id: str,
     current_user: user_schema.UserInDB = Depends(deps.get_current_active_user)
 ):
     """
     Get all historical versions of a student's submission.
     Requires current user to be the student themselves OR the team admin.
     """
     # (Similar authorization logic as get_student_submission_for_assignment)
     assignment = await crud_assignment.get_assignment_by_id(assignment_id)
     if not assignment: raise HTTPException(status_code=404, detail="Assignment not found")
     team = await crud_team.get_team_by_id(assignment.team_id)
     if not team: raise HTTPException(status_code=404, detail="Team not found")
     if not (current_user.id == student_id or current_user.id == team.admin_id):
         raise HTTPException(status_code=403, detail="Not authorized")

     doc_id = crud_submission.generate_submission_doc_id(assignment_id, student_id)
     submission = await crud_submission.get_submission_by_doc_id(doc_id)
     if not submission:
         raise HTTPException(status_code=404, detail="Submission not found")

     return submission.versions


# Add endpoint for admins/teachers to list all submissions for an assignment