# 🍽️ F&B Operations Agent

AI-powered staffing forecasting for restaurant operations.

## 📊 Problem

Restaurant managers spend **5-8h/week** on staffing planning with **70% accuracy**. This agent delivers **85%+ accuracy** in **2h/week**.

## ✨ Features (MVP)

- 🎯 **Prediction Display**: Covers forecast + confidence + staff recommendations
- 🧠 **Reasoning**: Explainable AI with similar pattern matching
- ✅ **Approval Flow**: Human-in-the-loop (approve/reject/adjust)
- 🎤 **Voice Input**: Hands-free predictions (opt-in)
- ⚡ **Command Palette**: Keyboard-first UX (⌘K / Ctrl+K / ²)

## 🏗️ Tech Stack

**Frontend:**
- Next.js 14 + TypeScript
- shadcn/ui + Tailwind CSS
- Vercel (hosting)

**Backend:**
- FastAPI + Python 3.11
- Render.com (hosting)

**AI/ML:**
- Claude Sonnet 4 (Anthropic)
- Qdrant Cloud (vector DB)
- ElevenLabs (voice)

**Data:**
- Supabase (PostgreSQL)
- Redis (session state)

## 📈 Cost Model

- **MVP**: $5.30/restaurant/month
- **Scale (500 restos)**: $1.14/restaurant/month
- [Full cost model →](https://docs.google.com/spreadsheets/d/1K2AZVUdOeTxWzZQb5FaFIbh_nJXkuGvjTrcNk0Z_OPQ/edit?usp=sharing)

## 🚀 Status

🚧 **Phase 0: Strategic Preparation** (Day 1/4 complete)

- ✅ Problem Statement
- ✅ MVP Scope (5 features, 43h effort)
- ✅ Cost Model
- 📋 Figma mockups (next)
- 📋 Architecture doc (next)

## 📚 Documentation

- **[Problem Statement](docs/Problem_Statement.md)** - Staffing forecasting problem, persona, metrics
- **[MVP Scope](docs/MVP_SCOPE.md)** - 5 core features, 43h effort, IN/OUT scope
- **[Technical Architecture](docs/ARCHITECTURE.md)** - System design, APIs, integrations, scalability
- **[Cost Model](docs/Cost_Model.md)** - $6.65/month MVP, scale economics | [Google Sheet](https://docs.google.com/spreadsheets/d/1K2AZVUdOeTxWzZQb5FaFIbh_nJXkuGvjTrcNk0Z_OPQ/edit)
- **[Phase 0 Review](docs/PHASE_0_REVIEW.md)** - Validation checklist, Go/No-Go decision

## 👨‍💻 Author

**Ivan de Murard**  
[Portfolio](https://ivandemurard.lovable.app) • [LinkedIn](https://linkedin.com/in/ivandemurard)

---

**Built for Mews PM application** • Portfolio case study demonstrating AI product management & agentic experience design
