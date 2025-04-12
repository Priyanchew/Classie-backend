from fastapi import APIRouter, Depends, HTTPException

from app.schemas import user as user_schema
from app.api import deps
from app.crud import crud_user

router = APIRouter()

@router.get("/me", response_model=user_schema.UserPublic)
async def read_users_me(current_user: user_schema.UserInDB = Depends(deps.get_current_active_user)):
    """
    Get current logged-in user's public information.
    """
    # Convert UserInDB to UserPublic before returning
    return user_schema.UserPublic.model_validate(current_user)

# Add endpoint to update user details if needed, e.g., PUT /me