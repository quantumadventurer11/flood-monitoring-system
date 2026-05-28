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

## Deployment

### Frontend on Vercel

1. Set the Vercel project root to `frontend`.
2. Add environment variable:
   - `VITE_API_URL=https://your-backend-url`
3. Deploy:

```bash
cd frontend
vercel --prod
```

`frontend/vercel.json` configures SPA rewrites, build command, install command, output directory, and `VITE_API_URL`.

### Backend on Render

1. Create a Render PostgreSQL database.
2. Create a Render Web Service from this repo.
3. Set root directory to `backend`.
4. Add environment variables:
   - `DATABASE_URL`
   - `COPERNICUS_USER`
   - `COPERNICUS_PASSWORD`
   - `CORS_ORIGINS`
5. Build command:

```bash
pip install -r requirements.txt
```

6. Start command:

```bash
alembic upgrade head && python seed_db.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Tests

```bash
docker compose exec -T backend pytest
docker compose build frontend
```
