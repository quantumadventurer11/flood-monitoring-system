# Flood Monitoring System

A full-stack flood monitoring and prediction web application based on the supplied GLOC 2026 research paper. The app combines Sentinel-1/Sentinel-2 acquisition, a 61-feature preprocessing pipeline, XGBoost flood classification, Open-Meteo forecasting, and a React dashboard that reproduces the methodology figures and tables.

## Prerequisites

- Docker Desktop
- Git
- A free Copernicus Data Space Ecosystem account from `https://dataspace.copernicus.eu`

Copernicus credentials are optional for local demos. Without them, the backend uses Open-Meteo weather/reanalysis data to generate fallback satellite-like arrays so prediction still works end-to-end.

## Environment Setup

```bash
git clone https://github.com/quantumadventurer11/flood-monitoring-system.git
cd flood-monitoring-system
copy .env.example .env
```

Edit `.env` and fill in:

```bash
COPERNICUS_USER=your_copernicus_username
COPERNICUS_PASSWORD=your_copernicus_password
```

## Quick Start

```bash
cd flood-monitoring-system
docker compose up --build
```

Open:

- Frontend: `http://localhost:3000`
- Backend API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

Stop the app:

```bash
docker compose down
```

## Repository Map

- `backend/` - FastAPI app, SQLAlchemy models, Alembic migrations, ML/weather/satellite services, and tests.
- `frontend/` - React/Vite/Tailwind app with dashboard pages and paper reproduction components.
- `docs/` - supporting project and research documents.
- `.readme` - detailed maintainer guide explaining repository contents.
- `docker-compose.yml` - local full-stack runtime.

## API Reference

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/ingest` | Fetch/validate Sentinel scene availability or fallback scene metadata. |
| `POST` | `/predict` | Fetch satellite/fallback arrays, preprocess, classify flood risk, and store prediction. |
| `POST` | `/forecast` | Fetch Open-Meteo weather/flood data and return a five-day flood likelihood forecast. |
| `GET` | `/paper-results` | Return seeded paper metrics, tables, sensitivity analysis, and key findings. |
| `GET` | `/events` | Return recent flood events. |
| `GET` | `/alerts` | Return active flood alerts. |
| `GET` | `/regions` | Return global flood-prone countries with centroids and baseline risk. |
| `POST` | `/predict/batch/regions` | Run prediction across all configured monitoring regions. |
| `GET` | `/validation/scenarios/bangladesh-2024` | Return local UNOSAT-derived Bangladesh 2024 flood-coordinate records. |

## Without Copernicus Credentials

The app still runs without `COPERNICUS_USER` and `COPERNICUS_PASSWORD`.

Fallback behavior:

- `/predict` uses Open-Meteo ERA5 proxy data to create satellite-like B03/B04/B08/VV/QA60 arrays.
- The real preprocessing pipeline still runs on those arrays.
- XGBoost still predicts from the extracted 61-feature vector.
- `/forecast` still uses live Open-Meteo forecast and flood APIs when available.

## Paper Reproduction

The Methodology page reproduces:

- Fig. 1 workflow diagram
- Fig. 2 NDWI water mask
- Fig. 3 patch grid
- Fig. 4 pixel distribution
- Table 2 dataset summary
- Fig. 5 ROC curves
- Table A1 model performance
- Table 3 ablation study

Table A1 and Table 3 values are treated as authoritative where PDF prose conflicts with structured results.

## Independent Validation Audit

The app documents UNOSAT FL20240825BGD as the independent validation source for the 2024 Bangladesh floods. The bundled validation script downloads the UNOSAT shapefile, converts the flood polygons into regular patch-centroid labels, and writes both summary and patch-level audit artifacts:

```bash
cd backend
python scripts/validate_unosat_bangladesh.py
```

Default artifacts:

- `backend/validation/unosat_bangladesh_2024_summary.json`
- `backend/validation/audits/bangladesh_2024/summary.json`
- `backend/validation/audits/bangladesh_2024/patch_level_audit.csv`

To compute publishable validation metrics, provide a CSV containing real patch-level scores generated independently from the UNOSAT labels:

```bash
python scripts/validate_unosat_bangladesh.py --scores-csv path/to/patch_scores.csv
```

The CSV must contain `patch_id`, `ndwi_water_fraction`, and `model_probability`. NDWI-derived water fraction is treated as a feature or score, not as the ground-truth label.

The patch audit CSV keeps the evidence tiers separate:

- UNOSAT/Copernicus EMS flood maps provide validation labels.
- Sentinel-derived NDWI/features and XGBoost probabilities provide model signal.
- Open-Meteo rainfall, soil moisture, and discharge provide operational forecast context only.

When scores are supplied, each patch receives an `error_type`: `true_positive`, `false_positive`, `false_negative`, or `true_negative`. When scores are missing, patches are marked `score_missing` and the artifact is not publishable.

## Deployment

Use `DEPLOYMENT.md` for the full production runbook. The public deployment path is:

- Frontend: Vercel from `frontend`
- Backend: Render Web Service from `backend`
- Database: Render Postgres from `render.yaml`

Run deployment preflight before publishing:

```powershell
Set-Location -LiteralPath "C:\Users\benja\OneDrive\Documents\Flood Monitoring System\flood-monitoring-system"
.\scripts\preflight-deploy.ps1 -BackendUrl "https://<render-backend-url>"
```

Deploy the frontend after the Render backend is live:

```powershell
.\scripts\deploy-vercel.ps1 -BackendUrl "https://<render-backend-url>" -Production
```

If the Vercel CLI is not installed:

```powershell
.\scripts\deploy-vercel.ps1 -BackendUrl "https://<render-backend-url>" -Production -InstallVercelCli
```

Do not use localtunnel for public review after the Vercel/Render deployment is active.

## Tests

```bash
docker compose exec -T backend pytest
docker compose build frontend
```
