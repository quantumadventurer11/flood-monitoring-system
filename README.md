# Flood Monitoring System

A full-stack flood monitoring and prediction web application based on the supplied GLOC 2026 research paper. The app combines a FastAPI backend, PostgreSQL persistence, seeded paper results, and a React dashboard that reproduces the methodology figures and tables.

## Run

Open PowerShell in the project root before running Docker Compose:

```bash
cd C:\software_engineering\flood-monitoring-system
docker compose up --build
```

Frontend: `http://localhost:3000`  
Backend API: `http://localhost:8000`

## Stack

- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic
- Frontend: React 18, TypeScript, Vite, Tailwind CSS, Recharts, Leaflet
- Database: PostgreSQL 15
- ML/services: XGBoost-compatible classifier wrapper, NumPy, SciPy, scikit-image, rasterio-ready dependency set
- Weather: Open-Meteo API with deterministic fallback
- Satellite: Copernicus credential shell with simulated fallback

## Repository Map

- `backend/` - FastAPI app, SQLAlchemy models, Alembic migration, ML/weather/satellite services, and tests.
- `frontend/` - React/Vite/Tailwind app with dashboard pages and paper reproduction components.
- `docs/` - supporting project and research documents.
- `.readme` - detailed maintainer guide explaining the repository contents.
- `docker-compose.yml` - local full-stack runtime.

## API

- `POST /ingest`
- `POST /predict`
- `POST /forecast`
- `GET /paper-results`
- `GET /events`
- `GET /alerts`
- `GET /regions`

The `/paper-results` endpoint returns the seeded dataset stats, model metrics, ablation results, confusion matrices, sensitivity analysis, key features, and paper notes used by the methodology page.

## Paper Reproduction

The methodology page reproduces:

- Fig. 1 workflow diagram
- Fig. 2 NDWI water mask
- Fig. 3 patch grid
- Fig. 4 pixel distribution
- Table 2 dataset summary
- Fig. 5 ROC curves
- Table A1 model performance
- Table 3 ablation study

Table A1 and Table 3 values are treated as authoritative where PDF prose conflicts with structured results.

## Fallback Behavior

The app is designed to render end-to-end without Copernicus credentials or a trained `xgboost_model.pkl`. Satellite ingest, patch thumbnails, NDWI masks, and predictions use deterministic simulated fallbacks until live data/model artifacts are supplied.
