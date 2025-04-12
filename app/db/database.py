import motor.motor_asyncio
from app.core.config import settings

client = motor.motor_asyncio.AsyncIOMotorClient(
    settings.DATABASE_URL,
    uuidRepresentation='standard' # Important for consistency
)
db = client[settings.DATABASE_NAME]

# Get database collections (used in CRUD operations)
def get_user_collection():
    return db.get_collection("users")

def get_team_collection():
    return db.get_collection("teams")

def get_assignment_collection():
    return db.get_collection("assignments")

def get_submission_collection():
    return db.get_collection("submissions")

# You might add specific indexes here on startup if needed
# async def create_indexes():
#     await get_user_collection().create_index("email", unique=True)
#     await get_team_collection().create_index("join_code", unique=True, sparse=True)
#     # Add other necessary indexes