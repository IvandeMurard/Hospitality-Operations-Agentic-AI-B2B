"""
F&B Operations Agent - Dashboard
Streamlit MVP for prediction visualization
"""

import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
import time
import plotly.graph_objects as go

# Configuration
API_URL = "https://ivandemurard-fb-agent-api.hf.space"

# Explanatory content
EXPLAINER_CONTENT = {
    "how_it_works": """
### 🔍 How does this prediction work?

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
    
    "mape_explanation": """
**MAPE** (Mean Absolute Percentage Error)

Measures the estimated average gap between prediction and reality.

| Value | Interpretation |
|-------|----------------|
| < 15% | ✅ Excellent — High reliability |
| 15-25% | ⚠️ Acceptable — Plan for a margin |
| > 25% | ⚠️ Caution — High variance in similar patterns |

*Note: Estimated from pattern variance, not yet backtested on real data.*
    """,
    
    "confidence_explanation": """
**Confidence Score**

Based on **cosine similarity** between your context and historical patterns.

| Score | Meaning |
|-------|---------|
| > 90% | Found patterns match your situation very well |
| 80-90% | Good match, minor differences |
| < 80% | Unusual context, few similar patterns |

*Calculation: Average of similarity scores from the 5 best patterns.*
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


def get_mape_interpretation(mape_value):
    """Return color and emoji for MAPE interpretation"""
    if mape_value is None:
        return "gray", "❓", "Not available"
    elif mape_value < 15:
        return "green", "✅", "Excellent"
    elif mape_value < 25:
        return "orange", "⚠️", "Acceptable"
    else:
        return "red", "⚠️", "High variance"


def get_confidence_interpretation(confidence):
    """Return color and emoji for confidence interpretation"""
    if confidence is None:
        return "gray", "❓", "Not available"
    elif confidence >= 0.90:
        return "green", "✅", "Very similar"
    elif confidence >= 0.80:
        return "orange", "👍", "Good match"
    else:
        return "red", "⚠️", "Unusual context"


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
    page_icon="🍽️",
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
st.title("🍽️ F&B Operations Agent")
st.markdown("*AI-powered demand forecasting for hotel restaurants*")

# How it works (collapsible)
with st.expander("ℹ️ How it works?", expanded=False):
    st.markdown(EXPLAINER_CONTENT["how_it_works"])
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("Historical Patterns", BASELINE_STATS["patterns_count"])
    with col_stat2:
        st.metric("Data Period", BASELINE_STATS["data_period"])
    with col_stat3:
        st.metric("Avg dinner/day", f"{BASELINE_STATS['avg_daily_dinner']} covers")

st.divider()

# Sidebar - Input
with st.sidebar:
    st.header("📅 Prediction Parameters")
    
    # View mode toggle
    view_mode = st.radio(
        "View Mode",
        options=["single", "weekly"],
        format_func=lambda x: "📍 Single Day" if x == "single" else "📆 Weekly Overview",
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
    
    button_label = "🔮 Get Prediction" if view_mode == "single" else "📆 Get Week Forecast"
    predict_button = st.button(button_label, type="primary", use_container_width=True)

# Main content
if predict_button:
    if view_mode == "single":
        # === SINGLE DAY VIEW (existing logic) ===
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
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader(f"📊 {service_date.strftime('%A, %B %d')} - {service_type.capitalize()}")
                    
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    
                    with metric_col1:
                        # Baseline comparison
                        baseline_key = f"avg_daily_{service_type}"
                        baseline = BASELINE_STATS.get(baseline_key, 0)
                        if baseline > 0:
                            delta = predicted_covers - baseline
                            delta_pct = (delta / baseline * 100) if baseline else 0
                            st.metric(
                                label="Predicted Covers",
                                value=f"{predicted_covers}",
                                delta=f"{delta:+.0f} vs baseline ({baseline})",
                                delta_color="normal",
                                help=f"Historical baseline for {service_type}: {baseline} covers/day"
                            )
                        else:
                            st.metric(
                                label="Predicted Covers",
                                value=f"{predicted_covers}",
                                help=f"Predicted covers for {service_type}"
                            )
                    
                    with metric_col2:
                        conf_color, conf_emoji, conf_text = get_confidence_interpretation(confidence)
                        st.metric(
                            label="Confidence",
                            value=f"{confidence:.0%} {conf_emoji}",
                            help="Average cosine similarity of found patterns. Click 'Understand metrics' for more details."
                        )
                        st.caption(conf_text)
                    
                    with metric_col3:
                        mape = accuracy.get("estimated_mape")
                        if mape:
                            mape_color, mape_emoji, mape_text = get_mape_interpretation(mape)
                            st.metric(
                                label="Est. MAPE",
                                value=f"{mape:.1f}% {mape_emoji}",
                                help="Estimated Mean Absolute Percentage Error. Measures expected average gap between prediction and reality."
                            )
                            st.caption(mape_text)
                        else:
                            st.metric(label="Est. MAPE", value="N/A")
                    
                    interval = accuracy.get("prediction_interval")
                    if interval:
                        st.caption(f"📈 Prediction interval: {interval[0]} - {interval[1]} covers")
                    
                    st.divider()
                    
                    st.subheader("👥 Staff Recommendation")
                    
                    if staff:
                        servers_data = staff.get("servers", {})
                        hosts_data = staff.get("hosts", {})
                        kitchen_data = staff.get("kitchen", {})
                        
                        staff_cols = st.columns(4)
                        
                        with staff_cols[0]:
                            rec_servers = servers_data.get("recommended", 0)
                            st.metric("Servers", rec_servers)
                        with staff_cols[1]:
                            rec_hosts = hosts_data.get("recommended", 0)
                            st.metric("Hosts", rec_hosts)
                        with staff_cols[2]:
                            rec_bussers = 0  # Not in current structure
                            st.metric("Bussers", rec_bussers)
                        with staff_cols[3]:
                            rec_kitchen = kitchen_data.get("recommended", 0)
                            st.metric("Kitchen", rec_kitchen)
                        
                        rationale = staff.get("rationale", "")
                        if rationale:
                            st.caption(f"💡 {rationale}")
                        
                        covers_per_staff = staff.get("covers_per_staff", 0)
                        if covers_per_staff > 0:
                            st.caption(f"📈 Covers per staff: {covers_per_staff:.1f}")
                    else:
                        st.info("No staff recommendation available")
                    
                    # Metrics explanation
                    with st.expander("📊 Understand metrics", expanded=False):
                        tab1, tab2 = st.tabs(["Confidence", "MAPE"])
                        with tab1:
                            st.markdown(EXPLAINER_CONTENT["confidence_explanation"])
                        with tab2:
                            st.markdown(EXPLAINER_CONTENT["mape_explanation"])
                
                with col2:
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=confidence * 100,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Confidence"},
                        gauge={
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "#667eea"},
                            'steps': [
                                {'range': [0, 70], 'color': "#ffcccc"},
                                {'range': [70, 85], 'color': "#fff3cd"},
                                {'range': [85, 100], 'color': "#d4edda"}
                            ]
                        }
                    ))
                    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("🧠 View AI Reasoning", expanded=False):
                    explanation = reasoning.get("explanation") or reasoning.get("summary", "No explanation available")
                    st.markdown(f"**Analysis:** {explanation}")
                
                with st.expander("🔧 Raw API Response", expanded=False):
                    st.json(data)
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ API Error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
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
                rows.append({
                    "Date": params.get("service_date"),
                    "Day": pd.to_datetime(params.get("service_date")).strftime("%a") if params.get("service_date") else "",
                    "Service": params.get("service_type", "").capitalize(),
                    "Covers": r.get("predicted_covers"),
                    "Confidence": r.get("confidence"),
                    "MAPE": r.get("accuracy_metrics", {}).get("estimated_mape") if r.get("accuracy_metrics") else None,
                    "Error": r.get("_error")
                })
            
            df = pd.DataFrame(rows)
            
            # Summary metrics
            st.subheader(f"📆 Week of {service_date.strftime('%B %d, %Y')}")
            
            valid_data = df[df["Covers"].notna()]
            
            if not valid_data.empty:
                total_covers = valid_data['Covers'].sum()
                baseline_low, baseline_high = BASELINE_STATS["weekly_covers_range"]
                
                # Context banner
                if total_covers < baseline_low:
                    st.info(f"📉 Quiet week expected ({total_covers:.0f} covers vs baseline {baseline_low}-{baseline_high})")
                elif total_covers > baseline_high:
                    st.success(f"📈 Busy week expected ({total_covers:.0f} covers vs baseline {baseline_low}-{baseline_high})")
                else:
                    st.info(f"📊 Standard week ({total_covers:.0f} covers, baseline {baseline_low}-{baseline_high})")
                
                summary_cols = st.columns(4)
                
                with summary_cols[0]:
                    delta_vs_baseline = total_covers - ((baseline_low + baseline_high) / 2)
                    st.metric(
                        "Total Covers", 
                        f"{total_covers:.0f}",
                        delta=f"{delta_vs_baseline:+.0f} vs avg.",
                        help=f"Historical weekly baseline: {baseline_low}-{baseline_high} covers"
                    )
                with summary_cols[1]:
                    st.metric("Avg per Service", f"{valid_data['Covers'].mean():.0f}")
                with summary_cols[2]:
                    st.metric("Peak", f"{valid_data['Covers'].max():.0f}")
                with summary_cols[3]:
                    avg_conf = valid_data['Confidence'].mean()
                    st.metric("Avg Confidence", f"{avg_conf:.0%}" if avg_conf else "N/A")
                
                st.divider()
                
                # Heatmap / Chart
                st.subheader("📊 Weekly Demand Heatmap")
                
                # Pivot for heatmap
                if len(service_types) > 1:
                    pivot_df = valid_data.pivot(index="Service", columns="Day", values="Covers")
                    # Reorder days
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
                
                # Detail table
                st.subheader("📋 Detailed Predictions")
                
                display_df = valid_data[["Date", "Day", "Service", "Covers", "Confidence", "MAPE"]].copy()
                display_df["Confidence"] = display_df["Confidence"].apply(lambda x: f"{x:.0%}" if pd.notna(x) else "N/A")
                display_df["MAPE"] = display_df["MAPE"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
                display_df["Covers"] = display_df["Covers"].apply(lambda x: f"{x:.0f}" if pd.notna(x) else "Error")
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # MAPE legend
                st.caption("**MAPE Legend:** ✅ < 15% (Excellent) | ⚠️ 15-25% (Acceptable) | ⚠️ > 25% (High variance)")
                
                # Metrics explanation for weekly view
                with st.expander("📊 Understand metrics", expanded=False):
                    tab1, tab2 = st.tabs(["Confidence", "MAPE"])
                    with tab1:
                        st.markdown(EXPLAINER_CONTENT["confidence_explanation"])
                    with tab2:
                        st.markdown(EXPLAINER_CONTENT["mape_explanation"])
                
                # Errors
                errors = df[df["Error"].notna()]
                if not errors.empty:
                    with st.expander(f"⚠️ {len(errors)} Failed Requests", expanded=False):
                        st.dataframe(errors[["Date", "Service", "Error"]], hide_index=True)
            else:
                st.error("All predictions failed. Check API connectivity.")

else:
    # Default state
    st.info("👈 Configure parameters and click **Get Prediction** to see results")
    
    # Demo section
    col_demo1, col_demo2 = st.columns(2)
    
    with col_demo1:
        st.markdown("""
        ### 🎯 What does this tool do?
        
        Predicts the number of **covers** (customers) for a hotel restaurant service.
        
        **Usage:**
        1. Select a date and service
        2. Get a prediction with confidence level
        3. Review staffing recommendation
        4. Understand the "why" via AI explanation
        """)
    
    with col_demo2:
        st.markdown("""
        ### 📊 Based on what?
        
        | Data | Source |
        |------|--------|
        | Historical patterns | 495 patterns (dataset 2015-2017) |
        | Similarity | Vector search Qdrant |
        | Reasoning | Claude AI (Anthropic) |
        | Embeddings | Mistral AI |
        """)
    
    st.divider()
    
    # Quick stats
    st.markdown("### 📈 Reference Statistics")
    
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
    [📖 API Documentation](https://ivandemurard-fb-agent-api.hf.space/docs) | 
    [💻 GitHub Repository](https://github.com/ivandemurard/fb-agent) |
    [👤 Portfolio](https://ivandemurard.com)
    """)

# Footer
st.divider()
st.caption("Built with ❤️ by Ivan de Murard | F&B Operations Agent v0.2")
