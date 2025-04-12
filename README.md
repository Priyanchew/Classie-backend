# Classie Backend

A FastAPI-based backend for the Classie application, featuring team management, assignments, and submissions with offline sync support.

## Features

- User authentication (email/password and Google OAuth)
- Team management with join codes
- Assignment creation and management
- File submissions with versioning
- Offline sync support using PouchDB/CouchDB protocol
- MongoDB database integration

## Prerequisites

- Python 3.8+
- MongoDB (local or Atlas)
- Google OAuth credentials (optional, for Google login)

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Classie-backend
```

2. Create and activate a virtual environment:
```bash
# uv initialisation
uv init
# venv creation
uv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following variables:
```env
# MongoDB Connection
DATABASE_URL=mongodb+srv://your_mongodb_url
DATABASE_NAME=assignment_portal

# JWT Settings
JWT_SECRET_KEY=your_super_secret_key_change_this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# OAuth Settings (Optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

## Running the Application

Start the server using Uvicorn:

```bash
uvicorn app.main:app --reload
```

The application will be available at `http://localhost:8000`

### Development Features

- `--reload` enables auto-reload on code changes
- API documentation available at:
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`

## API Endpoints

- `/api/auth` - Authentication endpoints
- `/api/users` - User management
- `/api/teams` - Team management
- `/api/teams/{team_id}/assignments` - Assignment management
- `/api/assignments/{assignment_id}/submissions` - Submission handling
- `/api/sync` - Offline sync endpoints

## Development

- The application uses FastAPI for the backend
- MongoDB for data storage
- Pydantic for data validation
- Motor for async MongoDB operations
- JWT for authentication

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here]
