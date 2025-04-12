from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.schemas import team as team_schema
from app.schemas import user as user_schema # For response model
from app.crud import crud_team, crud_user
from app.api import deps

router = APIRouter()

@router.post("", response_model=team_schema.TeamPublic, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_in: team_schema.TeamBase, # Use TeamBase, admin_id set internally
    current_user: user_schema.UserInDB = Depends(deps.get_current_active_user)
):
    """
    Create a new team. The creator becomes the admin.
    """
    team_create_data = team_schema.TeamCreate(**team_in.model_dump(), admin_id=current_user.id)
    team = await crud_team.create_team(team_in=team_create_data)
    # Calculate member count for public response
    member_count = len(team.member_ids)
    return team_schema.TeamPublic(**team.model_dump(), member_count=member_count)


@router.get("", response_model=List[team_schema.TeamPublic])
async def get_user_teams(
    current_user: user_schema.UserInDB = Depends(deps.get_current_active_user)
):
    """
    Get all teams the current user is a member or admin of.
    """
    teams_db = await crud_team.get_teams_for_user(user_id=current_user.id)
    teams_public = []
    for team in teams_db:
        member_count = len(team.member_ids)
        teams_public.append(team_schema.TeamPublic(**team.model_dump(), member_count=member_count))
    return teams_public


@router.post("/join", response_model=team_schema.TeamPublic)
async def join_team(
    join_data: team_schema.TeamJoin,
    current_user: user_schema.UserInDB = Depends(deps.get_current_active_user)
):
    """
    Join a team using its unique join code.
    """
    team = await crud_team.get_team_by_join_code(code=join_data.join_code)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team with this join code not found",
        )

    if current_user.id in team.member_ids:
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
             detail="User is already a member of this team",
         )

    success = await crud_team.add_member_to_team(team_id=team.id, user_id=current_user.id)
    if not success:
        # Should not happen if checks above pass, but handle potential DB error
         raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail="Failed to add user to the team",
         )

    # Return the joined team's public info
    # Refetch team to get updated member count, or calculate
    updated_team = await crud_team.get_team_by_id(team.id)
    if not updated_team: # Should exist
        raise HTTPException(status_code=500, detail="Failed to retrieve team after joining")

    member_count = len(updated_team.member_ids)
    return team_schema.TeamPublic(**updated_team.model_dump(), member_count=member_count)


@router.get("/{team_id}", response_model=team_schema.TeamWithMembers)
async def get_team_details(
    team_id: str,
    current_user: user_schema.UserInDB = Depends(deps.get_team_member) # Ensures user is member
):
    """
    Get details of a specific team, including its members (public info).
    Requires user to be a member of the team.
    """
    team = await crud_team.get_team_by_id(team_id)
    if not team: # Should be caught by dependency, but double check
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Fetch member details (public info only)
    member_details = []
    if team.member_ids:
        member_cursor = crud_user.user_collection.find(
            {"_id": {"$in": team.member_ids}},
            # Projection to fetch only fields needed for UserPublic
            {"_id": 1, "email": 1, "full_name": 1, "is_active": 1, "created_at": 1, "updated_at": 1}
        )
        members_db = await member_cursor.to_list(length=None)
        member_details = [user_schema.UserPublic.model_validate(m) for m in members_db]

    member_count = len(team.member_ids)
    return team_schema.TeamWithMembers(
        **team.model_dump(),
        member_count=member_count,
        members=member_details
    )

# Add endpoints for updating team (admin only), removing members (admin only), generating new join code etc.