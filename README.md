# TrackFlow — Backend API

An AI-powered personal finance tracker backend built with FastAPI. Tracks income, expenses, budgets, and goals, and includes a Gemini-powered AI assistant that reasons over a user's live financial data to answer questions and surface insights.

**Live API:** https://trackflow-backend-483d.onrender.com
**Frontend repo:** [link to your frontend repo]
**Live app:** https://gettrackflow-ai.vercel.app

## Features

- JWT-based authentication (access + refresh tokens, token blacklisting on logout)
- Full CRUD for income, expenditure, budgets, and goals
- AI financial assistant powered by Google Gemini — analyzes live user data to answer natural-language questions
- Dashboard/overview endpoint with automated spending insights
- Async SQLAlchemy 2.0 + PostgreSQL in production (SQLite for local dev)
- Alembic-managed database migrations
- Auto-generated interactive API docs (Swagger UI + ReDoc)

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL (production), SQLite (local dev)
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Auth:** JWT (PyJWT + bcrypt)
- **AI:** Google Gemini API
- **Deployment:** Render

## Getting Started

### Prerequisites

- Python 3.11+
- A PostgreSQL database (or use the SQLite default for local dev)

### Setup

```bash
# Clone the repo
git clone https://github.com/Konlan21/<backend-repo-name>.git
cd <backend-repo-name>

# Create a virtual environment
python -m venv env
source env/bin/activate   # Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment variables

Create a `.env` file in the project root:

SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite+aiosqlite:///./db.sqlite3
GEMINI_API_KEY=your-gemini-api-key
CORS_ALLOW_ALL_ORIGINS=true

### Run migrations

```bash
alembic upgrade head
```

### Start the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Interactive docs are auto-generated at `http://127.0.0.1:8000/docs`.

## API Documentation

Once running, visit `/docs` for a full interactive Swagger UI covering every endpoint (auth, income, expenditure, budgets, goals, and the AI assistant).