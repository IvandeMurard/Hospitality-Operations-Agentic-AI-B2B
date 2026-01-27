---
title: F&B Operations Agent
emoji: 🍽️
colorFrom: blue
colorTo: purple
sdk: docker
sdk_version: "4.0.0"
python_version: "3.11"
pinned: false
---

# F&B Operations Agent

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Active%20Development-green)](https://github.com/yourusername/fb-agent)
[![Deployment](https://img.shields.io/badge/Deployed-HuggingFace-FF9D00?logo=huggingface&logoColor=white)](https://huggingface.co/spaces/IvandeMurard/fb-agent-api)

> **AI-powered staffing forecasting for hotel F&B operations**  
> Semantic layer bridging external context (events, weather) with internal PMS data

---

## 🎯 Problem

Restaurant managers in hotels spend **5-8 hours/week** manually forecasting staffing needs with **~70% accuracy**, correlating data across siloed systems (PMS, event calendars, weather apps). This results in:
- Over/under-staffing → operational stress & revenue loss
- No integration between external context and internal operations
- Food waste from inaccurate demand predictions

---

## 💡 Solution

An **agentic AI system** that autonomously predicts staffing needs using:
- **RAG architecture** (Retrieval-Augmented Generation) for pattern-based forecasting
- **Semantic search** across historical scenarios to find similar operational contexts
- **PMS-agnostic design** compatible with any API-first system (Mews, Apaleo, etc.)
- **Human-in-the-loop** approach where managers approve predictions (augmented, not automated)

---

## ✨ Key Features

**🧠 Contextual Predictions**
- Combines external signals (city events, weather, holidays) with internal PMS historical data (occupancy, past demand)
- Qdrant vector search finds similar historical patterns
- Claude AI generates explainable reasoning

**🔍 Explainable AI**
- Every prediction shows WHY: "Based on 3 similar Saturday dinners with nearby concerts..."
- Confidence scores (85-90% typical)
- Pattern transparency for trust-building

**🤖 Multi-Agent Architecture**
- **Demand Predictor:** Forecasts covers using semantic pattern matching
- **Staff Recommender:** Calculates optimal staffing (servers, hosts, kitchen)
- **Reasoning Engine:** Generates human-readable explanations

**🔗 PMS-Agnostic Integration**
- API-first design works with any PMS (Mews, Apaleo, Opera, custom)
- No vendor lock-in
- RESTful endpoints for seamless integration

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│     USER INPUT (Manager Query)                  │
│  "Predict Saturday dinner staff needs"          │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│     CONTEXT ENRICHMENT                          │
│  External: Events API, Weather API, Holidays    │
│  Internal: PMS API (Occupancy, Past Demand)     │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│     SEMANTIC SEARCH (Qdrant)                    │
│  • Historical patterns as embeddings            │
│  • Vector similarity search (cosine distance)   │
│  • Returns top 3-5 matching scenarios           │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│     REASONING ENGINE (Claude)                   │
│  • Analyzes pattern relevance                   │
│  • Generates weighted prediction + confidence   │
│  • Produces natural language explanation        │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│     OUTPUT                                      │
│  145 covers (88% confidence)                    │
│  Recommended: 8 servers, 2 hosts, 3 kitchen     │
│  Reasoning: "Similar Saturday patterns..."      │
└─────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | FastAPI + Python 3.11 | REST API, multi-agent orchestration |
| **AI/ML** | Claude Sonnet 4 (Anthropic) | Reasoning engine, natural language explanations |
| **Embeddings** | Mistral Embed | Vector embeddings for semantic search (1024 dim) |
| **Vector DB** | Qdrant Cloud | Semantic pattern search |
| **Database** | Supabase (PostgreSQL) | Prediction history, analytics |
| **Cache** | Redis (Upstash) | Session state, conversation context |
| **Voice (opt-in)** | ElevenLabs | Speech-to-text (future: voice interface) |
| **PMS Integration** | Mews/Apaleo APIs | Hotel occupancy, internal context |
| **Deployment** | HuggingFace Spaces (Docker) | Cloud hosting, auto-scaling |

---

## 🚀 Live Demo

**API Endpoint:** [https://ivandemurard-fb-agent-api.hf.space](https://ivandemurard-fb-agent-api.hf.space)

**Interactive Documentation:** [https://ivandemurard-fb-agent-api.hf.space/docs](https://ivandemurard-fb-agent-api.hf.space/docs)

---

## ⚙️ Configuration

The system requires the following environment variables:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...          # Claude AI
QDRANT_API_KEY=...                    # Vector database
QDRANT_URL=https://...                # Qdrant cluster URL
MISTRAL_API_KEY=...                   # Embeddings generation

# Optional (for enhanced features)
SUPABASE_URL=...                      # Database
SUPABASE_KEY=...                      # Database auth
REDIS_URL=...                         # Session cache
ELEVENLABS_API_KEY=...                  # Voice interface (future)
PREDICTHQ_API_KEY=...                 # Events data (future)
OPENWEATHER_API_KEY=...               # Weather data (future)
```

See `requirements.txt` for Python dependencies.

---

## 📈 Roadmap

### ✅ Phase 1 - Backend API with mock patterns (BEFORE - done)

**Goal:** Ship a first end-to-end agent that can generate contextual staffing predictions from mock patterns.

Delivered:
- Multi-agent system (Demand Predictor, Staff Recommender, Reasoning Engine)
- Context-aware mock data generation (events, weather, holidays)
- Confidence scoring + explainable reasoning
- Integration test suite (7 scenarios)
- HuggingFace Spaces deployment

Timeline status:  
- **Before** → This phase moved the project from idea to a working backend with realistic mocked scenarios.

---

### ✅ Phase 2 - RAG Implementation with real patterns (BEFORE - done)

**Goal:** Replace mock patterns with real F&B behaviour extracted from hotel booking data.

Delivered:
- Kaggle Hotel Booking dataset processed (119K reservations → 495 F&B patterns)
- Qdrant vector database seeded with Mistral embeddings (1024 dim)
- Semantic similarity search powering predictions
- Validation tests passing on 4/4 core scenarios
- Live API deployed with real vector search

Technical details:
- Patterns derived from meal plans, day types, seasons, booking behaviour
- Cosine similarity scoring (typically 0.92–0.95)
- Safe fallback to mock data if Qdrant is unavailable

Timeline status:  
- **Before** → The agent now relies on real historical patterns instead of hard-coded mocks.

---

### 🔁 Phase 3 - Productisation & Observability (NOW)

**Goal:** Move from “cool API demo” to something that looks and behaves like a product F&B managers could trust.

Currently working on:
- Clarifying the F&B value story:
  - reframing outputs in business terms (labor hours, margin, guest experience)
- Designing the **manager-in-the-loop** workflow:
  - how managers approve, override, or comment on predictions
- Defining accuracy & impact metrics:
  - prediction vs actual covers
  - implications on staffing decisions
- Improving observability:
  - logging of predictions and explanations
  - tracking which historical patterns are retrieved for each decision

Timeline status:  
- **Now** → Focus is on credibility and usability for real hotel teams.

---

### 📋 Phase 4 - Dashboard & PMS Integrations (NEXT)

**Goal:** Build the first end-to-end experience that a hotel team could use day-to-day.

Planned next steps:
- Dashboard UI (Streamlit or Next.js) to:
  - visualize predictions vs actuals
  - inspect confidence scores and retrieved patterns
- Manager workflows:
  - approve / override staffing recommendations
  - log edits as feedback for the agent
- PMS-ready data model:
  - align entities with API-first systems like Mews and Apaleo
  - first experiments pulling real occupancy / reservations via PMS APIs
- Multi-property support for hotel groups

Timeline status:  
- **Next** → From infrastructure + API to a usable F&B operations tool.

---

### 🔮 Phase 5 - Agentic Operations Copilot (LATER)

**Goal:** Turn the F&B forecasting agent into a broader operations copilot for hospitality.

Longer-term ideas:
- Conversational interface (text + voice):
  - “What staffing do you recommend for Saturday dinner if the weather turns bad?”
  - “Show me services where we were overstaffed vs actual covers.”
- Proactive behaviour:
  - alerts for future under/over-staffed services vs historical norms
  - suggestions to adjust staffing or opening hours
- Extensions beyond F&B:
  - housekeeping workload forecasting
  - front desk peak prediction
  - simple, explainable agent workflows built on top of PMS APIs

Timeline status:  
- **Later** → Expanding a focused F&B agent into a general hospitality operations copilot.

---

## 📂 Project Structure

```
fb-agent/
├── backend/
│   ├── agents/              # Multi-agent system
│   │   ├── coordinator.py   # Request routing
│   │   ├── demand_predictor.py  # Qdrant vector search + prediction
│   │   ├── staff_recommender.py
│   │   └── reasoning_engine.py
│   ├── models/              # Pydantic schemas
│   ├── scripts/             # Data processing
│   │   ├── derive_covers.py     # Kaggle → F&B patterns
│   │   ├── seed_qdrant.py       # Patterns → Qdrant embeddings
│   │   └── create_qdrant_index.py
│   ├── data/
│   │   ├── raw/             # Source datasets
│   │   └── processed/       # Generated patterns (495)
│   ├── tests/               # Validation tests
│   │   └── test_rag_validation.py
│   ├── utils/               # Helpers (logging, config)
│   └── api.py               # FastAPI app
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PHASE_1_LIMITATIONS.md
│   └── Problem_Statement.md
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 💼 Portfolio Note

This is a **portfolio project** developed to demonstrate:
- Product management thinking (problem framing, MVP scoping, roadmap planning)
- Technical execution (RAG architecture, multi-agent systems, API design)
- Industry research (reports, hospitality AI trends, PMS integration strategies)
- End-to-end ownership (market research → architecture → deployment)

**Target role:** Product Manager - Builder. Happy to talk!

**Full case study:** [ivandemurard.com](https://ivandemurard.com)

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Ivan de Murard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📬 Contact

**Ivan de Murard**  
Zero-to-One Product Manager

- 🌐 Portfolio: [ivandemurard.com](https://ivandemurard.com)
- 💼 LinkedIn: [linkedin.com/in/ivandemurard](https://linkedin.com/in/ivandemurard)
- 📧 Email: ivandemurard@gmail.com

---

**Built with ❤️ for the hospitality industry**
