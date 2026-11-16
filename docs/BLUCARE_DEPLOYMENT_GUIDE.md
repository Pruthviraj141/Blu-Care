# BLUCARE+ — DEPLOYMENT & OPERATIONS GUIDE
## Reproducible Local and Containerized Production Deployment

**Document Version:** 1.0.0  
**Target Environment:** Local Developer Workstation & Docker Compose  
**Date:** 2026-11-04  

---

## 1. Prerequisites

Before deploying BluCare+, ensure the host system has:
- **Operating System:** Linux, macOS, or Windows WSL2
- **Python:** 3.10, 3.11, or 3.12 (virtual environment recommended)
- **Node.js:** v18.0.0 or higher & npm
- **Docker & Docker Compose:** Docker Engine 24+ and Compose v2+
- **Hardware:**
  - Minimum 4 GB RAM (8 GB recommended for local sentence-transformer models)
  - 5 GB free disk space

---

## 2. Environment Configuration

Copy the example environment configuration:
```bash
cp .env.example .env
```

Ensure your `.env` contains the required keys (replace placeholders with your real values):

```ini
# Application Mode & Ports
APP_ENV=development
API_V1_PREFIX=/api/v1
RATE_LIMIT_PER_MINUTE=60

# Clerk Authentication
CLERK_ISSUER_URL=https://your-instance.clerk.accounts.dev
CLERK_JWKS_URL=https://your-instance.clerk.accounts.dev/.well-known/jwks.json
CLERK_SECRET_KEY=sk_test_...
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
ALLOW_DEV_AUTH=false

# LLM Inference (Groq - Free Tier)
GROQ_API_KEY=gsk_...
GROQ_MODEL=openai/gpt-oss-120b

# Embeddings & CrossEncoder Reranker
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5
EMBEDDING_DIM=384
RERANKER_MODEL_NAME=BAAI/bge-reranker-base

# Vector Database (Qdrant)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_NAME=medical_triage_kb

# Primary Relational Database (PostgreSQL / Supabase)
DATABASE_URL=postgresql://user:password@hostname:5432/dbname
SUPABASE_DB_URL=

# OpenStreetMap Overpass (Free Public Infrastructure)
OVERPASS_ENABLED=true
OVERPASS_ENDPOINT=https://overpass-api.de/api/interpreter
OVERPASS_TIMEOUT_SECONDS=25
OVERPASS_DEFAULT_RADIUS_METERS=5000
OVERPASS_MAX_RADIUS_METERS=10000
OVERPASS_MAX_RESULTS=20
OVERPASS_CACHE_TTL_SECONDS=600
OVERPASS_USER_AGENT=BluCarePlus/1.0
```

> [!IMPORTANT]
> Never commit real secrets, private keys, or passwords to Git. The `.gitignore` file includes `.env`.

---

## 3. Local Bare-Metal Setup

### 3.1 Backend Setup
```bash
# 1. Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install backend dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Initialize database schema
python -c "from app.db.session import init_db; init_db()"

# 4. Ingest medical knowledge base into Qdrant
python -m app.rag.document_ingestion

# 5. Start development backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3.2 Frontend Setup
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install frontend dependencies
npm install

# 3. Start Vite development server
npm run dev
```
The application will be accessible at `http://localhost:5173`.

---

## 4. Containerized Docker Deployment

BluCare+ includes an orchestrated `docker-compose.yml` deploying:
1. **`blucare_redis`:** Alpine Redis for session caching and rate limits.
2. **`blucare_qdrant`:** High-performance vector database with volume persistence.
3. **`blucare_backend`:** FastAPI container with health check probe.
4. **`blucare_frontend`:** Nginx / Vite production bundle.

### 4.1 Launching the Stack
```bash
# Build and start all services in detached mode
docker compose up -d --build

# View container logs
docker compose logs -f backend

# Verify health status of all containers
docker compose ps
```

### 4.2 Graceful Shutdown
```bash
docker compose down
```

---

## 5. Automated Verification & Testing

Run the full end-to-end regression test suite:
```bash
# Run all tests across Phase 1, Phase 2, Phase 3, and API
PYTHONPATH=. venv/bin/pytest tests/test_phase3_facilities.py tests/test_phase2_rag.py tests/test_phase1.py tests/test_api.py -v
```

Expected test result:
```text
====================== 51 passed in ~34s =======================
```

Validate frontend production build:
```bash
cd frontend
npm run build
```

---

## 6. Health & Readiness Monitoring

The backend exposes standard cloud-native health probes:
- **Liveness Probe:** `GET /health` (or `/health/live`)
  - Returns `200 OK` with `{ "status": "healthy" }`.
- **Readiness Probe:** `GET /health/ready`
  - Validates PostgreSQL database connection and Qdrant connectivity.
  - Returns `{ "status": "ready", "database": "connected", "qdrant": "connected" }`.

---

## 7. Operational Troubleshooting

| Symptom | Probable Cause | Remediation |
|---|---|---|
| Database Connection Refused | PostgreSQL not running or network DNS unreachable | System automatically falls back to local SQLite `triage_data.sqlite`. Check `DATABASE_URL` credentials. |
| Qdrant Timeout | Vector store container down | Ingestion script and store provide embedded local file fallback (`qdrant_local_store`). |
| Overpass Timeout (>25s) | Public Overpass server overloaded | The API automatically degrades to `status: "unavailable"` and supplies direct Google Maps search URLs so the user is never blocked. |
| 401 Unauthorized on Chat | Expired or missing Clerk token | Ensure valid Clerk session in browser or set `ALLOW_DEV_AUTH=true` for local isolated testing. |
