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












# Frontend-Backend Integration Plan

This plan outlines the steps to tear out the frontend mock data (`mockData.ts`) and fully connect the React application to your newly built FastAPI backend for live prices, historical charts, and real paper trading execution.

> [!CAUTION]
> This requires removing the existing `mockData` reliance across all of your pages, which means the app will rely entirely on the backend server running to function.

## Proposed Changes

### Backend Refinements
The backend is mostly ready, but we need one small change to make charts and streams dynamic.

#### [MODIFY] `c:\Users\Admin\workspace\trade-spark-backend\main.py`
Currently, the WebSocket route `ws://localhost:8000/ws/price_stream` hardcodes `symbol = "AAPL"`. We will modify the URL to `/ws/price_stream/{symbol}` so the frontend can stream live data for any stock the user clicks on.

---

### Frontend Services

#### [MODIFY] `c:\Users\Admin\workspace\trade-spark\src\services\api.ts`
Add the new functions corresponding to our recently created backend endpoints:
- `getLivePrice(symbol: string)` -> calls `GET /trade/price/{symbol}`
- `getHistoricalData(symbol: string, period?: string, interval?: string)` -> calls `GET /trade/history/{symbol}`

#### [MODIFY] `c:\Users\Admin\workspace\trade-spark\src\hooks\useLivePrice.ts`
Update the hook setup to connect dynamically to the newly parameterized backend URL (e.g., `ws://localhost:8000/ws/price_stream/${symbol}`).

---

### Frontend UI Components 

#### [MODIFY] `c:\Users\Admin\workspace\trade-spark\src\pages\StockDetail.tsx`
- **Tear out `mockData.ts`**: Replace `generatePriceHistory(stock.price)` with a React hook (like `useEffect` or `react-query`) that calls `apiService.getHistoricalData(symbol)`.
- **Integrate WebSockets**: Implement the `useLivePrice` hook here to dynamically update the top price display in real-time as WebSocket ticks come in.
- **Render Real Charts**: Map the data from `getHistoricalData` (which has `time, open, high, low, close, volume`) directly into the existing `recharts` `<LineChart />` component.

#### [MODIFY] `c:\Users\Admin\workspace\trade-spark\src\components\TradeModal.tsx`
Ensure the BUY/SELL submission button utilizes `apiService.executeTrade` and passes the user’s JWT token safely, replacing the mock local context.

## Open Questions

> [!WARNING]
> 1. Your React app currently uses a Context (`TradingContext`) and Redux to manage state. Do you want me to wire up the API calls *inside* your existing Context/Redux actions, or should I fetch data directly within the components (like using standard `useEffect`)? 
> 2. Are you ready for me to rip out the mock data permanently, or do you want to keep a toggle somewhere to switch back to mock mode if the python backend isn't running?

## Verification Plan
1. Start both the Vite frontend and Uvicorn backend.
2. Click on a Stock Card (e.g., AAPL).
3. Verify the Recharts graph visually renders 1-month historical data mapping real data.
4. Watch the top screen price update automatically every 3 seconds via the WebSocket.
5. Successfully execute a Buy order and see the backend confirm a position.



# Backend CI/CD Pipeline Implementation Plan

This plan outlines the steps to implement a "Big Company" style CI/CD pipeline for the Trade Spark backend. This follows cloud-native best practices using containerization and automated quality gates.

## User Review Required

> [!IMPORTANT]
> - **GitHub Secrets**: To enable the "Push to Registry" parts of the pipeline, you will need to add secrets to your GitHub repository (e.g., `DOCKER_HUB_USERNAME`, `DOCKER_HUB_TOKEN`) or use the default `GITHUB_TOKEN` for GitHub Packages.
> - **Database for Tests**: I recommend using an **SQLite In-Memory** database for CI tests to keep the pipeline fast and simple, while keeping Postgres for production.

## Proposed Changes

### 1. Dependency Updates
We need to add tools for linting, security scanning, and testing.

#### [MODIFY] [requirements.txt](file:///c:/Users/Admin/workspace/trade-spark-backend/requirements.txt)
Add development/CI dependencies:
- `ruff` (Linting & Formatting)
- `bandit` (Security Scanning)
- `pytest` (Unit Testing)
- `httpx` (For testing FastAPI endpoints)

---

### 2. Quality Gate Configuration

#### [NEW] [pyproject.toml](file:///c:/Users/Admin/workspace/trade-spark-backend/pyproject.toml)
Configure `ruff` and `pytest` settings to ensure consistent code quality.

---

### 3. Automated Testing

#### [NEW] `tests/` directory
Create initial tests to verify the backend is healthy.

#### [NEW] [test_main.py](file:///c:/Users/Admin/workspace/trade-spark-backend/tests/test_main.py)
A basic test suite to check:
- `GET /` (Health check)
- Basic endpoint availability.

---

### 4. Containerization

#### [NEW] [Dockerfile](file:///c:/Users/Admin/workspace/trade-spark-backend/Dockerfile)
A production-ready Dockerfile:
- **Base**: Python 3.11-slim.
- **Security**: Non-root user.
- **Server**: Uvicorn.

#### [NEW] [.dockerignore](file:///c:/Users/Admin/workspace/trade-spark-backend/.dockerignore)
Prevent bloating the image with `venv`, `__pycache__`, etc.

---

### 5. GitHub Actions Workflow

#### [NEW] [.github/workflows/backend.yml](file:///c:/Users/Admin/workspace/trade-spark-backend/.github/workflows/backend.yml)
The automated pipeline:
1. **Lint Phase**: `ruff check` and `ruff format`.
2. **Security Phase**: `bandit`.
3. **Test Phase**: `pytest`.
4. **Build Phase**: `docker build`.
5. **Push Phase**: Push to GitHub Packages (GHCR) on `main` branch updates.

---

## Open Questions

> [!WARNING]
> 1. **Deployment Strategy**: Do you want me to include a "Manual" deployment step (click a button in GitHub Actions) or "Automatic" (deploys every time `main` is updated)?
> 2. **Server Access**: For the CD phase (Step 2 in your original request), I'll need to know if you're using a specific provider (Oracle/Hetzner) so I can tailor the deployment script (e.g., SSH, Docker Compose pull, etc.).

## Verification Plan

### Automated Tests
- Run `ruff check .` locally.
- Run `pytest` locally.
- Run `docker build -t trade-spark-backend .`

### Manual Verification
- Check the "Actions" tab on GitHub.
- Verify the image appears in GitHub Packages.
