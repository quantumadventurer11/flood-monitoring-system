# 🌊 Flood Monitoring System

An AI-powered flood monitoring system with a real-time interactive dashboard, satellite data ingestion, and alert management — built entirely with free and open-source tools.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite + Leaflet + Tailwind)               │
│  Port 3000  –  Interactive world map, dashboard, alerts     │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────────────┐
│  Backend (FastAPI + SQLAlchemy)                             │
│  Port 8000  –  Auth, CRUD, satellite ingestion endpoints    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  PostgreSQL + PostGIS                                       │
│  Port 5432  –  All structured data, geospatial queries      │
└─────────────────────────────────────────────────────────────┘
                       │
          Copernicus STAC API (FREE, no key needed for search)
          Sentinel-1 (SAR) + Sentinel-2 (Optical) imagery
```

## Quick Start (Docker – recommended)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

```bash
# Clone the repo
git clone https://github.com/quantumadventurer11/flood-monitoring-system.git
cd flood-monitoring-system

# Start all services
docker compose up

# In a second terminal – seed the database
docker compose exec backend python seed_db.py
```

Open **http://localhost:3000** and register an account.

---

## Manual Setup (no Docker)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Copy and edit environment variables
copy .env.example .env        # Windows
# Edit DATABASE_URL, SECRET_KEY etc.

# Run migrations and seed
python seed_db.py

# Start API server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**

---

## Features

| Feature | Description |
|---------|-------------|
| 🗺️ **World Map** | Interactive Leaflet map with 15 pre-seeded flood-prone regions worldwide |
| 🛰️ **Satellite Ingestion** | Trigger Sentinel-1/2 data fetches via free Copernicus STAC API |
| 🌊 **Flood Events** | View and filter AI-detected flood events by confidence level |
| 🔔 **Alerts** | Configurable threshold-based alerts with severity levels |
| 📊 **Dashboard** | Real-time overview of active events, alerts, and quick actions |
| 🔐 **Auth** | JWT-based registration and login |

## Free Data Sources

- **Sentinel-1 (SAR)** – ESA Copernicus, free STAC catalogue search
- **Sentinel-2 (Optical)** – ESA Copernicus, free STAC catalogue search
- **OpenStreetMap** – Free tile layer for the map

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS, Leaflet, Recharts |
| Backend | FastAPI, SQLAlchemy, Pydantic, python-jose |
| Database | PostgreSQL 16 + PostGIS |
| Satellite | Copernicus Data Space STAC API |
| Container | Docker Compose |
| Hosting | Railway (backend) + Vercel (frontend) – free tier |

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
flood-monitoring-system/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # FastAPI route handlers
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic & satellite integration
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   ├── requirements.txt
│   └── seed_db.py
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios API client
│   │   ├── components/       # Shared UI components
│   │   ├── pages/            # Route-level pages
│   │   └── types/            # TypeScript interfaces
│   ├── index.html
│   └── package.json
└── docker-compose.yml
```

## Deployment (Free Hosting)

### Backend → Railway
1. Push to GitHub
2. Create project at [railway.app](https://railway.app)
3. Add PostgreSQL plugin (free tier)
4. Set environment variables from `.env.example`
5. Deploy from GitHub

### Frontend → Vercel
1. Import repo at [vercel.com](https://vercel.com)
2. Set `VITE_API_URL` to your Railway backend URL
3. Deploy

---

*Research references: Sentinel-1/2 flood detection papers, DeepFuse, GAN-based SAR-optical fusion, Vision Transformer for flood detection.*
