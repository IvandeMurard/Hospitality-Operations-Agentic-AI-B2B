# Aetherix 
**PMS-agnostic intelligence layer to predict operational staffing & F&B needs in hotels & restaurants**

> The AI that comes to you (WhatsApp, Slack, Teams) instead of yet another dashboard to check.  
> Contextual predictions + feedback loop + explainability, no vendor lock-in.
> Still provides a dashboard for transparency and in-depth exploration

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live-orange?logo=streamlit)](https://aetherix.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![HF Spaces](https://img.shields.io/badge/HuggingFace-Spaces-blueviolet)](https://huggingface.co/spaces/ivandemurard/fb-agent-api)

**Live Dashboard (Phase 3 Prototype)** → https://aetherix.streamlit.app/

### Problem
Restaurant managers spend **5–8 hours/week** on manual forecasting with ~**70%** accuracy → over/under-staffing, food waste, operational stress.

### Solution: (Ambient) AI Colleague
An agent that:
- **Anticipates** demand (covers, staffing, purchases) using RAG + external signals (weather, events, holidays, real-time social sentiment)
- **Explains** its predictions (impact %, confidence score)
- **Learns** from your corrections (feedback loop → accuracy improves over time)
- **Delivers where you work**: WhatsApp/Slack for daily briefs, dashboard for config & deep dive
- **PMS-agnostic**: semantic layer connects Mews, Opera, Apaleo, Cloudbeds, etc. without lock-in

| Classic Dashboard            | Ambient Agent (Aetherix)              |
|------------------------------|---------------------------------------|
| You have to remember to check| Agent proactively sends you the brief |
| Painful context switching    | Integrated into your daily tools      |
| Feedback = separate step     | Natural correction in conversation    |
| PMS + external data silos    | Semantic unification + contextual RAG |

### Quick Look at the Current Interface (Phase 3 – MVP Dashboard)
<!-- Replace these placeholders with your real screenshots as soon as possible – huge impact boost -->

![Restaurant Configuration Dashboard](https://via.placeholder.com/800x450/1e3a8a/ffffff?text=Restaurant+Config+Profile+%7C+Streamlit+MVP)  
*Configuration screen: restaurant profile, historical ratios, simulated PMS sources*

![Daily Prediction + Explanation](https://via.placeholder.com/800x450/065f46/ffffff?text=Tomorrow's+Covers+Prediction+%7C+Claude+Explainability)  
*Example of explained prediction: +30% weather impact, +18% events, 82% confidence*

![Post-Service Feedback Loop](https://via.placeholder.com/800x450/ca8a04/ffffff?text=Feedback+Loop+%7C+Actual+vs+Predicted)  
*Real covers input + notes → continuous learning loop*

### Architecture (3 Layers)

┌─────────────────────────────────────────────────────────────┐
│                  F&B AMBIENT AGENT                          │
├─────────────────────────────────────────────────────────────┤
│ INTELLIGENCE LAYER (RAG + Reasoning)                        │
│ • Demand Predictor (Qdrant vector search + Mistral embeds)  │
│ • Claude Sonnet 4 - Explanations & confidence scoring       │
│ • Feedback Loop → continuous pattern fine-tuning            │
├─────────────────────────────────────────────────────────────┤
│ SEMANTIC LAYER (PMS-Agnostic)                               │
│ • Unified model across all PMS used                         │
│ • Adapts (Mews, Opera, Cloudbeds…)                          │
│ • External signals (X, PredictHQ, OpenWeather…)             │
├─────────────────────────────────────────────────────────────┤
│ DELIVERY LAYER (Ambient)                                    │
│ • Streamlit Dashboard (config, analytics)                   │
│ • WhatsApp / Slack / Teams (alerts & dialogue)              │
└─────────────────────────────────────────────────────────────┘


### Tech Stack

- **Backend**: FastAPI · Python 3.11
- **AI**: Claude Sonnet 4 (Anthropic) · Mistral Embeddings
- **Vector DB**: Qdrant Cloud (495 patterns indexed)
- **Storage**: Supabase (PostgreSQL) · Redis (cache & sessions)
- **Frontend MVP**: Streamlit · (Next.js planned for V2)
- **Deploy**: Hugging Face Spaces (Docker)

### Early Results (Phase 3 – synthetic/mock data)

- Initial accuracy (naive baseline): ~68–72%
- With RAG + feedback loop (3 iterations): **+7–12%** (MAPE down to ~18–22% on tests)
- Simulated time saved: **~4–6 hours/week** per restaurant
- Vector search latency: < 300 ms (Qdrant + Mistral)

### Roadmap (Linear-style)

- ✅ Phase 1: Backend API + agents (Q3 2025)
- ✅ Phase 2: RAG + 495 patterns (Q4 2025)
- 🚧 Phase 3: Dashboard + feedback loop (ongoing, the Streamlit prototype is live - shipping very early!)
- □ Phase 4: Semantic layer + real PMS (Open to partnerships!)
- □ Phase 5: Full ambient delivery (proactive WhatsApp, voice, NLP)

### Try It Now

- **Interactive Dashboard** → https://aetherix.streamlit.app/
- **API + Swagger docs** → https://ivandemurard-fb-agent-api.hf.space/docs
- **Feedback / beta testing** → DM me on X @ivandemurard or book a call: https://cal.com/ivandemurard/30min

**Looking for**: Feedback!, partnerships, beta hotels (even with mock data), **a product role in hotel tech**.

Built with ❤️ by Ivan de Murard for hotels, restaurants, and those who love them
[Portfolio](https://ivandemurard.com) · [X](https://x.com/ivandemurard) · [LinkedIn](https://linkedin.com/in/ivandemurard) · [Book a Call](https://cal.com/ivandemurard/30min)

MIT License
