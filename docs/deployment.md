
# RECALL AI — Deployment Guide

## 1. Deployment Overview

RECALL AI consists of two independently deployable applications:

- **Frontend:** React application built with Vite.
- **Backend:** FastAPI application providing the support workflow and integrations.

The backend communicates with Groq, Hindsight, and Supabase.

Deployment requires configuring these services independently and securely.

## 2. Environment Configuration

Configure the following backend environment variables in the deployment environment:

| Variable | Purpose |
|---|---|
| `APP_ENV` | Set to `production` |
| `SECRET_KEY` | Strong application signing secret |
| `FRONTEND_URL` | Public frontend origin |
| `GROQ_API_KEY` | Groq API credential |
| `GROQ_MODEL` | Configured language model |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend-only database credential |
| `HINDSIGHT_API_KEY` | Hindsight API credential |
| `HINDSIGHT_BASE_URL` | Hindsight API endpoint |
| `HINDSIGHT_BANK_ID_SECRET` | Hindsight bank identity secret |
| `IDENTITY_TOKEN_SECRET` | Identity token signing secret |

Use unique, strong secrets of at least 32 bytes for the production signing secrets.

Never expose backend credentials through frontend environment variables or public repositories.

## 3. Frontend Build

Build the frontend using:

```bash
cd frontend
npm install
npm run lint
npm run build
```

The production build is generated in the `frontend/dist` directory.

Deploy the generated static assets using a suitable static hosting provider.

Configure `VITE_API_BASE_URL` at build time when the backend is hosted at a non-default URL.

## 4. Backend Deployment

Install the Python dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Start the application using an ASGI server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Configure the hosting platform to provide the production environment variables.

Use HTTPS and an appropriate reverse proxy or managed application hosting service.

## 5. Database and External Services

Before enabling customer traffic:

1. Initialize the Supabase schema.
2. Configure database access and row-level security.
3. Verify Groq connectivity.
4. Verify Hindsight connectivity.
5. Confirm that the memory service initializes correctly.
6. Verify that the complete support workflow is available.

## 6. Security Requirements

- Set `APP_ENV=production`.
- Keep `ALLOW_SYNTHETIC_DEMO_SEED=false`.
- Do not deploy local synthetic customer credentials.
- Do not expose the development demo endpoint.
- Store secrets in the hosting provider's secret manager.
- Restrict database credentials to backend services.
- Configure HTTPS and appropriate access controls.
- Validate authentication and workspace authorization before accepting customer traffic.

## 7. Health Checks and Monitoring

Use the health endpoint:

`GET /health`

Monitor:

- Backend availability.
- Database connectivity.
- Hindsight memory operations.
- Groq API errors and latency.
- Request failures.
- Application logs.

## 8. Production Readiness

RECALL AI is currently a working prototype.

Before a production launch, additional work is required around:

- Complete authentication and authorization.
- Workspace isolation and security validation.
- Rate limiting and abuse protection.
- Production monitoring and alerting.
- Secret rotation and incident response.
- Deployment automation and rollback procedures.
- Load and reliability testing.

A successful local demonstration does not by itself establish production readiness.
