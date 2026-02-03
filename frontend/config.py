"""Aetherix Design System Configuration"""

import os
from pathlib import Path

# API
API_BASE = os.environ.get("AETHERIX_API_BASE", "http://localhost:8000")

# Brand
BRAND_NAME = "Aetherix"
BRAND_TAGLINE = "Intelligence layer for hotel F&B operations"

# Colors
COLORS = {
    # Primary (Green)
    "primary_900": "#081C15",
    "primary_800": "#1B4332",  # Sidebar background
    "primary_700": "#2D6A4F",  # Buttons, accents
    "primary_600": "#40916C",  # Hover, success
    "primary_100": "#D8F3DC",  # Light backgrounds
    # Neutral
    "white": "#FFFFFF",
    "gray_50": "#F8F9FA",  # Page background
    "gray_100": "#E9ECEF",  # Card borders
    "gray_200": "#DEE2E6",  # Dividers
    "gray_400": "#ADB5BD",  # Disabled
    "gray_500": "#6C757D",  # Secondary text
    "gray_700": "#495057",  # Body text
    "gray_900": "#212529",  # Headings
    # Semantic
    "success": "#40916C",
    "warning": "#E9C46A",
    "error": "#E76F51",
    "info": "#457B9D",
}

# Custom CSS
AETHERIX_CSS = """
<style>
    /* Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global */
    .stApp {
        background-color: #F8F9FA;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background-color: #1B4332;
        padding-top: 0.5rem;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0.5rem;
    }
    
    /* Sidebar text - white */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: white !important;
    }
    
    /* Sidebar labels */
    [data-testid="stSidebar"] label {
        color: rgba(255,255,255,0.7) !important;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Sidebar radio buttons - white text */
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        color: white !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stRadio"] label p,
    [data-testid="stSidebar"] [data-testid="stRadio"] label div {
        color: white !important;
    }
    
    /* Sidebar dividers */
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.2);
        margin: 1rem 0;
    }
    
    /* ===== MAIN CONTENT ===== */
    
    /* All main content text - dark */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
        color: #212529 !important;
    }
    
    .stApp p {
        color: #495057;
    }
    
    /* Form labels in main content - dark */
    .stApp .stTextInput label,
    .stApp .stNumberInput label,
    .stApp .stSelectbox label,
    .stApp .stTextArea label {
        color: #495057 !important;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    /* Radio buttons in main content - dark text */
    .stApp [data-testid="stRadio"] label {
        color: #212529 !important;
    }
    
    .stApp [data-testid="stRadio"] label p,
    .stApp [data-testid="stRadio"] label div,
    .stApp [data-testid="stRadio"] label span {
        color: #212529 !important;
    }
    
    /* Override for sidebar (more specific) */
    [data-testid="stSidebar"] [data-testid="stRadio"] label,
    [data-testid="stSidebar"] [data-testid="stRadio"] label p,
    [data-testid="stSidebar"] [data-testid="stRadio"] label div,
    [data-testid="stSidebar"] [data-testid="stRadio"] label span {
        color: white !important;
    }
    
    /* ===== KPI CARDS ===== */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        border: 1px solid #E9ECEF;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    
    div[data-testid="stMetric"] label {
        color: #6C757D !important;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #212529 !important;
        font-size: 2rem;
        font-weight: 600;
    }
    
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #40916C !important;
    }
    
    /* ===== BUTTONS ===== */
    .stButton > button {
        background-color: #2D6A4F;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #1B4332;
        border: none;
    }
    
    /* ===== VIEW TOGGLE (Day/Week/Month) ===== */
    /* Style as pill buttons */
    div[data-testid="stHorizontalBlock"] [data-testid="stRadio"] > div {
        gap: 0;
    }
    
    div[data-testid="stHorizontalBlock"] [data-testid="stRadio"] > div > label {
        background-color: white;
        border: 1px solid #DEE2E6;
        padding: 0.5rem 1rem;
        margin: 0;
        cursor: pointer;
        color: #495057 !important;
    }
    
    div[data-testid="stHorizontalBlock"] [data-testid="stRadio"] > div > label:first-child {
        border-radius: 6px 0 0 6px;
    }
    
    div[data-testid="stHorizontalBlock"] [data-testid="stRadio"] > div > label:last-child {
        border-radius: 0 6px 6px 0;
    }
    
    /* ===== SECTION HEADERS ===== */
    .section-header {
        color: rgba(255,255,255,0.5) !important;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.75rem;
    }
    
    /* ===== COMING SOON ===== */
    .coming-soon {
        color: rgba(255,255,255,0.4) !important;
        font-style: italic;
    }
    
    /* ===== INFO BOXES (placeholders) ===== */
    .stAlert {
        background-color: #E8F4FD;
        border: 1px solid #B8DAFF;
        border-radius: 8px;
    }
    
    /* ===== CHECKBOX ===== */
    .stCheckbox label {
        color: #495057 !important;
    }
</style>
"""


def get_text(key: str, lang: str = "en") -> str:
    """Get translated text by key"""
    import json

    locale_file = Path(__file__).parent / "locales" / f"{lang}.json"
    if locale_file.exists():
        with open(locale_file, "r", encoding="utf-8") as f:
            translations = json.load(f)
            keys = key.split(".")
            value = translations
            for k in keys:
                value = value.get(k, key)
            return value if isinstance(value, str) else key
    return key
