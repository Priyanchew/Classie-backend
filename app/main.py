from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
# from app.db.database import create_indexes # Optional: If creating indexes on startup

# Initialize FastAPI app
app = FastAPI(
    title="Assignment Portal API",
    description="API for managing teams, assignments, and submissions with offline sync support.",
    version="0.1.0",
    # Add other FastAPI configurations if needed
    # docs_url="/api/docs", openapi_url="/api/openapi.json"
)

# CORS Middleware Setup
# Adjust origins based on your frontend URL(s)
# Use settings.FRONTEND_URL if defined, or allow specific origins/wildcards carefully
origins = [
    "http://localhost:3000", # Common React dev port
    "http://localhost:5173", # Common Vite dev port
    # settings.FRONTEND_URL, # Add your deployed frontend URL from settings
    # Add Vercel preview deployment pattern if needed: "https://*-your-username.vercel.app"
]
# Filter out None values if FRONTEND_URL is optional
origins = [origin for origin in origins if origin]

if not origins: # Fallback if no origins configured (adjust as needed for security)
    print("WARN: No CORS origins specified, allowing all origins (adjust for production).")
    origins = ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all standard methods
    allow_headers=["*"], # Allow all headers, including Authorization
)

# Include the main API router
app.include_router(api_router, prefix="/api") # Prefix all API routes with /api

# --- Optional Startup/Shutdown Events ---
# @app.on_event("startup")
# async def startup_event():
#     # Connect to DB (Motor does this lazily, but can ensure connection here)
#     # await create_indexes() # Create MongoDB indexes if defined
#     print("Application startup complete.")

# @app.on_event("shutdown")
# async def shutdown_event():
#     # Clean up resources if needed
#     # client.close() # Close MongoDB connection (Motor might handle this)
#     print("Application shutdown.")


# Root endpoint (optional)
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Assignment Portal API!"}

# Add Prometheus monitoring endpoints or other root-level endpoints if needed