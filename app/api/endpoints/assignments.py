from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.schemas import assignment as assignment_schema
from app.schemas import user as user_schema # For dependency
from app.crud import crud_assignment, crud_team # Need crud_team to check team exists
from app.api import deps

router = APIRouter()

@router.post("", response_model=assignment_schema.AssignmentPublic, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    team_id: str, # Get team_id from path parameter usually
    assignment_in: assignment_schema.AssignmentBase, # Base schema, team_id/creator_id set internally
    # Ensure creator is the admin of this team
    current_user: user_schema.UserInDB = Depends(deps.get_team_admin)
):
    """
    Create a new assignment within a team. Only the team admin can create assignments.
    Assumes team_id is part of the path, e.g., /api/teams/{team_id}/assignments
    """
    assignment_create_data = assignment_schema.AssignmentCreate(
        **assignment_in.model_dump(),
        team_id=team_id,
        creator_id=current_user.id
    )
    assignment = await crud_assignment.create_assignment(assignment_in=assignment_create_data)
    return assignment_schema.AssignmentPublic.model_validate(assignment)


@router.get("", response_model=List[assignment_schema.AssignmentPublic])
async def get_team_assignments(
    team_id: str,
    # Ensure user is at least a member of the team to view assignments
    current_user: user_schema.UserInDB = Depends(deps.get_team_member)
):
    """
    Get all assignments for a specific team. Requires user to be a member.
    Assumes team_id is part of the path, e.g., /api/teams/{team_id}/assignments
    """
    # Optional: Check team exists explicitly, though dependency does implicitly
    # team = await crud_team.get_team_by_id(team_id)
    # if not team:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    assignments_db = await crud_assignment.get_assignments_for_team(team_id=team_id)
    return [assignment_schema.AssignmentPublic.model_validate(a) for a in assignments_db]


@router.get("/{assignment_id}", response_model=assignment_schema.AssignmentPublic)
async def get_assignment_details(
    team_id: str, # Require team context for authorization
    assignment_id: str,
    current_user: user_schema.UserInDB = Depends(deps.get_team_member) # Must be member
):
    """
    Get details of a specific assignment. Requires user to be a team member.
    """
    assignment = await crud_assignment.get_assignment_by_id(assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    # Ensure the assignment belongs to the team the user is authorized for
    if assignment.team_id != team_id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Assignment does not belong to this team context")

    return assignment_schema.AssignmentPublic.model_validate(assignment)


# Add endpoints for updating/deleting assignments (admin only)