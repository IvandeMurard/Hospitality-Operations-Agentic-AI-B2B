# F&B Operations Agent – MVP

**Portfolio case study to gain AI product management and agentic design expertise**

## 📊 Problem

1. Hotel & restaurant teams spend **5–8h/week** building staffing plans with **limited forecast accuracy**, instead of focusing on guests and operations.  
2. Core systems (PMS, RMS, POS, WFM) are rarely well integrated, so revenue forecasts and staffing/inventory decisions live in silos rather than feeding each other.  

## 🎯 Project Vision

Build an AI **decision engine** for hotel F&B operations that:

- Connects to existing systems (PMS, RMS, POS, WFM) instead of replacing them  
- Predicts demand (covers, sales, activity) using:
  - External context: events, weather, holidays, ...,
  - Historical patterns: vector search with Qdrant  
  - Internal hotel data: PMS occupancy, bookings, POS data (Phase 2)  
- Generates **staffing & F&B recommendations** that can be pushed into existing workforce management tools (e.g. HotSchedules)  
- Uses LLM reasoning to provide **explainable predictions and “what-if” scenarios** for managers  
- Exposes a **conversational agent** interface rather than “yet another dashboard”, with:
  - Minimal UI for traceability, audit, and multi-site monitoring  
  - On-demand views only when managers need to inspect or challenge the reasoning  

Core principle: **Augmented hospitality** – AI handles forecasting, data stitching, and suggestions; managers keep control, make the final call, and focus on high-value human interactions with guests and teams.

---

## 📋 Project Roadmap

**Current priorities and strategic direction:** [ROADMAP_NOW_NEXT_LATER.md](docs/ROADMAP_NOW_NEXT_LATER.md)

Updated weekly (Monday 9am) based on:
- Industry intelligence (Perplexity veille)
- Sprint progress and blockers
- Strategic pivots and learnings
- Meetings

**Quick status:**
- 🔥 **NOW:** Fix contextual patterns bug (IVA-29) - Critical blocker
- ⏭️ **NEXT:** Complete MVP (Staff Recommender, tests, deploy, docs)
- 📅 **LATER:** Phase 2 integrations (PMS, real APIs, Qdrant search)

---

## 🏗️ Architecture

**Phase 1 MVP (Current):**

```
FastAPI Backend
├── Agents
│   ├── DemandPredictorAgent (pattern matching, weighted average)
│   ├── ReasoningEngine (Claude AI explanations)
│   └── StaffRecommender (adaptive calculations) - TODO
├── Models (Pydantic schemas)
├── Utils (Claude client, Qdrant client)
└── Main (POST /predict endpoint)
```

**Tech Stack:**
- **Backend:** Python 3.13, FastAPI, Uvicorn
- **AI:** Claude Sonnet 4.1 (reasoning), Qdrant (vector DB)
- **Data:** Mock patterns (Phase 1), Real patterns (Phase 2)
- **Deploy:** Render.com (planned)

---

## 📊 Current Features (Phase 1 - 64% Complete)

### ✅ Working Features

- **Smart Prediction Engine**
  - Weighted average from 3 similar historical patterns
  - 91% average confidence scores
  - Covers range: 120-165 typical

- **Rich Context Analysis**
  - Events: Concerts, sports, conferences, theater
  - Weather: Temperature, precipitation, wind (seasonal variation)
  - Holidays: Major holidays detected and adjusted
  - Day types: Weekend vs weekday vs Friday

- **Claude-Powered Reasoning**
  - Natural language explanations
  - Context-specific confidence factors
  - No generic fallbacks

- **Staff Recommendations**
  - Servers, hosts, kitchen staff
  - Delta vs usual staffing levels
  - *Note: Phase 1 = hardcoded, Phase 2 = adaptive*

### ⚠️ Known Limitations

**Critical Issues (Phase 1):**
- ❌ Patterns always static
- ❌ Predictions lack context variation
- ❌ Christmas treated as regular day
- ❌ No PMS integration (missing 40% prediction accuracy)

---

## 🔮 What's Next (Phase 2-3)

**Phase 2 - Real Integrations + UI Features (Feb 2026)**

**Backlog - Advanced Features:**
- Continuous learning + prediction accuracy tracking
- No-show risk prediction
- NLU intent recognition
- Semantic layer (PMS-agnostic)

---

## 📚 Documentation

**Phase 0 (Strategic Foundation):**
- [Problem Statement](docs/Problem_Statement.md)
- [MVP Scope](docs/MVP_SCOPE.md)
- [Cost Model](docs/Cost_Model.md)
- [Architecture](docs/ARCHITECTURE.md) (12K+ words)
- [Phase 0 Review](docs/PHASE_0_REVIEW.md)

**Phase 1 (Backend API):**
- [API Examples](docs/API_EXAMPLES.md)
- [Development Notes](docs/DEVELOPMENT_NOTES.md)
- [Roadmap](docs/ROADMAP_NOW_NEXT_LATER.md) (updated weekly)

**Deployment:**
- [Deployment Guide](docs/DEPLOYMENT.md) (to create)

---

## 💡 Strategic Context

**Target Audience:** Mews Product Manager role application

**Key Differentiators:**
1. **Domain Expertise:** Former restaurant server (understands operations)
2. **Architecture:** Agentic-first approach (vs API-first competitors)
3. **Explainability:** Transparent reasoning (EU AI Act compliant)
4. **Focus:** Operations-driven (not just analytics dashboards)

**Why This Project?**
- Hospitality = 
- Agentic AI = emerging paradigm (first-mover advantage)
- Operations focus = real manager pain (not toy project)

---

## 📈 Metrics & Progress

**Phase 0 (Complete - Dec 2025):**
- Time: 10.5h
- Output: 6 documents, 4 Figma screens, ~25K words
- Validation: Problem validated, Cost model defined

**Phase 1 (64% Complete - Jan 2026):**
- Time: 4.5h (Hours 1-2 complete)
- Output: Backend API, Claude integration, 400+ LOC
- Progress: 7/11 issues done
- **Blocker:** IVA-29 (contextual patterns bug)

**Milestones:**
- ✅ Dec 15: Phase 0 complete (GO decision)
- ✅ Jan 7: Backend setup + Claude reasoning working
- 🎯 Jan 12: Critical bug resolved (IVA-29)
- 🎯 Jan 19: Staff Recommender complete
- 🎯 Jan 31: Phase 1 MVP deployed + documented

---

## 🔗 Links

**Linear Project:** https://linear.app/ivanportfolio/project/fandb-agent-640279ce7d36

**GitHub Repo:** https://github.com/IvandeMurard/fb-agent-mvp

**Figma Mockups:** [Link to Figma] (to add)

**Live Demo:** (Phase 1 deployment pending)

---

## 👤 Author

**Ivan de Murard**
- Portfolio: [ivandemurard.com](https://ivandemurard.com)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

**Last updated:** January 7, 2026  
**Status:** Phase 1 MVP in progress (64% complete)
