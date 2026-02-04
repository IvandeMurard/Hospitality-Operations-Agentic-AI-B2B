"""Forecast view - predictions, KPIs, timeline chart."""

import streamlit as st
import requests
from datetime import datetime, timedelta
from typing import Optional

from config import get_text, API_BASE
from components.header import render_header
from components.loading_steps import render_loading_steps, PREDICTION_STEPS
from components.timeline_chart import (
    get_week_predictions,
    get_month_predictions,
    render_week_chart,
    render_day_hero,
    render_month_chart_from_data,
)


def _confidence_label(confidence: float, lang: str) -> str:
    """Map confidence 0-1 to High/Medium/Low."""
    if confidence >= 0.85:
        return get_text("confidence.high", lang)
    if confidence >= 0.7:
        return get_text("confidence.medium", lang)
    return get_text("confidence.low", lang)


def _parse_staff(staff_rec: dict) -> str:
    """Extract server count from staff_recommendation."""
    if not isinstance(staff_rec, dict):
        return "—"
    servers_dict = staff_rec.get("servers", {})
    if isinstance(servers_dict, dict):
        servers = servers_dict.get("recommended", "—")
    else:
        servers = servers_dict if servers_dict else "—"
    if servers == "—" and "recommended" in staff_rec:
        servers = staff_rec.get("recommended", "—")
    return servers


def _render_kpi_cards_day(lang: str, prediction: dict, date_display: str) -> None:
    """Render KPI cards for day view (single day values)."""
    col1, col2, col3, col4 = st.columns(4)
    if prediction:
        covers = prediction.get("predicted_covers", "—")
        accuracy_metrics = prediction.get("accuracy_metrics", {})
        interval = accuracy_metrics.get("prediction_interval")
        range_text = f"{interval[0]} – {interval[1]}" if interval and len(interval) == 2 else "—"
        confidence_label = _confidence_label(prediction.get("confidence", 0), lang)
        servers = _parse_staff(prediction.get("staff_recommendation", {}))
        with col1:
            st.metric(get_text("kpi.covers", lang).upper(), str(covers) if covers != "—" else "—")
        with col2:
            st.metric(get_text("kpi.range", lang).upper(), range_text)
        with col3:
            st.metric(get_text("kpi.staff", lang).upper(), f"{servers} servers" if servers != "—" else "—")
        with col4:
            st.metric(get_text("kpi.confidence", lang).upper(), confidence_label)
    else:
        with col1:
            st.metric(get_text("kpi.covers", lang).upper(), "—")
        with col2:
            st.metric(get_text("kpi.range", lang).upper(), "—")
        with col3:
            st.metric(get_text("kpi.staff", lang).upper(), "—")
        with col4:
            st.metric(get_text("kpi.confidence", lang).upper(), "—")
        st.warning(f"Could not load prediction for {date_display}")


def _render_kpi_cards_week(lang: str, week_predictions: list) -> None:
    """Render KPI cards for week view (totals, peak, avg)."""
    col1, col2, col3, col4 = st.columns(4)
    if not week_predictions:
        for col in [col1, col2, col3, col4]:
            with col:
                st.metric("—", "—")
        return
    total = sum(p.get("covers", 0) for p in week_predictions)
    avg_covers = int(total / 7)
    peak_day = max(week_predictions, key=lambda x: x.get("covers", 0))
    confidences = [p.get("confidence", 0) for p in week_predictions]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0
    with col1:
        st.metric("TOTAL WEEK", f"{total} covers")
    with col2:
        st.metric("DAILY AVG", f"{avg_covers} covers")
    with col3:
        st.metric("PEAK DAY", f"{peak_day.get('day', '—')} ({peak_day.get('covers', 0)})")
    with col4:
        st.metric("AVG CONFIDENCE", _confidence_label(avg_conf, lang))


def _render_kpi_cards_month(
    lang: str, month_predictions: Optional[list] = None
) -> None:
    """Render KPI cards for month view (placeholders or aggregated from batch)."""
    col1, col2, col3, col4 = st.columns(4)
    if month_predictions:
        total = sum(p.get("predicted_covers", 0) for p in month_predictions)
        n = len(month_predictions)
        avg = int(total / n) if n else 0
        peak = max(month_predictions, key=lambda x: x.get("predicted_covers", 0))
        confidences = [p.get("confidence", 0) for p in month_predictions]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0
        with col1:
            st.metric("TOTAL MONTH", f"{total} covers")
        with col2:
            st.metric("DAILY AVG", f"{avg} covers")
        with col3:
            st.metric("PEAK DAY", f"Day {peak.get('date', '')[-2:]} ({peak.get('predicted_covers', 0)})")
        with col4:
            st.metric("AVG CONFIDENCE", _confidence_label(avg_conf, lang))
    else:
        with col1:
            st.metric("TOTAL MONTH", "…")
        with col2:
            st.metric("DAILY AVG", "…")
        with col3:
            st.metric("PEAK WEEK", "…")
        with col4:
            st.metric("CONFIDENCE", "…")


def fetch_prediction(date: datetime, restaurant: str, service: str) -> dict:
    """Fetch prediction from backend API."""
    try:
        restaurant_map = {
            "Main Restaurant": "hotel_main",
            "Pool Bar": "pool_bar",
            "Room Service": "room_service",
        }
        restaurant_id = restaurant_map.get(
            restaurant, restaurant.lower().replace(" ", "_")
        )
        response = requests.post(
            f"{API_BASE}/predict",
            json={
                "service_date": date.strftime("%Y-%m-%d"),
                "service_type": service.lower(),
                "restaurant_id": restaurant_id,
            },
            timeout=60,
        )
        if response.status_code == 200:
            return response.json()
        st.warning(f"Prediction API returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("Unable to connect to backend API. Please ensure the backend is running.")
    except requests.exceptions.Timeout:
        st.error(
            "Backend API request timed out. The first prediction can take up to a minute "
            "(embedding + Qdrant + Claude). Try again or check backend logs."
        )
    except Exception as e:
        st.error(f"Prediction error: {e}")
    return None


def render_forecast_view(context: dict) -> None:
    """Render the forecast page."""
    lang = context["language"]
    header = render_header(lang=lang)
    st.markdown("<br>", unsafe_allow_html=True)

    selected_date = header["selected_date"]
    date_display = selected_date.strftime("%A, %B %d")
    view = header["view"]
    week_predictions = None

    # Optional cache for day view prediction
    cache_key = f"{selected_date.strftime('%Y-%m-%d')}_{context['restaurant']}_{context['service']}"
    if "prediction_cache" not in st.session_state:
        st.session_state.prediction_cache = {}

    if view == "day" and cache_key not in st.session_state.prediction_cache:
        steps = [dict(s) for s in PREDICTION_STEPS]
        steps[-1]["action"] = lambda: fetch_prediction(
            date=selected_date,
            restaurant=context["restaurant"],
            service=context["service"],
        )
        prediction = render_loading_steps(steps)
        st.session_state.prediction_cache[cache_key] = prediction
    elif view == "day":
        prediction = st.session_state.prediction_cache.get(cache_key)
    else:
        prediction = fetch_prediction(
            date=selected_date,
            restaurant=context["restaurant"],
            service=context["service"],
        )

    # KPI cards (day view: single prediction; week/month handled below after data fetch)
    if view == "day":
        _render_kpi_cards_day(lang, prediction, date_display)
    elif view == "week":
        week_start = selected_date - timedelta(days=selected_date.weekday())
        if "week_predictions_cache" not in st.session_state:
            st.session_state.week_predictions_cache = {}
        week_cache_key = f"{week_start.strftime('%Y-%m-%d')}_{context['restaurant']}_{context['service']}"
        if week_cache_key not in st.session_state.week_predictions_cache:
            with st.spinner("Loading week forecast..."):
                week_predictions = get_week_predictions(
                    start_date=week_start,
                    restaurant=context["restaurant"],
                    service=context["service"],
                )
            st.session_state.week_predictions_cache[week_cache_key] = week_predictions
        else:
            week_predictions = st.session_state.week_predictions_cache[week_cache_key]
        _render_kpi_cards_week(lang, week_predictions or [])
    else:
        month_predictions = None
        with st.spinner("Loading month forecast..."):
            month_predictions = get_month_predictions(
                selected_date.year,
                selected_date.month,
                context["restaurant"],
                context["service"],
            )
        _render_kpi_cards_month(lang, month_predictions)

    st.markdown("<br>", unsafe_allow_html=True)

    if view == "day":
        if prediction:
            render_day_hero(prediction, selected_date)
        else:
            st.info("Select a date to view forecast")
    elif view == "week":
        if week_predictions:
            covers_list = [p["covers"] for p in week_predictions if p["covers"] > 0]
            baseline = (
                sum(covers_list) / len(covers_list) if covers_list else None
            )
            render_week_chart(
                predictions=week_predictions,
                selected_date=selected_date,
                baseline=baseline,
            )
        else:
            st.info("No week data available")
    elif view == "month":
        if month_predictions:
            render_month_chart_from_data(month_predictions)
        else:
            st.info("Monthly view: load failed or batch API not available.")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.info("Factors panel will be implemented in Phase 3")
    with col2:
        st.info("Feedback panel will be implemented in Phase 3")
