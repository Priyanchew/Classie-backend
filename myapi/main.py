from fastapi import FastAPI
from routes import users, teams, assignments, submissions

app = FastAPI()

app.include_router(users.router)
app.include_router(teams.router)
app.include_router(assignments.router)
app.include_router(submissions.router)
