```markdown
# Aetherix – F&B Ambient Agent  
**PMS-agnostic intelligence layer to anticipate staffing & F&B needs in hotels**

> The AI that comes to you (WhatsApp, Slack, Teams) instead of yet another dashboard to check.  
> Contextual predictions + feedback loop + explainability, no vendor lock-in.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live-orange?logo=streamlit)](https://aetherix.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![HF Spaces](https://img.shields.io/badge/HuggingFace-Spaces-blueviolet)](https://huggingface.co/spaces/ivandemurard/fb-agent-api)

**Live Dashboard (Phase 3 MVP)** → https://aetherix.streamlit.app/

### Real Problem (Hospitality 2026)
Restaurant managers spend **5–8 hours/week** on manual forecasting with ~**70%** accuracy → over/under-staffing, food waste, operational stress.

### Solution: Ambient AI Colleague
An agent that:
- **Anticipates** demand (covers, staffing, purchases) using RAG + external signals (weather, events, holidays)
- **Explains** its predictions (impact %, confidence score)
- **Learns** from your corrections (feedback loop → accuracy improves over time)
- **Delivers where you work**: WhatsApp/Slack for daily briefs, dashboard for config & deep dive
- **PMS-agnostic**: semantic layer connects Mews, Opera, Apaleo, Cloudbeds, etc. without lock-in

| Classic Dashboard            | Ambient Agent (Aetherix)              |
|------------------------------|----------------------------------------|
| You have to remember to check| Agent proactively sends you the brief |
| Painful context switching    | Integrated into your daily tools       |
| Feedback = separate step     | Natural correction in conversation     |
| PMS + external data silos    | Semantic unification + contextual RAG  |

### Quick Look at the Current Interface (Phase 3 – MVP Dashboard)
<!-- Replace these placeholders with real screenshots/GIFs when ready – huge impact -->

![Restaurant Configuration](https://via.placeholder.com/800x450/1e3a8a/ffffff?text=Config+Restaurant+Profile+%7C+Streamlit+MVP)  
*Configuration screen: restaurant profile, historical ratios, simulated PMS sources*

![Daily Prediction + Explanation](https://via.placeholder.com/800x450/065f46/ffffff?text=Tomorrow's+Covers+Prediction+%7C+Claude+Explainability)  
*Explained prediction example: weather impact +30%, events +18%, confidence 82%*

![Feedback Loop](https://via.placeholder.com/800x450/ca8a04/ffffff?text=Feedback+Loop+%7C+Actual+vs+Predicted)  
*Real covers input + notes → continuous learning*

### Architecture (3 Layers)

```mermaid
flowchart TD
    A[F&B Ambient Agent] --> B[Intelligence Layer<br>RAG + Reasoning]
    A --> C[Semantic Layer<br>PMS-Agnostic]
    A --> D[Delivery Layer<br>Ambient]

    subgraph Intelligence
        B --> E[• Demand Predictor<br>Qdrant vector search + Mistral embeds]
        B --> F[• Claude Sonnet 4<br>Explanations & confidence scoring]
        B --> G[• Feedback loop<br>continuous pattern fine-tuning]
    end

    subgraph Semantic
        C --> H[• Unified model across all PMS]
        C --> I[• Adapters<br>Mews, Opera, Cloudbeds…]
        C --> J[• External signals<br>PredictHQ, OpenWeather…]
    end

    subgraph Delivery
        D --> K[• Streamlit Dashboard<br>config & analytics]
        D --> L[• WhatsApp / Slack / Teams<br>alerts & dialogue]
    end

    style Intelligence fill:#1e3a8a,stroke:#333,stroke-width:2px,color:#fff
    style Semantic fill:#065f46,stroke:#333,stroke-width:2px,color:#fff
    style Delivery fill:#ca8a04,stroke:#333,stroke-width:2px,color:#fff

Tech Stack (2026-ready)Backend: FastAPI · Python 3.11
AI: Claude Sonnet 4 (Anthropic) · Mistral Embeddings
Vector DB: Qdrant Cloud (495 patterns indexed)
Storage: Supabase (PostgreSQL) · Redis (cache & sessions)
Frontend MVP: Streamlit · (Next.js planned for v2)
Deploy: Hugging Face Spaces (Docker)

Early Results (Phase 3 – synthetic/mock data)Initial accuracy (naive baseline): ~68–72%
With RAG + feedback loop (3 iterations): +7–12% (MAPE down to ~18–22% on tests)
Simulated time saved: ~4–6 hours/week per restaurant
Vector search latency: < 300 ms (Qdrant + Mistral)

Roadmap Phase 1: Backend API + agents (Q3 2025)
 Phase 2: RAG + 495 patterns (Q4 2025)
 Phase 3: Dashboard + feedback loop (ongoing – Streamlit live)
□ Phase 4: Semantic layer + real PMS (Mews first)
□ Phase 5: Full ambient (proactive WhatsApp, voice)

Try It NowInteractive Dashboard → https://aetherix.streamlit.app/
API + Swagger docs → https://ivandemurard-fb-agent-api.hf.space/docs
Feedback / beta testing → DM me on X @ivandemurard
 or book a call: https://cal.com/ivandemurard/30min

Looking for: beta hotels (even mock data), feedback on ambient UX, PMS integration ideas, product/tech roles in hospitality SaaS.Built with  for hospitality operations – Ivan de Murard
Portfolio · X
 · LinkedIn · ivandemurard@gmail.comMIT License

