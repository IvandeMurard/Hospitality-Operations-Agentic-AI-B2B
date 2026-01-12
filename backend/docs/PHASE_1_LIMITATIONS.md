# Phase 1 Limitations

> Transparency document for demo and Phase 2 planning.
> Last updated: 2026-01-12

## 🎯 What Works

### Prediction Engine
- ✅ Contextual predictions (covers vary by day, weather, events)
- ✅ Holiday logic (Christmas ~40, NYE ~200 covers)
- ✅ Weather adjustments (-10/-20 covers for rain)
- ✅ Event boost (+15 covers per nearby event)
- ✅ Confidence scoring (85-95%)

### Staff Recommender (Partial)
- ✅ Calculation logic works (servers, hosts, kitchen)
- ✅ Configurable ratios
- ✅ Delta vs usual staffing
- ⚠️ **Limited value without internal context** (reservations, private events, historical data)

### Reasoning Engine
- ✅ Rich explanations via Claude API
- ✅ Patterns used in reasoning
- ✅ Contextual factors mentioned

### API & Infrastructure
- ✅ FastAPI with Pydantic validation
- ✅ Documented Swagger UI (/docs)
- ✅ Deployed on HuggingFace Spaces
- ✅ 7 passing integration tests

---

## ⚠️ Current Limitations

### 1. Mock Data

| Component | Phase 1 (current) | Phase 2 (target) |
|-----------|-------------------|------------------|
| Events | Randomly generated | PredictHQ API |
| Weather | Simulated by season | OpenWeather API |
| Occupancy | Not available | PMS (Mews/Apaleo) |
| History | Generated patterns | Qdrant vector search |

**Impact:** Credible predictions but not calibrated on real data.

### 2. No PMS Integration

- No hotel occupancy data
- No guest profiles (VIP, dietary)
- No internal events (conferences, weddings)

**Impact:** Agent cannot correlate F&B demand with hotel occupancy.

### 3. Patterns Not Persisted

- Patterns generated per request (deterministic seed)
- No Qdrant vector search (collection created but unused)
- No learning from past predictions

**Impact:** No "memory" of actual restaurant patterns.

### 4. Hardcoded Restaurant Config
```python
# Current (hardcoded)
covers_per_server = 18
usual_servers = 7

# Phase 2 (per restaurant)
SELECT ratios FROM restaurant_config WHERE id = ?
```

**Impact:** All restaurants use the same ratios.

### 5. HuggingFace Performance

- Cold start: ~30s after inactivity
- No Redis caching
- Single instance (no scaling)

**Impact:** First request slow, acceptable for demo.

### 6. Staff Recommender Not Context-Aware

Current state:
- Calculates staffing based on predicted covers only
- No access to reservations, private events, staff availability
- Uses generic ratios (not restaurant-specific)

**Impact:** Recommendations are mathematically correct but not operationally meaningful without real restaurant data.

**Phase 2 fix:** Integrate PMS reservation data + restaurant-specific configurations.

---

## 📋 Phase 2 Roadmap

| Priority | Feature | Effort | Impact |
|----------|---------|--------|--------|
| 🔴 Critical | Mews PMS integration | 2 weeks | Real occupancy data |
| 🔴 Critical | PredictHQ events API | 3 days | Real events |
| 🟡 High | Qdrant pattern matching | 1 week | Semantic search |
| 🟡 High | Restaurant configs (Supabase) | 3 days | Multi-tenant |
| 🟢 Medium | Weather API | 1 day | Real weather |
| 🟢 Medium | Redis caching | 2 days | Performance |

---

## 💡 PM Decisions Documented

### Why mock data in Phase 1?

> "Ship fast, validate architecture, iterate with real data."

Phase 1 goal was to validate:
1. Multi-agent architecture ✅
2. Prediction → reasoning → staffing pipeline ✅
3. Explainability (AI Act compliance) ✅

Real integrations require hotel design partners.

### Why HuggingFace vs Render?

- Render free tier limited (1 project)
- HuggingFace = AI/ML signal for Mews portfolio
- Cold start acceptable for demo

### Why no frontend in Phase 1?

> "Backend-first proves the intelligence layer works."

The differentiator is the agent, not the UI. Phase 2 will add a minimal dashboard.

---

## 🔗 Resources

- **Live API:** https://ivandemurard-fb-agent-api.hf.space/docs
- **GitHub:** [fb-agent-mvp](https://github.com/...)
- **Linear:** [F&B Agent Project](https://linear.app/ivanportfolio/project/fandb-agent)
