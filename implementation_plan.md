# Paper Trading App Architecture Outline

This document outlines the architectural setup and foundational steps to build a real-time paper trading platform using **FastAPI (Python)** for the backend and your existing **React + Vite** frontend.

## Architecture Overview

We will configure this repository as a monorepo containing both the frontend and the backend.

### The Stack:
1. **Frontend (`frontend/`):** React, Vite, Shadcn, TypeScript, Zustand, Lightweight Charts. *(You already have the base of this in the root directory)*
2. **Backend (`backend/`):**
    *   **Framework:** FastAPI (Python)
    *   **Type Validation:** Pydantic
    *   **Server:** Uvicorn (ASGI server for handling async Python and WebSockets)
    *   **Database:** PostgreSQL (to store users, wallets, and executed trades securely)
    *   **Cache/Message Broker:** Redis (to store live price ticks and manage pub/sub for WebSocket scalability)
    *   **Market Data:** Ingesting from a service like Polygon.io or Alpaca via WebSockets.

---

## User Review Required
> [!IMPORTANT]
> Since you currently have your React code in the root directory (e.g., `src/`, `package.json` in `trade-spark/`), I recommend **moving the frontend code into a `frontend/` folder** to keep the backend clean and separated. Would you like me to restructure the project into `frontend/` and `backend/` folders? Let me know below!

---

## Setup Phases (The "From Scratch" Plan)

### Phase 1: Directory Restructuring (Monorepo Setup)

#### [NEW] `backend/` directory
We will create a dedicated python backend folder to keep dependencies isolated from `node_modules`.

#### [MODIFY] React application location
*Move all existing Vite/React files (like `src/`, `public/`, `package.json`, `index.html`) from the root folder into a new `frontend/` folder.*

### Phase 2: Python Backend Initialization

We will set up the Python environment using standard robust practices.

1. **Virtual Environment:** We will create a `venv` (Virtual Environment) inside `backend/`. This acts like a local `node_modules` for Python, ensuring global computer packages aren't disturbed.
2. **Dependencies (`requirements.txt`):** We will install:
    *   `fastapi` (The web framework)
    *   `uvicorn[standard]` (The server to run FastAPI)
    *   `websockets` (For real-time streaming)
3. **Core App File (`backend/main.py`):** We will create a barebones FastAPI app with a REST endpoint and a WebSocket endpoint.

### Phase 3: The "Hello World" Real-Time Server

We will write a simple `backend/main.py` to prove the concept:
*   A basic REST endpoint: `GET /api/health` -> returns `{"status": "running"}`.
*   A classic WebSocket endpoint: `ws://localhost:8000/ws/price_stream` which will simply stream a simulated ticking price every second to verify the connection works.

### Phase 4: Frontend Connection

We will write a small React component in your frontend to connect to the Python WebSocket and display the ticking simulated price on the screen.

---

## Open Questions

> [!WARNING]
> Do you have **Python 3.9+** installed on your Windows machine? If you open a terminal and run `python --version`, what does it say?

## Verification Plan

### Automated/Manual Verification
1.  Run the Python backend using Uvicorn on port `8000`.
2.  Navigate to `http://localhost:8000/docs` to see FastAPI's auto-generated Swagger UI (a huge benefit of FastAPI!).
3.  Start the Vite frontend on port `5173`.
4.  Verify that the frontend successfully connects to the backend WebSocket and displays live streaming numbers.




.\venv\Scripts\pip install -r requirements.txt


.\venv\Scripts\uvicorn main:app --reload
