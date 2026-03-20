# scripts/tooling/streamlit/

Internal Streamlit admin dashboard and prompt engineering playground.

**Purpose:** Not a customer-facing product. Used for:
- Backend vector/similarity visualization
- Prompt testing and LLM response inspection
- Diagnostic flows and reasoning engine debugging
- R&D sandbox for new features before productionizing in `nextjs-frontend/`

## Run locally

```bash
cd scripts/tooling/streamlit
pip install -r requirements.txt
streamlit run app.py
```

The production customer dashboard lives in `nextjs-frontend/`.
