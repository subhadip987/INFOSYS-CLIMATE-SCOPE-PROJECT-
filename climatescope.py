import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import re
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --------------------------------------------------
# PAGE CONFIG & SESSION SETUP
# --------------------------------------------------
st.set_page_config(page_title="ClimateScope", layout="wide", page_icon="🌍")

# session state defaults
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "users" not in st.session_state:
    # nested user info with email and password
    st.session_state.users = {
        "subhadip": {
            "email": "subhadip@gmail.com",
            "password": "subhadip123"
        }
    }

if "image_counter" not in st.session_state:
    st.session_state.image_counter = 0

# --------------------------------------------------
# DATA ENGINE & SEASONAL MAPPING (shared)
# --------------------------------------------------
@st.cache_data
def load_data():
    csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "GlobalWeatherRepository.csv"
    )

    if not os.path.exists(csv_path):
        csv_path = "GlobalWeatherRepository.csv"

    if not os.path.exists(csv_path):
        st.error(" GlobalWeatherRepository.csv not found. Upload it to GitHub repo.")
        st.stop()

    df = pd.read_csv(csv_path)
    # Date & Season Logic
    df["date"] = pd.to_datetime(df.get("last_updated"), errors="coerce")
    df['month'] = df['date'].dt.month

    def get_season(month):
        if month in [3, 4, 5]: return "Summer"
        if month in [6, 7, 8, 9]: return "Monsoon"
        if month in [10, 11]: return "Autumn"
        return "Winter"

    df['season'] = df['month'].apply(get_season)
    return df

# --------------------------------------------------
# ANALYTICAL HELPERS (shared)
# --------------------------------------------------
def calculate_health_score(cdf, metric):
    anomalies = np.abs((cdf[metric] - cdf[metric].mean()) / cdf[metric].std()) > 2
    anomaly_ratio = anomalies.mean()
    skew = abs(cdf[metric].skew())
    score = 100 - (anomaly_ratio * 100) - (skew * 10)
    return max(0, min(100, int(score)))

def city_similarity(df, city1, city2, metric):
    m1 = df[df['country'] == city1][metric].mean()
    m2 = df[df['country'] == city2][metric].mean()
    diff = abs(m1 - m2)
    return max(0, 100 - diff)

# --------------------------------------------------
# AUTHENTICATION PAGE
# --------------------------------------------------
def auth_page():
    # rotating background images for auth page
    auth_bg_images = [
        "https://images.unsplash.com/photo-1504608524841-42fe6f032b4b",  # cloud
        "https://images.unsplash.com/photo-1501630834273-4b5604d2ee31",  # storm
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee",  # rain
        "https://images.unsplash.com/photo-1493246507139-91e8bef99c02"   # sunrise
    ]
    if "auth_bg_idx" not in st.session_state:
        st.session_state.auth_bg_idx = 0
    st.session_state.auth_bg_idx = (st.session_state.auth_bg_idx + 1) % len(auth_bg_images)
    current_auth_bg = auth_bg_images[st.session_state.auth_bg_idx]
    st.markdown(f"""
    <style>
        .stApp {{
            background: url('{current_auth_bg}');
            background-attachment: fixed;
            background-size: cover;
        }}
    </style>
    """, unsafe_allow_html=True)

    # live timestamp
    st_autorefresh(interval=1000, key="auth_time")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"<div style='text-align:right; color:#ffffff; font-weight:bold;'>{now}</div>", unsafe_allow_html=True)

    st.image(
        "https://images.unsplash.com/photo-1504608524841-42fe6f032b4b",
        use_container_width=True
    )

    st.title("🔐 ClimateScope Authentication")
    st.caption("Login or Register to access the ClimateScope Dashboard")

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username in st.session_state.users and \
               st.session_state.users[username]["password"] == password:
                st.success("✅ Login Successful")
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

    with tab2:
        reg_user = st.text_input("Username", key="reg_user")
        reg_email = st.text_input("Email")
        reg_pass = st.text_input("Password", type="password", key="reg_pass")
        reg_conf = st.text_input("Confirm Password", type="password")

        if st.button("Register"):
            if not reg_user or not reg_email or not reg_pass:
                st.error("❌ All fields required")
            elif reg_user in st.session_state.users:
                st.error("❌ Username already exists")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", reg_email):
                st.error("❌ Invalid email format")
            elif reg_pass != reg_conf:
                st.error("❌ Passwords do not match")
            else:
                st.session_state.users[reg_user] = {
                    "email": reg_email,
                    "password": reg_pass
                }
                st.success("✅ Registration successful. Please login.")

# --------------------------------------------------
# BASIC DASHBOARD
# --------------------------------------------------
def dashboard_basic():
    # --- live image control ---
    st.header(" Live Weather Image Control")

    enable_timer = st.checkbox("Enable Auto Image Change")
    timer_options = {"15 seconds": 15000, "30 seconds": 30000, "1 minute": 60000}

    selected_timer = st.selectbox(
        "Select Timer",
        list(timer_options.keys()),
        disabled=not enable_timer
    )

    weather_images = [
        "https://images.unsplash.com/photo-1504608524841-42fe6f032b4b",
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee",
        "https://images.unsplash.com/photo-1501630834273-4b5604d2ee31",
        "https://images.unsplash.com/photo-1500674425229-f692875b0ab7"
    ]

    if enable_timer:
        st_autorefresh(interval=timer_options[selected_timer], key="auto")
        st.session_state.image_counter += 1
    else:
        st.session_state.image_counter = 0

    idx = st.session_state.image_counter % len(weather_images)
    st.image(weather_images[idx], use_container_width=True,
             caption=f"Live Weather Image (Update #{st.session_state.image_counter})")

    st.divider()

    st.title("🌍 ClimateScope Dashboard")
    st.subheader("Visualizing Global Weather Trends")
    st.success(f"Welcome {st.session_state.username} 👋")

    df = load_data()

    st.header("🔘 User Controls")
    countries = sorted(df["country"].dropna().unique())
    selected_country = st.selectbox(" Select Country", countries)
    unit = st.radio(" Temperature Unit", ["Celsius","Fahrenheit"])
    temp_col = "temperature_celsius" if unit == "Celsius" else "temperature_fahrenheit"

    country_df = df[df["country"] == selected_country]
    st.subheader(f"📄 Data Preview – {selected_country}")
    st.dataframe(country_df.head(), use_container_width=True)

    # smart summary
    avg_temp = country_df[temp_col].mean()
    max_temp = country_df[temp_col].max()
    avg_wind = country_df["wind_kph"].mean()
    common_condition = country_df["condition_text"].mode()[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(" Avg Temp", f"{avg_temp:.1f}")
    c2.metric(" Max Temp", f"{max_temp:.1f}")
    c3.metric(" Avg Wind (km/h)", f"{avg_wind:.1f}")
    c4.metric(" Common Weather", common_condition)

    if unit == "Celsius" and max_temp > 35:
        st.error(" Heat Alert: Extremely high temperature detected!")

    # climate risk
    st.header("⚠️ Climate Risk Index")
    risk_score = 0
    if max_temp > 35:
        risk_score += 40
    elif max_temp > 30:
        risk_score += 25
    if avg_wind > 30:
        risk_score += 30
    elif avg_wind > 20:
        risk_score += 15
    extreme_conditions = country_df["condition_text"].str.contains(
        "storm|thunder|snow|rain", case=False, na=False
    ).sum()
    risk_score += min(extreme_conditions / len(country_df) * 30, 30)
    risk_score = min(int(risk_score), 100)
    st.progress(risk_score / 100)
    if risk_score >= 70:
        st.error(f" High Climate Risk: {risk_score}/100")
    elif risk_score >= 40:
        st.warning(f" Moderate Climate Risk: {risk_score}/100")
    else:
        st.success(f" Low Climate Risk: {risk_score}/100")

    # AI insight
    st.header("🧠 AI Weather Insight")
    insight = (
        f"{selected_country} shows an average temperature of {avg_temp:.1f}{unit[0]}. "
        f"The maximum recorded temperature is {max_temp:.1f}{unit[0]}, "
        f"with predominant weather conditions being {common_condition.lower()}. "
    )
    if max_temp > 35:
        insight += "This indicates a potential heatwave risk. "
    if avg_wind > 30:
        insight += "Strong wind patterns suggest unstable atmospheric conditions. "
    st.info(insight)

    # monthly analysis
    if "last_updated" in country_df.columns:
        st.header("📅 Monthly Temperature Analysis")
        country_df["last_updated"] = pd.to_datetime(country_df["last_updated"])
        country_df["Month"] = country_df["last_updated"].dt.month_name()
        monthly_avg = country_df.groupby("Month")[temp_col].mean()
        st.bar_chart(monthly_avg)

    # extreme days
    st.header("🏆 Extreme Days")
    country_df["last_updated"] = pd.to_datetime(country_df["last_updated"], errors="coerce")
    hot_day = country_df.loc[country_df[temp_col].idxmax()]
    cold_day = country_df.loc[country_df[temp_col].idxmin()]
    c1, c2 = st.columns(2)
    with c1:
        st.metric(" Hottest Day", f"{hot_day[temp_col]:.1f}{unit[0]}")
        st.caption(f" Date: {hot_day['last_updated'].date()}")
    with c2:
        st.metric(" Coldest Day", f"{cold_day[temp_col]:.1f}{unit[0]}")
        st.caption(f" Date: {cold_day['last_updated'].date()}")

    # download
    st.header("📥 Download Data")
    csv = country_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Selected Country Data",
        csv,
        file_name=f"{selected_country}_weather.csv",
        mime="text/csv"
    )

    st.divider()
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.image_counter = 0
        st.rerun()

# --------------------------------------------------
# PRO DASHBOARD VIEW FUNCTIONS (advanced analytics helpers)

def single_country_view(df, metric):
    country = st.sidebar.selectbox("Country", sorted(df["country"].unique()))
    cdf = df[df["country"] == country].copy().sort_values("date")
    
    st.title(f"🌍 {country} Climate Analysis")
    
    # KPIs & Health Score
    c1, c2, c3, c4 = st.columns(4)
    health = calculate_health_score(cdf, metric)
    with c1: st.markdown(f'<div class="metric-card">Health Score<div class="health-score">{health}%</div></div>', unsafe_allow_html=True)
    c2.metric("Mean", f"{cdf[metric].mean():.2f}")
    c3.metric("Skewness", f"{cdf[metric].skew():.2f}")
    c4.metric("IQR Range", f"{(cdf[metric].quantile(0.75) - cdf[metric].quantile(0.25)):.2f}")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Distributions", "🍂 Seasonal Patterns", "🚨 Extreme Events", "📉 Decomposition"])

    with tab1:
        st.subheader("Distribution Analysis")
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(px.histogram(cdf, x=metric, color="season", marginal="rug"), use_container_width=True)
        col_b.plotly_chart(px.violin(cdf, y=metric, x="season", box=True, points="all", color="season"), use_container_width=True)

    with tab2:
        st.subheader("Seasonal & Rolling Trends")
        cdf['rolling_avg'] = cdf[metric].rolling(window=7).mean()
        fig = px.line(cdf, x="date", y=[metric, 'rolling_avg'], color_discrete_sequence=["#cbd5e0", "#3182bd"])
        st.plotly_chart(fig, use_container_width=True)
        
        # Season Comparison Bar
        seasonal_avg = cdf.groupby("season")[metric].mean().reset_index()
        st.plotly_chart(px.bar(seasonal_avg, x="season", y=metric, color="season"), use_container_width=True)

    with tab3:
        st.subheader("Extreme Weather Detection")
        # IQR Based Anomalies
        q1, q3 = cdf[metric].quantile(0.25), cdf[metric].quantile(0.75)
        iqr = q3 - q1
        cdf['is_extreme'] = (cdf[metric] < (q1 - 1.5 * iqr)) | (cdf[metric] > (q3 + 1.5 * iqr))
        
        fig_ext = px.scatter(cdf, x="date", y=metric, color="is_extreme", 
                             color_discrete_map={True: "red", False: "#3182bd"},
                             title="Extreme Event Markers")
        st.plotly_chart(fig_ext, use_container_width=True)
        
        if cdf['is_extreme'].any():
            st.warning(f"Total Extreme Days Detected: {cdf['is_extreme'].sum()}")
            st.dataframe(cdf[cdf['is_extreme']][['date', metric, 'condition_text']])

    with tab4:
        st.subheader("Conceptual Seasonal Decomposition")
        st.info("Visualizing Trend vs Residual Variance")
        cdf['trend'] = cdf[metric].rolling(window=15, center=True).mean()
        cdf['residual'] = cdf[metric] - cdf['trend']
        
        c_a, c_b = st.columns(2)
        c_a.plotly_chart(px.line(cdf, x="date", y="trend", title="Underlying Trend (15-Day)"), use_container_width=True)
        c_b.plotly_chart(px.area(cdf, x="date", y="residual", title="Residual (Noise/Extreme Variance)"), use_container_width=True)


def regional_comparison_view(df, metric):
    st.title("🏙 Regional Side-by-Side Comparison")
    countries = st.multiselect("Select Countries to Compare", df["country"].unique(), default=df["country"].unique()[:2])
    
    if countries:
        comp_df = df[df["country"].isin(countries)]
        
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.box(comp_df, x="country", y=metric, color="country", title="Statistical Range Comparison"), use_container_width=True)
        with c2:
            st.plotly_chart(px.line(comp_df, x="date", y=metric, color="country", title="Time-Series Overlay"), use_container_width=True)
        
        # Rainfall Pie for these regions
        if "precip_mm" in df.columns:
            st.plotly_chart(px.pie(comp_df.groupby("country")["precip_mm"].sum().reset_index(), values="precip_mm", names="country", title="Rainfall Share"), use_container_width=True)

def similarity_view(df, metric):
    st.title("🧠 Climate Similarity Index")
    c1, c2 = st.columns(2)
    city_a = c1.selectbox("City A", df["country"].unique(), index=0)
    city_b = c2.selectbox("City B", df["country"].unique(), index=1)
    
    score = city_similarity(df, city_a, city_b, metric)
    
    st.markdown(f"""
    <div class="main-card" style="text-align:center;">
        <h2>Similarity Score</h2>
        <h1 style="color:#3182bd; font-size:80px;">{score:.1f}%</h1>
        <p>Based on {metric} variances between these two locations.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Comparison Heatmap
    comp_data = df[df["country"].isin([city_a, city_b])]
    pivot = comp_data.pivot_table(index="season", columns="country", values=metric, aggfunc="mean")
    st.plotly_chart(px.imshow(pivot, text_auto=True, title="Seasonal Mean Comparison Heatmap"), use_container_width=True)

# --------------------------------------------------
# PRO DASHBOARD (advanced analytics)
# --------------------------------------------------
def dashboard_pro():
    # styling
    bg_images = [
        "https://images.unsplash.com/photo-1592210454359-9043f067919b",
        "https://images.unsplash.com/photo-1516912481808-3406841bd33c",
        "https://images.unsplash.com/photo-1428592953211-077101b2021b",
        "https://images.unsplash.com/photo-1493246507139-91e8bef99c02",
        "https://images.unsplash.com/photo-1470115636492-6d2b56f9146d",
        "https://images.unsplash.com/photo-1520108871036-7c9eb13eb532"
    ]
    if "img_idx" not in st.session_state:
        st.session_state.img_idx = 0
    st.session_state.img_idx = (st.session_state.img_idx + 1) % len(bg_images)
    current_bg = bg_images[st.session_state.img_idx]
    st.markdown(f"""
    <style>
        .stApp {{
            background: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url("{current_bg}");
            background-attachment: fixed; background-size: cover;
        }}
        .main-card {{
            background: white; padding: 20px; border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #edf2f7;
        }}
        .metric-card {{
            background: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #3182bd;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .health-score {{
            font-size: 48px; font-weight: bold; text-align: center; color: #2d3748;
        }}
    </style>
    """, unsafe_allow_html=True)

    df = load_data()
    st_autorefresh(interval=15000, key="auto_refresh")

    st.sidebar.title(" ClimateScope Pro")
    mode = st.sidebar.radio("Analysis Mode", ["Single Country", "Regional Comparison", "Similarity Index"])
    metric = st.sidebar.selectbox("Select Metric", df.select_dtypes(include=np.number).columns)

    if mode == "Single Country":
        single_country_view(df, metric)
    elif mode == "Regional Comparison":
        regional_comparison_view(df, metric)
    else:
        similarity_view(df, metric)

# --------------------------------------------------
# PAGE CONTROLLER
# --------------------------------------------------
if st.session_state.logged_in:
    app_mode = st.sidebar.radio("App Version", ["Standard", "Pro"])
    if app_mode == "Standard":                                          
        dashboard_basic()
    else:
        dashboard_pro()
else:
    auth_page()
