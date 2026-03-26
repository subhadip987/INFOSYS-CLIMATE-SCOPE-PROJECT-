import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import re
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --------------------------------------------------
# PAGE CONFIG & SESSION SETUP
# --------------------------------------------------
st.set_page_config(page_title="ClimateScope", layout="wide", page_icon="🌍")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "users" not in st.session_state:
    st.session_state.users = {
        "subhadip": {"email": "subhadip@gmail.com", "password": "subhadip123"}
    }

if "image_counter" not in st.session_state:
    st.session_state.image_counter = 0

if "login_bg_idx" not in st.session_state:
    st.session_state.login_bg_idx = 0

if "alert_dismissed" not in st.session_state:
    st.session_state.alert_dismissed = False

# --------------------------------------------------
# UTILITY: Hex color -> rgba string
# --------------------------------------------------
def hex_to_rgba(hex_color, alpha=0.27):
    """Convert '#rrggbb' to 'rgba(r,g,b,alpha)'."""
    h = hex_color.lstrip('#')
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    return hex_color  # fallback: return as-is

# --------------------------------------------------
# GLOBAL CSS — Glassmorphism + 3D card press effects
# --------------------------------------------------
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

/* Password masking font fallback */
@font-face {
  font-family: 'password';
  src: local('Arial');
  unicode-range: U+0021-007E;
  size-adjust: 120%;
}

:root {
  --primary: #00d4ff;
  --secondary: #7b2fff;
  --accent: #ff6b6b;
  --accent2: #ffd93d;
  --bg-dark: #0a0e1a;
  --bg-card: rgba(255,255,255,0.04);
  --border: rgba(255,255,255,0.08);
  --text: #e8eaf6;
  --text-muted: #8892a4;
  --glow: 0 0 30px rgba(0,212,255,0.25);
}

html, body, .stApp {
  font-family: 'DM Sans', sans-serif;
  background: var(--bg-dark) !important;
  color: var(--text) !important;
}

/* ---- STREAMLIT TOP HEADER / TOOLBAR — dark glassmorphism ---- */
[data-testid="stHeader"],
header[data-testid="stHeader"],
.stAppHeader,
header.stAppHeader {
  background: linear-gradient(90deg,
    rgba(10,14,26,0.98) 0%,
    rgba(20,10,40,0.96) 40%,
    rgba(0,30,45,0.96) 70%,
    rgba(10,14,26,0.98) 100%) !important;
  backdrop-filter: blur(20px) saturate(1.4) !important;
  -webkit-backdrop-filter: blur(20px) saturate(1.4) !important;
  border-bottom: 1px solid rgba(0,212,255,0.15) !important;
  box-shadow: 0 2px 24px rgba(0,0,0,0.5), 0 0 40px rgba(123,47,255,0.08) !important;
}

/* Toolbar icons (share, star, pencil, github) */
[data-testid="stHeader"] button,
[data-testid="stHeader"] a,
[data-testid="stToolbar"] button,
[data-testid="stToolbar"] a,
.stAppHeader button,
.stAppHeader a {
  color: #8892a4 !important;
  opacity: 0.8 !important;
  transition: color 0.2s, opacity 0.2s !important;
}
[data-testid="stHeader"] button:hover,
[data-testid="stHeader"] a:hover,
.stAppHeader button:hover,
.stAppHeader a:hover {
  color: #00d4ff !important;
  opacity: 1 !important;
}

/* Streamlit top-right deploy/menu button */
[data-testid="stToolbar"],
#MainMenu {
  color: #8892a4 !important;
}
#MainMenu button {
  color: #8892a4 !important;
}

/* Animated gradient line under header */
[data-testid="stHeader"]::after,
.stAppHeader::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, #7b2fff, #00d4ff, #ff6b6b, #7b2fff);
  background-size: 200% 100%;
  animation: headerGlow 4s linear infinite;
}
@keyframes headerGlow {
  0%   { background-position: 0% 0%; }
  100% { background-position: 200% 0%; }
}

/* Main content area top padding so content doesn't hide under header */
.main .block-container {
  padding-top: 1rem !important;
}

.stApp::before {
  content: '';
  position: fixed;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 20% 20%, rgba(123,47,255,0.18) 0%, transparent 60%),
    radial-gradient(ellipse 60% 80% at 80% 70%, rgba(0,212,255,0.14) 0%, transparent 60%),
    radial-gradient(ellipse 50% 50% at 50% 90%, rgba(255,107,107,0.10) 0%, transparent 60%);
  pointer-events: none;
  z-index: 0;
  animation: meshPulse 12s ease-in-out infinite alternate;
}

@keyframes meshPulse {
  0%   { opacity: 0.7; }
  100% { opacity: 1; }
}

[data-testid="stSidebar"] {
  background: rgba(10,14,26,0.95) !important;
  border-right: 1px solid var(--border);
  backdrop-filter: blur(20px);
}
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] p {
  color: var(--text) !important;
}

.kpi-card {
  background: linear-gradient(135deg, rgba(255,255,255,0.07) 0%, rgba(255,255,255,0.02) 100%);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 22px 18px;
  margin-bottom: 12px;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.15s cubic-bezier(.17,.67,.83,.67), box-shadow 0.15s ease;
  transform-style: preserve-3d;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 2px 8px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.08);
}
.kpi-card:hover {
  transform: translateY(-6px) scale(1.01) rotateX(2deg);
  box-shadow: 0 20px 48px rgba(0,0,0,0.6), var(--glow), inset 0 1px 0 rgba(255,255,255,0.12);
}
.kpi-card:active {
  transform: translateY(1px) scale(0.98) rotateX(-1deg) !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.5), inset 0 2px 4px rgba(0,0,0,0.3) !important;
  transition: transform 0.05s, box-shadow 0.05s;
}
.kpi-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--secondary), var(--primary));
  border-radius: 16px 16px 0 0;
}
.kpi-label {
  font-family: 'DM Sans', sans-serif;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 8px;
}
.kpi-value {
  font-family: 'Syne', sans-serif;
  font-size: 36px;
  font-weight: 800;
  color: var(--primary);
  line-height: 1;
  text-shadow: 0 0 20px rgba(0,212,255,0.4);
}
.kpi-sub {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 6px;
}
.kpi-icon {
  position: absolute;
  right: 18px; top: 18px;
  font-size: 32px;
  opacity: 0.25;
}

.insight-card {
  background: linear-gradient(135deg, rgba(0,212,255,0.08), rgba(123,47,255,0.06));
  border: 1px solid rgba(0,212,255,0.2);
  border-radius: 16px;
  padding: 20px 24px;
  margin: 12px 0;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.15s cubic-bezier(.17,.67,.83,.67), box-shadow 0.15s ease;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.insight-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 36px rgba(0,0,0,0.5), 0 0 0 1px rgba(0,212,255,0.3);
}
.insight-card:active {
  transform: translateY(2px) scale(0.99);
  box-shadow: 0 2px 8px rgba(0,0,0,0.5), inset 0 2px 6px rgba(0,0,0,0.2);
  transition: transform 0.05s, box-shadow 0.05s;
}
.insight-title {
  font-family: 'Syne', sans-serif;
  font-size: 15px;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 8px;
}
.insight-text {
  font-size: 14px;
  color: var(--text);
  line-height: 1.7;
}
.insight-badge {
  display: inline-block;
  background: rgba(0,212,255,0.15);
  color: var(--primary);
  border: 1px solid rgba(0,212,255,0.3);
  border-radius: 20px;
  padding: 2px 12px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1px;
  margin-bottom: 10px;
}

.section-header {
  font-family: 'Syne', sans-serif;
  font-size: 22px;
  font-weight: 800;
  color: var(--text);
  margin: 32px 0 16px 0;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 10px;
}

.risk-bar-wrap {
  background: rgba(255,255,255,0.05);
  border-radius: 100px;
  height: 10px;
  overflow: hidden;
  margin: 8px 0;
}
.risk-bar-fill {
  height: 100%;
  border-radius: 100px;
  transition: width 0.8s ease;
}

.hero-banner {
  background: linear-gradient(135deg, rgba(123,47,255,0.2) 0%, rgba(0,212,255,0.15) 50%, rgba(255,107,107,0.1) 100%);
  border: 1px solid rgba(0,212,255,0.2);
  border-radius: 20px;
  padding: 32px 36px;
  margin-bottom: 28px;
  position: relative;
  overflow: hidden;
}
.hero-banner::after {
  content: '🌍';
  position: absolute;
  right: 32px; top: 50%;
  transform: translateY(-50%);
  font-size: 80px;
  opacity: 0.15;
}
.hero-title {
  font-family: 'Syne', sans-serif;
  font-size: 38px;
  font-weight: 800;
  background: linear-gradient(90deg, var(--primary), var(--secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 4px;
}
.hero-sub {
  font-size: 15px;
  color: var(--text-muted);
}

.live-time {
  font-family: 'Syne', sans-serif;
  font-size: 13px;
  color: var(--primary);
  background: rgba(0,212,255,0.08);
  border: 1px solid rgba(0,212,255,0.15);
  border-radius: 8px;
  padding: 4px 12px;
  display: inline-block;
}

/* ---- WEATHER TICKER ---- */
.weather-ticker-wrap {
  overflow: hidden;
  background: rgba(0,212,255,0.06);
  border: 1px solid rgba(0,212,255,0.15);
  border-radius: 10px;
  padding: 8px 0;
  margin-bottom: 16px;
}
.weather-ticker {
  display: inline-block;
  white-space: nowrap;
  animation: tickerScroll 30s linear infinite;
  font-family: 'DM Sans', sans-serif;
  font-size: 13px;
  color: var(--primary);
  letter-spacing: 1px;
}
@keyframes tickerScroll {
  0%   { transform: translateX(100vw); }
  100% { transform: translateX(-100%); }
}

/* ---- ALERT BANNER ---- */
.alert-banner {
  background: linear-gradient(135deg, rgba(255,107,107,0.15), rgba(255,211,61,0.08));
  border: 1px solid rgba(255,107,107,0.4);
  border-radius: 14px;
  padding: 14px 20px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  animation: alertPulse 2s ease-in-out infinite;
}
@keyframes alertPulse {
  0%, 100% { border-color: rgba(255,107,107,0.4); }
  50%       { border-color: rgba(255,107,107,0.8); box-shadow: 0 0 18px rgba(255,107,107,0.2); }
}

/* ---- STAT MINI CARDS ---- */
.stat-mini {
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  text-align: center;
}
.stat-mini-val {
  font-family: 'Syne', sans-serif;
  font-size: 22px;
  font-weight: 800;
  color: var(--primary);
}
.stat-mini-label {
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 1px;
  text-transform: uppercase;
}

/* ---- FEATURE BADGE ---- */
.feature-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, rgba(123,47,255,0.2), rgba(0,212,255,0.1));
  border: 1px solid rgba(123,47,255,0.3);
  border-radius: 20px;
  padding: 4px 14px;
  font-size: 12px;
  font-weight: 600;
  color: #c0a0ff;
  margin: 3px;
  letter-spacing: 0.5px;
}

.stSelectbox > div > div,
.stTextInput > div > div > input,
.stTextArea textarea {
  background: rgba(255,255,255,0.05) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  border-radius: 10px !important;
}

/* ---- PASSWORD FIELD — always mask characters ---- */
input[type="password"],
.stTextInput > div > div > input[type="password"] {
  -webkit-text-security: disc !important;
  text-security: disc !important;
  font-family: 'password', monospace !important;
  letter-spacing: 4px !important;
  color: var(--text) !important;
}

/* ---- LOGIN PAGE INPUT STYLING ---- */
.login-glass-card .stTextInput > div > div > input {
  background: rgba(255,255,255,0.07) !important;
  border: 1px solid rgba(0,212,255,0.25) !important;
  color: #e8eaf6 !important;
  border-radius: 10px !important;
  padding: 10px 14px !important;
  font-size: 14px !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
.login-glass-card .stTextInput > div > div > input:focus {
  border-color: rgba(0,212,255,0.6) !important;
  box-shadow: 0 0 0 3px rgba(0,212,255,0.12) !important;
  outline: none !important;
}
.login-glass-card .stTextInput label {
  color: #8892a4 !important;
  font-size: 12px !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
}

/* Streamlit's show/hide eye icon — keep it visible */
.stTextInput > div > div > div[data-testid="InputInstructions"],
.stTextInput button[kind="secondaryFormSubmit"] {
  color: #8892a4 !important;
}
.stTextInput > div > div > button {
  background: transparent !important;
  border: none !important;
  color: #8892a4 !important;
  cursor: pointer !important;
}
.stTextInput > div > div > button:hover {
  color: #00d4ff !important;
}
.stDataFrame { border-radius: 12px; overflow: hidden; }
[data-testid="stMetricValue"] { color: var(--primary) !important; font-family: 'Syne', sans-serif !important; }
[data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size: 11px !important; letter-spacing: 1px; }
h1, h2, h3, h4 { font-family: 'Syne', sans-serif !important; color: var(--text) !important; }
p, label, .stMarkdown { color: var(--text) !important; }
.stProgress > div > div > div { background: linear-gradient(90deg, var(--secondary), var(--primary)) !important; }
.stAlert { border-radius: 12px !important; }
div[data-testid="stTab"] { color: var(--text) !important; }
button[data-testid="stDownloadButton"] > div,
.stButton > button {
  background: linear-gradient(135deg, var(--secondary), var(--primary)) !important;
  color: white !important;
  border: none !important;
  border-radius: 10px !important;
  font-family: 'Syne', sans-serif !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  transition: all 0.15s !important;
  box-shadow: 0 4px 16px rgba(0,212,255,0.25) !important;
}
.stButton > button:active {
  transform: scale(0.97) translateY(1px) !important;
  box-shadow: 0 2px 6px rgba(0,212,255,0.15) !important;
}
</style>
"""

# Login page animated background CSS with weather images slideshow
LOGIN_BG_CSS = """
<style>
/* Full-page animated weather background slideshow */
.login-bg-overlay {
  position: fixed;
  inset: 0;
  z-index: -2;
  background-size: cover;
  background-position: center;
  animation: bgFade 10s ease-in-out infinite;
}

/* Particle rain effect */
.rain-container {
  position: fixed;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  overflow: hidden;
}
.raindrop {
  position: absolute;
  width: 2px;
  border-radius: 2px;
  background: linear-gradient(180deg, rgba(0,212,255,0), rgba(0,212,255,0.6));
  animation: rain linear infinite;
}

@keyframes rain {
  0%   { transform: translateY(-100px); opacity: 0; }
  10%  { opacity: 1; }
  90%  { opacity: 0.7; }
  100% { transform: translateY(110vh); opacity: 0; }
}

/* Dark vignette overlay */
.login-vignette {
  position: fixed;
  inset: 0;
  z-index: -1;
  background:
    radial-gradient(ellipse 70% 70% at 50% 50%, transparent 30%, rgba(5,7,15,0.7) 100%),
    linear-gradient(180deg, rgba(5,7,15,0.55) 0%, rgba(5,7,15,0.3) 50%, rgba(5,7,15,0.75) 100%);
  pointer-events: none;
}

/* Floating weather particles */
@keyframes floatUp {
  0%   { transform: translateY(0) translateX(0) scale(1); opacity: 0.7; }
  50%  { transform: translateY(-60px) translateX(20px) scale(1.1); opacity: 1; }
  100% { transform: translateY(-120px) translateX(-10px) scale(0.8); opacity: 0; }
}
.weather-particle {
  position: fixed;
  font-size: 22px;
  animation: floatUp linear infinite;
  pointer-events: none;
  z-index: 0;
}

/* Login card glass */
.login-glass-card {
  background: rgba(10, 14, 26, 0.72);
  backdrop-filter: blur(28px) saturate(1.4);
  -webkit-backdrop-filter: blur(28px) saturate(1.4);
  border: 1px solid rgba(0,212,255,0.18);
  border-radius: 28px;
  padding: 44px 40px 36px;
  box-shadow:
    0 30px 80px rgba(0,0,0,0.6),
    0 0 0 1px rgba(255,255,255,0.04),
    inset 0 1px 0 rgba(255,255,255,0.08);
  position: relative;
  overflow: hidden;
}
.login-glass-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, #7b2fff, #00d4ff, #ff6b6b);
  border-radius: 28px 28px 0 0;
}

/* Slideshow bg images via JS injection */
#weather-bg-img {
  position: fixed;
  inset: 0;
  z-index: -3;
  width: 100%; height: 100%;
  object-fit: cover;
  transition: opacity 1.5s ease;
  opacity: 1;
}

/* Stats strip at bottom of login */
.login-stats-strip {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 24px;
  flex-wrap: wrap;
}
.login-stat-pill {
  background: rgba(0,212,255,0.1);
  border: 1px solid rgba(0,212,255,0.2);
  border-radius: 20px;
  padding: 6px 16px;
  font-size: 12px;
  color: #8892a4;
  display: flex;
  align-items: center;
  gap: 6px;
}
.login-stat-pill span { color: #00d4ff; font-weight: 700; }

/* ---- HARD OVERRIDE: password fields on login page ---- */
input[type="password"] {
  -webkit-text-security: disc !important;
  text-security: disc !important;
  letter-spacing: 6px !important;
  font-size: 18px !important;
  color: #e8eaf6 !important;
  background: rgba(255,255,255,0.07) !important;
  border: 1px solid rgba(0,212,255,0.25) !important;
  border-radius: 10px !important;
}
input[type="password"]::placeholder {
  letter-spacing: 1px !important;
  font-size: 13px !important;
}
/* Username / text inputs on login */
input[type="text"] {
  color: #e8eaf6 !important;
  background: rgba(255,255,255,0.07) !important;
  border: 1px solid rgba(0,212,255,0.25) !important;
  border-radius: 10px !important;
}
input[type="text"]:focus,
input[type="password"]:focus {
  border-color: rgba(0,212,255,0.6) !important;
  box-shadow: 0 0 0 3px rgba(0,212,255,0.12) !important;
  outline: none !important;
}
</style>
"""

# --------------------------------------------------
# DATA ENGINE & SEASONAL MAPPING
# --------------------------------------------------
@st.cache_data
def load_data():
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GlobalWeatherRepository.csv")
    if not os.path.exists(csv_path):
        csv_path = "GlobalWeatherRepository.csv"
    if not os.path.exists(csv_path):
        st.error("GlobalWeatherRepository.csv not found.")
        st.stop()

    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df.get("last_updated"), errors="coerce")
    df['month'] = df['date'].dt.month

    def get_season(month):
        if month in [3,4,5]:    return "Summer"
        if month in [6,7,8,9]:  return "Monsoon"
        if month in [10,11]:    return "Autumn"
        return "Winter"

    df['season'] = df['month'].apply(get_season)

    if 'temperature_celsius' in df.columns and 'humidity' in df.columns:
        df['heat_index'] = df['temperature_celsius'] + 0.33 * (df.get('humidity', 50) * 0.1) - 4
    if 'wind_kph' in df.columns and 'temperature_celsius' in df.columns:
        df['wind_chill'] = 13.12 + 0.6215 * df['temperature_celsius'] - 11.37 * (df['wind_kph']**0.16) + 0.3965 * df['temperature_celsius'] * (df['wind_kph']**0.16)
    if 'pressure_mb' in df.columns:
        df['pressure_trend'] = df.groupby('country')['pressure_mb'].diff().fillna(0)

    return df

# --------------------------------------------------
# COUNTRY ISO MAP HELPER
# --------------------------------------------------
@st.cache_data
def get_country_iso_map():
    return {
        "Afghanistan":"AFG","Albania":"ALB","Algeria":"DZA","Argentina":"ARG","Australia":"AUS",
        "Austria":"AUT","Bangladesh":"BGD","Belgium":"BEL","Bolivia":"BOL","Brazil":"BRA",
        "Bulgaria":"BGR","Cambodia":"KHM","Canada":"CAN","Chile":"CHL","China":"CHN",
        "Colombia":"COL","Congo":"COD","Cuba":"CUB","Czech Republic":"CZE","Denmark":"DNK",
        "Ecuador":"ECU","Egypt":"EGY","Ethiopia":"ETH","Finland":"FIN","France":"FRA",
        "Germany":"DEU","Ghana":"GHA","Greece":"GRC","Hungary":"HUN","India":"IND",
        "Indonesia":"IDN","Iran":"IRN","Iraq":"IRQ","Ireland":"IRL","Israel":"ISR",
        "Italy":"ITA","Japan":"JPN","Jordan":"JOR","Kenya":"KEN","Malaysia":"MYS",
        "Mexico":"MEX","Morocco":"MAR","Netherlands":"NLD","New Zealand":"NZL",
        "Nigeria":"NGA","Norway":"NOR","Pakistan":"PAK","Peru":"PER","Philippines":"PHL",
        "Poland":"POL","Portugal":"PRT","Romania":"ROU","Russia":"RUS","Saudi Arabia":"SAU",
        "Senegal":"SEN","Singapore":"SGP","South Africa":"ZAF","South Korea":"KOR",
        "Spain":"ESP","Sri Lanka":"LKA","Sudan":"SDN","Sweden":"SWE","Switzerland":"CHE",
        "Syria":"SYR","Thailand":"THA","Turkey":"TUR","Ukraine":"UKR","United Arab Emirates":"ARE",
        "United Kingdom":"GBR","United States":"USA","Uruguay":"URY","Venezuela":"VEN",
        "Vietnam":"VNM","Zimbabwe":"ZWE","Nepal":"NPL","Myanmar":"MMR","Libya":"LBY",
        "Tunisia":"TUN","Kazakhstan":"KAZ","Uzbekistan":"UZB","Azerbaijan":"AZE",
        "Georgia":"GEO","Armenia":"ARM","Tanzania":"TZA","Uganda":"UGA","Rwanda":"RWA",
        "Ivory Coast":"CIV","Cameroon":"CMR","Angola":"AGO","Mozambique":"MOZ",
        "Madagascar":"MDG","Somalia":"SOM","Yemen":"YEM","Oman":"OMN","Kuwait":"KWT",
        "Qatar":"QAT","Bahrain":"BHR","Lebanon":"LBN","Palestine":"PSE",
    }

@st.cache_data
def get_country_centers():
    return {
        "Afghanistan": (33.9391, 67.7100), "Albania": (41.1533, 20.1683),
        "Algeria": (28.0339, 1.6596), "Argentina": (-38.4161, -63.6167),
        "Australia": (-25.2744, 133.7751), "Austria": (47.5162, 14.5501),
        "Bangladesh": (23.6850, 90.3563), "Belgium": (50.5039, 4.4699),
        "Bolivia": (-16.2902, -63.5887), "Brazil": (-14.2350, -51.9253),
        "Bulgaria": (42.7339, 25.4858), "Cambodia": (12.5657, 104.9910),
        "Canada": (56.1304, -106.3468), "Chile": (-35.6751, -71.5430),
        "China": (35.8617, 104.1954), "Colombia": (4.5709, -74.2973),
        "Congo": (-4.0383, 21.7587), "Cuba": (21.5218, -77.7812),
        "Czech Republic": (49.8175, 15.4730), "Denmark": (56.2639, 9.5018),
        "Ecuador": (-1.8312, -78.1834), "Egypt": (26.8206, 30.8025),
        "Ethiopia": (9.1450, 40.4897), "Finland": (61.9241, 25.7482),
        "France": (46.2276, 2.2137), "Germany": (51.1657, 10.4515),
        "Ghana": (7.9465, -1.0232), "Greece": (39.0742, 21.8243),
        "Hungary": (47.1625, 19.5033), "India": (20.5937, 78.9629),
        "Indonesia": (-0.7893, 113.9213), "Iran": (32.4279, 53.6880),
        "Iraq": (33.2232, 43.6793), "Ireland": (53.1424, -7.6921),
        "Israel": (31.0461, 34.8516), "Italy": (41.8719, 12.5674),
        "Japan": (36.2048, 138.2529), "Jordan": (30.5852, 36.2384),
        "Kenya": (-0.0236, 37.9062), "Malaysia": (4.2105, 101.9758),
        "Mexico": (23.6345, -102.5528), "Morocco": (31.7917, -7.0926),
        "Netherlands": (52.1326, 5.2913), "New Zealand": (-40.9006, 174.8860),
        "Nigeria": (9.0820, 8.6753), "Norway": (60.4720, 8.4689),
        "Pakistan": (30.3753, 69.3451), "Peru": (-9.1900, -75.0152),
        "Philippines": (12.8797, 121.7740), "Poland": (51.9194, 19.1451),
        "Portugal": (39.3999, -8.2245), "Romania": (45.9432, 24.9668),
        "Russia": (61.5240, 105.3188), "Saudi Arabia": (23.8859, 45.0792),
        "Senegal": (14.4974, -14.4524), "Singapore": (1.3521, 103.8198),
        "South Africa": (-30.5595, 22.9375), "South Korea": (35.9078, 127.7669),
        "Spain": (40.4637, -3.7492), "Sri Lanka": (7.8731, 80.7718),
        "Sudan": (12.8628, 30.2176), "Sweden": (60.1282, 18.6435),
        "Switzerland": (46.8182, 8.2275), "Syria": (34.8021, 38.9968),
        "Thailand": (15.8700, 100.9925), "Turkey": (38.9637, 35.2433),
        "Ukraine": (48.3794, 31.1656), "United Arab Emirates": (23.4241, 53.8478),
        "United Kingdom": (55.3781, -3.4360), "United States": (37.0902, -95.7129),
        "Uruguay": (-32.5228, -55.7658), "Venezuela": (6.4238, -66.5897),
        "Vietnam": (14.0583, 108.2772), "Zimbabwe": (-19.0154, 29.1549),
        "Nepal": (28.3949, 84.1240), "Myanmar": (21.9162, 95.9560),
        "Libya": (26.3351, 17.2283), "Tunisia": (33.8869, 9.5375),
        "Kazakhstan": (48.0196, 66.9237), "Uzbekistan": (41.3775, 64.5853),
        "Azerbaijan": (40.1431, 47.5769), "Georgia": (42.3154, 43.3569),
        "Armenia": (40.0691, 45.0382), "Tanzania": (-6.3690, 34.8888),
        "Uganda": (1.3733, 32.2903), "Rwanda": (-1.9403, 29.8739),
        "Ivory Coast": (7.5400, -5.5471), "Cameroon": (3.8480, 11.5021),
        "Angola": (-11.2027, 17.8739), "Mozambique": (-18.6657, 35.5296),
        "Madagascar": (-18.7669, 46.8691), "Somalia": (5.1521, 46.1996),
        "Yemen": (15.5527, 48.5164), "Oman": (21.5129, 55.9233),
        "Kuwait": (29.3117, 47.4818), "Qatar": (25.3548, 51.1839),
        "Bahrain": (25.9304, 50.6378), "Lebanon": (33.8547, 35.8623),
        "Palestine": (31.9522, 35.2332),
    }

# --------------------------------------------------
# ANALYTICAL HELPERS
# --------------------------------------------------
def calculate_health_score(cdf, metric):
    if metric not in cdf.columns or len(cdf) < 3:
        return 50
    anomalies = np.abs((cdf[metric] - cdf[metric].mean()) / (cdf[metric].std() + 1e-9)) > 2
    anomaly_ratio = anomalies.mean()
    skew = abs(cdf[metric].skew())
    score = 100 - (anomaly_ratio * 100) - (skew * 10)
    return max(0, min(100, int(score)))

def city_similarity(df, city1, city2, metric):
    m1 = df[df['country'] == city1][metric].mean()
    m2 = df[df['country'] == city2][metric].mean()
    diff = abs(m1 - m2)
    return max(0, 100 - diff)

def kpi_card(label, value, sub="", icon="📊", color="#00d4ff"):
    st.markdown(f"""
    <div class="kpi-card" onclick="this.classList.toggle('pressed')">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color:{color};">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

def insight_card(badge, title, text):
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-badge">{badge}</div>
        <div class="insight-title">{title}</div>
        <div class="insight-text">{text}</div>
    </div>
    """, unsafe_allow_html=True)

def section_header(icon, title):
    st.markdown(f'<div class="section-header">{icon} {title}</div>', unsafe_allow_html=True)

# --------------------------------------------------
# PLOTLY DARK THEME HELPER
# --------------------------------------------------
def dark_theme():
    return dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='DM Sans', color='#e8eaf6', size=12),
        xaxis=dict(gridcolor='rgba(255,255,255,0.06)', zerolinecolor='rgba(255,255,255,0.1)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.06)', zerolinecolor='rgba(255,255,255,0.1)'),
        colorway=['#00d4ff','#7b2fff','#ff6b6b','#ffd93d','#06d6a0','#f72585'],
        margin=dict(l=20, r=20, t=40, b=20),
    )

def apply_dark(fig):
    fig.update_layout(**dark_theme())
    return fig

# --------------------------------------------------
# WEATHER TICKER HELPER
# --------------------------------------------------
def weather_ticker(df, country):
    cdf = df[df['country'] == country]
    temp = cdf['temperature_celsius'].mean() if 'temperature_celsius' in cdf.columns else 0
    wind = cdf['wind_kph'].mean() if 'wind_kph' in cdf.columns else 0
    hum  = cdf['humidity'].mean() if 'humidity' in cdf.columns else 0
    pres = cdf['pressure_mb'].mean() if 'pressure_mb' in cdf.columns else 0
    uv   = cdf['uv_index'].mean() if 'uv_index' in cdf.columns else 0
    vis  = cdf['visibility_km'].mean() if 'visibility_km' in cdf.columns else 0

    ticker_text = (
        f"🌡️ Avg Temp: {temp:.1f}°C   ·   "
        f"💨 Wind: {wind:.1f} km/h   ·   "
        f"💧 Humidity: {hum:.0f}%   ·   "
        f"🔵 Pressure: {pres:.0f} mb   ·   "
        f"☀️ UV Index: {uv:.1f}   ·   "
        f"👁️ Visibility: {vis:.1f} km   ·   "
        f"📍 {country} Live Metrics Feed   ·   "
        f"🌍 ClimateScope™ v3.0   ·   "
    )
    st.markdown(f"""
    <div class="weather-ticker-wrap">
        <span class="weather-ticker">{ticker_text * 3}</span>
    </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------
# CHOROPLETH MAP VIEW
# --------------------------------------------------
def choropleth_view(df, focused_country=None):
    section_header("🗺️", "Global Climate Choropleth Map")

    if focused_country:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(0,212,255,0.12), rgba(123,47,255,0.08));
                    border: 1px solid rgba(0,212,255,0.3); border-radius: 12px;
                    padding: 10px 18px; margin-bottom: 14px; display: flex; align-items: center; gap: 10px;">
            <span style="font-size:18px;">📍</span>
            <span style="font-family:'Syne',sans-serif; font-size:14px; font-weight:700; color:#00d4ff;">
                Map focused on: {focused_country}
            </span>
            <span style="font-size:12px; color:#8892a4; margin-left:auto;">Synced with country selection</span>
        </div>
        """, unsafe_allow_html=True)

    iso_map = get_country_iso_map()
    country_centers = get_country_centers()

    num_cols = [c for c in df.select_dtypes(include=np.number).columns
                if c not in ['month','lat','lon','latitude','longitude']]
    map_metric = st.selectbox("Select Map Metric", num_cols, key="map_metric_sel")
    agg_method = st.radio("Aggregation", ["Mean", "Max", "Min"], horizontal=True)

    country_agg = df.groupby("country")[map_metric].agg(agg_method.lower()).reset_index()
    country_agg.columns = ["country", "value"]
    country_agg["iso_alpha"] = country_agg["country"].map(iso_map)
    country_agg = country_agg.dropna(subset=["iso_alpha"])

    if country_agg.empty:
        st.warning("Not enough country matches for ISO codes.")
        return

    color_scales = {
        "Temperature": "RdYlBu_r", "Wind": "Blues",
        "Humidity": "Tealgrn", "Pressure": "Purpor", "Default": "Plasma"
    }
    scale = "Temperature" if "temp" in map_metric.lower() else \
            "Wind" if "wind" in map_metric.lower() else \
            "Humidity" if "humid" in map_metric.lower() else "Default"

    focused_iso = iso_map.get(focused_country) if focused_country else None

    fig = go.Figure()
    fig.add_trace(go.Choropleth(
        locations=country_agg["iso_alpha"], z=country_agg["value"],
        text=country_agg["country"], colorscale=color_scales[scale],
        autocolorscale=False, reversescale=False,
        marker_line_color='rgba(255,255,255,0.1)', marker_line_width=0.5,
        colorbar=dict(
            title=dict(text=map_metric, font=dict(color='#e8eaf6')),
            tickfont=dict(color='#e8eaf6'), bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(255,255,255,0.1)', len=0.7
        ),
        hovertemplate='<b>%{text}</b><br>' + map_metric + ': %{z:.2f}<extra></extra>'
    ))

    if focused_iso:
        focused_row = country_agg[country_agg["iso_alpha"] == focused_iso]
        if not focused_row.empty:
            fig.add_trace(go.Choropleth(
                locations=focused_row["iso_alpha"], z=focused_row["value"],
                text=focused_row["country"],
                colorscale=[[0, "#00d4ff"], [1, "#00d4ff"]],
                showscale=False, marker_line_color='#ffffff', marker_line_width=3,
                hovertemplate='<b>%{text}</b> ★ SELECTED<br>' + map_metric + ': %{z:.2f}<extra></extra>',
                name=focused_country
            ))

    geo_kwargs = dict(
        showframe=False, showcoastlines=True,
        coastlinecolor='rgba(255,255,255,0.15)', showland=True,
        landcolor='rgba(30,35,55,0.8)', showocean=True,
        oceancolor='rgba(10,14,26,0.9)', showcountries=True,
        countrycolor='rgba(255,255,255,0.08)', showlakes=True,
        lakecolor='rgba(10,14,26,0.7)', bgcolor='rgba(0,0,0,0)',
    )
    if focused_country and focused_country in country_centers:
        lat, lon = country_centers[focused_country]
        geo_kwargs["projection_type"] = "orthographic"
        geo_kwargs["projection_rotation"] = dict(lon=lon, lat=lat, roll=0)
        geo_kwargs["center"] = dict(lon=lon, lat=lat)
    else:
        geo_kwargs["projection_type"] = "natural earth"

    fig.update_layout(
        geo=geo_kwargs, paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=10, b=0), height=520,
        font=dict(color='#e8eaf6', family='DM Sans'), showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    col_toggle1, col_toggle2, _ = st.columns([1, 1, 3])
    if col_toggle1.button("🌍 Reset to World View", key="reset_map"):
        st.rerun()
    if focused_country and col_toggle2.button(f"📍 Re-focus {focused_country}", key="refocus_map"):
        st.rerun()

    top10 = country_agg.nlargest(10, "value")[["country", "value"]].reset_index(drop=True)
    top10.columns = ["Country", map_metric]
    if focused_country:
        top10["Selected"] = top10["Country"].apply(lambda x: "★" if x == focused_country else "")

    col1, col2 = st.columns([1, 2])
    with col1:
        section_header("🏆", f"Top 10 by {map_metric}")
        st.dataframe(top10.style.background_gradient(cmap='Blues', subset=[map_metric]), use_container_width=True)
    with col2:
        fig2 = px.bar(top10, x="Country", y=map_metric, color=map_metric,
                      color_continuous_scale="Plasma", title=f"Top 10 Countries — {map_metric}")
        apply_dark(fig2)
        st.plotly_chart(fig2, use_container_width=True)

    if focused_country:
        focused_val = country_agg[country_agg["country"] == focused_country]["value"]
        if not focused_val.empty:
            val = focused_val.values[0]
            global_mean = country_agg["value"].mean()
            rank = int((country_agg["value"] >= val).sum())
            total = len(country_agg)
            pct_diff = ((val - global_mean) / global_mean * 100) if global_mean != 0 else 0
            arrow = "▲" if pct_diff > 0 else "▼"
            insight_card(
                f"📍 {focused_country.upper()}",
                f"{focused_country} — {map_metric} Profile on Global Map",
                f"<b>{focused_country}</b> has a {agg_method.lower()} {map_metric} of <b>{val:.2f}</b>. "
                f"This is <b>{arrow} {abs(pct_diff):.1f}%</b> vs the global average of <b>{global_mean:.2f}</b>. "
                f"Ranked <b>#{rank}</b> out of <b>{total}</b> countries."
            )


# --------------------------------------------------
# VIOLIN + BOX CHART PANEL
# --------------------------------------------------
def violin_box_panel(df, country):
    section_header("🎻", "Violin & Box Distribution Analysis")
    cdf = df[df['country'] == country].copy()

    num_metrics = [c for c in cdf.select_dtypes(include=np.number).columns
                   if c not in ['month','lat','lon','latitude','longitude']]

    col_a, col_b = st.columns([1, 2])
    with col_a:
        vb_metric = st.selectbox("Metric for Violin/Box", num_metrics, key="vb_metric")
        group_by  = st.radio("Group by", ["season", "None"], key="vb_group")
    with col_b:
        chart_type = st.radio("Chart Type", ["Violin", "Box", "Both Side-by-Side"], horizontal=True, key="vb_chart_type")

    grp = "season" if (group_by == "season" and "season" in cdf.columns) else None

    if chart_type == "Violin" or chart_type == "Both Side-by-Side":
        if grp:
            fig_vio = px.violin(cdf, y=vb_metric, x=grp, color=grp, box=True,
                                points="outliers", title=f"🎻 Violin — {vb_metric} by Season",
                                color_discrete_sequence=['#00d4ff','#7b2fff','#ff6b6b','#ffd93d'])
        else:
            fig_vio = px.violin(cdf, y=vb_metric, box=True, points="all",
                                title=f"🎻 Violin — {vb_metric}",
                                color_discrete_sequence=['#00d4ff'])
        apply_dark(fig_vio)
        fig_vio.update_traces(meanline_visible=True, meanline_color='#ffd93d', meanline_width=2)

    if chart_type == "Box" or chart_type == "Both Side-by-Side":
        if grp:
            fig_box = px.box(cdf, y=vb_metric, x=grp, color=grp,
                             notched=True, points="outliers",
                             title=f"📦 Box Plot — {vb_metric} by Season",
                             color_discrete_sequence=['#06d6a0','#7b2fff','#ff6b6b','#ffd93d'])
        else:
            fig_box = px.box(cdf, y=vb_metric, notched=True, points="all",
                             title=f"📦 Box Plot — {vb_metric}",
                             color_discrete_sequence=['#06d6a0'])
        apply_dark(fig_box)

    if chart_type == "Violin":
        st.plotly_chart(fig_vio, use_container_width=True)
    elif chart_type == "Box":
        st.plotly_chart(fig_box, use_container_width=True)
    else:
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(fig_vio, use_container_width=True)
        with c2: st.plotly_chart(fig_box, use_container_width=True)

    # Quick stats summary strip
    q1  = cdf[vb_metric].quantile(0.25)
    med = cdf[vb_metric].median()
    q3  = cdf[vb_metric].quantile(0.75)
    iqr = q3 - q1
    mn  = cdf[vb_metric].mean()
    sd  = cdf[vb_metric].std()

    st.markdown(f"""
    <div style="display:flex; flex-wrap:wrap; gap:10px; margin-top:6px;">
        <div class="stat-mini"><div class="stat-mini-val">{q1:.2f}</div><div class="stat-mini-label">Q1 (25%)</div></div>
        <div class="stat-mini"><div class="stat-mini-val">{med:.2f}</div><div class="stat-mini-label">Median</div></div>
        <div class="stat-mini"><div class="stat-mini-val">{q3:.2f}</div><div class="stat-mini-label">Q3 (75%)</div></div>
        <div class="stat-mini"><div class="stat-mini-val">{iqr:.2f}</div><div class="stat-mini-label">IQR</div></div>
        <div class="stat-mini"><div class="stat-mini-val">{mn:.2f}</div><div class="stat-mini-label">Mean</div></div>
        <div class="stat-mini"><div class="stat-mini-val">{sd:.2f}</div><div class="stat-mini-label">Std Dev</div></div>
    </div>
    """, unsafe_allow_html=True)


# --------------------------------------------------
# CLIMATE FINGERPRINT (Radar + Percentile)
# --------------------------------------------------
def climate_fingerprint(df, country):
    section_header("🫆", "Climate Fingerprint")
    cdf = df[df['country'] == country]
    metrics = [c for c in ['temperature_celsius','humidity','wind_kph','pressure_mb','uv_index','visibility_km']
               if c in cdf.columns]
    if not metrics:
        st.info("Not enough metrics for fingerprint.")
        return

    global_means = {m: df[m].mean() for m in metrics}
    global_stds  = {m: df[m].std() for m in metrics}
    country_vals = {m: cdf[m].mean() for m in metrics}
    percentiles  = {m: int((df[m] < country_vals[m]).mean() * 100) for m in metrics}

    fig_r = go.Figure()
    fig_r.add_trace(go.Scatterpolar(
        r=list(percentiles.values()) + [list(percentiles.values())[0]],
        theta=metrics + [metrics[0]],
        fill='toself', name=country,
        line_color='#00d4ff', fillcolor='rgba(0,212,255,0.15)',
    ))
    fig_r.add_trace(go.Scatterpolar(
        r=[50]*len(metrics) + [50],
        theta=metrics + [metrics[0]],
        fill='toself', name='Global Avg (50th pct)',
        line_color='rgba(255,255,255,0.2)', fillcolor='rgba(255,255,255,0.04)',
        line_dash='dash'
    ))
    fig_r.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(range=[0,100], gridcolor='rgba(255,255,255,0.08)', color='#8892a4'),
            angularaxis=dict(color='#8892a4')
        ),
        title=f"Climate Fingerprint — {country} (Percentile vs Global)",
        **dark_theme()
    )
    st.plotly_chart(fig_r, use_container_width=True)

    insight_card("🫆 FINGERPRINT", f"{country} — Percentile Profile",
        " | ".join([f"<b>{m.replace('_celsius','').replace('_kph','').replace('_mb','').replace('_km','').replace('_','  ')}</b>: {percentiles[m]}th pct" for m in metrics]))


# --------------------------------------------------
# HEATWAVE CALENDAR HEATMAP
# --------------------------------------------------
def heatwave_calendar(df, country):
    section_header("🔥", "Heatwave Calendar")
    cdf = df[df['country'] == country].copy()
    if 'date' not in cdf.columns or 'temperature_celsius' not in cdf.columns:
        st.info("Date/temperature data not available.")
        return

    cdf = cdf.dropna(subset=['date','temperature_celsius'])
    cdf['date'] = pd.to_datetime(cdf['date'])
    cdf['dayofyear'] = cdf['date'].dt.dayofyear
    cdf['week']      = cdf['date'].dt.isocalendar().week.astype(int)
    cdf['dayofweek'] = cdf['date'].dt.dayofweek

    pivot = cdf.pivot_table(index='dayofweek', columns='week', values='temperature_celsius', aggfunc='mean')
    fig_cal = px.imshow(
        pivot, color_continuous_scale='RdYlBu_r',
        title=f"🗓️ Weekly Temperature Calendar — {country}",
        labels=dict(x="Week of Year", y="Day of Week", color="Temp °C"),
        aspect="auto"
    )
    apply_dark(fig_cal)
    fig_cal.update_layout(height=300)
    st.plotly_chart(fig_cal, use_container_width=True)


# --------------------------------------------------
# PERCENTILE BAND CHART
# --------------------------------------------------
def percentile_band_chart(df, country, metric):
    section_header("📉", "Percentile Band Chart")
    cdf = df[df['country'] == country].copy().sort_values('date')
    if metric not in cdf.columns or len(cdf) < 5:
        return

    cdf = cdf.dropna(subset=[metric, 'date'])
    cdf['p10'] = cdf[metric].expanding().quantile(0.10)
    cdf['p25'] = cdf[metric].expanding().quantile(0.25)
    cdf['p75'] = cdf[metric].expanding().quantile(0.75)
    cdf['p90'] = cdf[metric].expanding().quantile(0.90)
    cdf['med'] = cdf[metric].expanding().median()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cdf['date'], y=cdf['p90'], line_color='rgba(255,107,107,0.0)', name='P90', showlegend=False))
    fig.add_trace(go.Scatter(x=cdf['date'], y=cdf['p10'], fill='tonexty', fillcolor='rgba(0,212,255,0.06)', line_color='rgba(0,212,255,0.0)', name='P10–P90 band'))
    fig.add_trace(go.Scatter(x=cdf['date'], y=cdf['p75'], line_color='rgba(123,47,255,0.0)', name='P75', showlegend=False))
    fig.add_trace(go.Scatter(x=cdf['date'], y=cdf['p25'], fill='tonexty', fillcolor='rgba(123,47,255,0.15)', line_color='rgba(123,47,255,0.0)', name='P25–P75 band'))
    fig.add_trace(go.Scatter(x=cdf['date'], y=cdf['med'], line=dict(color='#00d4ff', width=2), name='Median'))
    fig.add_trace(go.Scatter(x=cdf['date'], y=cdf[metric], line=dict(color='rgba(255,255,255,0.2)', width=1), name='Raw'))

    fig.update_layout(title=f"Percentile Bands — {metric} ({country})", **dark_theme())
    st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------
# SCATTER MATRIX
# --------------------------------------------------
def scatter_matrix_view(df, country):
    section_header("🔷", "Multi-Variable Scatter Matrix")
    cdf = df[df['country'] == country].copy()
    available = [c for c in ['temperature_celsius','humidity','wind_kph','pressure_mb','uv_index','visibility_km','precip_mm']
                 if c in cdf.columns]
    selected = st.multiselect("Select Variables for Scatter Matrix", available,
                              default=available[:min(4, len(available))], key="smatrix_vars")
    if len(selected) < 2:
        st.info("Select at least 2 variables.")
        return

    color_col = "season" if "season" in cdf.columns else None
    fig = px.scatter_matrix(cdf.sample(min(500, len(cdf))), dimensions=selected,
                            color=color_col, opacity=0.6,
                            color_discrete_sequence=['#00d4ff','#7b2fff','#ff6b6b','#ffd93d'],
                            title=f"Scatter Matrix — {country}")
    apply_dark(fig)
    fig.update_traces(diagonal_visible=True, showupperhalf=False)
    st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------
# CLIMATE ANOMALY DETECTOR
# --------------------------------------------------
def anomaly_detector(df, country, metric):
    section_header("🚨", "Climate Anomaly Detector (Z-Score Method)")
    cdf = df[df['country'] == country].copy().sort_values('date')
    if metric not in cdf.columns or len(cdf) < 5:
        return

    cdf = cdf.dropna(subset=[metric, 'date'])
    mean_val = cdf[metric].mean()
    std_val  = cdf[metric].std()
    cdf['zscore'] = (cdf[metric] - mean_val) / (std_val + 1e-9)
    cdf['anomaly'] = cdf['zscore'].abs() > 2

    threshold = st.slider("Z-Score Threshold", 1.0, 4.0, 2.0, 0.1, key="anomaly_thresh")
    cdf['anomaly'] = cdf['zscore'].abs() > threshold

    fig = go.Figure()
    normal = cdf[~cdf['anomaly']]
    anoms  = cdf[cdf['anomaly']]
    fig.add_trace(go.Scatter(x=normal['date'], y=normal[metric], mode='markers',
                             marker=dict(color='rgba(0,212,255,0.4)', size=4), name='Normal'))
    fig.add_trace(go.Scatter(x=anoms['date'], y=anoms[metric], mode='markers',
                             marker=dict(color='#ff6b6b', size=9, symbol='star',
                                         line=dict(color='#fff', width=1)), name='⚡ Anomaly'))
    fig.add_hline(y=mean_val, line_dash="dash", line_color="rgba(255,255,255,0.3)",
                  annotation_text=f"Mean: {mean_val:.1f}")
    fig.add_hline(y=mean_val + threshold*std_val, line_dash="dot", line_color="rgba(255,107,107,0.5)")
    fig.add_hline(y=mean_val - threshold*std_val, line_dash="dot", line_color="rgba(255,107,107,0.5)")
    fig.update_layout(title=f"Anomaly Detection — {metric} ({country})", **dark_theme())
    st.plotly_chart(fig, use_container_width=True)

    n_anom = cdf['anomaly'].sum()
    pct = n_anom / len(cdf) * 100
    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("ANOMALIES", f"{n_anom}", f"{pct:.1f}% of records", "⚡", "#ff6b6b")
    with c2: kpi_card("Z-THRESHOLD", f"±{threshold:.1f}σ", "Standard deviations", "📐", "#ffd93d")
    with c3: kpi_card("DATA QUALITY", f"{100-pct:.1f}%", "Within normal range", "✅", "#06d6a0")


# --------------------------------------------------
# AUTHENTICATION PAGE
# --------------------------------------------------
def auth_page():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown(LOGIN_BG_CSS, unsafe_allow_html=True)

    login_weather_images = [
        "https://images.unsplash.com/photo-1504608524841-42fe6f032b4b?w=1600&q=80",
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1600&q=80",
        "https://images.unsplash.com/photo-1501630834273-4b5604d2ee31?w=1600&q=80",
        "https://images.unsplash.com/photo-1516912481808-3406841bd33c?w=1600&q=80",
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1600&q=80",
        "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1600&q=80",
        "https://images.unsplash.com/photo-1470770903676-69b98201ea1c?w=1600&q=80",
        "https://images.unsplash.com/photo-1482192596544-9eb780fc7f66?w=1600&q=80",
        "https://images.unsplash.com/photo-1428592953211-077101b2021b?w=1600&q=80",
        "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1600&q=80",
    ]

    st_autorefresh(interval=5000, key="login_bg_refresh")
    st.session_state.login_bg_idx = (st.session_state.login_bg_idx + 1) % len(login_weather_images)
    current_bg = login_weather_images[st.session_state.login_bg_idx]

    rain_drops = "".join([
        f'<div class="raindrop" style="left:{np.random.randint(0,100)}vw; '
        f'height:{np.random.randint(15,60)}px; '
        f'animation-duration:{np.random.uniform(0.8,2.0):.2f}s; '
        f'animation-delay:{np.random.uniform(0,3):.2f}s; opacity:{np.random.uniform(0.2,0.7):.2f};"></div>'
        for _ in range(30)
    ])

    particles = "".join([
        f'<div class="weather-particle" style="left:{p[0]}vw; bottom:{p[1]}vh; '
        f'animation-duration:{p[2]:.1f}s; animation-delay:{p[3]:.1f}s;">{p[4]}</div>'
        for p in [
            (5, 10, 8, 0, "🌧️"), (15, 5, 10, 2, "❄️"), (25, 15, 7, 1, "🌪️"),
            (35, 8, 9, 3, "⛈️"), (45, 12, 11, 0.5, "🌩️"), (55, 6, 8, 2.5, "🌨️"),
            (65, 18, 12, 1.5, "🌤️"), (75, 9, 7, 0.8, "🌊"), (85, 14, 10, 3.5, "☁️"),
            (92, 7, 9, 1.2, "🌬️"),
        ]
    ])

    st.markdown(f"""
    <img id="weather-bg-img" src="{current_bg}" alt="weather background">
    <div class="login-vignette"></div>
    <div class="rain-container">{rain_drops}</div>
    {particles}
    <script>
    // Force password masking — runs after Streamlit renders inputs
    function enforcePasswordMasking() {{
        const inputs = window.parent.document.querySelectorAll('input');
        inputs.forEach(inp => {{
            const label = inp.closest('[data-testid="stTextInput"]');
            if (label) {{
                const labelText = label.querySelector('label');
                if (labelText && (
                    labelText.textContent.toLowerCase().includes('password') ||
                    labelText.textContent.toLowerCase().includes('confirm')
                )) {{
                    inp.setAttribute('type', 'password');
                    inp.style.letterSpacing = '6px';
                    inp.style.fontSize = '18px';
                }}
            }}
        }});
    }}
    // Run immediately and after short delays for Streamlit's async render
    enforcePasswordMasking();
    setTimeout(enforcePasswordMasking, 300);
    setTimeout(enforcePasswordMasking, 800);
    setTimeout(enforcePasswordMasking, 1500);
    </script>
    """, unsafe_allow_html=True)

    st_autorefresh(interval=1000, key="auth_time")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    col_l, col_m, col_r = st.columns([1, 1.3, 1])
    with col_m:
        st.markdown(f'<div style="text-align:right; margin-bottom:12px;"><span class="live-time">⏱ {now}</span></div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="login-glass-card">
            <div style="text-align:center; margin-bottom:28px;">
                <div style="font-size:58px; margin-bottom:8px; filter: drop-shadow(0 0 16px rgba(0,212,255,0.5));">🌍</div>
                <div style="font-family:'Syne',sans-serif; font-size:34px; font-weight:800;
                            background:linear-gradient(90deg,#00d4ff,#7b2fff,#ff6b6b);
                            -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                    ClimateScope
                </div>
                <div style="color:#8892a4; font-size:12px; margin-top:5px; letter-spacing:3px; text-transform:uppercase;">
                    Global Weather Intelligence
                </div>
                <div style="margin-top:12px; display:flex; flex-wrap:wrap; gap:5px; justify-content:center;">
                    <span class="feature-badge">🎻 Violin Charts</span>
                    <span class="feature-badge">📦 Box Plots</span>
                    <span class="feature-badge">🗺️ 3D Globe</span>
                    <span class="feature-badge">⚡ Anomaly AI</span>
                    <span class="feature-badge">🫆 Fingerprint</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
        with tab1:
            username = st.text_input("Username", placeholder="Enter username", key="login_user")
            password = st.text_input("Password", type="password", placeholder="Enter password", key="login_pass")
            if st.button("Login →", use_container_width=True):
                if username in st.session_state.users and \
                   st.session_state.users[username]["password"] == password:
                    st.success("✅ Login Successful")
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

        with tab2:
            reg_user  = st.text_input("Username", key="reg_user")
            reg_email = st.text_input("Email", key="reg_email")
            reg_pass  = st.text_input("Password", type="password", key="reg_pass")
            reg_conf  = st.text_input("Confirm Password", type="password", key="reg_conf")
            if st.button("Register →", use_container_width=True):
                if not reg_user or not reg_email or not reg_pass:
                    st.error("❌ All fields required")
                elif reg_user in st.session_state.users:
                    st.error("❌ Username already exists")
                elif not re.match(r"[^@]+@[^@]+\.[^@]+", reg_email):
                    st.error("❌ Invalid email format")
                elif reg_pass != reg_conf:
                    st.error("❌ Passwords do not match")
                else:
                    st.session_state.users[reg_user] = {"email": reg_email, "password": reg_pass}
                    st.success("✅ Registration successful. Please login.")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <div class="login-stats-strip">
            <div class="login-stat-pill">🌍 Countries: <span>195+</span></div>
            <div class="login-stat-pill">📊 Metrics: <span>20+</span></div>
            <div class="login-stat-pill">🎻 Charts: <span>15+</span></div>
            <div class="login-stat-pill">⚡ Live Data: <span>ON</span></div>
        </div>
        """, unsafe_allow_html=True)

        bg_labels = ["⛈️ Storm Front", "⚡ Lightning", "🌧️ Rainfall", "🏔️ Snow Peaks",
                     "🌅 Sunset Sea", "🌫️ Misty Forest", "🌊 Foggy Lake", "🌈 Rainbow",
                     "🌇 Golden Sky", "☁️ Mountain Clouds"]
        st.markdown(f"""
        <div style="text-align:center; margin-top:14px;">
            <span style="font-size:11px; color:#8892a4;">
                📸 Background: {bg_labels[st.session_state.login_bg_idx % len(bg_labels)]} — auto-cycles every 5s
            </span>
        </div>
        """, unsafe_allow_html=True)


# --------------------------------------------------
# STANDARD DASHBOARD
# --------------------------------------------------
def dashboard_basic():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    enable_timer = st.sidebar.checkbox("⚡ Auto Refresh Images")
    timer_options = {"15 sec":15000, "30 sec":30000, "1 min":60000}
    selected_timer = st.sidebar.selectbox("Refresh Interval", list(timer_options.keys()), disabled=not enable_timer)

    weather_images = [
        "https://images.unsplash.com/photo-1504608524841-42fe6f032b4b?w=1400",
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1400",
        "https://images.unsplash.com/photo-1501630834273-4b5604d2ee31?w=1400",
        "https://images.unsplash.com/photo-1500674425229-f692875b0ab7?w=1400",
        "https://images.unsplash.com/photo-1516912481808-3406841bd33c?w=1400",
        "https://images.unsplash.com/photo-1428592953211-077101b2021b?w=1400",
        "https://images.unsplash.com/photo-1470115636492-6d2b56f9146d?w=1400",
        "https://images.unsplash.com/photo-1520108871036-7c9eb13eb532?w=1400",
        "https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=1400",
        "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=1400",
        "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1400",
        "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1400",
        "https://images.unsplash.com/photo-1497436072909-60f360e1d4b1?w=1400",
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1400",
        "https://images.unsplash.com/photo-1500534623283-312aade485b7?w=1400",
    ]

    if st.button("🔄 Refresh Weather Image"):
        st.session_state.image_counter += 1

    if enable_timer:
        st_autorefresh(interval=timer_options[selected_timer], key="auto_image_refresh")
        st.session_state.image_counter += 1

    idx = st.session_state.image_counter % len(weather_images)
    st_autorefresh(interval=1000, key="live_clock")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    st.markdown(f"""
    <div class="hero-banner">
        <div style="display:flex; justify-content:space-between;">
            <span class="live-time">⏱ {now}</span>
            <span class="live-time">👤 {st.session_state.username}</span>
        </div>
        <div class="hero-title">ClimateScope</div>
        <div class="hero-sub">Global Weather Intelligence • Real-time Analytics • AI Insights</div>
    </div>
    """, unsafe_allow_html=True)

    st.image(weather_images[idx], use_container_width=True, caption=f"🌤️ Weather Scene #{idx+1}")
    st.divider()

    df = load_data()

    st.sidebar.markdown("## 🎛️ Controls")
    countries = sorted(df["country"].dropna().unique())
    selected_country = st.sidebar.selectbox("🌍 Select Country", countries)
    unit = st.sidebar.radio("🌡️ Temperature Unit", ["Celsius", "Fahrenheit"])
    temp_col = "temperature_celsius" if unit == "Celsius" else "temperature_fahrenheit"

    country_df = df[df["country"] == selected_country].copy()

    weather_ticker(df, selected_country)

    section_header("📊", "Key Performance Indicators")

    avg_temp      = country_df[temp_col].mean()
    max_temp      = country_df[temp_col].max()
    min_temp      = country_df[temp_col].min()
    avg_wind      = country_df["wind_kph"].mean()
    max_wind      = country_df["wind_kph"].max()
    avg_humidity  = country_df["humidity"].mean() if "humidity" in country_df.columns else 0
    avg_pressure  = country_df["pressure_mb"].mean() if "pressure_mb" in country_df.columns else 0
    total_precip  = country_df["precip_mm"].sum() if "precip_mm" in country_df.columns else 0
    common_cond   = country_df["condition_text"].mode()[0] if "condition_text" in country_df.columns else "N/A"
    visibility    = country_df["visibility_km"].mean() if "visibility_km" in country_df.columns else 0
    uv_index      = country_df["uv_index"].mean() if "uv_index" in country_df.columns else 0
    dew_point     = country_df["dewpoint_c"].mean() if "dewpoint_c" in country_df.columns else 0
    cloud_cover   = country_df["cloud"].mean() if "cloud" in country_df.columns else 0
    feels_like    = country_df["feelslike_c"].mean() if "feelslike_c" in country_df.columns else 0
    gust_kph      = country_df["gust_kph"].mean() if "gust_kph" in country_df.columns else 0
    data_points   = len(country_df)

    col1, col2, col3, col4 = st.columns(4)
    with col1: kpi_card("AVG TEMPERATURE", f"{avg_temp:.1f}°", f"Max {max_temp:.1f}° | Min {min_temp:.1f}°", "🌡️", "#00d4ff")
    with col2: kpi_card("AVG WIND SPEED", f"{avg_wind:.1f}", f"km/h  |  Max: {max_wind:.0f} km/h", "💨", "#7b2fff")
    with col3: kpi_card("HUMIDITY", f"{avg_humidity:.0f}%", "Relative humidity average", "💧", "#06d6a0")
    with col4: kpi_card("PRESSURE", f"{avg_pressure:.0f}", "millibars (mb)", "🔵", "#ffd93d")

    col5, col6, col7, col8 = st.columns(4)
    with col5: kpi_card("TOTAL PRECIP", f"{total_precip:.1f}", "mm cumulative rainfall", "🌧️", "#ff6b6b")
    with col6: kpi_card("UV INDEX", f"{uv_index:.1f}", "Avg UV radiation level", "☀️", "#ffd93d")
    with col7: kpi_card("VISIBILITY", f"{visibility:.1f}", "km average visibility", "👁️", "#00d4ff")
    with col8: kpi_card("DATA POINTS", f"{data_points:,}", f"Records for {selected_country}", "📦", "#7b2fff")

    col9, col10, col11, col12 = st.columns(4)
    with col9:  kpi_card("FEELS LIKE", f"{feels_like:.1f}°", "Apparent temperature avg", "🤔", "#06d6a0")
    with col10: kpi_card("DEW POINT", f"{dew_point:.1f}°", "Avg dew point Celsius", "🌫️", "#ff6b6b")
    with col11: kpi_card("CLOUD COVER", f"{cloud_cover:.0f}%", "Average cloud coverage", "☁️", "#8892a4")
    with col12: kpi_card("WIND GUSTS", f"{gust_kph:.1f}", "km/h average gusts", "🌪️", "#ffd93d")

    section_header("⚠️", "Climate Risk Index")
    risk_score = 0
    if max_temp > 35: risk_score += 35
    elif max_temp > 30: risk_score += 20
    if avg_wind > 30: risk_score += 25
    elif avg_wind > 20: risk_score += 12
    if avg_humidity > 80: risk_score += 10
    extreme_cond = country_df["condition_text"].str.contains(
        "storm|thunder|snow|blizzard|hurricane|tornado|hail", case=False, na=False
    ).sum()
    risk_score += min(extreme_cond / max(len(country_df), 1) * 30, 30)
    risk_score = min(int(risk_score), 100)

    color_risk = "#ff6b6b" if risk_score >= 70 else "#ffd93d" if risk_score >= 40 else "#06d6a0"
    label_risk = "🔴 HIGH RISK" if risk_score >= 70 else "🟡 MODERATE RISK" if risk_score >= 40 else "🟢 LOW RISK"
    st.markdown(f"""
    <div class="kpi-card" style="padding: 24px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <div style="font-family:'Syne',sans-serif; font-size:18px; font-weight:700; color:{color_risk};">{label_risk}</div>
            <div style="font-family:'Syne',sans-serif; font-size:36px; font-weight:800; color:{color_risk};">{risk_score}/100</div>
        </div>
        <div class="risk-bar-wrap">
            <div class="risk-bar-fill" style="width:{risk_score}%; background:linear-gradient(90deg,#7b2fff,{color_risk});"></div>
        </div>
        <div style="color:#8892a4; font-size:12px; margin-top:8px;">Based on temperature extremes, wind speed, humidity & extreme weather events</div>
    </div>
    """, unsafe_allow_html=True)

    violin_box_panel(df, selected_country)
    climate_fingerprint(df, selected_country)
    heatwave_calendar(df, selected_country)

    section_header("🧠", "AI Weather Intelligence")
    temp_trend   = "warming" if country_df[temp_col].iloc[-1] > country_df[temp_col].iloc[0] else "cooling"
    precip_level = "high" if total_precip > 200 else "moderate" if total_precip > 80 else "low"
    wind_level   = "severe" if avg_wind > 40 else "strong" if avg_wind > 25 else "moderate" if avg_wind > 15 else "calm"

    insight_card("🌡️ TEMPERATURE", f"Thermal Profile of {selected_country}",
        f"{selected_country} records an average temperature of <b>{avg_temp:.1f}°{unit[0]}</b>, "
        f"with extremes ranging from <b>{min_temp:.1f}°</b> to <b>{max_temp:.1f}°</b>. "
        f"The apparent 'feels-like' temperature averages <b>{feels_like:.1f}°</b>. "
        f"{'⚠️ Potential heatwave conditions detected.' if max_temp > 35 else 'Temperature patterns appear within normal ranges.'}")
    insight_card("💨 WIND & ATMOSPHERE", "Atmospheric Dynamics",
        f"Wind speeds average <b>{avg_wind:.1f} km/h</b> with recorded gusts up to <b>{max_wind:.0f} km/h</b>. "
        f"Atmospheric pressure holds at <b>{avg_pressure:.0f} mb</b>. "
        f"{'⛈️ High wind activity suggests unstable atmospheric systems.' if avg_wind > 30 else 'Wind conditions are generally stable.'}")
    insight_card("🌧️ PRECIPITATION & HUMIDITY", "Moisture & Rainfall Analysis",
        f"Humidity averages <b>{avg_humidity:.0f}%</b> with a dew point of <b>{dew_point:.1f}°C</b>. "
        f"Total recorded precipitation is <b>{total_precip:.1f}mm</b> ({precip_level} precipitation level). "
        f"{'🌊 High humidity combined with precipitation signals potential flood risk.' if avg_humidity > 75 and total_precip > 100 else 'Moisture levels are manageable.'}")
    insight_card("☀️ UV & VISIBILITY", "Solar Radiation & Visibility Report",
        f"The average UV Index is <b>{uv_index:.1f}</b> "
        f"({'extreme' if uv_index > 10 else 'very high' if uv_index > 7 else 'high' if uv_index > 5 else 'moderate' if uv_index > 2 else 'low'} risk). "
        f"Average visibility is <b>{visibility:.1f}km</b>. "
        f"{'🕶️ High UV levels — sun protection strongly advised.' if uv_index > 6 else '👍 UV levels within acceptable limits.'}")

    section_header("📈", "Temperature & Trend Analysis")
    if "last_updated" in country_df.columns:
        country_df["last_updated"] = pd.to_datetime(country_df["last_updated"], errors="coerce")
        country_df["Month"] = country_df["last_updated"].dt.month_name()
        monthly_avg = country_df.groupby("Month")[temp_col].mean().reindex([
            'January','February','March','April','May','June',
            'July','August','September','October','November','December'
        ]).dropna()

        col1, col2 = st.columns(2)
        with col1:
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                x=monthly_avg.index, y=monthly_avg.values,
                marker=dict(color=monthly_avg.values, colorscale='RdYlBu_r', showscale=False),
                hovertemplate='%{x}: %{y:.1f}°<extra></extra>'
            ))
            fig1.update_layout(title="Monthly Avg Temperature", **dark_theme())
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            if "season" in country_df.columns:
                season_df = country_df.groupby("season")[temp_col].mean().reset_index()
                fig2 = px.bar_polar(season_df, r=temp_col, theta="season",
                                    color=temp_col, color_continuous_scale="RdYlBu_r",
                                    title="Seasonal Radar Chart")
                fig2.update_layout(**dark_theme())
                st.plotly_chart(fig2, use_container_width=True)

    anomaly_detector(df, selected_country, temp_col)
    percentile_band_chart(df, selected_country, temp_col)
    scatter_matrix_view(df, selected_country)

    section_header("🧭", "Wind Analysis")
    if "wind_degree" in country_df.columns:
        country_df['wind_dir_bin'] = pd.cut(country_df['wind_degree'],
            bins=[0,45,90,135,180,225,270,315,360],
            labels=['N','NE','E','SE','S','SW','W','NW'])
        wind_rose = country_df.groupby('wind_dir_bin', observed=True)['wind_kph'].mean().reset_index()
        col1, col2 = st.columns(2)
        with col1:
            fig_wind = go.Figure(go.Barpolar(
                r=wind_rose['wind_kph'], theta=wind_rose['wind_dir_bin'].astype(str),
                marker_color=wind_rose['wind_kph'], marker_colorscale='Blues',
            ))
            fig_wind.update_layout(title="Wind Rose (Speed by Direction)", **dark_theme(),
                polar=dict(bgcolor='rgba(0,0,0,0)',
                    radialaxis=dict(gridcolor='rgba(255,255,255,0.08)', color='#8892a4'),
                    angularaxis=dict(gridcolor='rgba(255,255,255,0.08)', color='#8892a4')))
            st.plotly_chart(fig_wind, use_container_width=True)
        with col2:
            fig_ws = px.scatter(country_df.sample(min(500, len(country_df))),
                x="wind_kph", y=temp_col,
                color="season" if "season" in country_df.columns else temp_col,
                size="humidity" if "humidity" in country_df.columns else None,
                title="Wind Speed vs Temperature", opacity=0.7)
            apply_dark(fig_ws)
            st.plotly_chart(fig_ws, use_container_width=True)

    section_header("🏆", "Extreme Days")
    hot_day  = country_df.loc[country_df[temp_col].idxmax()]
    cold_day = country_df.loc[country_df[temp_col].idxmin()]
    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("HOTTEST DAY", f"{hot_day[temp_col]:.1f}°{unit[0]}", str(hot_day.get('last_updated', 'N/A'))[:10], "🔥", "#ff6b6b")
    with c2: kpi_card("COLDEST DAY", f"{cold_day[temp_col]:.1f}°{unit[0]}", str(cold_day.get('last_updated', 'N/A'))[:10], "🧊", "#00d4ff")
    with c3: kpi_card("TEMP RANGE", f"{max_temp - min_temp:.1f}°{unit[0]}", "Max swing recorded", "📐", "#7b2fff")

    section_header("📄", f"Data Preview — {selected_country}")
    st.dataframe(country_df.head(20), use_container_width=True)

    section_header("📥", "Export Data")
    csv = country_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv, file_name=f"{selected_country}_weather.csv", mime="text/csv")

    st.divider()
    choropleth_view(df, focused_country=selected_country)

    st.divider()
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.image_counter = 0
        st.rerun()


# --------------------------------------------------
# PRO DASHBOARD VIEWS
# --------------------------------------------------
def single_country_view(df, metric):
    country = st.sidebar.selectbox("Country", sorted(df["country"].unique()))
    cdf = df[df["country"] == country].copy().sort_values("date")

    now = datetime.now().strftime("%H:%M:%S")
    st.markdown(f"""
    <div class="hero-banner">
        <div style="margin-bottom:6px;"><span class="live-time">⏱ {now}</span></div>
        <div class="hero-title">{country}</div>
        <div class="hero-sub">Deep Climate Analysis • {len(cdf)} data points</div>
    </div>
    """, unsafe_allow_html=True)

    weather_ticker(df, country)

    health = calculate_health_score(cdf, metric)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi_card("DATA HEALTH", f"{health}%", "Anomaly-adjusted", "💚", "#06d6a0")
    with c2: kpi_card("MEAN", f"{cdf[metric].mean():.2f}", metric, "📊", "#00d4ff")
    with c3: kpi_card("SKEWNESS", f"{cdf[metric].skew():.2f}", "Distribution skew", "📐", "#7b2fff")
    with c4: kpi_card("IQR RANGE", f"{(cdf[metric].quantile(0.75)-cdf[metric].quantile(0.25)):.2f}", "Interquartile range", "📏", "#ff6b6b")
    with c5: kpi_card("STD DEV", f"{cdf[metric].std():.2f}", "Standard deviation", "σ", "#ffd93d")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Distributions", "🎻 Violin & Box", "🍂 Seasonal",
        "🚨 Extremes", "📉 Decomposition", "🫆 Fingerprint", "🗺️ Global Map"
    ])

    with tab1:
        section_header("📊", "Distribution Analysis")
        col_a, col_b = st.columns(2)
        fig_h = px.histogram(cdf, x=metric, color="season", marginal="rug", barmode="overlay")
        apply_dark(fig_h)
        col_a.plotly_chart(fig_h, use_container_width=True)
        fig_v = px.violin(cdf, y=metric, x="season", box=True, points="all", color="season")
        apply_dark(fig_v)
        col_b.plotly_chart(fig_v, use_container_width=True)

        section_header("🔗", "Feature Correlation Heatmap")
        num_cols = cdf.select_dtypes(include=np.number).columns.tolist()
        corr = cdf[num_cols].corr()
        fig_corr = px.imshow(corr, text_auto=".1f", color_continuous_scale="RdBu_r",
                             title="Correlation Matrix", aspect="auto")
        apply_dark(fig_corr)
        st.plotly_chart(fig_corr, use_container_width=True)

    with tab2:
        violin_box_panel(df, country)
        st.divider()

        # ── Multi-metric box comparison — FIXED fillcolor ──
        section_header("📦", "Multi-Metric Box Comparison")
        num_metrics = [c for c in cdf.select_dtypes(include=np.number).columns
                       if c not in ['month','lat','lon']]
        sel_metrics = st.multiselect("Pick Metrics to Compare", num_metrics,
                                     default=num_metrics[:min(4, len(num_metrics))], key="box_multi")
        if sel_metrics:
            # Palette of hex colors — converted to proper rgba for fillcolor
            palette = ['#00d4ff', '#7b2fff', '#ff6b6b', '#ffd93d', '#06d6a0', '#f72585']
            fig_mbox = go.Figure()
            for i, m in enumerate(sel_metrics):
                line_col = palette[i % len(palette)]
                fill_col = hex_to_rgba(line_col, alpha=0.27)   # ← THE FIX
                fig_mbox.add_trace(go.Box(
                    y=cdf[m],
                    name=m,
                    boxmean='sd',
                    marker_color=line_col,
                    line_color=line_col,
                    fillcolor=fill_col,          # ← proper rgba string
                ))
            fig_mbox.update_layout(
                title="Multi-Metric Box Comparison (with Mean & SD)",
                **dark_theme()
            )
            st.plotly_chart(fig_mbox, use_container_width=True)

    with tab3:
        section_header("🍂", "Seasonal & Rolling Trends")
        cdf['rolling_avg'] = cdf[metric].rolling(window=7).mean()
        fig_s = px.line(cdf, x="date", y=[metric, 'rolling_avg'],
                        color_discrete_sequence=["rgba(255,255,255,0.3)","#00d4ff"],
                        labels={"value": metric, "variable": "Series"})
        apply_dark(fig_s)
        st.plotly_chart(fig_s, use_container_width=True)

        seasonal_avg = cdf.groupby("season")[metric].agg(['mean','std']).reset_index()
        col1, col2 = st.columns(2)
        fig_bar = px.bar(seasonal_avg, x="season", y="mean", error_y="std",
                         color="season", title="Seasonal Mean ± Std Dev")
        apply_dark(fig_bar)
        col1.plotly_chart(fig_bar, use_container_width=True)

        if 'month' in cdf.columns:
            monthly = cdf.groupby('month')[metric].mean().reset_index()
            fig_m = go.Figure(go.Scatter(
                x=monthly['month'], y=monthly[metric],
                fill='tozeroy', line_color='#7b2fff',
                fillcolor='rgba(123,47,255,0.15)'
            ))
            fig_m.update_layout(title="Monthly Profile", **dark_theme())
            col2.plotly_chart(fig_m, use_container_width=True)

    with tab4:
        section_header("🚨", "Extreme Weather Detection")
        q1, q3 = cdf[metric].quantile(0.25), cdf[metric].quantile(0.75)
        iqr = q3 - q1
        cdf['is_extreme'] = (cdf[metric] < (q1 - 1.5 * iqr)) | (cdf[metric] > (q3 + 1.5 * iqr))
        fig_ext = px.scatter(cdf, x="date", y=metric, color="is_extreme",
                             color_discrete_map={True: "#ff6b6b", False: "#00d4ff"},
                             title="Extreme Event Markers")
        apply_dark(fig_ext)
        st.plotly_chart(fig_ext, use_container_width=True)

        extreme_pct = cdf['is_extreme'].mean() * 100
        kpi_card("EXTREME EVENTS", f"{cdf['is_extreme'].sum()}", f"{extreme_pct:.1f}% of all records", "⚡", "#ff6b6b")
        if cdf['is_extreme'].any():
            st.dataframe(cdf[cdf['is_extreme']][['date', metric] + (
                ['condition_text'] if 'condition_text' in cdf.columns else []
            )].head(20), use_container_width=True)

        st.divider()
        anomaly_detector(df, country, metric)

    with tab5:
        section_header("📉", "Trend Decomposition")
        cdf['trend']    = cdf[metric].rolling(window=15, center=True).mean()
        cdf['residual'] = cdf[metric] - cdf['trend']

        fig_sub = make_subplots(rows=3, cols=1, shared_xaxes=True,
                                subplot_titles=["Original", "Trend (15-Day MA)", "Residual Noise"])
        fig_sub.add_trace(go.Scatter(x=cdf['date'], y=cdf[metric],
                                     line=dict(color='rgba(255,255,255,0.3)', width=1)), row=1, col=1)
        fig_sub.add_trace(go.Scatter(x=cdf['date'], y=cdf['trend'],
                                     line=dict(color='#00d4ff', width=2)), row=2, col=1)
        fig_sub.add_trace(go.Bar(x=cdf['date'], y=cdf['residual'],
                                 marker_color='#ff6b6b', opacity=0.5), row=3, col=1)
        fig_sub.update_layout(height=500, showlegend=False, **dark_theme())
        st.plotly_chart(fig_sub, use_container_width=True)

        st.divider()
        percentile_band_chart(df, country, metric)

    with tab6:
        climate_fingerprint(df, country)
        st.divider()
        heatwave_calendar(df, country)
        st.divider()
        scatter_matrix_view(df, country)

    with tab7:
        choropleth_view(df, focused_country=country)


def regional_comparison_view(df, metric):
    st.markdown('<div class="hero-banner"><div class="hero-title">Regional Comparison</div><div class="hero-sub">Side-by-side multi-country analysis</div></div>', unsafe_allow_html=True)
    countries = st.multiselect("Select Countries", df["country"].unique(), default=df["country"].unique()[:3])

    if not countries:
        st.info("Select at least one country.")
        return

    comp_df = df[df["country"].isin(countries)]
    c1, c2 = st.columns(2)
    with c1:
        fig_box = px.box(comp_df, x="country", y=metric, color="country", title="Statistical Range (Box Plot)")
        apply_dark(fig_box)
        st.plotly_chart(fig_box, use_container_width=True)
    with c2:
        fig_vio = px.violin(comp_df, x="country", y=metric, color="country", box=True,
                            title="Distribution Density (Violin Plot)")
        apply_dark(fig_vio)
        st.plotly_chart(fig_vio, use_container_width=True)

    fig_line = px.line(comp_df, x="date", y=metric, color="country", title="Time-Series Overlay")
    apply_dark(fig_line)
    st.plotly_chart(fig_line, use_container_width=True)

    section_header("🕸️", "Multi-Metric Radar Comparison")
    radar_metrics = [c for c in ['temperature_celsius','humidity','wind_kph','pressure_mb','uv_index']
                     if c in df.columns]
    if radar_metrics:
        fig_radar = go.Figure()
        for country in countries:
            cdf = df[df['country'] == country]
            vals = [cdf[m].mean() for m in radar_metrics]
            global_max = [df[m].max() for m in radar_metrics]
            vals_norm = [v / max(g, 0.001) * 100 for v, g in zip(vals, global_max)]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals_norm + [vals_norm[0]],
                theta=radar_metrics + [radar_metrics[0]],
                fill='toself', name=country, opacity=0.6
            ))
        fig_radar.update_layout(polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(gridcolor='rgba(255,255,255,0.08)', color='#8892a4'),
            angularaxis=dict(color='#8892a4')
        ), **dark_theme())
        st.plotly_chart(fig_radar, use_container_width=True)

    if "precip_mm" in df.columns:
        precip = comp_df.groupby("country")["precip_mm"].sum().reset_index()
        fig_pie = px.pie(precip, values="precip_mm", names="country",
                         title="Rainfall Share", hole=0.4,
                         color_discrete_sequence=['#00d4ff','#7b2fff','#ff6b6b','#ffd93d','#06d6a0'])
        apply_dark(fig_pie)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()
    choropleth_view(df, focused_country=countries[0] if countries else None)


def similarity_view(df, metric):
    st.markdown('<div class="hero-banner"><div class="hero-title">Climate Similarity Index</div><div class="hero-sub">AI-powered climate matching between regions</div></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    city_a = c1.selectbox("Location A", df["country"].unique(), index=0)
    city_b = c2.selectbox("Location B", df["country"].unique(), index=1)

    score = city_similarity(df, city_a, city_b, metric)
    color = "#06d6a0" if score > 70 else "#ffd93d" if score > 40 else "#ff6b6b"
    label = "Very Similar" if score > 70 else "Moderately Similar" if score > 40 else "Very Different"

    st.markdown(f"""
    <div class="kpi-card" style="text-align:center; padding:40px;">
        <div class="kpi-label">SIMILARITY SCORE</div>
        <div style="font-family:'Syne',sans-serif; font-size:80px; font-weight:800;
                    color:{color}; text-shadow:0 0 40px {color}88;">
            {score:.0f}%
        </div>
        <div style="font-size:18px; color:{color}; margin-top:4px;">{label}</div>
        <div style="color:#8892a4; font-size:13px; margin-top:8px;">Based on {metric}</div>
    </div>
    """, unsafe_allow_html=True)

    comp = df[df["country"].isin([city_a, city_b])]
    if "season" in comp.columns:
        pivot = comp.pivot_table(index="season", columns="country", values=metric, aggfunc="mean")
        fig_h = px.imshow(pivot, text_auto=".1f", color_continuous_scale="RdYlBu_r",
                          title="Seasonal Mean Heatmap")
        apply_dark(fig_h)
        st.plotly_chart(fig_h, use_container_width=True)

    col1, col2 = st.columns(2)
    for idx, city in enumerate([city_a, city_b]):
        cdf = df[df['country'] == city]
        c_hist, c_vio = [col1, col2][idx].columns(2)
        with c_hist:
            fig = px.histogram(cdf, x=metric, title=f"{city} — Histogram",
                               color_discrete_sequence=['#00d4ff' if idx == 0 else '#7b2fff'])
            apply_dark(fig)
            st.plotly_chart(fig, use_container_width=True)
        with c_vio:
            fig2 = px.violin(cdf, y=metric, box=True, title=f"{city} — Violin",
                             color_discrete_sequence=['#06d6a0' if idx == 0 else '#ff6b6b'])
            apply_dark(fig2)
            st.plotly_chart(fig2, use_container_width=True)

    a_mean = df[df['country'] == city_a][metric].mean()
    b_mean = df[df['country'] == city_b][metric].mean()
    insight_card("🤖 AI COMPARISON", f"{city_a} vs {city_b}",
        f"<b>{city_a}</b> averages <b>{a_mean:.2f}</b> for {metric} while <b>{city_b}</b> averages <b>{b_mean:.2f}</b>. "
        f"The {score:.0f}% similarity score indicates these climates are <b>{label.lower()}</b>. "
        f"{'Consider similar agriculture, clothing, and infrastructure strategies.' if score > 70 else 'Climate adaptation strategies should differ significantly between these regions.'}")

    st.divider()
    choropleth_view(df, focused_country=city_a)


# --------------------------------------------------
# PRO DASHBOARD
# --------------------------------------------------
def dashboard_pro():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    df = load_data()
    st_autorefresh(interval=15000, key="auto_refresh")

    st.sidebar.markdown("## 🌐 ClimateScope Pro")
    mode = st.sidebar.radio("Analysis Mode", [
        "Single Country", "Regional Comparison", "Similarity Index", "🗺️ Global Map"
    ])
    metric = st.sidebar.selectbox("Select Metric", [c for c in df.select_dtypes(include=np.number).columns
                                                     if c not in ['month']])

    sidebar_imgs = [
        "https://images.unsplash.com/photo-1592210454359-9043f067919b?w=400",
        "https://images.unsplash.com/photo-1493246507139-91e8bef99c02?w=400",
    ]
    if "pro_img" not in st.session_state: st.session_state.pro_img = 0
    st.session_state.pro_img = (st.session_state.pro_img + 1) % len(sidebar_imgs)
    st.sidebar.image(sidebar_imgs[st.session_state.pro_img], use_container_width=True)

    if mode == "Single Country":
        single_country_view(df, metric)
    elif mode == "Regional Comparison":
        regional_comparison_view(df, metric)
    elif mode == "Similarity Index":
        similarity_view(df, metric)
    else:
        choropleth_view(df)

    st.divider()
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()


# --------------------------------------------------
# ROUTER
# --------------------------------------------------
if st.session_state.logged_in:
    app_mode = st.sidebar.radio("🚀 App Version", ["Standard", "Pro"])
    if app_mode == "Standard":
        dashboard_basic()
    else:
        dashboard_pro()
else:
    auth_page()
