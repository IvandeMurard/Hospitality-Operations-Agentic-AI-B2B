"""Loading Steps Component - Show AI reasoning transparency."""

import streamlit as st
import time
from typing import List, Dict, Callable, Any, Optional


def render_loading_steps(
    steps: List[Dict], execute: bool = True
) -> Optional[Any]:
    """
    Render loading progress with AI reasoning steps.

    Args:
        steps: List of {"label": str, "action": callable or None}
        execute: Whether to actually execute actions and run the last one for result

    Returns:
        Result of the last step's action, or None.
    """
    steps_placeholder = st.empty()
    result = None
    completed: List[str] = []

    for i, step in enumerate(steps):
        label = step["label"]
        action = step.get("action")

        # Build HTML: completed (checkmark), current (arrow), remaining (circle)
        lines = []
        for j, completed_label in enumerate(completed):
            lines.append(
                f'<div style="display: flex; align-items: center; margin-bottom: 0.5rem; color: #40916C;">'
                f'<span style="margin-right: 0.5rem;">✓</span>'
                f'<span style="font-size: 0.875rem;">{completed_label}</span></div>'
            )
        lines.append(
            f'<div style="display: flex; align-items: center; margin-bottom: 0.5rem; color: #495057;">'
            f'<span style="margin-right: 0.5rem;">→</span>'
            f'<span style="font-size: 0.875rem;">{label}</span></div>'
        )
        for k in range(i + 1, len(steps)):
            lines.append(
                f'<div style="display: flex; align-items: center; margin-bottom: 0.5rem; color: #ADB5BD;">'
                f'<span style="margin-right: 0.5rem;">○</span>'
                f'<span style="font-size: 0.875rem;">{steps[k]["label"]}</span></div>'
            )

        card_html = f"""
        <div style="
            background-color: #FFFFFF;
            border: 1px solid #E9ECEF;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
        ">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <div style="
                    width: 8px; height: 8px;
                    background-color: #2D6A4F;
                    border-radius: 50%;
                    margin-right: 0.75rem;
                    animation: pulse 1s infinite;
                "></div>
                <span style="color: #212529; font-weight: 500;">Generating forecast...</span>
            </div>
            {"".join(lines)}
        </div>
        """
        steps_placeholder.markdown(card_html, unsafe_allow_html=True)

        if execute and action and callable(action):
            result = action()
        else:
            time.sleep(0.25)
        completed.append(label)

    # Final state - all complete (show briefly then clear)
    final_lines = []
    for completed_label in completed:
        final_lines.append(
            f'<div style="display: flex; align-items: center; margin-bottom: 0.5rem; color: #40916C;">'
            f'<span style="margin-right: 0.5rem;">✓</span>'
            f'<span style="font-size: 0.875rem;">{completed_label}</span></div>'
        )
    final_html = f"""
    <div style="
        background-color: #FFFFFF;
        border: 1px solid #E9ECEF;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <span style="color: #212529; font-weight: 500;">Forecast ready</span>
        </div>
        {"".join(final_lines)}
    </div>
    """
    steps_placeholder.markdown(final_html, unsafe_allow_html=True)
    steps_placeholder.empty()

    return result


# Predefined step sequences (caller attaches action to last step)
PREDICTION_STEPS = [
    {"label": "Loading historical data...", "action": None},
    {"label": "Analyzing day-of-week patterns...", "action": None},
    {"label": "Checking for local events...", "action": None},
    {"label": "Finding similar past days...", "action": None},
    {"label": "Calculating confidence interval...", "action": None},
    {"label": "Generating staff recommendation...", "action": None},
]

WEEK_PREDICTION_STEPS = [
    {"label": "Loading week data...", "action": None},
    {"label": "Analyzing 7-day patterns...", "action": None},
    {"label": "Processing each day...", "action": None},
    {"label": "Calculating weekly totals...", "action": None},
]
