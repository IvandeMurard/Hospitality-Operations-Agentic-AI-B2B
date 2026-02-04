"""Timeline Chart Component - Apollo Style"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests

from config import API_BASE


def render_day_hero(prediction: dict, date: datetime) -> None:
    """Render day view as prominent hero card instead of bar chart."""
    if not prediction:
        st.warning("No prediction available for this date")
        return

    covers = prediction.get("predicted_covers", 0)
    metrics = prediction.get("accuracy_metrics") or {}
    interval = metrics.get("prediction_interval") or []
    range_low = interval[0] if len(interval) >= 1 else max(0, covers - 10)
    range_high = interval[1] if len(interval) >= 2 else covers + 10
    confidence = prediction.get("confidence", 0)  # 0-1
    confidence_pct = int(confidence * 100)

    if confidence_pct >= 85:
        conf_label = "High"
        conf_color = "#40916C"
    elif confidence_pct >= 70:
        conf_label = "Medium"
        conf_color = "#E9C46A"
    else:
        conf_label = "Low"
        conf_color = "#E76F51"

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1B4332 0%, #2D6A4F 100%);
            border-radius: 12px;
            padding: 2.5rem;
            text-align: center;
            margin: 1rem 0;
        ">
            <p style="
                color: rgba(255,255,255,0.7);
                font-size: 0.875rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                margin-bottom: 0.5rem;
            ">{date.strftime('%A, %B %d, %Y')}</p>
            
            <h1 style="
                color: #FFFFFF;
                font-size: 4rem;
                font-weight: 700;
                margin: 0.5rem 0;
                letter-spacing: -0.02em;
            ">{covers}</h1>
            
            <p style="
                color: rgba(255,255,255,0.8);
                font-size: 1.125rem;
                margin-bottom: 1.5rem;
            ">expected covers</p>
            
            <div style="
                display: flex;
                justify-content: center;
                gap: 3rem;
                margin-top: 1rem;
            ">
                <div>
                    <p style="color: rgba(255,255,255,0.6); font-size: 0.75rem; margin: 0;">Range</p>
                    <p style="color: #FFFFFF; font-size: 1.25rem; font-weight: 600; margin: 0.25rem 0 0 0;">
                        {range_low} – {range_high}
                    </p>
                </div>
                <div>
                    <p style="color: rgba(255,255,255,0.6); font-size: 0.75rem; margin: 0;">Confidence</p>
                    <p style="color: {conf_color}; font-size: 1.25rem; font-weight: 600; margin: 0.25rem 0 0 0;">
                        {conf_label}
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _restaurant_to_id(restaurant: str) -> str:
    """Map restaurant display name to backend ID."""
    restaurant_map = {
        "Main Restaurant": "hotel_main",
        "Pool Bar": "pool_bar",
        "Room Service": "room_service",
    }
    return restaurant_map.get(restaurant, restaurant.lower().replace(" ", "_"))


def get_week_predictions(
    start_date: datetime, restaurant: str, service: str
) -> List[Dict]:
    """Fetch predictions for 7 days starting from start_date."""
    predictions = []
    restaurant_id = _restaurant_to_id(restaurant)
    service_type = service.lower()

    for i in range(7):
        date = start_date + timedelta(days=i)
        try:
            response = requests.post(
                f"{API_BASE}/predict",
                json={
                    "service_date": date.strftime("%Y-%m-%d"),
                    "service_type": service_type,
                    "restaurant_id": restaurant_id,
                },
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                metrics = data.get("accuracy_metrics") or {}
                interval = metrics.get("prediction_interval") or [0, 0]
                range_low = interval[0] if len(interval) >= 1 else 0
                range_high = interval[1] if len(interval) >= 2 else 0
                predictions.append({
                    "date": date,
                    "day": date.strftime("%a"),
                    "covers": data.get("predicted_covers", 0),
                    "range_low": range_low,
                    "range_high": range_high,
                    "confidence": data.get("confidence", 0),
                })
            else:
                predictions.append({
                    "date": date,
                    "day": date.strftime("%a"),
                    "covers": 0,
                    "range_low": 0,
                    "range_high": 0,
                    "confidence": 0,
                })
        except Exception:
            predictions.append({
                "date": date,
                "day": date.strftime("%a"),
                "covers": 0,
                "range_low": 0,
                "range_high": 0,
                "confidence": 0,
            })
    return predictions


def get_month_predictions(
    year: int, month: int, restaurant: str, service: str
) -> Optional[List[Dict]]:
    """Fetch all predictions for a month using batch API."""
    from calendar import monthrange
    from datetime import date as date_cls

    _, last_day = monthrange(year, month)
    dates = [date_cls(year, month, day).strftime("%Y-%m-%d") for day in range(1, last_day + 1)]
    restaurant_id = _restaurant_to_id(restaurant)
    service_type = service.lower()
    try:
        response = requests.post(
            f"{API_BASE}/predict/batch",
            json={
                "dates": dates,
                "service_type": service_type,
                "restaurant_id": restaurant_id,
            },
            timeout=120,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("predictions") or []
    except Exception:
        pass
    return None


def render_week_chart(
    predictions: List[Dict],
    selected_date: Optional[datetime] = None,
    baseline: Optional[float] = None,
) -> None:
    """Render Apollo-style weekly bar chart."""
    if not predictions:
        st.info("No prediction data available")
        return

    days = [p["day"] for p in predictions]
    covers = [p["covers"] for p in predictions]

    colors = []
    for p in predictions:
        if selected_date and p["date"].date() == selected_date.date():
            colors.append("#1B4332")
        else:
            colors.append("#2D6A4F")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=days,
            y=covers,
            marker_color=colors,
            text=covers,
            textposition="outside",
            textfont=dict(size=14, color="#212529"),
            hovertemplate="<b>%{x}</b><br>%{y} covers<extra></extra>",
        )
    )

    if baseline is not None:
        fig.add_hline(
            y=baseline,
            line_dash="dash",
            line_color="#ADB5BD",
            annotation_text=f"Avg: {int(baseline)}",
            annotation_position="right",
        )

    fig.update_layout(
        title=None,
        xaxis=dict(
            title=None,
            tickfont=dict(size=14, color="#495057"),
            showgrid=False,
        ),
        yaxis=dict(
            title=None,
            tickfont=dict(size=12, color="#6C757D"),
            gridcolor="#E9ECEF",
            zeroline=False,
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=40, t=20, b=40),
        height=300,
        showlegend=False,
        bargap=0.3,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_day_chart(prediction: Dict) -> None:
    """Render single day view with range indicator."""
    covers = prediction.get("covers", 0)
    range_low = prediction.get("range_low", 0)
    range_high = prediction.get("range_high", 0)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=["Forecast"],
            y=[range_high - range_low],
            base=range_low,
            marker_color="#D8F3DC",
            name="Range",
            hoverinfo="skip",
            width=0.6,
        )
    )
    fig.add_trace(
        go.Bar(
            x=["Forecast"],
            y=[covers],
            marker_color="#2D6A4F",
            name="Predicted",
            text=[f"{covers}"],
            textposition="outside",
            textfont=dict(size=24, color="#212529"),
            width=0.4,
        )
    )
    fig.update_layout(
        title=None,
        xaxis=dict(visible=False),
        yaxis=dict(
            title="Covers",
            tickfont=dict(size=12, color="#6C757D"),
            gridcolor="#E9ECEF",
            zeroline=False,
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=60, r=40, t=20, b=20),
        height=250,
        showlegend=False,
        barmode="overlay",
    )
    fig.add_annotation(
        x="Forecast",
        y=range_high,
        text=f"Range: {range_low} – {range_high}",
        showarrow=False,
        yshift=30,
        font=dict(size=12, color="#6C757D"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_month_chart_from_data(month_predictions: List[Dict]) -> None:
    """Render monthly bar chart from pre-fetched predictions."""
    if not month_predictions:
        return
    days = [p.get("date", "")[-2:] for p in month_predictions]
    covers = [p.get("predicted_covers", 0) for p in month_predictions]
    colors = ["#2D6A4F"] * len(covers)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=days,
            y=covers,
            marker_color=colors,
            text=covers,
            textposition="outside",
            textfont=dict(size=10, color="#212529"),
            hovertemplate="<b>Day %{x}</b><br>%{y} covers<extra></extra>",
        )
    )
    fig.update_layout(
        title=None,
        xaxis=dict(title="Day", tickfont=dict(size=11, color="#495057"), showgrid=False),
        yaxis=dict(title=None, tickfont=dict(size=11, color="#6C757D"), gridcolor="#E9ECEF", zeroline=False),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=40, t=20, b=40),
        height=300,
        showlegend=False,
        bargap=0.3,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_month_chart(
    year: int, month: int, restaurant: str, service: str
) -> None:
    """Render monthly view using batch API (fetches and renders)."""
    month_predictions = get_month_predictions(year, month, restaurant, service)
    if not month_predictions:
        st.info("Monthly view: load failed or batch API not available.")
        st.markdown("*Ensure backend is running and supports `/predict/batch`*")
        return
    render_month_chart_from_data(month_predictions)
