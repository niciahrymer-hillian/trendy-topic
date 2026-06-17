# How to run Trendy Topic

## Start everything (one command)

From the repo root:

```bash
./start.sh
```

This frees ports 8000/5173, starts the API + frontend, and opens the dashboard.

- Backend (FastAPI): http://localhost:8000  (`uvicorn api.main:app`)
- Frontend (Vite):    http://localhost:5173  ← open this for the demo

Press **Ctrl-C** to stop both.

## First-time setup (only once)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd frontend && npm install && cd ..
```

## Run pieces manually (if needed)

```bash
# Backend only
.venv/bin/uvicorn api.main:app --reload --port 8000

# Frontend only
cd frontend && npm run dev

# Tests / build
.venv/bin/python -m pytest -q     # backend: 232 tests
cd frontend && npm run build      # frontend typecheck + build
```
