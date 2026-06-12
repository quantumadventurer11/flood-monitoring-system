# Secure Production Deployment

This project should not be exposed with localtunnel for public review. The secure deployment path is:

- Frontend: Vercel, root directory `frontend`
- Backend: Render Web Service, root directory `backend`
- Database: Render Postgres 15, provisioned from `render.yaml`

Vercel is the right fit for the React/Vite frontend. The FastAPI backend should stay on Render or an equivalent managed web-service host because it uses ML/geospatial dependencies, a persistent database, startup seeding, and long-running API behavior.

## Required Accounts

- GitHub access to `quantumadventurer11/flood-monitoring-system`
- Vercel account for the frontend
- Render account for the backend and database

## Backend On Render

1. Open Render.
2. Select **New +** then **Blueprint**.
3. Connect `quantumadventurer11/flood-monitoring-system`.
4. Use the repository root so Render can read `render.yaml`.
5. Confirm Render creates:
   - `flood-monitoring-system-backend`
   - `flood-monitoring-system-db`
6. Set backend environment variables:

| Variable | Required | Value |
| --- | --- | --- |
| `DATABASE_URL` | Yes | Render injects this from `flood-monitoring-system-db`. |
| `ALLOWED_ORIGINS` | Yes | Production Vercel URL, for example `https://your-project.vercel.app`. |
| `CORS_ORIGIN_REGEX` | Optional | Defaults to `https://.*\.vercel\.app`; override only for stricter custom-domain deployments. |
| `COPERNICUS_USER` | Required for satellite-backed inference | Copernicus Data Space username. |
| `COPERNICUS_PASSWORD` | Required for satellite-backed inference | Copernicus Data Space password. |

7. Deploy the backend.
8. Verify:

```powershell
Invoke-RestMethod "https://<render-backend-url>/health"
Invoke-RestMethod "https://<render-backend-url>/model-status"
Invoke-RestMethod "https://<render-backend-url>/validation/scenarios/bangladesh-2024"
```

`/model-status` must report `data_mode: copernicus_sentinel` and `fallback_active: false` before the dashboard should be treated as satellite-backed production inference. If it reports `fallback_open_meteo_proxy`, the backend is online but predictions are not publishable validation output.

The backend start command runs migrations and seed data before Uvicorn:

```bash
alembic upgrade head && python seed_db.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Frontend On Vercel

1. Install and authenticate the Vercel CLI:

```powershell
npm install -g vercel
vercel login
```

2. Link the frontend project:

```powershell
Set-Location -LiteralPath "C:\Users\benja\OneDrive\Documents\Flood Monitoring System\flood-monitoring-system\frontend"
vercel link
```

3. Configure the environment variable:

```powershell
"https://<render-backend-url>" | vercel env add VITE_API_URL production
```

4. Deploy production:

```powershell
vercel --prod
```

`frontend/vercel.json` configures SPA rewrites, build command, install command, and output directory.

## Automated Local Preflight

Run this before any production deployment:

```powershell
Set-Location -LiteralPath "C:\Users\benja\OneDrive\Documents\Flood Monitoring System\flood-monitoring-system"
.\scripts\preflight-deploy.ps1 -BackendUrl "https://<render-backend-url>"
```

The preflight script checks:

- expected branch,
- untracked `.env` safety,
- banned wording,
- backend tests,
- frontend production build,
- backend `/health`,
- backend `/model-status`,
- Bangladesh 2024 local-data scenario.

## Automated Vercel Deployment

After the Render backend is live:

```powershell
Set-Location -LiteralPath "C:\Users\benja\OneDrive\Documents\Flood Monitoring System\flood-monitoring-system"
.\scripts\deploy-vercel.ps1 -BackendUrl "https://<render-backend-url>" -Production
```

If the Vercel CLI is not installed:

```powershell
.\scripts\deploy-vercel.ps1 -BackendUrl "https://<render-backend-url>" -Production -InstallVercelCli
```

The script links the Vercel project, sets `VITE_API_URL`, deploys the frontend, and prints the Vercel URL.

## Post-Deploy Smoke Test

Replace the placeholders and run:

```powershell
$BackendUrl = "https://<render-backend-url>"
$FrontendUrl = "https://<vercel-url>"

Invoke-RestMethod "$BackendUrl/health"
Invoke-RestMethod "$BackendUrl/model-status"
Invoke-RestMethod "$BackendUrl/paper-results"
Invoke-RestMethod "$BackendUrl/validation/scenarios/bangladesh-2024"
Invoke-RestMethod "$BackendUrl/predict/batch/regions" -Method Post -ContentType "application/json" -Body '{"date":"2024-09-04"}'
Invoke-WebRequest $FrontendUrl -UseBasicParsing
```

Then open the Vercel URL and check:

- dashboard map renders,
- Bangladesh 2024 scenario shows local UNOSAT-derived flood coordinates,
- all monitored countries batch run completes,
- Methodology page renders.

## Security Notes

- Do not commit `.env`, `.vercel`, generated logs, or secrets.
- Keep backend secrets only in Render.
- Keep Vercel environment variables frontend-only.
- Set `ALLOWED_ORIGINS` to the production Vercel domain.
- Override `CORS_ORIGIN_REGEX` only if the team wants to restrict API access to a custom domain instead of Vercel deployment domains.
- Stop localtunnel and the public demo server after migration; keep them as local development fallback only.
