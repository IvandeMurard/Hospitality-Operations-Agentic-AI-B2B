"""Aetherix - Intelligence layer for hotel F&B operations"""

import streamlit as st
import requests
from datetime import datetime

# Page config must be first Streamlit command
st.set_page_config(
    page_title="Aetherix",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import after page config
from config import AETHERIX_CSS, get_text, API_BASE
from components.sidebar import render_sidebar
from components.header import render_header

# Initialize session state for prediction persistence (Phase 2)
if "prediction_data" not in st.session_state:
    st.session_state.prediction_data = None
if "has_prediction" not in st.session_state:
    st.session_state.has_prediction = False

# Inject custom CSS
st.markdown(AETHERIX_CSS, unsafe_allow_html=True)


def fetch_prediction(date: datetime, restaurant: str, service: str) -> dict:
    """Fetch prediction from backend API"""
    try:
        # Map restaurant names to backend IDs
        restaurant_map = {
            "Main Restaurant": "hotel_main",
            "Pool Bar": "pool_bar",
            "Room Service": "room_service"
        }
        restaurant_id = restaurant_map.get(restaurant, restaurant.lower().replace(" ", "_"))
        
        response = requests.post(
            f"{API_BASE}/predict",
            json={
                "service_date": date.strftime("%Y-%m-%d"),
                "service_type": service.lower(),
                "restaurant_id": restaurant_id
            },
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"Prediction API returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("Unable to connect to backend API. Please ensure the backend is running.")
    except requests.exceptions.Timeout:
        st.error("Backend API request timed out.")
    except Exception as e:
        st.error(f"Prediction error: {e}")
    return None

# Get language from session state (set by sidebar selectbox)
lang = st.session_state.get("lang_select", "en")

# Render sidebar and get context
context = render_sidebar(lang=lang)

# Main content area
if context["page"] == "forecast":
    # Render header
    header = render_header(lang=context["language"])

    st.markdown("<br>", unsafe_allow_html=True)

    # Fetch prediction from backend
    with st.spinner("Loading prediction..."):
        prediction = fetch_prediction(
            date=header["selected_date"],
            restaurant=context["restaurant"],
            service=context["service"]
        )

    # KPI cards with real data
    col1, col2, col3, col4 = st.columns(4)

    if prediction:
        # Extract prediction data
        covers = prediction.get("predicted_covers", "—")
        
        # Get prediction interval for range
        accuracy_metrics = prediction.get("accuracy_metrics", {})
        interval = accuracy_metrics.get("prediction_interval")
        if interval and len(interval) == 2:
            range_text = f"{interval[0]} – {interval[1]}"
        else:
            range_text = "—"
        
        # Get confidence score
        confidence = prediction.get("confidence", 0)
        if confidence >= 0.85:
            confidence_label = get_text("confidence.high", lang)
        elif confidence >= 0.7:
            confidence_label = get_text("confidence.medium", lang)
        else:
            confidence_label = get_text("confidence.low", lang)
        
        # Get staff recommendation
        staff = prediction.get("staff_recommendation", {})
        if isinstance(staff, dict):
            servers = staff.get("servers", staff.get("recommended_staff", {}).get("servers", "—"))
        else:
            servers = "—"
        
        with col1:
            st.metric(
                label=get_text("kpi.covers", lang).upper(),
                value=str(covers) if covers != "—" else "—",
            )
        with col2:
            st.metric(
                label=get_text("kpi.range", lang).upper(),
                value=range_text,
            )
        with col3:
            st.metric(
                label=get_text("kpi.staff", lang).upper(),
                value=f"{servers} servers" if servers != "—" else "—",
            )
        with col4:
            st.metric(
                label=get_text("kpi.confidence", lang).upper(),
                value=confidence_label,
            )
    else:
        # Fallback when no prediction available
        with col1:
            st.metric(label=get_text("kpi.covers", lang).upper(), value="—")
        with col2:
            st.metric(label=get_text("kpi.range", lang).upper(), value="—")
        with col3:
            st.metric(label=get_text("kpi.staff", lang).upper(), value="—")
        with col4:
            st.metric(label=get_text("kpi.confidence", lang).upper(), value="—")

    st.markdown("<br>", unsafe_allow_html=True)

    # Placeholder for chart (Phase 2)
    st.info("Timeline chart will be implemented in Phase 2")

    # Placeholder for panels (Phase 3)
    col1, col2 = st.columns(2)
    with col1:
        st.info("Factors panel will be implemented in Phase 3")
    with col2:
        st.info("Feedback panel will be implemented in Phase 3")

elif context["page"] == "history":
    st.title("History")
    st.info("History page will be implemented in Phase 5")

elif context["page"] == "settings":
    from pages.settings import render_settings_page

    render_settings_page(lang=context["language"])
