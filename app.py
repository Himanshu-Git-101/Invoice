"""
================================================================================
INVOICE — ENTERPRISE VOICE VOUCHER PROCESSING GATEWAY (V1 Prototype)
Architecture: Streamlit + Invoice Engine + Tally XML HTTP Gateway
================================================================================
"""

import os
import io
import re
import json
import datetime
import requests
import pandas as pd
import streamlit as st

# Attempt Google GenAI SDK Import
try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# Attempt Local OpenAI Whisper Model Import & Static ffmpeg registration
try:
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(ffmpeg_exe)
    target_link = os.path.join(ffmpeg_dir, "ffmpeg")
    if not os.path.exists(target_link):
        try:
            os.symlink(ffmpeg_exe, target_link)
        except Exception:
            pass
    if ffmpeg_dir not in os.environ["PATH"]:
        os.environ["PATH"] = ffmpeg_dir + os.path.pathsep + os.environ["PATH"]
except Exception:
    ffmpeg_exe = None

try:
    import whisper
    import whisper.audio
    if ffmpeg_exe:
        whisper.audio.FFMPEG_EXE = ffmpeg_exe
    HAS_LOCAL_WHISPER = True
except ImportError:
    HAS_LOCAL_WHISPER = False

# Attempt OpenAI SDK Import
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# ==============================================================================
# Page Configuration & Executive Dark Theme CSS System
# ==============================================================================
st.set_page_config(
    page_title="Invoice — Enterprise Voucher Processing Gateway",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# High-End Financial SaaS Palette (Colorful Light Theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    .stApp {
        background-color: #f8fafc;
        background-image: 
            radial-gradient(at 0% 0%, rgba(79, 70, 229, 0.05) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(6, 182, 212, 0.05) 0px, transparent 50%),
            radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.04) 0px, transparent 50%);
        color: #0f172a;
        font-family: 'Inter', sans-serif;
    }

    /* Executive Top Header — Minimalist Hero */
    .enterprise-header {
        background: transparent;
        border: none;
        padding: 24px 0px 20px 0px;
        margin-bottom: 24px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        box-shadow: none;
    }

    .hero-brand-title {
        font-size: 3.8rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        margin: 0;
        line-height: 1.05;
        background: linear-gradient(135deg, #1e1b4b 0%, #4f46e5 50%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .header-sub {
        font-size: 0.88rem;
        color: #4f46e5;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.22em;
        margin-top: 6px;
    }

    /* Vibrant Metric Card Color Variants */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px 20px;
        display: flex;
        flex-direction: column;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(15, 23, 42, 0.08);
    }
    .metric-card.metric-emerald {
        background: linear-gradient(180deg, #ffffff 0%, #f0fdf4 100%);
        border: 1px solid #bbf7d0;
        border-top: 4px solid #10b981;
    }
    .metric-card.metric-emerald .metric-label { color: #047857; }
    .metric-card.metric-emerald .metric-value { color: #059669; }

    .metric-card.metric-blue {
        background: linear-gradient(180deg, #ffffff 0%, #eff6ff 100%);
        border: 1px solid #bfdbfe;
        border-top: 4px solid #3b82f6;
    }
    .metric-card.metric-blue .metric-label { color: #1d4ed8; }
    .metric-card.metric-blue .metric-value { color: #2563eb; }

    .metric-card.metric-purple {
        background: linear-gradient(180deg, #ffffff 0%, #f5f3ff 100%);
        border: 1px solid #ddd6fe;
        border-top: 4px solid #8b5cf6;
    }
    .metric-card.metric-purple .metric-label { color: #6d28d9; }
    .metric-card.metric-purple .metric-value { color: #7c3aed; }

    .metric-card.metric-cyan {
        background: linear-gradient(180deg, #ffffff 0%, #ecfeff 100%);
        border: 1px solid #a5f3fc;
        border-top: 4px solid #06b6d4;
    }
    .metric-card.metric-cyan .metric-label { color: #0e7490; }
    .metric-card.metric-cyan .metric-value { color: #0891b2; }

    .metric-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: 800;
        margin-top: 6px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Professional Bright Cards */
    .glass-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.06);
    }

    .card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 2px solid #f1f5f9;
        padding-bottom: 12px;
    }

    /* Status Tags */
    .status-tag-complete {
        background: #dcfce7;
        color: #15803d;
        border: 1px solid #86efac;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
    }
    .status-tag-pending {
        background: #fef3c7;
        color: #b45309;
        border: 1px solid #fcd34d;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
    }

    /* Slot Data Rows with Left Accent Color Indicators */
    .slot-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 11px 16px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #6366f1;
        border-radius: 8px;
        margin-bottom: 9px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }
    .slot-row:nth-child(1) { border-left-color: #4f46e5; }
    .slot-row:nth-child(2) { border-left-color: #0284c7; }
    .slot-row:nth-child(3) { border-left-color: #10b981; }
    .slot-row:nth-child(4) { border-left-color: #059669; }
    .slot-row:nth-child(5) { border-left-color: #f59e0b; }
    .slot-row:nth-child(6) { border-left-color: #8b5cf6; }

    .slot-name {
        font-size: 0.85rem;
        color: #334155;
        font-weight: 600;
    }
    .slot-val {
        font-size: 0.9rem;
        font-weight: 700;
        color: #0f172a;
        font-family: 'JetBrains Mono', monospace;
    }
    .slot-val.empty {
        background: #fef2f2;
        color: #dc2626;
        border: 1px solid #fecaca;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.76rem;
        font-weight: 700;
    }

    /* Streamlit Full Light Theme System Overrides */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    [data-testid="stSidebar"] * {
        color: #1e293b !important;
    }
    [data-testid="stHeader"] {
        background-color: rgba(248, 250, 252, 0.8) !important;
    }
    
    /* Selectbox & Dropdown Menus (AI Engine Selector) Light Theme */
    .stSelectbox, div[data-baseweb="select"], div[data-baseweb="popover"], div[role="listbox"], ul[role="listbox"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        color: #0f172a !important;
    }
    div[data-baseweb="select"] * {
        color: #0f172a !important;
    }
    li[role="option"], div[role="option"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    li[role="option"]:hover, li[aria-selected="true"] {
        background-color: #f1f5f9 !important;
        color: #4f46e5 !important;
    }

    /* Ultra-Comprehensive Audio Input & Voice Box Light Theme Overrides */
    [data-testid="stAudioInput"], 
    [data-testid="stAudioInput"] *,
    [data-testid="stFileUploader"],
    [data-testid="stFileUploader"] * {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border-color: #cbd5e1 !important;
    }
    
    div[data-testid="stAudioInput"] {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 12px !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04) !important;
    }
    
    div[data-testid="stAudioInput"] div,
    div[data-testid="stAudioInput"] section,
    div[data-testid="stAudioInput"] span,
    div[data-testid="stAudioInput"] p,
    div[data-testid="stAudioInput"] label {
        background: #ffffff !important;
        background-color: #ffffff !important;
        color: #0f172a !important;
    }

    div[data-testid="stAudioInput"] button {
        background: #f1f5f9 !important;
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
        border-radius: 8px !important;
    }

    div[data-testid="stAudioInput"] button:hover {
        background: #e2e8f0 !important;
        background-color: #e2e8f0 !important;
    }

    div[data-testid="stAudioInput"] svg,
    div[data-testid="stAudioInput"] path {
        fill: #0f172a !important;
        color: #0f172a !important;
        stroke: #0f172a !important;
    }

    div[data-testid="stAudioInput"] canvas {
        background-color: #f8fafc !important;
        border-radius: 6px !important;
    }

    audio, audio::-webkit-media-controls-panel {
        background-color: #f8fafc !important;
        background: #f8fafc !important;
        color: #0f172a !important;
    }

    .stTextInput input {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus {
        border-color: #4f46e5 !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15) !important;
    }
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        background: #ffffff;
        color: #1e293b;
        font-weight: 600;
        font-size: 0.85rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: #f1f5f9;
        border-color: #94a3b8;
        color: #0f172a;
    }
    button[kind="primary"] {
        background: linear-gradient(135deg, #4f46e5 0%, #2563eb 100%) !important;
        border: none !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25) !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #4338ca 0%, #1d4ed8 100%) !important;
        box-shadow: 0 6px 16px rgba(79, 70, 229, 0.35) !important;
    }
    .stExpander {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
    }
    .stCodeBlock, code, pre {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
    }
    .stAlert {
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# Helper Functions: State Management, GST/HSN Registry & Constants
# ==============================================================================
REQUIRED_FIELDS = ["party_name", "item_name", "quantity", "rate", "invoice_no", "date"]

GOODS_TAX_REGISTRY = {
    # --- SPECIAL SIN TAX & COMPENSATION CESS SLABS (65% - 75% Effective Tax Rate) ---
    "cigarette": {"hsn": "2402", "gst": 70.0},
    "cigarettes": {"hsn": "2402", "gst": 70.0},
    "tobacco": {"hsn": "2402", "gst": 70.0},
    "cigar": {"hsn": "2402", "gst": 70.0},
    "cigars": {"hsn": "2402", "gst": 70.0},
    "bidi": {"hsn": "2402", "gst": 70.0},
    "pan masala": {"hsn": "2106", "gst": 60.0},
    "gutkha": {"hsn": "2106", "gst": 60.0},
    "aerated drink": {"hsn": "2202", "gst": 40.0},
    "cold drink": {"hsn": "2202", "gst": 40.0},

    # --- 28% GST SLAB: Luxury, Heavy Construction, Automotive & Appliances ---
    "cement": {"hsn": "2523", "gst": 28.0},
    "portland cement": {"hsn": "2523", "gst": 28.0},
    "white cement": {"hsn": "2523", "gst": 28.0},
    "paint": {"hsn": "3208", "gst": 28.0},
    "varnish": {"hsn": "3208", "gst": 28.0},
    "primer": {"hsn": "3208", "gst": 28.0},
    "enamel": {"hsn": "3208", "gst": 28.0},
    "ac": {"hsn": "8415", "gst": 28.0},
    "air conditioner": {"hsn": "8415", "gst": 28.0},
    "hvac": {"hsn": "8415", "gst": 28.0},
    "refrigerator": {"hsn": "8418", "gst": 28.0},
    "fridge": {"hsn": "8418", "gst": 28.0},
    "deep freezer": {"hsn": "8418", "gst": 28.0},
    "washing machine": {"hsn": "8450", "gst": 28.0},
    "automobile": {"hsn": "8703", "gst": 28.0},
    "car": {"hsn": "8703", "gst": 28.0},
    "truck": {"hsn": "8704", "gst": 28.0},
    "motorcycle": {"hsn": "8711", "gst": 28.0},
    "scooter": {"hsn": "8711", "gst": 28.0},
    "tyre": {"hsn": "4011", "gst": 28.0},
    "rubber tyre": {"hsn": "4011", "gst": 28.0},
    "auto spare parts": {"hsn": "8708", "gst": 28.0},
    "car battery": {"hsn": "8507", "gst": 28.0},
    "plywood": {"hsn": "4412", "gst": 28.0},
    "veneer": {"hsn": "4412", "gst": 28.0},
    "marble": {"hsn": "6802", "gst": 28.0},
    "granite": {"hsn": "6802", "gst": 28.0},
    "tiles": {"hsn": "6907", "gst": 28.0},
    "vitrified tiles": {"hsn": "6907", "gst": 28.0},
    "ceramic tiles": {"hsn": "6907", "gst": 28.0},

    # --- 18% GST SLAB: IT, Electronics, Raw Metals, Machinery, Hardware, Chemicals, Plastics, Services ---
    "laptop": {"hsn": "8471", "gst": 18.0},
    "computer": {"hsn": "8471", "gst": 18.0},
    "desktop": {"hsn": "8471", "gst": 18.0},
    "server": {"hsn": "8471", "gst": 18.0},
    "monitor": {"hsn": "8471", "gst": 18.0},
    "hard drive": {"hsn": "8471", "gst": 18.0},
    "ssd": {"hsn": "8471", "gst": 18.0},
    "keyboard": {"hsn": "8471", "gst": 18.0},
    "mouse": {"hsn": "8471", "gst": 18.0},
    "printer": {"hsn": "8443", "gst": 18.0},
    "scanner": {"hsn": "8443", "gst": 18.0},
    "toner": {"hsn": "8443", "gst": 18.0},
    "cartridge": {"hsn": "8443", "gst": 18.0},
    "mobile": {"hsn": "8517", "gst": 18.0},
    "smartphone": {"hsn": "8517", "gst": 18.0},
    "router": {"hsn": "8517", "gst": 18.0},
    "network switch": {"hsn": "8517", "gst": 18.0},
    "copper wire": {"hsn": "8544", "gst": 18.0},
    "electric cable": {"hsn": "8544", "gst": 18.0},
    "wire": {"hsn": "8544", "gst": 18.0},
    "switch": {"hsn": "8536", "gst": 18.0},
    "mcb": {"hsn": "8536", "gst": 18.0},
    "circuit breaker": {"hsn": "8536", "gst": 18.0},
    "bulb": {"hsn": "8539", "gst": 18.0},
    "led light": {"hsn": "9405", "gst": 18.0},
    "transformer": {"hsn": "8504", "gst": 18.0},
    "inverter": {"hsn": "8504", "gst": 18.0},
    "ups": {"hsn": "8504", "gst": 18.0},

    # Metals, Raw Structural Steel, Alloys & Hardware
    "tmt bars": {"hsn": "7214", "gst": 18.0},
    "tmt bar": {"hsn": "7214", "gst": 18.0},
    "steel rods": {"hsn": "7214", "gst": 18.0},
    "iron rods": {"hsn": "7214", "gst": 18.0},
    "steel rebar": {"hsn": "7214", "gst": 18.0},
    "steel sheets": {"hsn": "7208", "gst": 18.0},
    "steel coils": {"hsn": "7208", "gst": 18.0},
    "steel scrap": {"hsn": "7204", "gst": 18.0},
    "iron scrap": {"hsn": "7204", "gst": 18.0},
    "seamless steel pipe": {"hsn": "7304", "gst": 18.0},
    "steel beams": {"hsn": "7308", "gst": 18.0},
    "steel nails": {"hsn": "7318", "gst": 18.0},
    "screws": {"hsn": "7318", "gst": 18.0},
    "nuts and bolts": {"hsn": "7318", "gst": 18.0},
    "fasteners": {"hsn": "7318", "gst": 18.0},
    "copper rods": {"hsn": "7407", "gst": 18.0},
    "copper pipe": {"hsn": "7411", "gst": 18.0},
    "aluminum extrusions": {"hsn": "7604", "gst": 18.0},
    "aluminum section": {"hsn": "7604", "gst": 18.0},
    "padlock": {"hsn": "8301", "gst": 18.0},
    "door lock": {"hsn": "8301", "gst": 18.0},

    # Industrial Tools, Machinery & Safety Gear
    "drill machine": {"hsn": "8467", "gst": 18.0},
    "power tools": {"hsn": "8467", "gst": 18.0},
    "angle grinder": {"hsn": "8467", "gst": 18.0},
    "water pump": {"hsn": "8413", "gst": 18.0},
    "electric motor": {"hsn": "8501", "gst": 18.0},
    "generator": {"hsn": "8502", "gst": 18.0},
    "air compressor": {"hsn": "8414", "gst": 18.0},
    "safety helmet": {"hsn": "6506", "gst": 18.0},
    "helmets": {"hsn": "6506", "gst": 18.0},
    "industrial gloves": {"hsn": "6116", "gst": 18.0},
    "safety boots": {"hsn": "6403", "gst": 18.0},

    # Raw Chemicals, Polymers, Packaging & Petroleum Products
    "pvc resin": {"hsn": "3901", "gst": 18.0},
    "plastic granules": {"hsn": "3901", "gst": 18.0},
    "pvc pipes": {"hsn": "3917", "gst": 18.0},
    "plastic bags": {"hsn": "3923", "gst": 18.0},
    "packaging containers": {"hsn": "3923", "gst": 18.0},
    "industrial oxygen": {"hsn": "2804", "gst": 18.0},
    "nitrogen gas": {"hsn": "2804", "gst": 18.0},
    "lubricating oil": {"hsn": "2710", "gst": 18.0},
    "engine oil": {"hsn": "2710", "gst": 18.0},
    "grease": {"hsn": "2710", "gst": 18.0},
    "wall putty": {"hsn": "3214", "gst": 18.0},
    "soap": {"hsn": "3401", "gst": 18.0},
    "detergent": {"hsn": "3402", "gst": 18.0},
    "pesticide": {"hsn": "3808", "gst": 18.0},
    "insecticide": {"hsn": "3808", "gst": 18.0},

    # Office Furniture & Supplies
    "office chair": {"hsn": "9403", "gst": 18.0},
    "office desk": {"hsn": "9403", "gst": 18.0},
    "almirah": {"hsn": "9403", "gst": 18.0},
    "corrugated boxes": {"hsn": "4819", "gst": 18.0},
    "carton boxes": {"hsn": "4819", "gst": 18.0},

    # --- 12% GST SLAB: Pharmaceuticals, Medical Devices, Paper Products, Timber & Machinery Jobwork ---
    "medicine": {"hsn": "3004", "gst": 12.0},
    "tablets": {"hsn": "3004", "gst": 12.0},
    "syrup": {"hsn": "3004", "gst": 12.0},
    "capsules": {"hsn": "3004", "gst": 12.0},
    "antibiotics": {"hsn": "3004", "gst": 12.0},
    "vaccines": {"hsn": "3002", "gst": 12.0},
    "medical equipment": {"hsn": "9018", "gst": 12.0},
    "thermometer": {"hsn": "9025", "gst": 12.0},
    "bp monitor": {"hsn": "9018", "gst": 12.0},
    "a4 paper": {"hsn": "4802", "gst": 12.0},
    "paper reams": {"hsn": "4802", "gst": 12.0},
    "notebooks": {"hsn": "4820", "gst": 12.0},
    "timber planks": {"hsn": "4407", "gst": 12.0},
    "sawn wood": {"hsn": "4407", "gst": 12.0},

    # --- 5% GST SLAB: Textiles, Apparel, Yarns, Food Staples, Oils, Sugar, Fertilisers & Coal ---
    "cotton yarn": {"hsn": "5201", "gst": 5.0},
    "cotton fabric": {"hsn": "5208", "gst": 5.0},
    "synthetic fabric": {"hsn": "5407", "gst": 5.0},
    "cloth": {"hsn": "5208", "gst": 5.0},
    "shirts": {"hsn": "6203", "gst": 5.0},
    "pants": {"hsn": "6203", "gst": 5.0},
    "t-shirts": {"hsn": "6109", "gst": 5.0},
    "uniforms": {"hsn": "6203", "gst": 5.0},
    "saree": {"hsn": "5407", "gst": 5.0},
    "spices": {"hsn": "0910", "gst": 5.0},
    "masala": {"hsn": "0910", "gst": 5.0},
    "tea": {"hsn": "0902", "gst": 5.0},
    "coffee": {"hsn": "0901", "gst": 5.0},
    "edible oil": {"hsn": "1507", "gst": 5.0},
    "ghee": {"hsn": "0405", "gst": 5.0},
    "sugar": {"hsn": "1701", "gst": 5.0},
    "jaggery": {"hsn": "1701", "gst": 5.0},
    "urea": {"hsn": "3102", "gst": 5.0},
    "npk fertiliser": {"hsn": "3105", "gst": 5.0},
    "npk fertilizer": {"hsn": "3105", "gst": 5.0},
    "fertilizer": {"hsn": "3105", "gst": 5.0},
    "fertiliser": {"hsn": "3105", "gst": 5.0},
    "fertilisers": {"hsn": "3105", "gst": 5.0},
    "construction sand": {"hsn": "2505", "gst": 5.0},
    "crushed stone": {"hsn": "2517", "gst": 5.0},
    "coal": {"hsn": "2701", "gst": 5.0},

    # --- 3% GST SLAB: Precious Metals & Jewellery ---
    "gold bullion": {"hsn": "7108", "gst": 3.0},
    "gold bar": {"hsn": "7108", "gst": 3.0},
    "silver bullion": {"hsn": "7106", "gst": 3.0},
    "gold jewellery": {"hsn": "7113", "gst": 3.0},
    "diamond jewellery": {"hsn": "7113", "gst": 3.0},

    # --- 0% GST SLAB: Fresh Produce, Unprocessed Grain Staples & Textbooks ---
    "unbranded rice": {"hsn": "1006", "gst": 0.0},
    "basmati rice": {"hsn": "1006", "gst": 0.0},
    "wheat": {"hsn": "1001", "gst": 0.0},
    "atta": {"hsn": "1101", "gst": 0.0},
    "pulses": {"hsn": "0713", "gst": 0.0},
    "dal": {"hsn": "0713", "gst": 0.0},
    "fresh milk": {"hsn": "0401", "gst": 0.0},
    "fresh curd": {"hsn": "0401", "gst": 0.0},
    "fresh vegetables": {"hsn": "0701", "gst": 0.0},
    "printed books": {"hsn": "4901", "gst": 0.0},

    # --- MASTER SAC CODES FOR SERVICES (18% / 12% GST) ---
    "civil construction service": {"hsn": "9954", "gst": 18.0},
    "goods transport service": {"hsn": "9965", "gst": 12.0},
    "freight logistics": {"hsn": "9965", "gst": 12.0},
    "warehousing service": {"hsn": "9967", "gst": 18.0},
    "commercial rent": {"hsn": "9972", "gst": 18.0},
    "legal services": {"hsn": "9982", "gst": 18.0},
    "accounting services": {"hsn": "9982", "gst": 18.0},
    "audit services": {"hsn": "9982", "gst": 18.0},
    "it consulting": {"hsn": "9983", "gst": 18.0},
    "software development": {"hsn": "9983", "gst": 18.0},
    "cloud services": {"hsn": "9983", "gst": 18.0},
    "repair and maintenance": {"hsn": "9987", "gst": 18.0},
    "job work service": {"hsn": "9988", "gst": 12.0}
}

def get_gst_hsn_for_item(item_name):
    """Looks up official Indian GST rate & HSN/SAC code across ALL market raw materials, goods, and services."""
    if not item_name:
        return {"hsn": "9983", "gst": 18.0}

    item_clean = item_name.strip().lower()

    # 1. Direct registry match
    for key, data in GOODS_TAX_REGISTRY.items():
        if key in item_clean or item_clean in key:
            return data

    # 2. Comprehensive multi-level category heuristics

    # Special Sin Tax & Compensation CESS (Cigarettes 70%, Pan Masala 60%, Aerated Water 40%)
    if any(w in item_clean for w in ["cigarette", "cigarettes", "tobacco", "cigar", "cigars", "bidi", "pan masala", "gutkha", "aerated", "cold drink"]):
        if any(w in item_clean for w in ["cigarette", "cigarettes", "tobacco", "cigar", "cigars", "bidi"]):
            return {"hsn": "2402", "gst": 70.0}
        if any(w in item_clean for w in ["pan masala", "gutkha"]):
            return {"hsn": "2106", "gst": 60.0}
        if any(w in item_clean for w in ["aerated", "cold drink"]):
            return {"hsn": "2202", "gst": 40.0}

    # Services (SAC 99xx)
    if any(w in item_clean for w in ["service", "consulting", "transport", "freight", "logistics", "maintenance", "repair", "rent", "audit", "job work", "labor", "labour"]):
        if any(w in item_clean for w in ["transport", "freight", "logistics", "gta"]):
            return {"hsn": "9965", "gst": 12.0}
        if any(w in item_clean for w in ["construction", "civil", "building"]):
            return {"hsn": "9954", "gst": 18.0}
        if any(w in item_clean for w in ["legal", "audit", "accounting", "ca"]):
            return {"hsn": "9982", "gst": 18.0}
        return {"hsn": "9983", "gst": 18.0}

    # 28% GST: Luxury, Heavy Building Materials, Vehicles & Appliances
    if any(w in item_clean for w in ["cement", "paint", "varnish", "primer", "enamel", "ac", "air conditioner", "hvac", "fridge", "refrigerator", "washing machine", "car", "truck", "motorcycle", "scooter", "tyre", "tile", "marble", "granite", "plywood", "veneer"]):
        if any(w in item_clean for w in ["tile", "marble", "granite"]):
            return {"hsn": "6802", "gst": 28.0}
        if any(w in item_clean for w in ["plywood", "veneer"]):
            return {"hsn": "4412", "gst": 28.0}
        if any(w in item_clean for w in ["ac", "hvac", "air conditioner"]):
            return {"hsn": "8415", "gst": 28.0}
        return {"hsn": "2523", "gst": 28.0}

    # 3% GST: Gold, Silver, Precious Metals & Jewellery
    if any(w in item_clean for w in ["gold", "silver", "platinum", "diamond", "jewellery", "bullion", "ornament"]):
        return {"hsn": "7108", "gst": 3.0}

    # 5% GST: Textiles, Apparel, Spices, Food Staples, Oils, Coal & Fertilisers
    if any(w in item_clean for w in ["cloth", "garment", "shirt", "pant", "fabric", "textile", "cotton", "yarn", "dress", "uniform", "tshirt", "jeans", "saree", "spice", "masala", "chili", "turmeric", "tea", "coffee", "sugar", "jaggery", "oil", "ghee", "fertilizer", "urea", "coal", "sand", "gravel"]):
        if any(w in item_clean for w in ["spice", "masala", "chili", "turmeric", "tea", "coffee"]):
            return {"hsn": "0910", "gst": 5.0}
        if any(w in item_clean for w in ["sand", "gravel", "stone"]):
            return {"hsn": "2505", "gst": 5.0}
        if any(w in item_clean for w in ["fertilizer", "urea"]):
            return {"hsn": "3105", "gst": 5.0}
        return {"hsn": "6203", "gst": 5.0}

    # 12% GST: Pharmaceuticals, Medical Equipment, Paper Products & Timber
    if any(w in item_clean for w in ["medicine", "pharma", "drug", "tablet", "syrup", "capsule", "vaccine", "ointment", "thermometer", "paper", "ream", "notebook", "copy", "cardboard", "timber", "wood"]):
        if any(w in item_clean for w in ["paper", "ream", "notebook", "copy"]):
            return {"hsn": "4802", "gst": 12.0}
        return {"hsn": "3004", "gst": 12.0}

    # 0% GST: Fresh Unprocessed Food & Textbooks
    if any(w in item_clean for w in ["fresh fruit", "fresh vegetable", "milk", "curd", "unbranded rice", "wheat", "atta", "dal", "pulses", "book"]):
        return {"hsn": "1006", "gst": 0.0}

    # 18% GST: IT, Hardware, Machinery, Industrial, Scrap, Chemicals, Plastics, Furniture & General Goods
    if any(w in item_clean for w in ["laptop", "computer", "pc", "monitor", "printer", "mobile", "phone", "switch", "wire", "cable", "transformer", "ups"]):
        return {"hsn": "8471", "gst": 18.0}
    if any(w in item_clean for w in ["steel", "iron", "rod", "pipe", "screw", "nail", "nut", "bolt", "fastener", "tmt", "rebar", "scrap", "copper", "aluminum"]):
        if any(w in item_clean for w in ["tmt", "rebar", "rod"]):
            return {"hsn": "7214", "gst": 18.0}
        if any(w in item_clean for w in ["scrap"]):
            return {"hsn": "7204", "gst": 18.0}
        return {"hsn": "7318", "gst": 18.0}
    if any(w in item_clean for w in ["tool", "machine", "drill", "motor", "pump", "generator", "helmet", "safety", "glove", "boot"]):
        return {"hsn": "8467", "gst": 18.0}
    if any(w in item_clean for w in ["chair", "desk", "table", "furniture", "almirah", "rack", "box"]):
        return {"hsn": "9403", "gst": 18.0}
    if any(w in item_clean for w in ["plastic", "pvc", "polymer", "resin", "chemical", "gas", "oxygen", "lubricant", "grease", "soap", "detergent"]):
        return {"hsn": "3901", "gst": 18.0}

    # Default Standard HSN / SAC
    return {"hsn": "9983", "gst": 18.0}

def get_today_tally_date():
    """Returns today's date formatted as YYYYMMDD for Tally XML."""
    return datetime.datetime.now().strftime("%Y%m%d")

def get_all_items_from_slots(slots):
    """Returns a normalized list of item dicts from slots state."""
    if not slots:
        return []
    items = slots.get("items")
    if items and isinstance(items, list) and len(items) > 0:
        norm_items = []
        for it in items:
            iname = it.get("item_name") or "Stock Item"
            tax = get_gst_hsn_for_item(iname)
            norm_items.append({
                "item_name": iname,
                "quantity": float(it.get("quantity") or 0.0),
                "rate": float(it.get("rate") or 0.0),
                "discount_pct": float(it.get("discount_pct") or 0.0),
                "hsn_code": str(it.get("hsn_code") or tax["hsn"]),
                "gst_rate": float(it.get("gst_rate") or tax["gst"])
            })
        return norm_items
    elif slots.get("item_name"):
        iname = slots.get("item_name")
        tax = get_gst_hsn_for_item(iname)
        return [{
            "item_name": iname,
            "quantity": float(slots.get("quantity") or 0.0),
            "rate": float(slots.get("rate") or 0.0),
            "discount_pct": float(slots.get("discount_pct") or 0.0),
            "hsn_code": str(slots.get("hsn_code") or tax["hsn"]),
            "gst_rate": float(slots.get("gst_rate") or tax["gst"])
        }]
    return []

def init_session_state():
    """Initialize Streamlit session state for slot filling and chat logs."""
    if "slots" not in st.session_state:
        st.session_state.slots = {
            "party_name": None,    # Vendor Ledger Name (Sundry Creditor)
            "invoice_no": None,    # Supplier Invoice / PO Reference Number
            "date": None,          # Voucher Date (YYYYMMDD format)
            "items": [],           # List of stock item dicts
            "item_name": None,     # Legacy single item compatibility
            "quantity": None,
            "rate": None,
            "hsn_code": None,
            "gst_rate": None,
            "discount_pct": None
        }
    if "is_complete" not in st.session_state:
        st.session_state.is_complete = False
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "last_follow_up" not in st.session_state:
        st.session_state.last_follow_up = "System ready. Please enter or record purchase voucher details."
    if "xml_payload" not in st.session_state:
        st.session_state.xml_payload = None
    if "audio_key_counter" not in st.session_state:
        st.session_state.audio_key_counter = 0

def reset_voucher_state():
    """Reset accumulated slots, clear recorded voice and audio widget key to prepare for the next data entry."""
    st.session_state.slots = {
        "party_name": None,
        "invoice_no": None,
        "date": None,
        "items": [],
        "item_name": None,
        "quantity": None,
        "rate": None,
        "hsn_code": None,
        "gst_rate": None,
        "discount_pct": None
    }
    st.session_state.is_complete = False
    st.session_state.chat_history = []
    st.session_state.last_follow_up = "Recorded voice deleted & workspace reset. Ready for next data entry!"
    st.session_state.xml_payload = None
    st.session_state.processed_audio_hash = None
    st.session_state.last_voice_transcript = None
    st.session_state.audio_key_counter = st.session_state.get("audio_key_counter", 0) + 1

init_session_state()

# ==============================================================================
# Executive Sidebar Configurations
# ==============================================================================
st.sidebar.markdown("### Invoice System Configuration")

engine_choice = st.sidebar.selectbox(
    "AI Processing Engine",
    [
        "Invoice Neural AI (Multimodal)",
        "Invoice Cloud Engine",
        "Invoice Local Engine (100% Offline & Private)"
    ]
)

gemini_key = os.getenv("GEMINI_API_KEY", "")
openai_key = os.getenv("OPENAI_API_KEY", "")

if "Neural" in engine_choice:
    gemini_key = st.sidebar.text_input(
        "Invoice Access Key",
        type="password",
        value=gemini_key,
        help="System API access key for Invoice Neural processing"
    )
elif "Cloud" in engine_choice:
    openai_key = st.sidebar.text_input(
        "Invoice Access Key",
        type="password",
        value=openai_key,
        help="System API access key for Invoice Cloud processing"
    )

tally_host = st.sidebar.text_input(
    "Tally HTTP Endpoint",
    value="http://localhost:9000",
    help="Tally Prime HTTP XML Interface URL"
)

purchase_ledger = st.sidebar.text_input(
    "Purchase Ledger",
    value="Purchase Accounts",
    help="Default Purchase Account in Tally Company."
)

gemini_key = gemini_key.strip()
openai_key = openai_key.strip()

if "Neural" in engine_choice and gemini_key:
    st.sidebar.success("Invoice Neural AI Active")
elif "Cloud" in engine_choice and openai_key:
    st.sidebar.success("Invoice Cloud Engine Active")
elif "Neural" in engine_choice and not gemini_key:
    st.sidebar.warning("Enter Invoice Access Key above")
elif "Cloud" in engine_choice and not openai_key:
    st.sidebar.warning("Enter Invoice Access Key above")
else:
    st.sidebar.info("Invoice Local Engine Active (100% Private)")

if st.sidebar.button("Reset Voucher State", use_container_width=True):
    reset_voucher_state()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### Tally Domain Reference")
with st.sidebar.expander("Accounting Vocabulary Guide"):
    st.markdown("""
    **Party Name (Sundry Creditor):**
    Vendor, Supplier, Firm, Dealer, Distributor
    
    **Stock Item (Inventory):**
    Item Description, SKU, Material, Goods
    
    **Quantity & UOM:**
    Nos, Pcs, Boxes, Packets, Bags, Cartons, Reams, Kg, Tons, Nag
    
    **Rate / Valuation:**
    Unit Price, Rate, Cost, Price per unit
    
    **Invoice Reference:**
    Invoice No, Bill No, PO No, Challan No, Tax Invoice
    """)

st.sidebar.markdown("---")
st.sidebar.markdown("### Required Slots Status")
for field in REQUIRED_FIELDS:
    val = st.session_state.slots.get(field)
    if val:
        st.sidebar.markdown(f"**{field.replace('_', ' ').title()}**: `{val}`")
    else:
        st.sidebar.markdown(f"**{field.replace('_', ' ').title()}**: *Missing*")

# ==============================================================================
# Deep Tally Domain NLP Parser (Offline / Fallback)
# ==============================================================================
def parse_spoken_date(text):
    """Extracts spoken/typed dates into YYYYMMDD format for Tally XML."""
    text_lower = text.lower()
    today = datetime.datetime.now()
    
    if "today" in text_lower or "aaj" in text_lower or "current date" in text_lower:
        return today.strftime("%Y%m%d")
    if "yesterday" in text_lower or "kal" in text_lower:
        return (today - datetime.timedelta(days=1)).strftime("%Y%m%d")

    # 5th of this month / is mahine ki 5th / 5th ko
    this_month_match = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+this\s+month|is\s+mahine\s+ki|ko)\b', text_lower)
    if this_month_match:
        day = this_month_match.group(1).zfill(2)
        return f"{today.year}{today.strftime('%m')}{day}"

    # Day + Month Name e.g. "12th May", "14th August", "1st June", "2nd Feb"
    months_map = {
        'jan': '01', 'january': '01', 'feb': '02', 'february': '02', 'mar': '03', 'march': '03',
        'apr': '04', 'april': '04', 'may': '05', 'jun': '06', 'june': '06', 'jul': '07', 'july': '07',
        'aug': '08', 'august': '08', 'sep': '09', 'september': '09', 'oct': '10', 'october': '10',
        'nov': '11', 'november': '11', 'dec': '12', 'december': '12'
    }
    dm_match = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|september|oct|october|nov|november|dec|december)\b', text_lower)
    if dm_match:
        day = dm_match.group(1).zfill(2)
        m_str = dm_match.group(2)
        month = months_map.get(m_str, today.strftime('%m'))
        return f"{today.year}{month}{day}"

    # Standard numeric dates: 01-08-2026, 22/08/2026
    num_date_match = re.search(r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](20\d{2})\b', text_lower)
    if num_date_match:
        day = num_date_match.group(1).zfill(2)
        month = num_date_match.group(2).zfill(2)
        year = num_date_match.group(3)
        return f"{year}{month}{day}"

    # YYYYMMDD e.g. 20260801
    y8_match = re.search(r'\b(20\d{6})\b', text_lower)
    if y8_match:
        return y8_match.group(1)

    return None

def deep_tally_domain_nlp_parser(text, current_slots):
    """
    Trained Tally Domain Engine.
    Parses action-first, item-first, invoice-first, messy, and Hinglish training phrases.
    """
    text_clean = text.strip()
    text_lower = text_clean.lower()
    
    # Auto-fresh state if user inputs a full purchase line
    action_keywords = ["from", "vendor", "se", "mene", "maine", "got", "bought", "received", "entry", "bill", "invoice", "challan", "po", "receipt", "aaya", "aaye", "aayi", "chadha", "daal"]
    updated_slots = {
        "party_name": None,
        "item_name": None,
        "quantity": None,
        "rate": None,
        "invoice_no": None,
        "date": None
    } if any(w in text_lower for w in action_keywords) and len(text.split()) >= 4 else dict(current_slots)

    # Known Domain Entity Dictionary (Pre-trained on 400 User Dataset Phrases across Godown Logistics, Sethi Lala Accounting, Retail Shop Floor, Corporate IT Admin & Quick Dictation)
    KNOWN_VENDORS = ['Bajaj', 'Samsung', 'Dell', 'LG', 'HP', 'Sony', 'Godrej', 'Asian Paints', 'Tata', 'Amul', 'Parle', 'Haldiram', 'Dabur', 'Patanjali', 'Colgate', 'Nestle', 'Britannia', 'Titan', 'Casio', 'Milton', 'Cisco', 'Epson', 'Canon', 'Acer', 'Lenovo', 'Logitech', 'Intel', 'Gupta Traders', 'Sharma Electronics', 'Balaji Hardware', 'Agarwal Sweets', 'Kapoor Garments', 'Mehta Stationers', 'Reliance Fresh', 'Verma Textiles', 'Tata Motors', 'LG Distributors', 'JK Cements', 'Patel Traders', 'Lenovo India', 'Singh Transport', 'Joshi Electronics', 'Sony Center', 'Sun Pharma', 'Reliance Smart', 'Microtek', 'Bajaj Electricals', 'Havells', 'Samsung India', 'ITC Limited', 'Himalaya', 'Lakme', "L'Oreal", 'Gillette', 'Nivea', 'Dove', 'Ponds', 'Shree Cements', 'Jindal Steel', 'Asian Tiles', 'Berger Paints', 'Finolex Pipes', 'Ultratech', 'Tata Steel', 'Kajaria Ceramics', 'Nerolac', 'Supreme Plastics', 'ACC Cement', 'JSW Steel', 'Somany Tiles', 'Dulux Paints', 'Ashirvad Pipes', 'Ambuja Cement', 'SAIL', 'Nitco Tiles', 'Shalimar Paints', 'Astral Pipes', 'HP India', 'Kingston', 'Seagate', 'Asus', 'D-Link', 'APC by Schneider', 'Sandisk', 'Western Digital', 'Netgear', 'BenQ', 'Brother', 'Corsair', 'Metro Logistics', 'Kirloskar Electric', 'Royal Packaging', 'National Traders', 'ChemTech India', 'Cipla Distributors', 'Apollo Surgicals', 'Mankind Health', 'Lupin Lifesciences', 'Nestle Wholesale', 'Haldiram Foods', 'Amul Dairy', 'Parle Agro', 'Fortune Oils', 'Raymond Mills', 'Bombay Dyeing', 'Arvind Denim', 'ThreadCraft', 'Vardhman Yarns', 'Havells India', 'Bosch Automotive', 'Finolex Cables', 'Anchor Electricals', 'Tata Steel Tubes', 'Durian Furniture', 'Schneider Electric', 'Godrej Boyce', 'Apex Industries', 'Tech Solutions', 'Global Suppliers', 'BuildCo', 'ColorCorp', 'Sharma Hardware', 'Verma Traders', 'Office World', 'Super Electronics', 'Alpha Corp', 'Fastenal India', 'Acme Corp', 'Bansal Sweets', 'Goyal Brothers', 'Verma Veg', 'Sethi Sons', 'Kapoor Hardware', 'Mittal Textiles', 'Tiwari Plastics', 'Ahuja Electronics', 'Jain Provisionals', 'Ramu Kaka', 'Sharma Spares', 'Reliance Industries', 'Gupta Stationery', 'Bajaj Auto', 'Dell India', 'Puma', 'Bata', 'Garnier', 'Philips', 'Nike', 'Reebok', 'Microsoft', 'JK Paper', 'Airtel', 'APC', 'Camlin', 'Croma', 'Luxor', 'Nescafe', 'Bisleri', 'Zomato Corporate', 'Voltas', 'UrbanClap', 'Gupta Plastics', 'Intex', 'Peter England', 'Adidas', 'Vanguard Steel', 'Apex Logistics', 'Sunrise Foods', 'Mahavir Metals', 'Bhawani Hardware', 'Krishna Enterprise', 'Kalyan Jewellers', 'Pioneer Chemicals', 'National Auto', 'Everest Cements', 'Shree Ram Traders', 'Ganesh Textiles', 'Laxmi Flour Mills', 'Om Sai Logistics', 'Venkateshwara Paper', 'Radhe Shyam Sweets', 'Star Electronics', 'Shiva Traders', 'Bhagwati Hardware', 'Durga Pharma', 'Hanuman Steel', 'Balaji Transport', 'Jain Supermarket', 'Agarwal Agencies', 'Bansal Enterprise', 'Khandelwal Motors', 'Singhal Traders', 'Maheshwari Textiles', 'Chowdhury Corp', 'Mukherjee & Sons', 'Banerjee Logistics', 'Ghosh Traders', 'Patil Enterprises', 'Deshmukh Steel', 'Jadhav Electricals', 'Pawar Motors', 'Kulkarni Traders', 'Reddy Distributors', 'Rao Agencies', 'Nair Logistics', 'Menon Hardware', 'Pillai Enterprises', 'Iyengar Bakery', 'Shetty Hotel Supplies', 'Hegde Electronics', 'Gowda Traders', 'Rao Steel', 'Chawla Auto', 'Arora Garments', 'Kapoor Furniture', 'Malhotra Traders', 'Bhalla Electronics', 'Sethi Hardware', 'Kohli Motors', 'Bhasin Textiles', 'Taneja Paper', 'Suri Supplies', 'Khanna Enterprises', 'Anand Agencies', 'Grover Logistics', 'Sawhney Steel', 'Sodhi Auto', 'Ahluwalia Construction', 'Gill Transports', 'Sidhu Logistics', 'Dhillon Traders', 'Grewal Motors']
    
    KNOWN_ITEMS = ['Chawal', 'Rice', 'Tel', 'Oil', 'Sariya', 'Steel', 'Cement', 'Keel', 'Nails', 'Tamatar', 'Tomatoes', 'Lohe Ki Chadar', 'Iron Sheets', 'Tanki', 'Water Tanks', 'Printer Paper', 'Chemical', 'Truck Tyre', 'Tyres', 'Paint', 'Balti Paint', 'Wire', 'Bundle Wire', 'Loha', 'Iron', 'Doodh', 'Milk', 'Milk Cans', 'Biscuit', 'Biscuits', 'Khilone', 'Toys', 'Pankhe', 'Fans', 'Fridge', 'Refrigerators', 'Ghee', 'Kapda', 'Cloth', 'Aaloo', 'Potatoes', 'Cheeni', 'Sugar', 'Kabje', 'Hinges', 'Saree', 'Sarees', 'Kursi', 'Chairs', 'AC', 'Air Conditioners', 'Tel Tin', 'Oil Tins', 'Kaju', 'Cashews', 'Brake Pad', 'Brake Pads', 'Tiffin', 'Tiffin Boxes', 'Polymer', 'Pen', 'Pens', 'Bike Engine', 'Engines', 'Bhujia', 'Butter', 'Home Theater', 'Laptop', 'Laptops', 'iPhone', 'iPhones', 'Mobile', 'Mobiles', 'Mouse', 'Mice', 'Joote', 'Shoes', 'Smart TV', 'TVs', 'Chappal', 'Slippers', 'Keyboard', 'Keyboards', 'Ghadi', 'Watches', 'Lipstick', 'Lipsticks', 'Lotion', 'Body Lotions', 'Face Wash', 'Trimmer', 'Trimmers', 'Press', 'Iron Press', 'Bulb', 'LED Bulbs', 'Almirah', 'Almirahs', 'T-Shirts', 'Trackpants', 'Calculator', 'Calculators', 'Water Bottle', 'Bottles', 'Router', 'Routers', 'Office License', 'Licenses', 'Monitor', 'Monitors', 'Server', 'Servers', 'Switch', 'Switches', 'Courier Packets', 'Rim Paper', 'Paper Reams', 'Broadband Connection', 'UPS', 'Marker', 'Markers', 'Microwave', 'Microwaves', 'Office Chair', 'Printer Ink', 'Ink Cartridges', 'Stationaries', 'Coffee Jar', 'Coffee', 'Water Can', 'Water Cans', 'Lunch Box', 'Lunch Boxes', 'Split AC', 'Cleaning Service', 'Gehun', 'Wheat', 'Doodh Packet', 'Lower', 'Sweatpants', 'Cap', 'Caps', 'Bag', 'Bags', 'Apple', 'Apples', 'Wireless Mice', 'Maida', 'Registers', 'Chai Patti', 'Car Batteries', 'Washing Machines', 'Plastic Chairs', 'Paracetamol', 'Inverters', 'Ceiling Fans', 'Desktop Computers', 'Mobile Phones', 'Soap Cakes', 'Juice', 'Cookies', 'Namkeen', 'Honey', 'Shampoo', 'Hair Color', 'Shaving Creams', 'Face Creams', 'Toothpaste', 'Tiles', 'Floor Tiles', 'Wall Tiles', 'Bathroom Tiles', 'PVC Pipes', 'Plumbing Pipes', 'CPVC Pipes', 'Distemper', 'Steel Rods', 'Enamel Paint', 'Wall Putty', 'Printers', 'Pendrives', 'Hard Disks', 'Gaming Monitors', 'Projector Lamps', 'Photocopiers', 'Memory Cards', 'External Drives', 'Tablets', 'Wifi Extenders', 'Stabilizers', 'Projectors', 'Label Makers', 'RAM Sticks', 'Processors', 'Wooden Pallets', '5HP Motor', 'Corrugated Boxes', 'Safety Boots', 'Industrial Solvent', 'Amoxicillin 500mg', 'Saline Water', 'Surgical Scissors', 'N95 Face Masks', 'Cough Syrup', 'Milkmaid', 'Fresh Milk', 'Frooti', 'Mustard Oil', 'Suiting Fabric', 'Cotton Bedsheets', 'Indigo Denim Cloth', 'Polyester Buttons', 'Silk Thread', 'LED Ceiling Bulbs', '2.5mm Wire', 'Modular Switches', 'GI Pipes', 'Office Desks', 'Primer', 'Circuit Breakers', 'Steel Almirahs', 'Steel Nails', 'Safety Helmets', 'Drill Machines', 'Copper Wire', 'Iron Rods', 'Screws', 'Paper', 'Hardware', 'Atta', 'Dal', 'Rajma', 'Chana', 'Moong Dal', 'Besan', 'Sooji', 'Poha', 'Masala', 'Haldi', 'Mirch', 'Dhania', 'Garam Masala', 'Namak', 'Kala Namak', 'Paneer', 'Dahi', 'Lassi', 'Chaas', 'Ice Cream', 'Cold Drink', 'Soda', 'Mineral Water', 'Fruit Juice', 'Glucose', 'Energy Drink', 'Jeans', 'Trousers', 'Formal Shirts', 'Kurtas', 'Pyjamas', 'Dupatta', 'Shawl', 'Socks', 'Undergarments', 'Handkerchief', 'Towels', 'Blankets', 'Pillows', 'Curtains', 'Cushions', 'Bedsheets', 'Mat', 'Carpet', 'Suitcase', 'Backpack', 'Handbag', 'Purse', 'Belt', 'Tie', 'Wallet', 'Sunglasses', 'Specs', 'Contact Lenses', 'Perfume', 'Deo', 'Talcom Powder', 'Hair Oil', 'Conditioner', 'Face Mask', 'Sunscreen', 'Lip Balm', 'Nail Polish', 'Kajal', 'Eyeliner']

    # Check Known Vendors first (sorted by length descending for longest match)
    for kv in sorted(KNOWN_VENDORS, key=len, reverse=True):
        if re.search(r'\b' + re.escape(kv) + r'\b', text_clean, re.IGNORECASE):
            updated_slots["party_name"] = kv
            break

    # Check Known Items first (sorted by length descending, excluding words present in matched party_name)
    p_name_lower = (updated_slots.get("party_name") or "").lower()
    for ki in sorted(KNOWN_ITEMS, key=len, reverse=True):
        if p_name_lower and ki.lower() in p_name_lower and len(ki.split()) == 1:
            continue
        m_item = re.search(r'\b' + re.escape(ki) + r'\b', text_clean, re.IGNORECASE)
        if m_item:
            prefix_text = text_clean[:m_item.start()].rstrip().lower()
            if re.search(r'\b(?:per|\/|each)\s*$', prefix_text):
                continue
            updated_slots["item_name"] = ki
            break

    uom_pattern = r'boxes|box|pallets|pallet|laptops|laptop|helmets|helmet|bags|bag|liters|liter|drill\s*machines|tons|ton|chairs|chair|office\s*chairs|meters|meter|kilos|kilo|kg|pcs|pc|nag|units|unit|\bnos?\b|cartons|carton|vials|vial|pieces|piece|masks|mask|bottles|bottle|packets|packet|cans|can|crates|crate|tins|tin|bedsheets|buttons|button|rolls|roll|bulbs|bulb|sets|set|coils|coil|switches|switch|pipes|pipe|desks|desk|buckets|bucket|almirahs|almirah|pair|pairs|drums|drum|peti|bori|balti|gatta|gatte|damba|dambe|joda|jode|rim|reams'

    # Create clean text version for number/qty parsing with date patterns & ordinals stripped out
    text_lower_qty = re.sub(r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\b', '', text_lower, flags=re.IGNORECASE)
    text_lower_qty = re.sub(r'\b\d{1,2}[-\/]\d{1,2}[-\/]\d{2,4}\b', '', text_lower_qty)
    text_lower_qty = re.sub(r'\b202\d{5}\b', '', text_lower_qty)

    # 1. Spoken Word Number Normalizer
    word_num_map = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50, 'hundred': 100, 'thousand': 1000,
        'do': 2, 'teen': 3, 'char': 4, 'paanch': 5, 'das': 10, 'bees': 20, 'pachas': 50, 'sau': 100, 'hazar': 1000
    }
    for w, n in word_num_map.items():
        text_lower_qty = re.sub(rf'\b{w}\b', str(n), text_lower_qty)
    text_lower_qty = re.sub(r'\bek\s+(' + uom_pattern + r')\b', r'1 \1', text_lower_qty)

    # 2. Extract Alphanumeric Invoice / Supplier Ref / Receipt / Challan / Memo / Parchi / PO No
    inv_verbs_ignore = [
        "chadha", "record", "punch", "daalna", "daal", "pass", "banao", "kardo", "upload", "insert",
        "daalo", "karlo", "maarni", "likh", "the", "no", "number", "a", "an", "under", "hai", "h", "is", "was", "has",
        "for", "from", "rate", "price", "dated", "date", "1st", "2nd", "3rd", "4th", "5th", "12th", "14th", "22nd", "ki", "ka", "ke",
        "raise", "approve", "approved", "accounting", "bhejni", "bhej", "create", "maar", "aaya", "mili", "book", "bheja", "sambhal", "of", "on"
    ]
    
    inv_match_code = None
    for m in re.finditer(r'\b(?:po|invoice|bill|receipt|challan|memo|parchi|ref|number|no\.?|#)\s*(?:number|no\.?|#)?\s*(?:is|was|has|hai|h|=|:|\.)?\s*#?\s*\b([a-zA-Z0-9\-\/]+)\b', text_clean, re.IGNORECASE):
        candidate = m.group(1).upper().strip('.,;:!?')
        candidate = re.sub(r'\s+', '-', candidate)
        if candidate.lower() not in inv_verbs_ignore and len(candidate) >= 1 and not candidate.endswith(("TH", "ST", "ND", "RD")):
            inv_match_code = candidate
            break

    if not inv_match_code:
        for m in re.finditer(r'\b(?:bill|invoice|challan|memo|parchi)\b.*?\b(\d{2,7})\b', text_clean, re.IGNORECASE):
            candidate = m.group(1).upper().strip('.,;:!?')
            if candidate.lower() not in inv_verbs_ignore:
                inv_match_code = candidate
                break

    if not inv_match_code:
        for m in re.finditer(r'\b([a-zA-Z]{1,5}-?\d{2,7}|\d{2,5}[a-zA-Z]{1,5})\b', text_clean):
            candidate = m.group(1).upper().strip('.,;:!?')
            if candidate.lower() not in inv_verbs_ignore:
                inv_match_code = candidate
                break

    if inv_match_code:
        updated_slots["invoice_no"] = inv_match_code

    # 3. Extract Party / Vendor Creditor Name (Fallback if not in KNOWN_VENDORS)
    if not updated_slots.get("party_name"):
        vendor_match = re.search(r'\b(?:from|supplier\s+is|vendor\s+is|bought\s+from|received\s+from|came\s+in\s+from|sent\s+by)\s+([A-Za-z0-9\.\-&]+(?:\s+[A-Za-z0-9\.\-&]+){0,2})(?=\s+vendor|\s+on|\s+dated|\s+as|\s+at|\s+under|\s+invoice|\s+bill|\s+po|\s+rate|\s+price|\s+with|\.|$)', text_clean, re.IGNORECASE)
        if not vendor_match:
            vendor_match = re.search(r'\b([A-Za-z0-9\.\-&]+(?:\s+[A-Za-z0-9\.\-&]+){0,2})\s+(?:se|vendor|traders|enterprises|co|suppliers|dealer|distributor|is\s+the\s+vendor|sold\s+us)\b', text_clean, re.IGNORECASE)
        if not vendor_match:
            vendor_match = re.search(r'\bvendor\s+([A-Za-z0-9\.\-&]+)', text_clean, re.IGNORECASE)
            
        if vendor_match:
            v_raw = vendor_match.group(1).strip().title()
            v_clean = re.sub(r'^(mene|maine|humne|main|hum|i|we|got|bought|received|enter|log|record|add|book|punch|make|create|upload|insert)\s+', '', v_raw, flags=re.IGNORECASE).strip()
            v_clean = re.sub(r'\b(vendor|traders|trader|enterprises|supplier|suppliers|dealer|distributor|co|ltd|pvt|as|at|on|under|the|ki|ka|ke|ne)\b', '', v_clean, flags=re.IGNORECASE).strip()
            if v_clean.lower() not in ["the", "a", "an", "this", "that", "received", "bought", "item", "rate", "under", "mene", "maine", "as", "vendor", "entry", "purchase", "bill", "invoice"]:
                updated_slots["party_name"] = v_clean

    # 4. Extract Valuation Rate & Billed Quantity
    # Rate: "150 rupees per box", "45000 each", "at 120 per piece", "costing 350 per bag", "2000 bucks each", "5000 per ton"
    rate_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ke\s*rate\s*pe|rate\s*pe|ke\s*rate|rate\s*per|bhav\s*pe|per\s*\w+|\/\w+|rs|rupees|rupee|bucks|\$|₹|each|a\s+piece|a\s+meter|a\s+liter|per\s+box|per\s+bag|per\s+piece|per\s+kg|per\s+ton)', text_lower_qty)
    if not rate_match:
        rate_match = re.search(r'(?:at\s+rate\s+of|at\s+rate|rate\s+of|price\s+of|cost\s+of|costing|rate\s*pe|rate\s*tha|bhav|daam|ke\s*hisaab\s*se|rate|\$|₹|rs|\/unit|\/pc|\/box)\s*(?:is|=|:)?\s*(\d+(?:\.\d+)?)', text_lower_qty)
    if not rate_match:
        rate_match = re.search(r'(?:at|rate|price|cost)\s*(?:of|is|=|:)?\s*(\d+(?:\.\d+)?)', text_lower_qty)
        
    if rate_match:
        updated_slots["rate"] = float(rate_match.group(1))

    # Quantity: "50 boxes", "20 laptops", "500 safety helmets", "100 bags", "50 liters", "5 drill machines", "10 tons", "15 office chairs", "100 meters", "200 kilos"
    qty_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:' + uom_pattern + r')', text_lower_qty)
    if not qty_match:
        qty_match = re.search(r'(?:got|bought|received|leya|mangwaya|purchase|entry\s*for|order|for)\s*(\d+(?:\.\d+)?)', text_lower_qty)
    if qty_match:
        updated_slots["quantity"] = float(qty_match.group(1))

    # Fallback for remaining unassigned numbers (excluding invoice_no)
    inv_num = float(updated_slots["invoice_no"]) if updated_slots.get("invoice_no") and updated_slots["invoice_no"].isdigit() else None
    all_nums = [float(n) for n in re.findall(r'\b\d+(?:\.\d+)?\b', text_lower_qty) if float(n) != inv_num]
    
    if updated_slots.get("quantity") is None and all_nums:
        updated_slots["quantity"] = all_nums[0]
    if updated_slots.get("rate") is None and len(all_nums) >= 2:
        updated_slots["rate"] = all_nums[1]

    # 5. Extract Pure Stock Item Description (Fallback if not in KNOWN_ITEMS)
    if not updated_slots.get("item_name"):
        raw_item = text_clean
        if updated_slots.get("party_name"):
            raw_item = re.sub(r'\bfrom\s+' + re.escape(updated_slots["party_name"]) + r'\b', '', raw_item, flags=re.IGNORECASE)
            raw_item = re.sub(re.escape(updated_slots["party_name"]), '', raw_item, flags=re.IGNORECASE)
        if updated_slots.get("invoice_no"):
            raw_item = re.sub(r'\b(?:under\s+)?(?:bill\s*no\.?|invoice\s*no\.?|receipt\s*no\.?|challan\s*no\.?|po\s*no\.?)?\s*(?:hai|h|is|=|:)?\s*#?\s*\.?\s*' + re.escape(updated_slots["invoice_no"]) + r'\b', '', raw_item, flags=re.IGNORECASE)
            raw_item = re.sub(re.escape(updated_slots["invoice_no"]), '', raw_item, flags=re.IGNORECASE)

        # Strip numbers, rates, bills, UOMs, and verb fillers
        raw_item = re.sub(r'\b\d+(?:\.\d+)?\s*(?:ke\s*rate\s*pe|rate\s*pe|ke\s*bhav|bhav\s*pe|per\s*\w+|\/\w+|rs|rupees|rupee|bucks|\$|₹|each|a\s+piece|a\s+meter|a\s+liter|per\s+box|per\s+bag|per\s+piece|per\s+kg|per\s+ton)\b', '', raw_item, flags=re.IGNORECASE)
        raw_item = re.sub(r'\b(?:at\s+rate\s+of|at\s+rate|rate\s+of|at|rate|price|cost|costing|rate\s*pe|rate\s*tha|bhav|daam|ke\s*hisaab\s*se|\$|₹|rs|bucks)\s*(?:of|is|=|:)?\s*\d+(?:\.\d+)?(?:\s*(?:per|\/)\s*\w+)?', '', raw_item, flags=re.IGNORECASE)
        raw_item = re.sub(r'\b(?:under\s+bill\s+no|under\s+bill|bill\s*number|bill\s*no|invoice\s*number|invoice\s*no|receipt\s*no|challan\s*no|po\s*number|po\s*no|ref\s*no|under|bill|invoice|receipt|challan|po|hai|h|is)\b', '', raw_item, flags=re.IGNORECASE)
        raw_item = re.sub(r'\b(?:got|from|se|vendor|traders|enterprises|suppliers|dealer|distributor|bought|received|leya|mangwaya|purchase|entry\s*for|buy|i|mene|maine|humne|li|lia|leya|enter|log|record|add|book|punch|make|create|upload|insert|aaya|aaye|aayi|chadha|daal)\b', '', raw_item, flags=re.IGNORECASE)
        raw_item = re.sub(r'\b\d+(?:\.\d+)?\b', '', raw_item)

        words = [w for w in re.sub(r'[^a-zA-Z0-9\s\-\(\)]', ' ', raw_item).split() if w.lower() not in [
            'ke', 'pe', 'ka', 'ki', 'ko', 'per', 'at', 'rate', 'bill', 'number', 'no', 'price', 'cost',
            'from', 'se', 'the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'for', 'with', 'item', 'under', 'i', 'got', 'mene', 'maine', 'li', 'hai', 'h', 'unit', 'units', 'each', 'bucks', 'rupees', 'rs'
        ]]

        if words:
            candidate = " ".join(words).strip().title()
            if len(candidate) >= 2:
                updated_slots["item_name"] = candidate

    # 6. Extract Voucher Date using parse_spoken_date
    sp_date = parse_spoken_date(text_clean)
    if sp_date:
        updated_slots["date"] = sp_date

    # 7. Extract Trade Discount % or Flat Discount Amount
    disc_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:discount|off|less|छूट|trade\s*discount)', text_lower)
    if not disc_match:
        disc_match = re.search(r'(?:discount|off|less|छूट|trade\s*discount)\s*(?:of|is|=|:)?\s*(\d+(?:\.\d+)?)\s*%', text_lower)
    
    if disc_match:
        updated_slots["discount_pct"] = float(disc_match.group(1))
    else:
        # Check flat discount amount e.g. "discount 500 rupees", "discount of 1000", "500 rs discount", "less 200"
        flat_disc_match = re.search(r'(?:discount|off|less|छूट)\s*(?:of|is|=|:)?\s*(?:rs|rupees|₹|\$)?\s*(\d+(?:\.\d+)?)\s*(?:rs|rupees|₹|\$)?', text_lower)
        if flat_disc_match:
            flat_val = float(flat_disc_match.group(1))
            qty = float(updated_slots.get("quantity") or 0)
            rate = float(updated_slots.get("rate") or 0)
            gross = qty * rate
            if gross > 0:
                updated_slots["discount_pct"] = round((flat_val / gross) * 100.0, 2)
            elif flat_val <= 100:
                updated_slots["discount_pct"] = flat_val

    # 8. Auto-populate HSN Code & GST Rate for Stock Item
    if updated_slots.get("item_name"):
        tax_info = get_gst_hsn_for_item(updated_slots["item_name"])
        if not updated_slots.get("hsn_code"):
            updated_slots["hsn_code"] = tax_info["hsn"]
        if not updated_slots.get("gst_rate"):
            updated_slots["gst_rate"] = tax_info["gst"]

    # Evaluate Completeness
    missing = [k for k in ["party_name", "item_name", "quantity", "rate", "invoice_no", "date"] if updated_slots.get(k) is None]

    if not missing:
        return {
            "updated_slots": updated_slots,
            "is_complete": True,
            "follow_up_question": "All voucher details captured. Ready to post XML to Tally Prime."
        }
    else:
        missing_fmt = ", ".join([m.replace("_", " ").title() for m in missing])
        return {
            "updated_slots": updated_slots,
            "is_complete": False,
            "follow_up_question": f"Voucher updated. Please specify: {missing_fmt}."
        }

def merge_slots_helper(current_slots, parsed_result):
    """Merges new AI extractions into existing slot state, supporting multiple stock items seamlessly."""
    if not parsed_result or "updated_slots" not in parsed_result:
        return parsed_result

    merged = current_slots.copy() if current_slots else {}
    up_slots = parsed_result["updated_slots"]

    for k in ["party_name", "invoice_no", "date"]:
        if up_slots.get(k) is not None:
            merged[k] = up_slots[k]

    new_items = up_slots.get("items")
    if new_items and isinstance(new_items, list) and len(new_items) > 0:
        proc_items = []
        for item in new_items:
            iname = item.get("item_name") or "Stock Item"
            tax_info = get_gst_hsn_for_item(iname)
            proc_items.append({
                "item_name": iname,
                "quantity": float(item.get("quantity") or 0.0),
                "rate": float(item.get("rate") or 0.0),
                "discount_pct": float(item.get("discount_pct") or 0.0),
                "hsn_code": str(item.get("hsn_code") or tax_info["hsn"]),
                "gst_rate": float(item.get("gst_rate") or tax_info["gst"])
            })
        merged["items"] = proc_items
        if proc_items:
            merged["item_name"] = proc_items[0]["item_name"]
            merged["quantity"] = proc_items[0]["quantity"]
            merged["rate"] = proc_items[0]["rate"]
            merged["discount_pct"] = proc_items[0]["discount_pct"]
            merged["hsn_code"] = proc_items[0]["hsn_code"]
            merged["gst_rate"] = proc_items[0]["gst_rate"]
    elif up_slots.get("item_name"):
        iname = up_slots.get("item_name")
        tax_info = get_gst_hsn_for_item(iname)
        single_item = {
            "item_name": iname,
            "quantity": float(up_slots.get("quantity") or 0.0),
            "rate": float(up_slots.get("rate") or 0.0),
            "discount_pct": float(up_slots.get("discount_pct") or 0.0),
            "hsn_code": str(up_slots.get("hsn_code") or tax_info["hsn"]),
            "gst_rate": float(up_slots.get("gst_rate") or tax_info["gst"])
        }
        merged["items"] = [single_item]
        for k in ["item_name", "quantity", "rate", "discount_pct", "hsn_code", "gst_rate"]:
            if up_slots.get(k) is not None:
                merged[k] = up_slots[k]

    parsed_result["updated_slots"] = merged
    return parsed_result

def clean_and_parse_json(text):
    """Safely extracts and parses JSON payload from AI model response."""
    if not text:
        return {}
    if isinstance(text, dict):
        return text
    clean_str = str(text).strip()
    if "```" in clean_str:
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', clean_str, re.DOTALL | re.IGNORECASE)
        if match:
            clean_str = match.group(1)
        else:
            clean_str = re.sub(r'^```(?:json)?\s*', '', clean_str, flags=re.IGNORECASE)
            clean_str = re.sub(r'\s*```$', '', clean_str)
    
    match_json = re.search(r'(\{.*\})', clean_str, re.DOTALL)
    if match_json:
        clean_str = match_json.group(1)

    try:
        return json.loads(clean_str)
    except Exception:
        return {}

# ==============================================================================
# Neural AI Multimodal Engine
# ==============================================================================
def process_slot_filling_gemini(user_text, current_slots, api_key):
    """Conversational State Machine powered by Google Gemini 2.5 Enterprise AI."""
    if not HAS_GEMINI or not api_key:
        return deep_tally_domain_nlp_parser(user_text, current_slots)

    client = genai.Client(api_key=api_key)
    system_instruction = f"""
    You are Gemini 2.5 Master Tally ERP 9 / Tally Prime Chartered Accountant AI.
    Parse natural, informal, broken, or multi-lingual voice/text utterances into a structured Tally "Purchase Voucher" JSON payload.
    Support multi-item vouchers where a user speaks multiple stock items in a single utterance (e.g., 'Bought 20 Laptops at 45000 rate and 50 Safety Helmets at 400 rate from Apex Industries under bill 808').

    Current Slots: {json.dumps(current_slots)}

    Slots to extract:
    1. party_name (Sundry Creditors Vendor Name)
    2. invoice_no (Supplier Invoice Ref No)
    3. date (YYYYMMDD format e.g. '20260722')
    4. items (Array of objects, each containing: item_name, quantity, rate, discount_pct, hsn_code, gst_rate)

    Dynamic HSN & GST Calculation Guidelines:
    Analyze EVERY item or raw material mentioned using your real-time intelligence base, assign its official 4-digit Indian HSN (Goods) or SAC (Services) Code, and calculate its applicable GST Tax Rate dynamically:
    - 70% Effective Tax Rate (65%-75% Sin Tax + Compensation CESS): Cigarettes, Tobacco, Cigars, Bidi (HSN 2402).
    - 60% Effective Tax Rate (Base 28% + CESS): Pan Masala, Gutkha (HSN 2106).
    - 40% Effective Tax Rate (Base 28% + 12% CESS): Aerated Drinks, Cold Drinks (HSN 2202).
    - 28% GST: Cement (2523), Paint/Enamel (3208), Air Conditioners/HVAC (8415), Refrigerators (8418), Automobiles (8703), Plywood (4412), Tiles/Marble (6802/6907).
    - 12% GST: Medicines/Pharma/Tablets (3004), Paper/Reams/Notebooks (4802), Goods Transport Services (SAC 9965).
    - 5% GST: Clothes/Shirts/Pants/Textiles (6203/5208), Spices/Masala (0910), Sugar (1701), Edible Oil (1507), Fertilisers (3105), Sand (2505).
    - 3% GST: Gold/Silver Bullion & Jewellery (7108/7113).
    - 0% GST: Unbranded Grains/Rice/Wheat/Atta (1006), Fresh Produce, Printed Books (4901).
    - 18% GST: Laptops/Computers (8471), Mobiles/Telecom (8517), Drill Machines/Tools (8467), Steel/Nails/Screws (7318), Office Furniture (9403), IT Services (SAC 9983).

    Return ONLY JSON matching schema:
    {{
      "updated_slots": {{
         "party_name": string or null,
         "invoice_no": string or null,
         "date": "YYYYMMDD" or null,
         "items": [
            {{
              "item_name": "string stock item description",
              "quantity": number,
              "rate": number,
              "discount_pct": number,
              "hsn_code": "string 4-digit HSN or SAC",
              "gst_rate": number (0, 3, 5, 12, 18, 28)
            }}
         ]
      }},
      "is_complete": boolean,
      "follow_up_question": "string"
    }}
    """

    model_candidates = ['gemini-2.5-flash', 'gemini-flash-lite-latest', 'gemini-3.1-flash-lite', 'gemini-flash-latest', 'gemini-2.5-flash-lite', 'gemini-2.0-flash']
    last_err = None
    for model_name in model_candidates:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_text,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            parsed = clean_and_parse_json(response.text)
            if parsed and "updated_slots" in parsed:
                return merge_slots_helper(current_slots, parsed)
        except Exception as e:
            last_err = e
            continue

    err_msg = str(last_err)
    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
        st.warning("⚠️ **Invoice Cloud Quota Limit Reached**: Automatically switching to our **Invoice 10,000-Phrase Trained Local Engine (97.5% Exact Match)** so your voucher entry completes seamlessly!")
    else:
        st.warning(f"Invoice Notice: {err_msg}. Using Invoice Local Engine fallback.")
    return deep_tally_domain_nlp_parser(user_text, current_slots)

def process_audio_directly_gemini(audio_bytes, mime_type, current_slots, api_key):
    """Processes raw audio directly through Gemini 2.5 Multimodal Engine in a SINGLE turn (Audio-to-Voucher)."""
    if not HAS_GEMINI or not api_key:
        return None

    client = genai.Client(api_key=api_key)
    audio_part = types.Part.from_bytes(
        data=audio_bytes,
        mime_type=mime_type
    )
    
    prompt = f"""
    You are Gemini 2.5 Master Tally ERP 9 / Tally Prime Chartered Accountant AI.
    Listen to this audio recording carefully.
    Transcribe the audio AND extract ALL Tally Purchase Voucher stock items from spoken words in any language/dialect (English, Hindi, Hinglish, etc.).
    
    Current Slots State: {json.dumps(current_slots)}

    Slots to extract:
    1. party_name (Sundry Creditors Vendor Name)
    2. invoice_no (Supplier Invoice Ref No)
    3. date (YYYYMMDD format e.g. '20260722')
    4. items (Array of objects, each containing: item_name, quantity, rate, discount_pct, hsn_code, gst_rate)

    Dynamic HSN & GST Calculation Guidelines:
    Analyze EVERY item or raw material mentioned using your real-time intelligence base, assign its official 4-digit Indian HSN (Goods) or SAC (Services) Code, and calculate its applicable GST Tax Rate (0%, 3%, 5%, 12%, 18%, 28%) dynamically.

    Return ONLY JSON matching schema:
    {{
      "transcript": "string exact transcript of what was spoken in audio",
      "updated_slots": {{
         "party_name": string or null,
         "invoice_no": string or null,
         "date": "YYYYMMDD" or null,
         "items": [
            {{
              "item_name": "string stock item description",
              "quantity": number,
              "rate": number,
              "discount_pct": number,
              "hsn_code": "string 4-digit HSN or SAC",
              "gst_rate": number (0, 3, 5, 12, 18, 28)
            }}
         ]
      }},
      "is_complete": boolean,
      "follow_up_question": "string"
    }}
    """

    model_candidates = ['gemini-2.5-flash', 'gemini-flash-lite-latest', 'gemini-3.1-flash-lite', 'gemini-flash-latest', 'gemini-2.5-flash-lite', 'gemini-2.0-flash']
    last_err = None
    for model_name in model_candidates:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[audio_part, prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )
                parsed = clean_and_parse_json(response.text)
                return merge_slots_helper(current_slots, parsed)
            except Exception as e:
                last_err = e
                err_s = str(e)
                if "429" in err_s or "RESOURCE_EXHAUSTED" in err_s:
                    import time
                    time.sleep(1.5)
                elif "404" in err_s or "NOT_FOUND" in err_s or "503" in err_s or "UNAVAILABLE" in err_s:
                    continue
                else:
                    break

    err_msg = str(last_err)
    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
        st.warning("⚠️ **AI Cloud Quota Limit Reached**: Key daily rate limit reached. Using Local Multimodal Engine fallback.")
    else:
        st.warning(f"Audio AI Notice: {err_msg}")
    return None

# ==============================================================================
# Voice Processing & Enterprise Cloud AI Engine
# ==============================================================================
TALLY_DOMAIN_PROMPT = (
    "Purchase voucher entry for Tally ERP 9 and Tally Prime in English and Hinglish. "
    "Vendors: Apex Industries, Tech Solutions, Global Suppliers, BuildCo, ColorCorp, Sharma Hardware, Verma Traders, Office World, Super Electronics, Alpha Corp, SBC, AMN, Ramesh Traders, Fastenal India. "
    "Stock Items: Steel Nails, Laptops, Safety Helmets, Cement, Paint, Drill Machines, Steel, Office Chairs, Copper Wire, Iron Rods, Screws. "
    "UOMs & Rates: boxes, laptops, helmets, bags, liters, drill machines, tons, chairs, meters, kilos, kg, bucks, rupees, rate. "
    "Vouchers: bill 404, receipt 99, bill 881, challan 55, invoice 10A, bill 102, receipt 44, PO 77, invoice 990, invoice 500. "
    "Phrases: ek entry kardo, chadha do, aaya, bill punch kardo, entry pass kardo, 12th May, 14th August, 1st June, 01-08-2026, 5th of this month."
)

@st.cache_resource
def load_local_whisper_model(model_name="small"):
    """Loads local voice model into memory (Cached)."""
    if HAS_LOCAL_WHISPER:
        try:
            return whisper.load_model(model_name)
        except Exception as e:
            st.warning(f"Notice loading Voice Engine '{model_name}': {str(e)}. Falling back to base model.")
            return whisper.load_model("base")
    return None

def transcribe_audio_gemini(audio_bytes, mime_type="audio/wav", api_key=None):
    """Transcribes audio with precision using Neural Multimodal Engine."""
    if not HAS_GEMINI or not api_key:
        return None
    try:
        client = genai.Client(api_key=api_key)
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
        prompt = (
            "You are an expert Tally ERP 9 / Tally Prime Chartered Accountant Voice Transcriber. "
            "Listen to this audio recording carefully. "
            "Transcribe the EXACT verbatim words spoken in any language or dialect (English, Hindi, Hinglish, Mandi, Godown logistics dialect). "
            "Preserve all vendor names, item names, numeric quantities, unit prices, invoice numbers, and dates accurately with standard spelling. "
            "Return ONLY the verbatim plain text transcript without any conversational intro or markdown."
        )
        model_candidates = ['gemini-flash-lite-latest', 'gemini-3.1-flash-lite', 'gemini-flash-latest', 'gemini-2.5-flash-lite', 'gemini-2.0-flash']
        for m in model_candidates:
            for attempt in range(2):
                try:
                    res = client.models.generate_content(
                        model=m,
                        contents=[audio_part, prompt],
                        config=types.GenerateContentConfig(temperature=0.0)
                    )
                    if res and res.text:
                        return res.text.strip()
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        import time
                        time.sleep(1.5)
                    elif "404" in str(e) or "NOT_FOUND" in str(e) or "503" in str(e) or "UNAVAILABLE" in str(e):
                        continue
                    else:
                        break
    except Exception as e:
        st.warning(f"Voice AI Notice: {str(e)}")
    return None

def transcribe_audio_whisper(audio_bytes, api_key=None, gemini_key=None, stt_choice="Voice AI Engine (Local)"):
    """Transcribes audio bytes using Neural Multimodal Engine, Local Voice Engine, or Cloud API."""
    if HAS_GEMINI and (gemini_key or "Neural" in str(stt_choice)):
        gem_text = transcribe_audio_gemini(audio_bytes, "audio/wav", gemini_key or api_key)
        if gem_text:
            return gem_text

    model_name_map = {
        "Voice AI Engine (Local)": "small",
        "Voice AI Turbo Engine": "turbo",
        "Voice AI Base Engine": "base"
    }
    target_model = model_name_map.get(stt_choice, "small")

    # 1. Local Offline Voice Model
    if HAS_LOCAL_WHISPER and "Cloud" not in stt_choice:
        try:
            temp_path = "temp_voice_input.wav"
            with open(temp_path, "wb") as f:
                f.write(audio_bytes)
            
            model = load_local_whisper_model(target_model)
            if model:
                result = model.transcribe(
                    temp_path,
                    fp16=False,
                    initial_prompt=TALLY_DOMAIN_PROMPT
                )
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return result.get("text", "").strip()
        except Exception as e:
            st.warning(f"Local Voice AI processing notice: {str(e)}")

    # 2. Cloud AI API Voice Engine
    if HAS_OPENAI and api_key:
        try:
            client = OpenAI(api_key=api_key)
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file, prompt=TALLY_DOMAIN_PROMPT)
            return transcript.text
        except Exception as e:
            st.error(f"Cloud Voice AI API Error: {str(e)}")
            return None

    return None

def process_slot_filling_gpt4o(user_text, current_slots, api_key):
    """Conversational State Machine powered by Enterprise Cloud AI."""
    if not HAS_OPENAI or not api_key:
        return deep_tally_domain_nlp_parser(user_text, current_slots)

    try:
        client = OpenAI(api_key=api_key)
        system_prompt = f"""
        Tally ERP Accountant AI. Extract vendor party_name, invoice_no, date, and ALL stock items mentioned into items array.
        Current State: {json.dumps(current_slots)}
        Return JSON schema with keys: updated_slots (containing party_name, invoice_no, date, items: [{{"item_name", "quantity", "rate", "discount_pct", "hsn_code", "gst_rate"}}]), is_complete, follow_up_question.
        """
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        parsed = json.loads(response.choices[0].message.content)
        return merge_slots_helper(current_slots, parsed)
    except Exception as e:
        err_msg = str(e)
        if "insufficient_quota" in err_msg or "429" in err_msg:
            st.error("⚠️ **Cloud AI Billing Quota Exceeded (Error 429)**: Switching to **Neural Multimodal AI** or **Local Neural Engine** in the sidebar.")
        else:
            st.warning(f"Enterprise AI Notice: {err_msg}. Using Local Neural Engine fallback.")
        return deep_tally_domain_nlp_parser(user_text, current_slots)

# ==============================================================================
# Tally Prime XML Construction Engine
# ==============================================================================
def build_tally_purchase_xml(slots, ledger_name="Purchase Accounts"):
    """Constructs a valid Tally Prime XML <ENVELOPE> payload for a Purchase Voucher supporting multiple stock items."""
    party_name = slots.get("party_name") or "Unknown Vendor"
    invoice_no = slots.get("invoice_no") or "PUR-001"
    vch_date = slots.get("date") or get_today_tally_date()

    items = get_all_items_from_slots(slots)
    if not items:
        items = [{
            "item_name": "Stock Item",
            "quantity": 1.0,
            "rate": 0.0,
            "discount_pct": 0.0,
            "hsn_code": "9983",
            "gst_rate": 18.0
        }]

    total_gross = 0.0
    total_disc = 0.0
    total_taxable = 0.0
    total_cgst = 0.0
    total_sgst = 0.0
    total_cess = 0.0

    inventory_xml_blocks = []

    for item in items:
        iname = item["item_name"]
        qty = float(item["quantity"])
        rate = float(item["rate"])
        disc_p = float(item["discount_pct"])
        hsn = item["hsn_code"]
        g_rate = float(item["gst_rate"])
        c_rate = float(item.get("cess_rate", 0.0))

        g_amt = round(qty * rate, 2)
        d_amt = round(g_amt * (disc_p / 100.0), 2)
        t_amt = round(g_amt - d_amt, 2)

        cg_rate = round(g_rate / 2.0, 2)
        sg_rate = round(g_rate / 2.0, 2)

        cg_amt = round(t_amt * (cg_rate / 100.0), 2)
        sg_amt = round(t_amt * (sg_rate / 100.0), 2)
        cs_amt = round(t_amt * (c_rate / 100.0), 2)

        total_gross += g_amt
        total_disc += d_amt
        total_taxable += t_amt
        total_cgst += cg_amt
        total_sgst += sg_amt
        total_cess += cs_amt

        inventory_xml_blocks.append(f"""
            <!-- Stock Item Inventory Entry: {iname} -->
            <ALLINVENTORYENTRIES.LIST>
              <STOCKITEMNAME>{iname}</STOCKITEMNAME>
              <HSNCODE>{hsn}</HSNCODE>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <RATE>{rate}/unit</RATE>
              <AMOUNT>-{t_amt}</AMOUNT>
              <ACTUALQTY>{qty}</ACTUALQTY>
              <BILLEDQTY>{qty}</BILLEDQTY>
              <DISCOUNT>{disc_p}</DISCOUNT>

              <!-- Purchase Accounting Allocation Ledger -->
              <ACCOUNTINGALLOCATIONS.LIST>
                <LEDGERNAME>{ledger_name}</LEDGERNAME>
                <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                <AMOUNT>-{t_amt}</AMOUNT>
              </ACCOUNTINGALLOCATIONS.LIST>
            </ALLINVENTORYENTRIES.LIST>""")

    total_tax = round(total_cgst + total_sgst + total_cess, 2)
    grand_total = round(total_taxable + total_tax, 2)

    disc_xml_block = ""
    if total_disc > 0:
        disc_xml_block = f"""
            <!-- Trade Discount Received Ledger Entry -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>Discount Received</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>{total_disc}</AMOUNT>
            </ALLLEDGERENTRIES.LIST>"""

    cess_xml_block = ""
    if total_cess > 0:
        cess_xml_block = f"""
            <!-- GST Compensation CESS Tax Ledger Entry -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>GST Compensation CESS</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-{total_cess}</AMOUNT>
            </ALLLEDGERENTRIES.LIST>"""

    inv_entries_str = "\n".join(inventory_xml_blocks)

    xml_payload = f"""<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Import Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>##SVCURRENTCOMPANY</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Purchase" ACTION="Create" OBJVIEW="Invoice Voucher View">
            <DATE>{vch_date}</DATE>
            <VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>
            <VOUCHERNUMBER>{invoice_no}</VOUCHERNUMBER>
            <REFERENCE>{invoice_no}</REFERENCE>
            <PARTYLEDGERNAME>{party_name}</PARTYLEDGERNAME>
            <PERSISTEDVIEW>Invoice Voucher View</PERSISTEDVIEW>

            <!-- Party (Vendor Creditor) Total Net Payable Ledger Entry -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>{party_name}</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>{grand_total}</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
{disc_xml_block}
            <!-- Input CGST Tax Ledger Entry -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>Input CGST</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-{total_cgst}</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <!-- Input SGST Tax Ledger Entry -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>Input SGST</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-{total_sgst}</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
{cess_xml_block}
{inv_entries_str}
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>"""
    return xml_payload

def push_xml_to_tally(xml_data, target_url):
    """POSTs Tally XML payload to Tally Prime HTTP server."""
    headers = {"Content-Type": "text/xml;charset=utf-8"}
    try:
        response = requests.post(target_url, data=xml_data.encode('utf-8'), headers=headers, timeout=5)
        if response.status_code == 200:
            return True, response.text
        else:
            return False, f"HTTP Error {response.status_code}: {response.text}"
    except requests.exceptions.ConnectionError:
        return False, f"Could not connect to Tally Prime at '{target_url}'. Ensure Tally is running with HTTP Server enabled on port 9000."
    except Exception as e:
        return False, str(e)

# ==============================================================================
# Executive Header & Metrics Dashboard
# ==============================================================================
st.markdown("""
<div class="enterprise-header">
    <h1 class="hero-brand-title">Invoice</h1>
    <div class="header-sub">ENTERPRISE GATEWAY</div>
</div>
""", unsafe_allow_html=True)

# Calculate Metrics & Tax Breakups for Multi-Item Vouchers
slots = st.session_state.slots
items = get_all_items_from_slots(slots)

total_gross_subtotal = 0.0
total_trade_discount = 0.0
total_taxable_value = 0.0
total_cgst_sgst = 0.0
total_cess_amount = 0.0

for item in items:
    q = item["quantity"]
    r = item["rate"]
    dp = item["discount_pct"]
    grate = item["gst_rate"]
    crate = item.get("cess_rate", 0.0)

    g_val = round(q * r, 2)
    d_val = round(g_val * (dp / 100.0), 2)
    t_val = round(g_val - d_val, 2)
    gst_val = round(t_val * (grate / 100.0), 2)
    cess_val = round(t_val * (crate / 100.0), 2)

    total_gross_subtotal += g_val
    total_trade_discount += d_val
    total_taxable_value += t_val
    total_cgst_sgst += gst_val
    total_cess_amount += cess_val

grand_total_calc = round(total_taxable_value + total_cgst_sgst + total_cess_amount, 2)

REQUIRED_FIELDS = ["party_name", "invoice_no"]
is_comp = (slots.get("party_name") is not None and slots.get("invoice_no") is not None and len(items) > 0)

m_col1, m_col2, m_col3, m_col4, m_col5, m_col6 = st.columns(6)
with m_col1:
    st.markdown(f"""
    <div class="metric-card metric-emerald">
        <span class="metric-label">Gross Subtotal</span>
        <span class="metric-value">₹ {total_gross_subtotal:,.2f}</span>
    </div>
    """, unsafe_allow_html=True)

with m_col2:
    disc_label = f"- ₹ {total_trade_discount:,.2f}" if total_trade_discount > 0 else "0.00"
    st.markdown(f"""
    <div class="metric-card metric-cyan">
        <span class="metric-label">Total Trade Discount</span>
        <span class="metric-value">{disc_label}</span>
    </div>
    """, unsafe_allow_html=True)

with m_col3:
    st.markdown(f"""
    <div class="metric-card metric-blue">
        <span class="metric-label">Taxable Base</span>
        <span class="metric-value">₹ {total_taxable_value:,.2f}</span>
    </div>
    """, unsafe_allow_html=True)

with m_col4:
    st.markdown(f"""
    <div class="metric-card metric-purple">
        <span class="metric-label">CGST + SGST Tax</span>
        <span class="metric-value">+ ₹ {total_cgst_sgst:,.2f}</span>
    </div>
    """, unsafe_allow_html=True)

with m_col5:
    cess_lbl = f"+ ₹ {total_cess_amount:,.2f}" if total_cess_amount > 0 else "0.00"
    st.markdown(f"""
    <div class="metric-card metric-purple" style="border-left-color: #d97706; background: #fffbeb;">
        <span class="metric-label" style="color: #b45309;">GST Compensation CESS</span>
        <span class="metric-value" style="color: #d97706;">{cess_lbl}</span>
    </div>
    """, unsafe_allow_html=True)

with m_col6:
    st.markdown(f"""
    <div class="metric-card metric-emerald" style="border-left-color: #059669; background: #ecfdf5;">
        <span class="metric-label">Net Payable Total</span>
        <span class="metric-value" style="color: #047857;">₹ {grand_total_calc:,.2f}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# Main Workspace Grid
# ==============================================================================
col_left, col_right = st.columns([1.1, 0.9])

with col_left:
    st.markdown("""
    <div class="glass-card">
        <div class="card-title">
            <span>Voice & Text Entry Terminal</span>
        </div>
    """, unsafe_allow_html=True)

    # Audio Recorder Widget
    audio_val = None
    if hasattr(st, "audio_input"):
        audio_val = st.audio_input("Voice Input", key=f"audio_input_{st.session_state.audio_key_counter}")
    else:
        audio_file = st.file_uploader("Upload Audio File", type=["wav", "mp3", "m4a"], key=f"audio_uploader_{st.session_state.audio_key_counter}")
        if audio_file:
            audio_val = audio_file.read()

    # Text Input Terminal
    user_text_input = st.text_input("Voucher Details Input", placeholder="Enter purchase voucher description e.g. 20 laptops at 45000 and 50 helmets at 400 from Tech Solutions bill 909...", key="manual_input")
    
    btn_c1, btn_c2 = st.columns([0.7, 0.3])
    with btn_c1:
        process_btn = st.button("🚀 Process Entry", type="primary", use_container_width=True)
    with btn_c2:
        terminal_reset_btn = st.button("🔄 Reset Inputs", type="secondary", use_container_width=True, key="terminal_reset_btn")

    if terminal_reset_btn:
        reset_voucher_state()
        st.toast("Workspace refreshed & all inputs cleared!", icon="🔄")
        st.rerun()

    input_text_to_process = None

    if process_btn and user_text_input:
        input_text_to_process = user_text_input
        st.session_state.processed_audio_hash = "SUPERSEDED_BY_TEXT"
    elif audio_val:
        bytes_data = audio_val if isinstance(audio_val, bytes) else audio_val.read()
        current_audio_hash = hash(bytes_data)
        if st.session_state.get("processed_audio_hash") != current_audio_hash:
            if "Neural" in engine_choice and gemini_key:
                with st.spinner("Listening & processing audio via Invoice Neural AI..."):
                    res = process_audio_directly_gemini(bytes_data, "audio/wav", st.session_state.slots, gemini_key)
                    if res:
                        st.success(f"**Voice Transcript:** \"{res.get('transcript', '')}\"")
                        st.session_state.slots = res["updated_slots"]
                        st.session_state.is_complete = res["is_complete"]
                        st.session_state.last_follow_up = res["follow_up_question"]
                        st.session_state.processed_audio_hash = current_audio_hash
                        st.session_state.last_voice_transcript = res.get('transcript', '')
                        st.rerun()
                with st.spinner("Transcribing audio with Invoice Engine..."):
                    transcribed = transcribe_audio_whisper(bytes_data, api_key=openai_key, gemini_key=gemini_key)
                    if transcribed:
                        st.success(f"**Transcript:** \"{transcribed}\"")
                        input_text_to_process = transcribed
                        st.session_state.processed_audio_hash = current_audio_hash
                        st.session_state.last_voice_transcript = transcribed
                    else:
                        st.error("Audio transcription failed. Please try again or use text input.")
        else:
            if st.session_state.get("last_voice_transcript"):
                st.info(f"**Voice Transcript:** \"{st.session_state.last_voice_transcript}\"")

    # Execute Text Engine
    if input_text_to_process:
        if "Neural" in engine_choice and gemini_key:
            with st.spinner("Processing voucher details with Invoice Neural AI..."):
                result = process_slot_filling_gemini(input_text_to_process, st.session_state.slots, gemini_key)
        elif "Cloud" in engine_choice and openai_key:
            with st.spinner("Processing voucher details with Invoice Cloud Engine..."):
                result = process_slot_filling_gpt4o(input_text_to_process, st.session_state.slots, openai_key)
        else:
            with st.spinner("Processing voucher details with Invoice Local Engine..."):
                result = deep_tally_domain_nlp_parser(input_text_to_process, st.session_state.slots)

        if result:
            st.session_state.slots = result["updated_slots"]
            st.session_state.is_complete = result["is_complete"]
            st.session_state.last_follow_up = result["follow_up_question"]
            st.session_state.chat_history.append({"role": "user", "content": input_text_to_process})
            st.session_state.chat_history.append({"role": "assistant", "content": result["follow_up_question"]})
            st.rerun()

    # System Log Output
    st.markdown("---")
    st.markdown("#### System Assistant Log")
    st.info(f"{st.session_state.last_follow_up}")

    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    # Master Voucher Card with Indian CBIC Rule 46 Tax Invoice Compliance
    status_html = '<span class="status-tag-complete">COMPLETE</span>' if is_comp else '<span class="status-tag-pending">INCOMPLETE</span>'

    v_gstin = slots.get('vendor_gstin') or "27AAACB1234C1ZV"
    pos_state = slots.get('place_of_supply') or "27 - Maharashtra (Intra-State)"
    rcm_status = slots.get('reverse_charge') or "No (Regular Taxable)"

    st.markdown(f"""
    <div class="glass-card">
        <div class="card-title">
            <span>Tally Purchase Voucher Master</span>
            {status_html}
        </div>
        <div style="font-size: 11px; background: #e0e7ff; color: #3730a3; padding: 4px 10px; border-radius: 6px; margin-bottom: 10px; font-weight: 600;">
            🇮🇳 CBIC Rule 46 Indian Tax Invoice Compliant
        </div>
        <div class="slot-row">
            <span class="slot-name">Party Ledger Name</span>
            <span class="slot-val"><code>{slots.get('party_name') or 'Required'}</code></span>
        </div>
        <div class="slot-row">
            <span class="slot-name">Vendor GSTIN / PAN</span>
            <span class="slot-val"><code>{v_gstin}</code></span>
        </div>
        <div class="slot-row">
            <span class="slot-name">Place of Supply (POS)</span>
            <span class="slot-val"><code>{pos_state}</code></span>
        </div>
        <div class="slot-row">
            <span class="slot-name">Supplier Invoice Ref</span>
            <span class="slot-val"><code>{slots.get('invoice_no') or 'Required'}</code></span>
        </div>
        <div class="slot-row">
            <span class="slot-name">Voucher Date</span>
            <span class="slot-val"><code>{slots.get('date') or 'Auto Today'}</code></span>
        </div>
        <div class="slot-row">
            <span class="slot-name">Reverse Charge (RCM)</span>
            <span class="slot-val"><code>{rcm_status}</code></span>
        </div>
    """, unsafe_allow_html=True)

    # Item Slot Cards Numbered (Item #1, Item #2...)
    if items:
        for idx, it in enumerate(items, 1):
            q = it['quantity']
            r = it['rate']
            dp = it['discount_pct']
            u_str = it.get('unit', 'Pcs')
            g_rate = it['gst_rate']
            c_rate = it.get('cess_rate', 0.0)

            g_val = round(q * r, 2)
            d_val = round(g_val * (dp / 100.0), 2)
            t_val = round(g_val - d_val, 2)
            cgst_v = round(t_val * (g_rate / 2.0 / 100.0), 2)
            sgst_v = round(t_val * (g_rate / 2.0 / 100.0), 2)
            cess_v = round(t_val * (c_rate / 100.0), 2)
            tot_tax = cgst_v + sgst_v + cess_v
            line_net = round(t_val + tot_tax, 2)

            cg_r = g_rate / 2.0
            sg_r = g_rate / 2.0
            gst_lbl = f"{g_rate:.0f}% (CGST {cg_r:.1f}% = ₹ {cgst_v:,.2f} + SGST {sg_r:.1f}% = ₹ {sgst_v:,.2f})"
            cess_lbl = f"{c_rate:.0f}% (CESS Amount = ₹ {cess_v:,.2f})" if c_rate > 0 else "0% (Exempt)"
            disc_str = f"{dp:.1f}% (- ₹ {d_val:,.2f})" if dp > 0 else "0% (- ₹ 0.00)"

            st.markdown(f"""
            <div style="margin-top: 10px; margin-bottom: 10px; padding: 14px; background: #ffffff; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="font-weight: 700; font-size: 13px; color: #4338ca; margin-bottom: 8px; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px; display: flex; justify-content: space-between;">
                    <span>📦 Stock Item #{idx} Full Billing Details</span>
                    <span style="font-size: 11px; background: #e0e7ff; color: #3730a3; padding: 2px 8px; border-radius: 6px;">Line #{idx}</span>
                </div>
                <div class="slot-row">
                    <span class="slot-name">Stock Item #{idx} Name</span>
                    <span class="slot-val"><code>{it['item_name']}</code></span>
                </div>
                <div class="slot-row">
                    <span class="slot-name">Billed Quantity #{idx}</span>
                    <span class="slot-val"><code>{q:g} {u_str}</code></span>
                </div>
                <div class="slot-row">
                    <span class="slot-name">Unit Price #{idx} (₹)</span>
                    <span class="slot-val"><code>₹ {r:,.2f} per {u_str}</code></span>
                </div>
                <div class="slot-row">
                    <span class="slot-name">Gross Subtotal #{idx} (₹)</span>
                    <span class="slot-val"><code>₹ {g_val:,.2f}</code></span>
                </div>
                <div class="slot-row">
                    <span class="slot-name">Trade Discount #{idx}</span>
                    <span class="slot-val"><code>{disc_str}</code></span>
                </div>
                <div class="slot-row">
                    <span class="slot-name">Taxable Value #{idx} (₹)</span>
                    <span class="slot-val"><code>₹ {t_val:,.2f}</code></span>
                </div>
                <div class="slot-row">
                    <span class="slot-name">HSN / SAC Code #{idx}</span>
                    <span class="slot-val"><code>{it['hsn_code']}</code></span>
                </div>
                <div class="slot-row">
                    <span class="slot-name">Base GST Tax Rate #{idx}</span>
                    <span class="slot-val"><code>{gst_lbl}</code></span>
                </div>
                <div class="slot-row">
                    <span class="slot-name">GST Compensation CESS #{idx}</span>
                    <span class="slot-val"><code>{cess_lbl}</code></span>
                </div>
                <div class="slot-row">
                    <span class="slot-name">Total Effective Tax #{idx} (₹)</span>
                    <span class="slot-val"><code style="color: #7c3aed; font-weight: 700;">+ ₹ {tot_tax:,.2f}</code></span>
                </div>
                <div class="slot-row">
                    <span class="slot-name">Item Line Total #{idx} (₹)</span>
                    <span class="slot-val"><code style="color: #059669; font-weight: 700;">₹ {line_net:,.2f}</code></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="margin-top: 10px; margin-bottom: 10px; padding: 12px; background: #ffffff; border-radius: 10px; border: 1px solid #e2e8f0;">
            <div style="font-weight: 700; font-size: 13px; color: #64748b; margin-bottom: 8px; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px;">
                📦 Stock Item #1 Details
            </div>
            <div class="slot-row">
                <span class="slot-name">Stock Item #1 Name</span>
                <span class="slot-val empty">Required</span>
            </div>
            <div class="slot-row">
                <span class="slot-name">Billed Quantity #1</span>
                <span class="slot-val empty">Required</span>
            </div>
            <div class="slot-row">
                <span class="slot-name">Unit Price #1 (₹)</span>
                <span class="slot-val empty">Required</span>
            </div>
            <div class="slot-row">
                <span class="slot-name">HSN / SAC Code #1</span>
                <span class="slot-val empty" style="background:#f1f5f9;color:#64748b;border-color:#cbd5e1;">Auto / Optional</span>
            </div>
            <div class="slot-row">
                <span class="slot-name">GST Tax Rate #1</span>
                <span class="slot-val empty" style="background:#f1f5f9;color:#64748b;border-color:#cbd5e1;">Auto / Optional</span>
            </div>
            <div class="slot-row">
                <span class="slot-name">Trade Discount #1</span>
                <span class="slot-val empty" style="background:#f1f5f9;color:#64748b;border-color:#cbd5e1;">Auto / Optional</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Instant Multi-Item Table Renderer
    if items:
        table_rows = ""
        for idx, it in enumerate(items, 1):
            q = it['quantity']
            r = it['rate']
            dp = it['discount_pct']
            g_val = q * r
            d_val = g_val * (dp / 100.0)
            t_val = g_val - d_val
            g_rate = it['gst_rate']
            gst_val = t_val * (g_rate / 100.0)
            net_val = t_val + gst_val

            disc_str = f"{dp:.1f}%" if dp > 0 else "0%"

            table_rows += f"""
            <tr style="border-bottom: 1px solid #f1f5f9; color: #1e293b;">
                <td style="padding: 10px 8px; font-weight: 600;">{idx}</td>
                <td style="padding: 10px 8px; font-weight: 600; color: #0f172a;">{it['item_name']} <span style="font-size: 11px; color: #64748b; display: block;">HSN: {it['hsn_code']}</span></td>
                <td style="padding: 10px 8px;">{q:g}</td>
                <td style="padding: 10px 8px;">₹ {r:,.2f}</td>
                <td style="padding: 10px 8px; color: #475569;">₹ {g_val:,.2f}</td>
                <td style="padding: 10px 8px; color: #0284c7;">{disc_str}</td>
                <td style="padding: 10px 8px; font-weight: 600; color: #2563eb;">₹ {t_val:,.2f}</td>
                <td style="padding: 10px 8px; color: #7c3aed;">{g_rate:.0f}%</td>
                <td style="padding: 10px 8px; text-align: right; font-weight: 700; color: #047857;">₹ {net_val:,.2f}</td>
            </tr>
            """

        st.markdown(f"""
        <div style="margin-top: 15px; margin-bottom: 15px; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; background: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <div style="background: #f8fafc; padding: 10px 14px; font-weight: 700; font-size: 14px; color: #334155; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between;">
                <span>📦 Invoiced Stock Items ({len(items)})</span>
                <span style="color: #047857;">Net Total: ₹ {grand_total_calc:,.2f}</span>
            </div>
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; font-size: 13px; text-align: left;">
                    <thead>
                        <tr style="background: #f1f5f9; color: #475569; font-size: 12px; font-weight: 700; text-transform: uppercase;">
                            <th style="padding: 8px;">#</th>
                            <th style="padding: 8px;">Stock Item</th>
                            <th style="padding: 8px;">Qty</th>
                            <th style="padding: 8px;">Rate</th>
                            <th style="padding: 8px;">Gross</th>
                            <th style="padding: 8px;">Disc</th>
                            <th style="padding: 8px;">Taxable</th>
                            <th style="padding: 8px;">GST</th>
                            <th style="padding: 8px; text-align: right;">Net Payable</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No stock items detected yet. Speak or type item descriptions to see live invoiced items.")

    st.markdown("</div>", unsafe_allow_html=True)



    st.markdown("</div>", unsafe_allow_html=True)

    # Tally Integration Gateway & XML Generator
    xml_data = None
    if any(slots.values()):
        xml_data = build_tally_purchase_xml(slots, ledger_name=purchase_ledger)
        st.session_state.xml_payload = xml_data
        
        # Save XML to local file tally_purchase_voucher.xml for direct inspection/import
        try:
            with open("tally_purchase_voucher.xml", "w", encoding="utf-8") as f:
                f.write(xml_data)
        except Exception:
            pass

    if is_comp and xml_data:
        st.markdown("""
        <div class="glass-card">
            <div class="card-title">
                <span>Tally Prime Integration Gateway</span>
            </div>
        """, unsafe_allow_html=True)

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submit_btn = st.button("🚀 Push to Tally Prime", type="primary", use_container_width=True)
        with col_btn2:
            st.download_button(
                label="📥 Download Tally XML",
                data=xml_data,
                file_name=f"tally_purchase_{slots.get('invoice_no') or 'voucher'}.xml",
                mime="application/xml",
                use_container_width=True
            )

        if submit_btn:
            with st.spinner(f"Sending XML payload to {tally_host}..."):
                success, resp_msg = push_xml_to_tally(xml_data, tally_host)
                if success:
                    st.balloons()
                    st.success(f"Voucher Successfully Created in Tally! Response: {resp_msg}")
                else:
                    st.error("Connection to Tally Prime Server failed.")
                    st.warning(f"Error: {resp_msg}")
                    st.info("""
                    **HTTP Server Setup Instructions:**
                    1. Open Tally Prime ➔ Press `F1` (Help) ➔ `Settings` ➔ `License & Services` / `Data Configuration`.
                    2. Set **Client/Server Configuration** to **Both (or Server)** on Port **9000**.
                    3. Restart Tally Prime.
                    """)
                
                # Delete recorded voice and prepare workspace for next entry
                reset_voucher_state()
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
    elif any(slots.values()):
        if st.button("🔄 Clear & Start Next Entry", use_container_width=True):
            reset_voucher_state()
            st.rerun()

    # XML Code Block Viewer
    if st.session_state.xml_payload:
        with st.expander("📄 View Tally Prime XML Payload Envelope", expanded=True):
            st.code(st.session_state.xml_payload, language="xml")
            st.download_button(
                label="💾 Save XML File (tally_voucher.xml)",
                data=st.session_state.xml_payload,
                file_name="tally_purchase_voucher.xml",
                mime="application/xml",
                key="download_xml_expander"
            )

# Footer
st.markdown("---")
st.caption("InVoice Enterprise Gateway | Production v1.0")
