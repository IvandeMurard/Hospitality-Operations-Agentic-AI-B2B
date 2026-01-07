# F&B Operations Agent - Portfolio Case Study

AI agent predicting restaurant covers and recommending optimal staffing levels.

**Status:** Phase 1 MVP - 64% complete (7/11 issues)  
**Target:** Demo-ready backend API by January 31, 2026  
**Time invested:** 15 hours (Phase 0: 10.5h, Phase 1: 4.5h)

---

## 🎯 Project Vision

Predictive AI agent for hotel F&B operations that combines:
- **External context:** Events, weather, holidays
- **Historical patterns:** Vector search with Qdrant
- **Internal hotel data:** PMS occupancy (Phase 2)
- **Claude AI reasoning:** Explainable predictions

**Core principle:** *Augmented Hospitality* - AI handles mundane predictions, managers focus on high-value human interactions.

---

## 📋 Project Roadmap

**Current priorities and strategic direction:** [ROADMAP_NOW_NEXT_LATER.md](docs/ROADMAP_NOW_NEXT_LATER.md)

Updated weekly (Monday 9am) based on:
- Industry intelligence (Perplexity veille)
- Sprint progress and blockers
- Strategic pivots and learnings

**Quick status:**
- 🔥 **NOW:** Fix contextual patterns bug (IVA-29) - Critical blocker
- ⏭️ **NEXT:** Complete MVP (Staff Recommender, tests, deploy, docs)
- 📅 **LATER:** Phase 2 integrations (PMS, real APIs, Qdrant search)

---

## 🚀 Quick Start

### Backend API (Local Development)

```bash
# Clone repo
git clone https://github.com/IvandeMurard/fb-agent-mvp.git
cd fb-agent-mvp/backend

# Setup environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# Run server
python main.py
```

Server available at: http://localhost:8000

Interactive docs: http://localhost:8000/docs

---

## 📡 API Usage

### Make a prediction

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": "resto_123",
    "service_date": "2024-12-15",
    "service_type": "dinner"
  }'
```

### Response example

```json
{
  "prediction_id": "pred_abc123",
  "predicted_covers": 143,
  "confidence": 0.91,
  "reasoning": {
    "summary": "High confidence for Saturday dinner. Marketing Expo nearby (0.9km) and consistent weekend patterns suggest strong traffic.",
    "confidence_factors": [
      "Similar Saturday patterns",
      "Conference nearby (0.9km)",
      "Weather: Partly Cloudy"
    ]
  },
  "staff_recommendation": {
    "servers": {"recommended": 8, "usual": 7, "delta": 1},
    "hosts": {"recommended": 2, "usual": 2, "delta": 0},
    "kitchen": {"recommended": 3, "usual": 3, "delta": 0}
  }
}
```

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
- **AI:** Claude Haiku 3.5 (reasoning), Qdrant (vector DB)
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
- ❌ Patterns always static (Coldplay/U2 concerts hardcoded)
- ❌ Predictions always ~143 covers (no context variation)
- ❌ Christmas treated as regular day (should be 40-70 covers)
- ❌ No PMS integration (missing 40% prediction accuracy)

**See full limitations:** [PHASE_1_LIMITATIONS.md](docs/PHASE_1_LIMITATIONS.md) (to create)

**Why document honestly?**
Demonstrates PM critical thinking > marketing spin. Mews PM values transparency.

---

## 🔮 What's Next (Phase 2-3)

**Phase 2 - Real Integrations (Feb 2026):**
- PMS integration (Mews/Apaleo) - occupancy, events, guests
- Real APIs: PredictHQ (events), Weather
- Qdrant semantic pattern matching
- Restaurant-specific configurations

**Phase 2 - UI Features:**
- Manager approval workflows
- Voice input (evaluate based on industry research)
- Command palette
- ElevenLabs voice synthesis

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

**Portfolio Goal:**
Demonstrate AI PM capabilities through:
- Working prototype (technical execution)
- Comprehensive case study (strategic thinking)
- Critical analysis (honest assessment of limitations)

**Why This Project?**
- Hospitality = target industry (Mews, Apaleo)
- Agentic AI = emerging paradigm (first-mover advantage)
- Operations focus = real manager pain (not toy project)

---

## 📈 Metrics & Progress

**Phase 0 (Complete - Dec 2025):**
- Time: 10.5h
- Output: 6 documents, 4 Figma screens, ~25K words
- Validation: Problem validated, Cost model profitable (89% margin)

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
- Former restaurant server → AI Product Manager
- Background: Hospitality operations + AI/ML
- Target role: Product Manager @ Mews
- Portfolio: [ivandemurard.com](https://ivandemurard.com) (to create)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

**Last updated:** January 7, 2026  
**Status:** Phase 1 MVP in progress (64% complete)
