# RupeeRadar 💳📡

**AI-Powered Personal Finance Assistant for Indian Bank Statements**

RupeeRadar helps working professionals in India understand *where their money is going* by transforming messy bank statements (UPI, card, NEFT, IMPS) into structured transactions, detected recurring payments (subscriptions, EMIs, SIPs, rent), key financial metrics, and personalized spending insights.

---

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python 3.13), SQLAlchemy 2.0, SQLite (Local), pandas, Groq LLM API
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, TanStack Query, Recharts, Lucide Icons
- **Architecture:** Pipeline-oriented modular monolith with privacy-first ephemeral data handling

---

## 🚀 Quick Start

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your GROQ_API_KEY if testing AI categorization
uvicorn app.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`.
API documentation is interactive at `http://localhost:8000/docs`.

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:5173`.

### 3. Deployment Configuration (Railway + Vercel)

#### Backend on Railway

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Required env vars (server-side only):
  - `DATABASE_URL` — set to a durable Postgres URL in production or a Railway volume-backed SQLite path
  - `GROQ_API_KEY` — Groq API key, kept as a Railway secret
  - `GROQ_MODEL=llama-3.3-70b-versatile`
  - `CORS_ORIGINS` — exact deployed frontend origin(s), e.g. `https://your-app.vercel.app`
  - `SESSION_TTL_HOURS`, `MAX_UPLOAD_SIZE_MB`, `LOG_LEVEL`
- Keep uploaded CSVs in temporary storage and delete them after processing, including on failure paths.
- Do not expose the Groq key to the browser or commit secrets to the repository.

#### Frontend on Vercel

- Build command: `npm run build`
- Output directory: `dist`
- Required public env var: `VITE_API_BASE_URL=https://<railway-service-domain>/api/v1`
- Add a SPA rewrite so `/analysis/:sessionId` resolves to `index.html`.
- Keep all API secrets out of `VITE_*` variables; only the public API base URL belongs in frontend config.

---

## 📂 Project Structure

```
rupee-radar/
├── docs/                     # Specifications & Architecture
│   ├── context.md
│   ├── architecture.md
│   ├── implementation-plan.md
│   └── edge-case.md
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/routes/       # API route controllers
│   │   ├── models/           # SQLAlchemy ORM & Pydantic schemas
│   │   ├── parsers/          # Bank statement parsers
│   │   ├── pipeline/         # Data cleaning, categorization, metrics
│   │   ├── services/         # Groq LLM & report generation
│   │   └── utils/            # Merchant dictionaries & validators
│   └── tests/fixtures/       # Anonymized test statements
└── frontend/                 # React + TypeScript + Vite
    └── src/
        ├── components/       # Reusable UI components
        ├── pages/            # Landing and Dashboard pages
        ├── api/              # Axios API client
        └── types/            # TypeScript schemas
```
