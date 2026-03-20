<p align="center">
  <img src="docs/images/banner.png" alt="Aetherix" width="420" style="display:block;margin:auto;padding-bottom:16px">
</p>
<h1 align="center">Aetherix</h1>
<p align="center"><em>Proactive Agentic AI for Hospitality F&B Operations</em></p>
<p align="center">
  <img src="https://img.shields.io/badge/phase-3%20%E2%80%94%20Dashboard%20MVP-blue" alt="Phase 3">
  <img src="https://img.shields.io/badge/stack-FastAPI%20%7C%20Next.js%2016%20%7C%20Supabase-informational" alt="Stack">
  <img src="https://img.shields.io/badge/AI-Claude%20Sonnet%204-blueviolet" alt="Claude">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

## What It Does

Hotel F&B managers spend **5–8 hours/week** doing manual staffing forecasts at ~70% accuracy. One missed event means understaffed dinner service, unhappy guests, and lost revenue.

Aetherix eliminates that. It watches your property data, local events, and weather — and pushes a single, actionable directive to your phone before you need it:

> *"Anticipating +£1,200 in F&B revenue tonight (6–9 PM) due to a nearby tech conference. Recommend calling 2 servers + 1 prep cook (est. £180 labor). Target: 14 total staff."*

No dashboards to check. No guesswork. Just a decision, explained.

| | Traditional | Aetherix |
|---|---|---|
| **Forecast accuracy** | ~70% | 85%+ target |
| **Time spent** | 5–8 hrs/week | <2 hrs/week |
| **Data model** | Static PMS history | PMS + events + weather + vectors |
| **Delivery** | Manager opens a dashboard | Push → WhatsApp / SMS / Email |
| **Explainability** | None | "Why?" → instant mathematical breakdown |

---

## Architecture

**Thin Frontend. Fat Backend. Agentic Core.**

```
┌────────────────────────────────────────────────────────────┐
│                    External Integrations                   │
│  Mews / Apaleo PMS  ·  PredictHQ Events  ·  Weather API   │
└──────────────┬──────────────────────────────────┬──────────┘
               │ read-only webhooks               │ enrichment
               ▼                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  Fat Backend  (FastAPI + Python)             │
│                                                             │
│  PMS Sync Service  →  Semantic Reasoning Engine  →  LLM    │
│                             ↕                    Orchestrator│
│              Supabase PostgreSQL + pgvector (RAG)           │
└────────────────────────┬────────────────────────────────────┘
                         │ typed OpenAPI contract
          ┌──────────────┴──────────────┐
          ▼                             ▼
  Next.js Frontend             Delivery Layer
  (App Router + shadcn/ui)     WhatsApp · SMS · Email
```

### Tech Stack

| Layer | Tech |
|---|---|
| **Frontend** | Next.js 16 (App Router), React 19, Tailwind CSS, shadcn/ui |
| **Backend** | Python 3.12, FastAPI, async SQLAlchemy |
| **AI / Reasoning** | Claude Sonnet 4 (Anthropic), Qdrant vector DB, Mistral Embed |
| **Database** | Supabase PostgreSQL, pgvector, Row-Level Security (multi-tenant) |
| **PMS Integrations** | Apaleo OAuth2, Mews webhooks |
| **Delivery** | Twilio (SMS/WhatsApp), SendGrid |
| **Contract** | OpenAPI spec → `openapi-fetch` (end-to-end type safety) |
| **Infrastructure** | Docker Compose (local), Supabase migrations |
| **MCP** | Custom MCP servers for PMS + search extensibility |

---

## Repository Structure

```
Hospitality-Operations-Agentic-AI-B2B/
│
├── fastapi-backend/          ← ACTIVE: Python AI/orchestration backend
│   ├── app/
│   │   ├── api/              HTTP routes (thin presentation layer)
│   │   ├── db/               SQLAlchemy models, Supabase/pgvector
│   │   └── services/         Reasoning engine, PMS sync, LLM chains
│   ├── tests/                Backend unit tests
│   ├── pyproject.toml        Python 3.12, modern packaging
│   ├── Dockerfile
│   └── .env.example
│
├── nextjs-frontend/          ← ACTIVE: React/Next.js dashboard UI
│   ├── src/app/              App Router pages
│   ├── src/components/       UI components (shadcn/ui)
│   ├── shared-data/          Auto-generated OpenAPI client
│   ├── openapi-ts.config.js  Type generation from backend spec
│   ├── Dockerfile
│   └── .env.example
│
├── mcp_servers/              MCP servers (PMS, search integrations)
├── supabase/migrations/      PostgreSQL schema versions
├── scripts/                  Operational scripts (seed, smoke test, scenarios)
│   ├── experimental/         PoC agents (autonomous, MCP, voice, router)
│   └── tooling/streamlit/    Internal Streamlit admin/prompt playground
│
├── tests/                    Integration tests
│   └── qa/                   QA suites (Phase 2 + Phase 3)
│
├── docs/                     All product + technical documentation
│   ├── ARCHITECTURE.md       Detailed technical architecture
│   ├── ROADMAP_NOW_NEXT_LATER.md
│   ├── Problem_Statement.md
│   ├── Cost_Model.md
│   ├── DEPLOYMENT.md
│   └── _bmad/                BMAD methodology framework (AI dev guidelines)
│
├── _ai_workspace/            AI agent artifacts (BMAD outputs, Cursor plans)
├── _legacy/                  Archived code from Phase 1–2 (reference only)
│   ├── backend/              Phase 1–2 FastAPI (superseded by fastapi-backend/)
│   └── aetherix-dashboard/   Earlier Next.js variant (superseded by nextjs-frontend/)
│
├── docker-compose.yml        ← START HERE for local dev
├── .env.example              Root environment template
└── WARP.md                   AI agent workspace context
```

> **Active code lives in:** `fastapi-backend/`, `nextjs-frontend/`, `mcp_servers/`
> **Legacy reference:** `_legacy/` (do not modify)
> **Internal tooling:** `scripts/tooling/streamlit/` (admin/R&D use)

---

## Quick Start

**Prerequisites:** Docker + Docker Compose.

```bash
# 1. Clone
git clone <repository_url>
cd Hospitality-Operations-Agentic-AI-B2B

# 2. Configure environment
cp fastapi-backend/.env.example fastapi-backend/.env
cp nextjs-frontend/.env.example nextjs-frontend/.env.local
# → Fill in: ANTHROPIC_API_KEY, SUPABASE_*, QDRANT_*

# 3. Boot the stack
docker compose up --build

# 4. Open
# Dashboard:    http://localhost:3000
# API docs:     http://localhost:8000/api/docs
# Mail (dev):   http://localhost:8025
```

---

## Development Phases

| Phase | Status | Scope |
|---|---|---|
| **Phase 1** | ✅ Done | Backend MVP — prediction + reasoning engines |
| **Phase 2** | ✅ Done | RAG with 495 vector patterns, Qdrant |
| **Phase 3** | 🔄 Now | Dashboard MVP — Aetherix UI (Next.js) |
| **Phase 4** | 📋 Next | Feedback loop, accuracy tracking, MAPE metrics |
| **Phase 5** | 📋 Later | Voice input, POS integrations, multi-property |

---

## Key Design Decisions

**Why push, not pull?**
Managers don't have time to check dashboards. The insight must arrive at the moment of decision (morning briefing, 24h before service).

**Why explainability-first?**
Adoption dies when managers don't trust the recommendation. Every directive includes a "Why?" path — historical patterns, confidence score, comparable events.

**Why read-only PMS integration?**
Zero-friction pilot. No IT approval needed. Aetherix only needs a read-only webhook to start establishing baselines.

**Why OpenAPI type contract?**
Frontend and backend are co-generated from a single spec. Type mismatches are caught at build time, not in production.

---

## Documentation

| Doc | Description |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Full system architecture (v0.2.0) |
| [`docs/ROADMAP_NOW_NEXT_LATER.md`](docs/ROADMAP_NOW_NEXT_LATER.md) | Product roadmap |
| [`docs/Problem_Statement.md`](docs/Problem_Statement.md) | Problem framing + ICP |
| [`docs/Cost_Model.md`](docs/Cost_Model.md) | Unit economics + pricing model |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Deployment guide |
| [`docs/WALKTHROUGH_APALEO.md`](docs/WALKTHROUGH_APALEO.md) | Apaleo integration walkthrough |
| [`WARP.md`](WARP.md) | AI agent workspace context + principles |

---

*Aetherix — Contextual Intelligence for Hospitality.*
