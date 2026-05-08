# 🌊 Flood Monitoring System

A full-stack flood monitoring dashboard with a React frontend, FastAPI backend, PostGIS database, and Copernicus/Sentinel satellite data integration.

---

## 👋 Hey team — here's how to get the app running on your machine

You only need **two things** installed:
- [Git](https://git-scm.com/downloads)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ← **make sure it's running before you start**

---

## ⚡ Quick Start (copy-paste into PowerShell)

### Step 1 — Clone the repo

```powershell
git clone https://github.com/quantumadventurer11/flood-monitoring-system.git
cd flood-monitoring-system
```

### Step 2 — Start the whole app (first time takes ~3–5 minutes to download)

```powershell
docker compose up --build
```

Wait until you see **both** of these lines in the terminal:
```
backend-1  | INFO:     Application startup complete.
frontend-1 |   ➜  Local:   http://localhost:3000/
```

### Step 3 — Seed the database (open a **new** PowerShell window for this)

```powershell
cd flood-monitoring-system
docker compose exec backend python seed_db.py
```

You should see: `✅ Database seeded successfully.`

### Step 4 — Open the dashboard

Open your browser and go to: **http://localhost:3000**

- Click **"Register"** to create your account
- Log in → explore the dashboard!

---

## 🛑 Stopping the app

Press **Ctrl+C** in the terminal running `docker compose up`, then run:

```powershell
docker compose down
```

---

## 🔄 Starting again later (after first setup)

You don't need `--build` again. Just run:

```powershell
cd flood-monitoring-system
docker compose up
```

The database keeps its data between restarts.

---

## 🗺️ What's in the dashboard

| Page | What you can do |
|------|----------------|
| **Dashboard** | Live stats — active flood events, alerts, sensor count |
| **World Map** | Click any of 15 flood-prone regions worldwide to select it |
| **Flood Events** | Browse all recorded flood events by region and severity |
| **Alerts** | View triggered flood alerts and their status |
| **Data Ingestion** | Select a region + Sentinel-1 or Sentinel-2 + date range → fetch real satellite data |

---

## 🐛 Troubleshooting

**Port already in use?**
```powershell
docker compose down
docker compose up
```

**Database errors after updating?**
```powershell
docker compose down -v   # ⚠️ This wipes the database
docker compose up --build
docker compose exec backend python seed_db.py
```

**Want to see live logs?**
```powershell
docker compose logs -f backend
docker compose logs -f frontend
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React-Leaflet |
| Backend | FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL 16 + PostGIS |
| Satellite data | Copernicus Data Space (Sentinel-1 SAR + Sentinel-2 optical) |
| Auth | JWT (python-jose) + bcrypt |
| Deployment | Docker + Docker Compose |

---

## 📁 Project Structure

```
flood-monitoring-system/
├── backend/
│   ├── app/
│   │   ├── api/routes/     # FastAPI route handlers
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   └── services/       # Business logic (satellite, seeding)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/     # Shared UI components (Layout, sidebar)
│       └── pages/          # Dashboard, Map, Events, Alerts, Ingest
├── docker-compose.yml
└── seed_db.py
```
