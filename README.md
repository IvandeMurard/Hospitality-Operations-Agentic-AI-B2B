[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Powered by](https://img.shields.io/badge/Powered%20by-Hospitality--Operations--Agentic--AI-blue.svg)](https://github.com/IvandeMurard/Hospitality-Operations-Agentic-AI)

Powered by [Hospitality-Operations-Agentic-AI](https://github.com/IvandeMurard/Hospitality-Operations-Agentic-AI) – MIT licensed

# F&B Operations Agent – MVP

**Portfolio case study to gain AI product management and agentic design expertise**

## 📊 Problem

1. Hotel & restaurant teams spend **5–8h/week** building staffing plans with **limited forecast accuracy**, instead of focusing on guests and operations.  
2. Core systems (PMS, RMS, POS, WFM) are rarely well connected, so revenue forecasts and staffing/inventory decisions live in silos rather than feeding each other.  

## 🎯 Project Vision

F&B Operations Agent (intelligence layer for staffing predictions):

- Connects to existing systems (PMS, RMS, POS, WFM). Glue, not replacement.
- Predicts demand (covers, sales, activity) using:
  - External context: events, weather, holidays, ...,
  - Historical patterns: vector search with Qdrant  
  - Internal hotel data: PMS occupancy, bookings, POS data (Phase 2)  
- Generates **staffing & F&B recommendations** that can be pushed into existing workforce management tools (e.g. HotSchedules)  
- Uses LLM reasoning to provide **explainable predictions** for managers  
- Exposes a **conversational agent**-first interface with:
  - Minimal UI for traceability and audit 
  - On-demand views only when managers need to inspect or challenge the reasoning

Core principle: **Augmented hospitality**. AI handles forecasting, data stitching, and suggestions; managers keep control, make the final call (human-in-the-loop), and can focus on high-value human interactions with guests and teams.

---

## 📋 Project Roadmap

Context updated weekly (Monday 9am) based on:
- Industry intelligence (Perplexity veille)
- Sprint progress made and blockers
- Strategic pivots and learnings
- Meetings and continous discovery

**Quick status:**
- 🔥 **NOW:** Fix contextual patterns bug (IVA-29) - Critical blocker
- ⏭️ **NEXT:** Finish MVP (Staff Recommender, tests, deploy, docs)
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
- **Roadmap:** Linear
- **Documentation:** Obsidian

---

## 📊 Current Features (Phase 1 - 64% Complete)

### ✅ Working Features

- **Smart Prediction Engine**
  - Weighted average from 3 similar historical patterns
  - 91% average confidence scores

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
- Semantic layer (the PMS-agnostic glue)

---

## 💡 Strategic Context

**Why This Project?**
- Hospitality = Former restaurant waiter, barman, barista, passion for the sector
- Agentic AI = emerging paradigm (first-mover advantage)
- Operations focus = real manager pain (not toy project)

---

## 🔗 Links

**Linear Project:** https://linear.app/ivanportfolio/project/fandb-agent-640279ce7d36

**GitHub Repo:** https://github.com/IvandeMurard/fb-agent-mvp

**Figma Mockups:** [Link to Figma] (to add)

**Live Demo:** **coming soon, keep in touch!**

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
