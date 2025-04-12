# 🧋 Lassi.Ai — Backend

> 🍃 *Offline-First Assignment Submission Platform for Hackathons & Classrooms.*

Welcome to the backend repository for **Lassi.Ai**, a powerful and minimal offline-first assignment portal built for schools, colleges, and hackathons. Designed for resilience in low-connectivity environments, this backend handles everything from user authentication and assignment versioning to data syncing when connections are restored.

---

## ✨ Features

- 🔌 **Offline-First**: Works even without internet using PouchDB/LocalForage on the frontend, and syncs with MongoDB backend when online.
- 🧠 **Smart Syncing**: Efficient and conflict-aware syncing mechanism that ensures assignments are always up to date.
- 📁 **Version Controlled Submissions**: Tracks every version of a student's assignment.
- 👥 **User Roles**: Students, Teachers/Admins with access control.
- 📤 **Submission API**: Clean RESTful endpoints to push/pull assignments.
- 🛡️ **Secure**: Authentication and secure API access.

---

## 🏗️ Tech Stack

- **Backend**: Node.js + Express.js
- **Database**: MongoDB (with future plans to support CouchDB-style syncing)
- **Authentication**: JWT / Session-based (configurable)
- **Offline Syncing**: Supports PouchDB replication-compatible APIs (coming soon)

---

## 📁 Folder Structure

```
backend/
├── controllers/     # Logic for handling routes
├── models/          # Mongoose schemas
├── routes/          # API routes
├── middleware/      # Auth, error handling etc.
├── utils/           # Helper functions
├── .env             # Environment variables
├── server.js        # Entry point
└── README.md        # This file
```

---

## ⚙️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/lassi-backend.git
cd lassi-backend
```

### 2. Install dependencies

```bash
npm install
```

### 3. Configure environment variables

Create a `.env` file:

```env
PORT=5000
MONGODB_URI=your_mongo_connection_string
JWT_SECRET=your_jwt_secret
```

### 4. Start the server

```bash
npm run dev
```

Server will be running at `http://localhost:5000`.

---

## 📡 API Overview

| Method | Route                      | Description                    |
|--------|----------------------------|--------------------------------|
| `POST` | `/api/auth/register`       | Register a new user            |
| `POST` | `/api/auth/login`          | Login                          |
| `GET`  | `/api/assignments/`        | Get assignments                |
| `POST` | `/api/assignments/submit`  | Submit or update an assignment |
| `GET`  | `/api/sync/`               | Trigger a manual sync          |

---

## 🧠 Future Scope

- Real-time sync with CouchDB support
- Conflict resolution and merge logic
- Web UI for teachers to review submissions
- Analytics dashboard for submission tracking

---

## 💡 Inspiration

We built Lassi.Ai to ensure **connectivity is never a barrier** to learning and collaboration. Whether you're in a remote village or a bustling hackathon hall, assignments should *just work™️*.

---

## 🧑‍💻 Team Lassi.Ai

- Randi and team 🍃

> *“Built with ❤️, under pressure, and with way too much caffeine.”*