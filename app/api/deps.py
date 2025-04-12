from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import ValidationError

from app.core import security
from app.schemas.user import UserInDB
from app.core.security import TokenData
from app.crud import crud_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login") # Point to your login endpoint

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    token_data = security.decode_access_token(token)
    if not token_data or not token_data.user_id:
        raise security.credentials_exception

    user = await crud_user.get_user_by_id(user_id=token_data.user_id)
    if user is None:
        raise security.credentials_exception
    return user

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Dependency to check if user is an admin of a specific team
async def get_team_admin(
    team_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
) -> UserInDB:
    from app.crud.crud_team import get_team_by_id # Avoid circular import
    team = await get_team_by_id(team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    if team.admin_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the team admin")
    return current_user

# Dependency to check if user is a member of a specific team
async def get_team_member(
    team_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
) -> UserInDB:
     from app.crud.crud_team import get_team_by_id # Avoid circular import
     team = await get_team_by_id(team_id)
     if not team:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
     # Check if user is admin OR in the member_ids list
     if team.admin_id != current_user.id and current_user.id not in team.member_ids:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this team")
     return current_user