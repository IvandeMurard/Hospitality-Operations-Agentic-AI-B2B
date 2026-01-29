"""
F&B Operations Agent - Dashboard
Streamlit MVP for prediction visualization
"""

import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta, datetime
from concurrent.futures import ThreadPoolExecutor
import time
import plotly.graph_objects as go

# Configuration
API_URL = "https://ivandemurard-fb-agent-api.hf.space"

# Explanatory content (English)
EXPLAINER_CONTENT = {
    "how_it_works": """
### How does this prediction work?

**Data source:**
- 495 historical patterns derived from a hotel dataset (119K reservations, 2015-2017)
- Each pattern captures: day of week, weather, events, holidays, actual covers

**Method:**
1. Your request (date, service) is converted into a numerical "fingerprint" (embedding)
2. Search for the 5 most similar historical patterns (cosine similarity)
3. Weighted average of covers from these patterns = prediction
4. AI generates a natural language explanation

**Current limitations:**
- Derived data (not real hotel data)
- No PMS connection (simulated occupancy)
- Weather and events are simulated
    """,
    
    "reliability_explanation": """
**Estimated Reliability**

Based on MAPE (Mean Absolute Percentage Error) — measures the estimated average gap between prediction and reality.

| Score | Meaning | Recommendation |
|-------|---------|----------------|
| Excellent | < 15% variance | Plan normally |
| Acceptable | 15-25% variance | Consider ±10% buffer |
| Monitor | 25-40% variance | Plan for flexibility |
| Low reliability | > 40% variance | High variance expected |

*Note: Estimated from pattern variance, not backtested on real predictions.*
    """,
    
    "model_diagnostics": """
**Model Diagnostics**

Advanced metrics for technical users:

**Pattern Similarity (Confidence)**
- Measures how well historical patterns match your query context
- High similarity (>90%) = patterns found are very relevant
- Low similarity (<70%) = unusual context, fewer comparable patterns

**Drift Detection**
- If Confidence drops AND MAPE spikes → patterns may be outdated
- Triggers: Confidence < 60% combined with MAPE > 40%
    """
}

# Historical baseline (derived from patterns)
BASELINE_STATS = {
    "weekly_covers_range": (180, 320),
    "avg_daily_dinner": 35,
    "avg_daily_lunch": 22,
    "avg_daily_breakfast": 28,
    "patterns_count": 495,
    "data_period": "2015-2017"
}


def get_reliability_score(mape_value):
    """
    Calculate reliability score based on MAPE.
    Returns: (color, emoji, label, advice)
    """
    if mape_value is None:
        return ("gray", "", "Unknown", "Insufficient data for reliability estimate.")
    elif mape_value < 15:
        return ("green", "", "Excellent", "High reliability. Plan staffing normally.")
    elif mape_value < 25:
        return ("yellow", "", "Acceptable", "Good reliability. Consider a ±10% staffing buffer.")
    elif mape_value < 40:
        return ("orange", "", "Monitor", "Moderate variance. Plan for flexibility — have backup staff available.")
    else:
        return ("red", "", "Low reliability", f"High variance expected. Consider a wider staffing range.")

def get_prediction_interval_text(interval, predicted):
    """Format prediction interval for display"""
    if interval:
        low, high = interval
        return f"Expected range: {low} – {high} covers"
    return None

def detect_drift(confidence, mape):
    """
    Detect potential model drift based on combined metrics.
    Returns alert message or None.
    """
    if confidence is None or mape is None:
        return None
    if confidence < 0.60 and mape > 40:
        return "Potential drift detected — patterns may be outdated or context is highly unusual. Manual review recommended."
    elif confidence < 0.70 and mape > 50:
        return "Model uncertainty high — consider manual validation for this prediction."
    return None


def fetch_prediction(params: dict) -> dict:
    """Fetch a single prediction from API"""
    try:
        response = requests.post(
            f"{API_URL}/predict",
            json=params,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        data["_params"] = params  # Keep track of request params
        data["_error"] = None
        return data
    except Exception as e:
        return {
            "_params": params,
            "_error": str(e),
            "predicted_covers": None,
            "confidence": None
        }


def fetch_week_predictions(start_date: date, service_types: list, restaurant_id: str) -> list:
    """Fetch predictions for a week (7 days × service types)"""
    requests_list = []
    
    for day_offset in range(7):
        current_date = start_date + timedelta(days=day_offset)
        for service in service_types:
            requests_list.append({
                "restaurant_id": restaurant_id,
                "service_date": current_date.isoformat(),
                "service_type": service
            })
    
    # Parallel fetch (max 5 concurrent)
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch_prediction, requests_list))
    
    return results


st.set_page_config(
    page_title="F&B Operations Agent",
    page_icon=None,
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .prediction-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
    }
    .metric-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
    }
    .confidence-high { color: #28a745; }
    .confidence-medium { color: #ffc107; }
    .confidence-low { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# Header
st.title("F&B Operations Agent")
st.markdown("*AI-powered demand forecasting for hotel restaurants*")

# How it works (collapsible)
with st.expander("How it works", expanded=False):
    st.markdown(EXPLAINER_CONTENT["how_it_works"])
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("Historical patterns", BASELINE_STATS["patterns_count"])
    with col_stat2:
        st.metric("Data period", BASELINE_STATS["data_period"])
    with col_stat3:
        st.metric("Avg dinner/day", f"{BASELINE_STATS['avg_daily_dinner']} covers")

st.divider()

# Data timestamp
st.caption(f"📡 Data as of {datetime.now().strftime('%B %d, %Y at %H:%M')} | Patterns: {BASELINE_STATS['patterns_count']} | Period: {BASELINE_STATS['data_period']}")

# Sidebar - Input
with st.sidebar:
    st.header("Prediction Parameters")
    
    # View mode toggle
    view_mode = st.radio(
        "View Mode",
        options=["single", "weekly"],
        format_func=lambda x: "Single Day" if x == "single" else "Weekly Overview",
        horizontal=True
    )
    
    st.divider()
    
    if view_mode == "single":
        service_date = st.date_input(
            "Service Date",
            value=date.today() + timedelta(days=1),
            min_value=date.today(),
            max_value=date.today() + timedelta(days=90)
        )
        
        service_type = st.selectbox(
            "Service Type",
            options=["breakfast", "lunch", "dinner"],
            index=2  # Default: dinner
        )
        service_types = [service_type]
    else:
        # Weekly mode
        week_start = st.date_input(
            "Week Starting",
            value=date.today(),
            min_value=date.today(),
            max_value=date.today() + timedelta(days=90)
        )
        service_date = week_start
        
        service_types = st.multiselect(
            "Service Types",
            options=["breakfast", "lunch", "dinner"],
            default=["dinner"]
        )
        
        if not service_types:
            st.warning("Select at least one service type")
    
    restaurant_id = st.text_input(
        "Restaurant ID",
        value="hotel_main",
        help="Identifier for your restaurant"
    )
    
    button_label = "Get Prediction" if view_mode == "single" else "Get Week Forecast"
    predict_button = st.button(button_label, type="primary", use_container_width=True)

# Main content
if predict_button:
    if view_mode == "single":
        # === SINGLE DAY VIEW ===
        with st.spinner("Analyzing patterns..."):
            try:
                response = requests.post(
                    f"{API_URL}/predict",
                    json={
                        "restaurant_id": restaurant_id,
                        "service_date": service_date.isoformat(),
                        "service_type": service_type
                    },
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                predicted_covers = data.get("predicted_covers", 0)
                confidence = data.get("confidence", 0)
                reasoning = data.get("reasoning", {})
                staff = data.get("staff_recommendation", {})
                accuracy = data.get("accuracy_metrics", {})
                
                mape = accuracy.get("estimated_mape")
                interval = accuracy.get("prediction_interval")
                
                # Get reliability score
                rel_color, rel_emoji, rel_label, rel_advice = get_reliability_score(mape)
                
                # Check for drift
                drift_alert = detect_drift(confidence, mape)
                
                # Display drift alert if detected
                if drift_alert:
                    st.warning(drift_alert)
                
                # Main layout
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader(f"{service_date.strftime('%A, %B %d')} - {service_type.capitalize()}")
                    
                    # Primary metrics row
                    metric_col1, metric_col2 = st.columns(2)
                    
                    with metric_col1:
                        # Predicted covers with baseline comparison
                        baseline = BASELINE_STATS[f"avg_daily_{service_type}"]
                        delta = predicted_covers - baseline
                        st.metric(
                            label="Predicted Covers",
                            value=f"{predicted_covers}",
                            delta=f"{delta:+.0f} vs baseline ({baseline})",
                            help=f"Historical baseline for {service_type}: {baseline} covers/day"
                        )
                        
                        # Prediction interval (primary actionable info)
                        if interval:
                            st.info(f"**Expected range: {interval[0]} – {interval[1]} covers**")
                    
                    with metric_col2:
                        # Reliability score (single metric replacing Confidence + MAPE)
                        st.markdown(f"**Estimated Reliability**")
                        st.markdown(f"### {rel_emoji} {rel_label}")
                        if mape:
                            st.caption(f"±{mape:.0f}% variance")
                    
                    # Operational advice
                    st.success(f"**Recommendation:** {rel_advice}")
                    
                    st.divider()
                    
                    # Staff Recommendation
                    st.subheader("Staff Recommendation")
                    
                    if staff and staff.get("recommended_staff"):
                        rec_staff = staff.get("recommended_staff", {})
                        staff_cols = st.columns(4)
                        
                        with staff_cols[0]:
                            st.metric("Servers", rec_staff.get("servers", 0))
                        with staff_cols[1]:
                            st.metric("Hosts", rec_staff.get("hosts", 0))
                        with staff_cols[2]:
                            st.metric("Bussers", rec_staff.get("bussers", 0))
                        with staff_cols[3]:
                            st.metric("Kitchen", rec_staff.get("kitchen", 0))
                        
                        # Staff recommendation summary
                        if staff.get("recommendation"):
                            st.caption(f"{staff.get('recommendation')}")
                    elif staff:
                        # Fallback for old structure
                        servers_data = staff.get("servers", {})
                        hosts_data = staff.get("hosts", {})
                        kitchen_data = staff.get("kitchen", {})
                        
                        staff_cols = st.columns(4)
                        
                        with staff_cols[0]:
                            rec_servers = servers_data.get("recommended", 0) if isinstance(servers_data, dict) else 0
                            st.metric("Servers", rec_servers)
                        with staff_cols[1]:
                            rec_hosts = hosts_data.get("recommended", 0) if isinstance(hosts_data, dict) else 0
                            st.metric("Hosts", rec_hosts)
                        with staff_cols[2]:
                            st.metric("Bussers", 0)
                        with staff_cols[3]:
                            rec_kitchen = kitchen_data.get("recommended", 0) if isinstance(kitchen_data, dict) else 0
                            st.metric("Kitchen", rec_kitchen)
                        
                        if staff.get("rationale"):
                            st.caption(f"{staff.get('rationale')}")
                
                with col2:
                    # Reliability gauge (based on MAPE, inverted so higher = better)
                    reliability_value = max(0, 100 - (mape if mape else 50))
                    
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=reliability_value,
                        number={'suffix': '%'},
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Reliability"},
                        gauge={
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "#667eea"},
                            'steps': [
                                {'range': [0, 60], 'color': "#ffcccc"},
                                {'range': [60, 75], 'color': "#fff3cd"},
                                {'range': [75, 85], 'color': "#d4f5d4"},
                                {'range': [85, 100], 'color': "#28a745"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 2},
                                'thickness': 0.75,
                                'value': 75
                            }
                        }
                    ))
                    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                
                # Expandable sections
                with st.expander("Understand this prediction", expanded=False):
                    st.markdown(EXPLAINER_CONTENT["reliability_explanation"])
                
                with st.expander("🔧 Model Diagnostics", expanded=False):
                    st.markdown(EXPLAINER_CONTENT["model_diagnostics"])
                    
                    diag_col1, diag_col2, diag_col3 = st.columns(3)
                    with diag_col1:
                        st.metric("MAPE (estimated)", f"{mape:.1f}%" if mape else "N/A")
                    with diag_col2:
                        st.metric("Pattern Similarity", f"{confidence:.0%}" if confidence else "N/A")
                    with diag_col3:
                        st.metric("Patterns Analyzed", accuracy.get("patterns_analyzed", "N/A"))
                    
                    # Drift status
                    if drift_alert:
                        st.error(drift_alert)
                    else:
                        st.success("✅ No drift detected — model operating normally")
                
                with st.expander("AI Reasoning", expanded=False):
                    explanation = reasoning.get("explanation", "") or reasoning.get("summary", "No explanation available")
                    st.markdown(f"**Analysis:** {explanation}")
                    
                    # Handle both similar_patterns and patterns_used
                    patterns = reasoning.get("similar_patterns", []) or reasoning.get("patterns_used", [])
                    if patterns:
                        st.markdown("**Similar Historical Patterns:**")
                        for i, pattern in enumerate(patterns[:3], 1):
                            if isinstance(pattern, dict):
                                p_date = pattern.get("date", "Unknown")
                                p_covers = pattern.get("actual_covers", "?")
                                p_sim = pattern.get("similarity", 0)
                                st.markdown(f"{i}. {p_date} — {p_covers} covers (similarity: {p_sim:.0%})")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"API Error: {str(e)}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    else:
        # === WEEKLY VIEW ===
        if not service_types:
            st.error("Please select at least one service type")
        else:
            with st.spinner(f"Fetching predictions for 7 days × {len(service_types)} services..."):
                results = fetch_week_predictions(service_date, service_types, restaurant_id)
            
            # Process results into DataFrame
            rows = []
            for r in results:
                params = r.get("_params", {})
                mape = r.get("accuracy_metrics", {}).get("estimated_mape") if r.get("accuracy_metrics") else None
                conf = r.get("confidence")
                
                # Get reliability
                rel_color, rel_emoji, rel_label, _ = get_reliability_score(mape)
                
                rows.append({
                    "Date": params.get("service_date"),
                    "Day": pd.to_datetime(params.get("service_date")).strftime("%a") if params.get("service_date") else "",
                    "Service": params.get("service_type", "").capitalize(),
                    "Covers": r.get("predicted_covers"),
                    "Reliability": f"{rel_emoji} {rel_label}" if mape else "N/A",
                    "Range": f"{r.get('accuracy_metrics', {}).get('prediction_interval', ['-', '-'])[0]}-{r.get('accuracy_metrics', {}).get('prediction_interval', ['-', '-'])[1]}" if r.get("accuracy_metrics", {}).get("prediction_interval") else "N/A",
                    "MAPE": mape,
                    "Confidence": conf,
                    "Error": r.get("_error")
                })
            
            df = pd.DataFrame(rows)
            
            # Header
            st.subheader(f"Week of {service_date.strftime('%B %d, %Y')}")
            
            valid_data = df[df["Covers"].notna()]
            
            if not valid_data.empty:
                total_covers = valid_data['Covers'].sum()
                baseline_low, baseline_high = BASELINE_STATS["weekly_covers_range"]
                
                # Context banner
                if total_covers < baseline_low:
                    st.info(f"Quiet week expected ({total_covers:.0f} covers vs baseline {baseline_low}-{baseline_high})")
                elif total_covers > baseline_high:
                    st.success(f"Busy week expected ({total_covers:.0f} covers vs baseline {baseline_low}-{baseline_high})")
                else:
                    st.info(f"Standard week ({total_covers:.0f} covers, baseline {baseline_low}-{baseline_high})")
                
                # Check for any drift alerts
                drift_days = []
                for _, row in valid_data.iterrows():
                    drift = detect_drift(row.get("Confidence"), row.get("MAPE"))
                    if drift:
                        drift_days.append(f"{row['Day']} {row['Service']}")
                
                if drift_days:
                    st.warning(f"Model uncertainty detected for: {', '.join(drift_days)}. Review these predictions manually.")
                
                # Summary metrics
                summary_cols = st.columns(4)
                
                with summary_cols[0]:
                    delta_vs_baseline = total_covers - ((baseline_low + baseline_high) / 2)
                    st.metric(
                        "Total Covers", 
                        f"{total_covers:.0f}",
                        delta=f"{delta_vs_baseline:+.0f} vs avg.",
                        help=f"Weekly baseline: {baseline_low}-{baseline_high} covers"
                    )
                with summary_cols[1]:
                    st.metric("Avg per Service", f"{valid_data['Covers'].mean():.0f}")
                with summary_cols[2]:
                    st.metric("Peak", f"{valid_data['Covers'].max():.0f}")
                with summary_cols[3]:
                    # Average reliability (inverse of MAPE)
                    avg_mape = valid_data['MAPE'].mean() if 'MAPE' in valid_data else None
                    if avg_mape:
                        avg_reliability = max(0, 100 - avg_mape)
                        st.metric("Avg Reliability", f"{avg_reliability:.0f}%")
                    else:
                        st.metric("Avg Reliability", "N/A")
                
                st.divider()
                
                # Chart
                st.subheader("Weekly Demand Overview")
                
                if len(service_types) > 1:
                    # Heatmap for multiple services
                    pivot_df = valid_data.pivot(index="Service", columns="Day", values="Covers")
                    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                    pivot_df = pivot_df.reindex(columns=[d for d in day_order if d in pivot_df.columns])
                    
                    fig = go.Figure(data=go.Heatmap(
                        z=pivot_df.values,
                        x=pivot_df.columns,
                        y=pivot_df.index,
                        colorscale="Blues",
                        text=pivot_df.values,
                        texttemplate="%{text:.0f}",
                        textfont={"size": 14},
                        hovertemplate="Day: %{x}<br>Service: %{y}<br>Covers: %{z}<extra></extra>"
                    ))
                    fig.update_layout(
                        height=200 + (len(service_types) * 50),
                        margin=dict(l=20, r=20, t=20, b=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    # Bar chart for single service
                    fig = go.Figure(data=go.Bar(
                        x=valid_data["Day"],
                        y=valid_data["Covers"],
                        marker_color="#667eea",
                        text=valid_data["Covers"],
                        textposition="outside"
                    ))
                    fig.update_layout(
                        height=300,
                        xaxis_title="Day",
                        yaxis_title="Predicted Covers",
                        margin=dict(l=20, r=20, t=20, b=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                st.divider()
                
                # Detailed table
                st.subheader("Detailed Predictions")
                
                # Prepare display dataframe with better column names
                display_df = valid_data[["Date", "Day", "Service", "Covers", "Range", "Reliability"]].copy()
                display_df = display_df.rename(columns={"Range": "Expected Range"})
                display_df["Covers"] = display_df["Covers"].apply(lambda x: f"{x:.0f}" if pd.notna(x) else "Error")
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Date": st.column_config.TextColumn("Date", help="Service date"),
                        "Day": st.column_config.TextColumn("Day", help="Day of week"),
                        "Service": st.column_config.TextColumn("Service", help="Meal service type"),
                        "Covers": st.column_config.NumberColumn("Covers", help="Predicted number of customers"),
                        "Expected Range": st.column_config.TextColumn("Expected Range", help="Min-max covers based on similar historical patterns"),
                        "Reliability": st.column_config.TextColumn("Reliability", help="Prediction reliability based on MAPE: 🟢 <15% | 🟡 15-25% | 🟠 25-40% | 🔴 >40%")
                    }
                )
                
                # Legend
                st.caption("**Reliability:** Excellent (<15%) | Acceptable (15-25%) | Monitor (25-40%) | Low (>40%)")
                
                # Model diagnostics
                with st.expander("Understand predictions", expanded=False):
                    st.markdown(EXPLAINER_CONTENT["reliability_explanation"])
                
                with st.expander("🔧 Model Diagnostics", expanded=False):
                    st.markdown(EXPLAINER_CONTENT["model_diagnostics"])
                    
                    # Show technical metrics table
                    tech_df = valid_data[["Date", "Day", "Service", "MAPE", "Confidence"]].copy()
                    tech_df["MAPE"] = tech_df["MAPE"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
                    tech_df["Confidence"] = tech_df["Confidence"].apply(lambda x: f"{x:.0%}" if pd.notna(x) else "N/A")
                    st.dataframe(tech_df, use_container_width=True, hide_index=True)
                
                # Errors
                errors = df[df["Error"].notna()]
                if not errors.empty:
                    with st.expander(f"{len(errors)} Failed Requests", expanded=False):
                        st.dataframe(errors[["Date", "Service", "Error"]], hide_index=True)
            else:
                st.error("All predictions failed. Check API connectivity.")

else:
    # Default state
    st.info("Configure parameters and click **Get Prediction** to see results")
    
    # Demo section
    col_demo1, col_demo2 = st.columns(2)
    
    with col_demo1:
        st.markdown("""
        ### What does this tool do?
        
        Predicts the number of **covers** (customers) for a hotel restaurant service.
        
        **How to use:**
        1. Select a date and service type
        2. Get a prediction with reliability score
        3. Review staffing recommendation
        4. Understand the "why" via AI explanation
        """)
    
    with col_demo2:
        st.markdown("""
        ### Based on what?
        
        | Data | Source |
        |------|--------|
        | Historical patterns | 495 patterns (dataset 2015-2017) |
        | Similarity | Qdrant vector search |
        | Reasoning | Claude AI (Anthropic) |
        | Embeddings | Mistral AI |
        """)
    
    st.divider()
    
    # Quick stats
    st.markdown("### Reference Statistics")
    
    ref_cols = st.columns(4)
    with ref_cols[0]:
        st.metric("Available Patterns", "495")
    with ref_cols[1]:
        st.metric("Avg dinner/day", "35 covers")
    with ref_cols[2]:
        st.metric("Avg lunch/day", "22 covers")
    with ref_cols[3]:
        st.metric("Avg breakfast/day", "28 covers")
    
    st.divider()
    
    # Links
    st.markdown("""
    **Useful links:**
    [API Documentation](https://ivandemurard-fb-agent-api.hf.space/docs) | 
    [GitHub Repository](https://github.com/ivandemurard/fb-agent) |
    [Portfolio](https://ivandemurard.com)
    """)

# Footer
st.divider()
st.caption("Built by Ivan de Murard | F&B Operations Agent v0.3")
