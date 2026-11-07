
# RECALL AI — Development Setup

This guide explains how to configure and run RECALL AI locally.

## 1. Prerequisites

Install the following:

- Python 3.11
- Node.js and npm
- Git
- A Supabase project
- A Groq API key
- Hindsight API credentials

## 2. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd recall-ai
```

## 3. Backend Configuration

Navigate to the backend directory:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create the local environment file:

```bash
cp .env.example .env
```

Configure the credentials in `backend/.env`:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Application signing secret |
| `FRONTEND_URL` | Frontend origin |
| `GROQ_API_KEY` | Groq API key |
| `GROQ_MODEL` | Language model |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase backend credential |
| `HINDSIGHT_API_KEY` | Hindsight API key |
| `HINDSIGHT_BASE_URL` | Hindsight API endpoint |
| `HINDSIGHT_BANK_ID_SECRET` | Hindsight bank identity secret |
| `IDENTITY_TOKEN_SECRET` | Identity token signing secret |

Use strong, unique secrets. Never commit the `.env` file.

## 4. Database Initialization

1. Open your Supabase project.
2. Navigate to the SQL Editor.
3. Open `backend/database/schema.sql`.
4. Execute the SQL statements.
5. Verify that the required tables and policies were created.

## 5. Start the Backend

From the `backend` directory:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify the health endpoint:

`http://localhost:8000/health`

Interactive API documentation:

`http://localhost:8000/docs`

The complete support workflow requires valid Groq, Supabase, and Hindsight configuration.

## 6. Start the Frontend

Open a separate terminal:

```bash
cd ~/projects/recall-ai/frontend
npm install
npm run dev
```

Open the Vite development URL, normally:

`http://localhost:5173`

If the frontend uses a different port, update `FRONTEND_URL` in the backend environment accordingly.

For a non-default backend URL, configure `VITE_API_BASE_URL` using the frontend's Vite environment configuration.

## 7. Run Backend Tests

From the backend directory with the virtual environment activated:

```bash
pytest -q
```

## 8. Frontend Validation

From the frontend directory:

```bash
npm run lint
npm run build
```

## 9. Synthetic Customer Demonstration

The synthetic Sarah Mitchell demonstration is intended for local development.

It requires the explicitly enabled development configuration and private local demo credentials.

Do not enable synthetic demo seeding in production or publish the private demo configuration.

For available seeding options, inspect:

```bash
cd backend
python scripts/seed_sarah_demo.py --help
```

## 10. Troubleshooting

### Backend fails to initialize

- Check that the virtual environment is activated.
- Verify the required environment variables.
- Confirm that external service credentials are valid.

### Frontend cannot reach the backend

- Confirm that FastAPI is running.
- Check the configured API base URL.
- Verify that `FRONTEND_URL` matches the frontend origin.

### Memory operations fail

- Verify the Hindsight API key and base URL.
- Check the Hindsight bank identity configuration.
- Inspect backend logs for memory-service errors.
