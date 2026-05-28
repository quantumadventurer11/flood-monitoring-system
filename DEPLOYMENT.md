# Production Deployment

This project deploys as three services:

- Frontend: Vercel, root directory `frontend`
- Backend: Render Web Service, root directory `backend`
- Database: Render Postgres 15, provisioned from `render.yaml`

## Service Choice

Vercel is the best fit for the React/Vite frontend because it provides static builds, GitHub preview deployments, and simple build-time environment variables. Render is the best fit for the FastAPI backend and Postgres database because it supports long-running Python web services, health checks, Blueprint infrastructure, environment variable injection, and a managed Postgres add-on on the same platform.

## Backend Environment Variables

Set these in the Render backend service dashboard.

| Variable | Required | Value |
| --- | --- | --- |
| `DATABASE_URL` | Yes | Render Postgres internal connection string. The Blueprint injects this automatically from `flood-monitoring-system-db`. |
| `COPERNICUS_USER` | Optional | Your Copernicus Data Space username from `https://dataspace.copernicus.eu`. |
| `COPERNICUS_PASSWORD` | Optional | Your Copernicus Data Space password. |
| `ALLOWED_ORIGINS` | Yes | Your Vercel frontend URL, for example `https://your-project.vercel.app`. You may include comma-separated local/dev origins if needed. |

Without Copernicus credentials, the backend still runs with the Open-Meteo fallback path.

## Frontend Environment Variables

Set this in the Vercel project dashboard for Production, Preview, and Development.

| Variable | Required | Value |
| --- | --- | --- |
| `VITE_API_URL` | Yes | Your Render backend URL, for example `https://flood-monitoring-system-backend.onrender.com`. |

## Render Setup

1. Create or log into a Render account.
2. Select **New +** then **Blueprint**.
3. Connect `quantumadventurer11/flood-monitoring-system`.
4. Render will read the root `render.yaml` and create:
   - `flood-monitoring-system-backend`
   - `flood-monitoring-system-db`
5. Add `COPERNICUS_USER`, `COPERNICUS_PASSWORD`, and `ALLOWED_ORIGINS` in the backend service environment settings.
6. Deploy the backend.
7. Confirm `https://your-backend-url.onrender.com/health` returns `{"status":"ok","version":"1.0.0"}`.

The backend start command runs `alembic upgrade head` and `python seed_db.py` before starting Uvicorn. Both are safe to run on every deploy.

## Vercel Setup

1. Create or log into a Vercel account.
2. Import `quantumadventurer11/flood-monitoring-system`.
3. Set the Vercel project **Root Directory** to `frontend`.
4. Set `VITE_API_URL` to your Render backend URL.
5. Deploy the frontend.

Vercel auto-deploys on pushes to `main`. Render also auto-deploys on pushes to `main` after the Blueprint/service is connected.

## Post-Deploy Smoke Test

1. Open the Render backend `/health` URL.
2. Open the Vercel frontend URL.
3. Click a country on the dashboard map and confirm a prediction appears.
4. Open Predictor and submit Bangladesh for today's date.
5. Open Forecast and confirm five days render with precipitation, soil moisture, and river discharge.
6. Open Methodology and confirm the five figures and three tables render.
