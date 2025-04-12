from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from app.schemas import user as user_schema
from app.schemas import token as token_schema
from app.crud import crud_user
from app.core import security
from app.core.config import settings
from app.api import deps

router = APIRouter()

@router.post("/register", response_model=user_schema.UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: user_schema.UserCreate):
    """
    Register a new user with email and password.
    """
    existing_user = await crud_user.get_user_by_email(email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = await crud_user.create_user_email_pwd(user_in=user_in)
    # Return public user data, not the full DB model
    return user_schema.UserPublic.model_validate(user)


@router.post("/login", response_model=token_schema.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Authenticate user with email/password and return JWT token.
    Uses OAuth2PasswordRequestForm for standard form data input.
    """
    user = await crud_user.get_user_by_email(email=form_data.username) # Form uses 'username' for email
    if not user or not user.hashed_password or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "id": str(user.id)}, # Use user.id (aliased from _id)
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- Google OAuth Placeholders ---

@router.get("/google")
async def auth_google():
    """
    Redirects the user to Google's OAuth 2.0 server.
    (Placeholder - requires implementation)
    """
    # 1. Construct the Google OAuth URL with client_id, redirect_uri, scope, etc.
    # google_oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?..."
    # return RedirectResponse(google_oauth_url)
    raise HTTPException(status_code=501, detail="Google OAuth redirect not implemented")

@router.get("/google/callback", response_model=token_schema.Token)
async def auth_google_callback(code: str | None = None, error: str | None = None):
    """
    Handles the callback from Google after user authentication.
    Exchanges the code for tokens, gets user info, creates/updates user, returns JWT.
    (Placeholder - requires implementation)
    """
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code from Google")

    # 1. Exchange 'code' for access token with Google using httpx POST request
    # 2. Get user info (email, name, google_id) from Google API using the access token
    # 3. Check if user exists by google_id or email using crud_user
    # 4. If user exists, log them in. If email exists but no google_id, link accounts?
    # 5. If user doesn't exist, create a new user using crud_user.create_user_google
    # 6. Create JWT token for the user (similar to email/password login)
    # 7. Return the JWT token

    # Placeholder response:
    # fake_user_email = "user@example.com"
    # fake_user_id = "some_fake_user_id"
    # access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # access_token = security.create_access_token(
    #     data={"sub": fake_user_email, "id": fake_user_id},
    #     expires_delta=access_token_expires,
    # )
    # return {"access_token": access_token, "token_type": "bearer"}

    raise HTTPException(status_code=501, detail="Google OAuth callback not implemented")