#!/usr/bin/env bash
# Start the full Trendy Topic stack.
# Safe to run multiple times — kills any stale processes on ports 8000 and 5173 first.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$REPO/.venv/bin"

# ── helpers ──────────────────────────────────────────────────────────────────

log()  { echo "▶  $*"; }
die()  { echo "✗  $*" >&2; exit 1; }

free_port() {
  local port=$1
  local pids
  pids=$(lsof -ti tcp:"$port" 2>/dev/null || true)
  if [[ -n "$pids" ]]; then
    log "Stopping existing process on port $port (PID $pids)"
    echo "$pids" | xargs kill -9 2>/dev/null || true
    sleep 0.4
  fi
}

check_venv() {
  [[ -x "$VENV/python" ]] || die "Virtualenv not found at $REPO/.venv — run: python3 -m venv .venv && $VENV/pip install -r requirements.txt"
  [[ -x "$VENV/uvicorn" ]] || die "uvicorn not installed — run: $VENV/pip install -r requirements.txt"
}

check_node() {
  [[ -d "$REPO/frontend/node_modules" ]] || die "Frontend deps missing — run: cd frontend && npm install"
}

# ── preflight ─────────────────────────────────────────────────────────────────

log "Trendy Topic startup"
check_venv
check_node

free_port 8000
free_port 5173

# ── backend ───────────────────────────────────────────────────────────────────

log "Starting FastAPI backend on http://localhost:8000"
cd "$REPO"
"$VENV/uvicorn" api.main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait up to 6 s for the API to accept connections.
for i in $(seq 1 12); do
  if curl -sf http://127.0.0.1:8000/api/summary > /dev/null 2>&1; then
    log "API ready ✓"
    break
  fi
  sleep 0.5
done

# ── frontend ──────────────────────────────────────────────────────────────────

log "Starting Vite frontend on http://localhost:5173"
cd "$REPO/frontend"
npm run dev -- --host &
FRONTEND_PID=$!

# Wait for Vite to print its Local URL, then open the browser.
for i in $(seq 1 20); do
  sleep 0.5
done

log "Opening dashboard at http://localhost:5173"
open http://localhost:5173 2>/dev/null || xdg-open http://localhost:5173 2>/dev/null || true

log "Stack is running. Press Ctrl-C to stop everything."

# ── wait / cleanup ────────────────────────────────────────────────────────────

trap 'log "Shutting down…"; kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true' EXIT INT TERM
wait "$BACKEND_PID" "$FRONTEND_PID"
