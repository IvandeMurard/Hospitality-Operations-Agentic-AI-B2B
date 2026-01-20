"""
F&B Operations Agent - Dashboard
Streamlit MVP for prediction visualization
"""

import streamlit as st
import requests
import pandas as pd
from datetime import date, timedelta
import plotly.graph_objects as go

# Configuration
API_URL = "https://ivandemurard-fb-agent-api.hf.space"

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

st.divider()

# Sidebar - Input
with st.sidebar:
    st.header("📅 Prediction Parameters")
    
    service_date = st.date_input(
        "Service Date",
        value=date.today() + timedelta(days=1),
        min_value=date.today(),
        max_value=date.today() + timedelta(days=90)
    )
    
    service_type = st.selectbox(
        "Service Type",
        options=["lunch", "dinner", "brunch"],
        index=1  # Default: dinner
    )
    
    restaurant_id = st.text_input(
        "Restaurant ID",
        value="hotel_main",
        help="Identifier for your restaurant"
    )
    
    predict_button = st.button("🔮 Get Prediction", type="primary", use_container_width=True)

# Main content
if predict_button:
    with st.spinner("Analyzing patterns..."):
        try:
            # Call API
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
            
            # Extract data (adapted to actual API structure)
            predicted_covers = data.get("predicted_covers", 0)
            confidence = data.get("confidence", 0)
            reasoning = data.get("reasoning", {})
            staff = data.get("staff_recommendation", {})
            
            # Confidence color
            if confidence >= 0.85:
                conf_class = "confidence-high"
                conf_emoji = "🟢"
            elif confidence >= 0.70:
                conf_class = "confidence-medium"
                conf_emoji = "🟡"
            else:
                conf_class = "confidence-low"
                conf_emoji = "🔴"
            
            # Layout
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Prediction Card
                st.subheader(f"📊 {service_date.strftime('%A, %B %d')} - {service_type.capitalize()}")
                
                # Main metrics
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                
                with metric_col1:
                    st.metric(
                        label="Predicted Covers",
                        value=f"{predicted_covers}",
                        delta=None
                    )
                
                with metric_col2:
                    st.metric(
                        label="Confidence",
                        value=f"{confidence:.0%}",
                        delta=None
                    )
                
                with metric_col3:
                    # Note: accuracy_metrics not in current API response
                    st.metric(
                        label="Method",
                        value="RAG",
                        delta=None,
                        help="Retrieval-Augmented Generation"
                    )
                
                st.divider()
                
                # Staff Recommendation
                st.subheader("👥 Staff Recommendation")
                
                if staff:
                    # Extract staff data (adapted to actual API structure)
                    servers_data = staff.get("servers", {})
                    hosts_data = staff.get("hosts", {})
                    kitchen_data = staff.get("kitchen", {})
                    
                    staff_col1, staff_col2, staff_col3 = st.columns(3)
                    
                    with staff_col1:
                        rec_servers = servers_data.get("recommended", 0)
                        usual_servers = servers_data.get("usual", 0)
                        delta_servers = servers_data.get("delta", 0)
                        st.metric(
                            "Servers",
                            rec_servers,
                            delta=delta_servers if delta_servers != 0 else None
                        )
                    
                    with staff_col2:
                        rec_hosts = hosts_data.get("recommended", 0)
                        usual_hosts = hosts_data.get("usual", 0)
                        delta_hosts = hosts_data.get("delta", 0)
                        st.metric(
                            "Hosts",
                            rec_hosts,
                            delta=delta_hosts if delta_hosts != 0 else None
                        )
                    
                    with staff_col3:
                        rec_kitchen = kitchen_data.get("recommended", 0)
                        usual_kitchen = kitchen_data.get("usual", 0)
                        delta_kitchen = kitchen_data.get("delta", 0)
                        st.metric(
                            "Kitchen",
                            rec_kitchen,
                            delta=delta_kitchen if delta_kitchen != 0 else None
                        )
                    
                    # Rationale
                    rationale = staff.get("rationale", "")
                    if rationale:
                        st.caption(f"💡 {rationale}")
                    
                    # Covers per staff
                    covers_per_staff = staff.get("covers_per_staff", 0)
                    if covers_per_staff > 0:
                        st.caption(f"📈 Covers per staff: {covers_per_staff:.1f}")
                else:
                    st.info("No staff recommendation available")
            
            with col2:
                # Confidence gauge
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
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 2},
                            'thickness': 0.75,
                            'value': 85
                        }
                    }
                ))
                fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)
            
            # Reasoning (expandable)
            with st.expander("🧠 View AI Reasoning", expanded=False):
                # Use reasoning.summary (actual API structure)
                summary = reasoning.get("summary", "No explanation available")
                st.markdown(f"**Analysis:** {summary}")
                
                # Similar patterns (adapted to reasoning.patterns_used)
                patterns = reasoning.get("patterns_used", [])
                if patterns:
                    st.markdown("**Similar Historical Patterns:**")
                    for i, pattern in enumerate(patterns[:3], 1):
                        p_date = pattern.get("date", "Unknown")
                        p_covers = pattern.get("actual_covers", "?")
                        p_sim = pattern.get("similarity", 0)
                        p_event = pattern.get("event_type", "Regular service")
                        st.markdown(f"{i}. {p_date} — {p_covers} covers (similarity: {p_sim:.0%}) — {p_event}")
                
                # Confidence factors
                confidence_factors = reasoning.get("confidence_factors", [])
                if confidence_factors:
                    st.markdown("**Confidence Factors:**")
                    for factor in confidence_factors:
                        st.markdown(f"- {factor}")
            
            # Raw response (debug)
            with st.expander("🔧 Raw API Response", expanded=False):
                st.json(data)
                
        except requests.exceptions.RequestException as e:
            st.error(f"❌ API Error: {str(e)}")
            st.info("💡 Make sure the API is running at: " + API_URL)
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            with st.expander("🔍 Error Details"):
                st.code(traceback.format_exc())

else:
    # Default state
    st.info("👈 Configure parameters and click **Get Prediction** to see results")
    
    # Demo card
    st.markdown("""
    ### How it works
    
    1. **Select a date** — Choose the service date you want to predict
    2. **Choose service type** — Lunch, dinner, or brunch
    3. **Get prediction** — Our AI analyzes similar historical patterns
    4. **Review reasoning** — Understand WHY the prediction was made
    
    ---
    
    ### About
    
    This dashboard uses **RAG (Retrieval-Augmented Generation)** to find similar historical patterns 
    and predict demand. The system considers:
    
    - 📅 Day of week & seasonality
    - 🎉 Local events
    - 🌤️ Weather conditions
    - 🏨 Hotel occupancy patterns
    
    [View API Documentation](https://ivandemurard-fb-agent-api.hf.space/docs) | 
    [GitHub Repository](https://github.com/ivandemurard/fb-agent)
    """)

# Footer
st.divider()
st.caption("Built with ❤️ by Ivan de Murard | F&B Operations Agent v0.2")
