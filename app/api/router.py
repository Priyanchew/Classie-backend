from fastapi import APIRouter

from app.api.endpoints import auth, users, teams, assignments, submissions, sync

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])
# Nest assignments under teams
api_router.include_router(assignments.router, prefix="/teams/{team_id}/assignments", tags=["Assignments"])
# Nest submissions under assignments
api_router.include_router(submissions.router, prefix="/assignments/{assignment_id}/submissions", tags=["Submissions"])
# Sync endpoint (adjust prefix as needed)
api_router.include_router(sync.router, prefix="/sync", tags=["Synchronization"])

# Simple health check endpoint
@api_router.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}