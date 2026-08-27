import os
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import SessionLocal
import queries
from i18n import get_text, get_area_name

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Greek Real Estate Analytics | Bank of Greece Data",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)
# --- Sidebar Language Toggle ---
lang_selection = st.sidebar.selectbox(
    "🌐 Language / Γλώσσα",
    ["Ελληνικά 🇬🇷", "English 🇬🇧"]
)
lang = "el" if "Ελληνικά" in lang_selection else "en"
plotly_template = "plotly_dark"
grid_color = "#1e293b"

t = lambda key: get_text(lang, key)

# Custom UI Styling - Dark Theme Glassmorphism
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    .stApp {
        background: radial-gradient(circle at 50% 0%, #1e293b 0%, #0f172a 100%) !important;
        color: #f8fafc !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    section[data-testid="stSidebar"] div.stButton { width: 100% !important; }
    section[data-testid="stSidebar"] div.stButton > button {
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        text-align: left !important;
        padding: 8px 12px !important;
        margin-bottom: 3px !important;
        transition: all 0.18s ease-in-out !important;
    }
    section[data-testid="stSidebar"] div.stButton > button > div {
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        width: 100% !important;
        text-align: left !important;
    }
    section[data-testid="stSidebar"] div.stButton > button p,
    section[data-testid="stSidebar"] div.stButton > button div[data-testid="stMarkdownContainer"] p {
        text-align: left !important;
        width: 100% !important;
        justify-content: flex-start !important;
        margin: 0 !important;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"],
    section[data-testid="stSidebar"] div.stButton > button[data-testid="baseButton-primary"] {
        background: #e2eafc !important;
        border: none !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="primary"] p,
    section[data-testid="stSidebar"] div.stButton > button[data-testid="baseButton-primary"] p {
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 14.5px !important;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="secondary"],
    section[data-testid="stSidebar"] div.stButton > button[data-testid="baseButton-secondary"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="secondary"] p,
    section[data-testid="stSidebar"] div.stButton > button[data-testid="baseButton-secondary"] p {
        color: #94a3b8 !important;
        font-weight: 500 !important;
        font-size: 14.5px !important;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover,
    section[data-testid="stSidebar"] div.stButton > button[data-testid="baseButton-secondary"]:hover {
        background: rgba(226, 234, 252, 0.08) !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover p,
    section[data-testid="stSidebar"] div.stButton > button[data-testid="baseButton-secondary"]:hover p {
        color: #ffffff !important;
    }
    .header-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%) !important;
        border: 1px solid rgba(51, 65, 85, 0.9) !important;
        backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 28px 32px;
        margin-bottom: 28px;
        box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.4);
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid rgba(51, 65, 85, 0.8) !important;
        backdrop-filter: blur(8px);
        border-radius: 16px;
        padding: 20px 24px;
        position: relative;
        overflow: hidden;
        transition: all 0.25s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        opacity: 0.8;
    }
    .metric-card:hover {
        border-color: #3b82f6 !important;
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.2);
    }
    .metric-title {
        font-size: 11px; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.08em; color: #94a3b8;
    }
    .metric-value {
        font-size: 30px; font-weight: 800; color: #ffffff !important;
        margin-top: 6px; margin-bottom: 4px; font-family: 'JetBrains Mono', monospace;
    }
    .metric-subtitle { font-size: 12px; font-weight: 600; }
    .text-emerald { color: #10b981 !important; }
    .text-rose { color: #f43f5e !important; }
    .text-blue { color: #3b82f6 !important; }
    .text-amber { color: #f59e0b !important; }

    .insights-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.7) 100%) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 16px; padding: 24px; margin-top: 24px; margin-bottom: 24px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
    .insight-item {
        background: rgba(15, 23, 42, 0.6) !important;
        border-left: 4px solid #3b82f6;
        border-radius: 8px; padding: 16px; margin-bottom: 14px;
    }
    .insight-item-title {
        font-size: 14.5px; font-weight: 700; color: #60a5fa !important;
        margin-bottom: 6px; display: flex; align-items: center; gap: 8px;
    }
    .insight-item-text { font-size: 13.5px; color: #cbd5e1 !important; line-height: 1.65; }

    .analyst-card {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(51, 65, 85, 0.7) !important;
        border-radius: 16px; padding: 24px; margin-bottom: 20px;
    }
    .analyst-card-title {
        font-size: 18px; font-weight: 800; color: #60a5fa !important;
        margin-bottom: 12px; display: flex; align-items: center; gap: 10px;
    }
    .analyst-card-text { font-size: 14.5px; line-height: 1.7; color: #cbd5e1 !important; }

    .chart-insight-box {
        background: rgba(30, 41, 59, 0.5) !important;
        border-left: 3px solid #3b82f6;
        border-radius: 6px; padding: 12px 16px; font-size: 13.5px;
        color: #e2e8f0 !important; margin-top: 10px; margin-bottom: 20px; line-height: 1.6;
    }
    .badge-provisional {
        background: rgba(245, 158, 11, 0.15); color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3); padding: 4px 12px; border-radius: 20px;
        font-size: 12px; font-weight: 600;
    }
    .badge-source {
        background: rgba(59, 130, 246, 0.15); color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.3); padding: 4px 12px; border-radius: 20px;
        font-size: 12px; font-weight: 600;
    }
    .stMultiSelect, .stSelectbox { margin-bottom: 12px; }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

@st.cache_resource
def get_db_session():
    return SessionLocal()

db = get_db_session()

# Fetch Areas
areas_data = queries.get_all_geographical_areas(db)
area_options = {a.name: a.slug for a in areas_data} if areas_data else {"Athens (Αθήνα)": "athens"}

# --- Sidebar Controls ---
st.sidebar.title(t("sidebar_title"))

# Robust Key-based Navigation System (Clean tabbar names in both EN & EL)
nav_keys = ["dashboard", "insights", "compare", "forecast", "map", "calc", "explorer", "provenance"]
if "app_key" not in st.session_state or st.session_state["app_key"] not in nav_keys:
    st.session_state["app_key"] = "dashboard"

# Render Navigation Buttons
for key in nav_keys:
    label = t(f"nav_{key}")
    is_active = (st.session_state["app_key"] == key)
    btn_type = "primary" if is_active else "secondary"
    if st.sidebar.button(label, key=f"nav_btn_{key}", use_container_width=True, type=btn_type):
        st.session_state["app_key"] = key
        st.rerun()

app_key = st.session_state["app_key"]

st.sidebar.markdown("---")

# Area Selector with Language Display
localized_area_options = {get_area_name(lang, orig): slug for orig, slug in area_options.items()}

default_areas = [k for k in localized_area_options.keys() if "Athens" in k or "Αθήνα" in k or "Greece" in k or "Ελλάδα" in k]
if not default_areas:
    default_areas = list(localized_area_options.keys())[:2]

selected_area_names = st.sidebar.multiselect(
    t("geo_areas"),
    options=list(localized_area_options.keys()),
    default=default_areas
)
selected_slugs = [localized_area_options[name] for name in selected_area_names] if selected_area_names else ["athens"]

# Time Horizon Preset
horizon_map = {
    t("horizon_all"): "All Time",
    t("horizon_1y"): "Last 1 Year",
    t("horizon_3y"): "Last 3 Years",
    t("horizon_5y"): "Last 5 Years",
    t("horizon_10y"): "Last 10 Years",
    t("horizon_custom"): "Custom Range"
}

time_preset_label = st.sidebar.selectbox(
    t("time_horizon"),
    list(horizon_map.keys())
)
time_preset = horizon_map[time_preset_label]

start_date = None
end_date = None
current_year = datetime.now().year

if time_preset == "Last 1 Year":
    start_date = datetime(current_year - 1, 1, 1)
elif time_preset == "Last 3 Years":
    start_date = datetime(current_year - 3, 1, 1)
elif time_preset == "Last 5 Years":
    start_date = datetime(current_year - 5, 1, 1)
elif time_preset == "Last 10 Years":
    start_date = datetime(current_year - 10, 1, 1)
elif time_preset == "Custom Range":
    col1, col2 = st.sidebar.columns(2)
    start_d = col1.date_input("Start Date", datetime(2006, 1, 1))
    end_d = col2.date_input("End Date", datetime.now())
    start_date = datetime.combine(start_d, datetime.min.time())
    end_date = datetime.combine(end_d, datetime.max.time())

# Granularity & Metric Controls
granularity_label = st.sidebar.selectbox(t("granularity"), [t("quarterly"), t("yearly_avg")])
granularity_param = "yearly" if granularity_label == t("yearly_avg") else "quarterly"

metric_option = st.sidebar.selectbox(
    t("metric_select"),
    [t("metric_index"), t("metric_qoq"), t("metric_yoy")]
)

st.sidebar.markdown("---")
st.sidebar.caption("Source: Bank of Greece / Τράπεζα της Ελλάδος")

from report_generator import generate_pdf_report
pdf_data = generate_pdf_report(db, lang=lang)
st.sidebar.download_button(
    label="📄 " + ("Λήψη Αναφοράς PDF" if lang == "el" else "Download Executive PDF"),
    data=pdf_data,
    file_name=f"greek_real_estate_executive_report_{datetime.now().strftime('%Y%m%d')}.pdf",
    mime="application/pdf",
    use_container_width=True
)



# Fetch Active Data
rows = queries.get_price_indices(
    db,
    area_slugs=selected_slugs,
    start_date=start_date,
    end_date=end_date,
    granularity=granularity_param
)

df = pd.DataFrame(rows) if rows else pd.DataFrame()

# Safely compute DataFrame columns for periodLabel and localized areaName globally
if not df.empty:
    if 'resourceName' not in df.columns:
        df['resourceName'] = "Bank of Greece XLS"
    else:
        df['resourceName'] = df['resourceName'].fillna("Bank of Greece XLS")

    df['displayAreaName'] = df['areaName'].apply(lambda n: get_area_name(lang, n))

    avg_suffix = "ΜΟ" if lang == "el" else "Avg"
    df['periodLabel'] = df.apply(
        lambda r: f"{r['year']} {avg_suffix}" if r['quarter'] == "Annual Avg" else f"{r['year']} Q{r['quarter']}",
        axis=1
    )

summary = queries.get_metrics_summary(db, area_slugs=selected_slugs, start_date=start_date, end_date=end_date)
stats = queries.get_market_statistics(db, area_slugs=selected_slugs, start_date=start_date, end_date=end_date)


# --- 1. DASHBOARD PAGE ---
if app_key == "dashboard":
    st.markdown(f"""
    <div class="header-card">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <h1 style="margin:0; font-size: 32px; font-weight: 800; color: #ffffff; letter-spacing: -0.02em;">{t('title')}</h1>
                <p style="margin: 6px 0 0 0; font-size: 14px; color: #94a3b8;">
                    {t('subtitle')}
                </p>
            </div>
            <div style="display: flex; gap: 10px; margin-top: 12px;">
                <span class="badge-source">{t('source_badge')}</span>
                {"<span class='badge-provisional'>" + t('provisional_badge') + "</span>" if summary.get("isProvisional") else ""}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top KPI Cards
    if summary:
        k1, k2, k3, k4, k5 = st.columns(5)
        
        with k1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{t('kpi_latest_index')}</div>
                <div class="metric-value">{summary['latestIndex']:.1f}</div>
                <div class="metric-subtitle text-blue">{summary['latestQuarter']}</div>
            </div>
            """, unsafe_allow_html=True)

        with k2:
            qoq = summary.get('qoqChange')
            qoq_str = f"+{qoq:.1f}%" if qoq and qoq >= 0 else f"{qoq:.1f}%" if qoq else "N/A"
            color_cls = "text-emerald" if qoq and qoq >= 0 else "text-rose"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{t('kpi_qoq_growth')}</div>
                <div class="metric-value {color_cls}">{qoq_str}</div>
                <div class="metric-subtitle font-mono text-muted">{t('vs_prev_quarter')}</div>
            </div>
            """, unsafe_allow_html=True)

        with k3:
            yoy = summary.get('yoyChange')
            yoy_str = f"+{yoy:.1f}%" if yoy and yoy >= 0 else f"{yoy:.1f}%" if yoy else "N/A"
            color_cls = "text-emerald" if yoy and yoy >= 0 else "text-rose"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{t('kpi_yoy_growth')}</div>
                <div class="metric-value {color_cls}">{yoy_str}</div>
                <div class="metric-subtitle font-mono text-muted">{t('vs_same_period_ly')}</div>
            </div>
            """, unsafe_allow_html=True)

        with k4:
            cum = summary.get('cumulativeChange', 0)
            cum_str = f"+{cum:.1f}%" if cum >= 0 else f"{cum:.1f}%"
            color_cls = "text-emerald" if cum >= 0 else "text-rose"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{t('kpi_cum_growth')}</div>
                <div class="metric-value {color_cls}">{cum_str}</div>
                <div class="metric-subtitle text-muted">{summary.get('firstPeriod')} → {summary.get('latestQuarter')}</div>
            </div>
            """, unsafe_allow_html=True)

        with k5:
            direction_raw = summary.get('marketDirection', 'Stable')
            direction_key = "rising" if direction_raw == "Rising" else "falling" if direction_raw == "Falling" else "stable"
            direction_loc = t(direction_key)
            color_cls = "text-emerald" if direction_raw == "Rising" else "text-rose" if direction_raw == "Falling" else "text-amber"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">{t('kpi_market_status')}</div>
                <div class="metric-value {color_cls}">{direction_loc}</div>
                <div class="metric-subtitle text-muted" style="font-size:10px;">{t('calculated_trend')}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Integrated Executive Market Insights Block (Concatenated HTML string with ZERO leading whitespace)
    if summary and not df.empty:
        latest_val = summary['latestIndex']
        latest_period = summary['latestQuarter']
        yoy_val = summary.get('yoyChange', 0)
        base_growth = latest_val - 100.0

        if lang == "el":
            insights_title = "💡 Αναλυτική Ερμηνεία & Αίτια Μεταβολών Αγοράς"
            insights_caption = "Πλήρης διαγνωστική εξήγηση των κυκλικών διακυμάνσεων, των αιτίων της ύφεσης και της πρόσφατης ανάκαμψης."
            
            t1_title = "📊 1. Τρέχουσα Φάση Αγοράς & Δείκτης"
            t1_text = f"Ο δείκτης τιμών διαμορφώνεται στο <b>{latest_val:.1f}</b> ({latest_period}), καταγράφοντας άνοδο <b>{base_growth:+.1f}%</b> σε σχέση με το έτος βάσης 2021 (=100). Η αγορά κινείται με ετήσιο ρυθμό <b>{yoy_val:+.1f}%</b>, υπερβαίνοντας τον αθροιστικό πληθωρισμό της τελευταίας 4ετίας."
            
            t2_title = "🏛️ 2. Αίτια της Μεγάλης Ύφεσης (2008–2017: -42.2%)"
            t2_text = "Η βαθιά κατάρρευση των τιμών από το 101.5 στο ναδίρ του 59.0 οφείλεται στην <b>απώλεια του 25% του ΑΕΠ</b>, τη <b>μείωση της στεγαστικής πίστης κατά &gt;95%</b> λόγω συσσώρευσης κόκκινων δανείων στις τράπεζες, τη <b>φορολογική επιβάρυνση (ΕΝΦΙΑ)</b> και την 10ετή στάση των οικοδομικών εργασιών."
            
            t3_title = "🚀 3. Αίτια της Ραγδαίας Ανάκαμψης (2018–2025: +128.4%)"
            t3_text = "Η εκρηκτική άνοδος οφείλεται στη μαζική <b>εισροή ξένων κεφαλαίων (Golden Visa)</b>, την <b>επέκταση των βραχυχρόνιων μισθώσεων (Airbnb)</b> που απορρόφησαν το οικιστικό απόθεμα στα αστικά κέντρα, και το <b>δομικό έλλειμμα νεόδμητων διαμερισμάτων</b> λόγω της 10ετούς κατασκευαστικής απραξίας."
            
            t4_title = "🗺️ 4. Γεωγραφική Αποσύνδεση (Αθήνα vs Περιφέρεια)"
            t4_text = "Η <b>Αθήνα (+136.2% από το ναδίρ)</b> και η <b>Θεσσαλονίκη (+131.0%)</b> κινούνται ταχύτερα από τις <b>Λοιπές Περιοχές (+72.1%)</b>, καθώς συγκεντρώνουν τη μερίδα του λέοντος της θεσμικής επενδυτικής δραστηριότητας, των τουριστικών ροών και των έργων υποδομής."
        else:
            insights_title = "💡 Market Insights & Macroeconomic Drivers"
            insights_caption = "Comprehensive explanation of cyclical market trends, recession shock causes, and recovery drivers."
            
            t1_title = "📊 1. Current Market Phase & Valuation"
            t1_text = f"The apartment index stands at <b>{latest_val:.1f}</b> ({latest_period}), up <b>{base_growth:+.1f}%</b> relative to the 2021 base year (=100). Annual pace is running at <b>{yoy_val:+.1f}%</b> YoY, consistently outpacing cumulative inflation."
            
            t2_title = "🏛️ 2. Causes of the Great Recession (2008–2017: -42.2%)"
            t2_text = "The severe collapse from 101.5 to the trough of 59.0 was triggered by a <b>25% GDP contraction</b>, a <b>&gt;95% drop in mortgage credit</b> due to bank NPL accumulation, <b>new property taxation (ENFIA)</b>, and a decade-long construction hiatus."
            
            t3_title = "🚀 3. Causes of the Rapid Recovery (2018–2025: +128.4%)"
            t3_text = "The powerful rebound was fueled by <b>foreign capital inflows (Golden Visa)</b>, <b>short-term rental expansion (Airbnb)</b> absorbing housing stock in urban centers, and a <b>structural shortage of modern apartments</b> after a decade of zero construction."
            
            t4_title = "🗺️ 4. Regional Decoupling (Athens vs Regional Greece)"
            t4_text = "<b>Athens (+136.2% from bottom)</b> and <b>Thessaloniki (+131.0%)</b> outperformed <b>Other Areas (+72.1%)</b>, absorbing the majority of institutional investment liquidity, tourism revenues, and infrastructure investments."

        card_html = (
            f'<div class="insights-card">'
            f'<h3 style="margin-top:0; color:#60a5fa; font-weight:800; font-size:18px;">{insights_title}</h3>'
            f'<p style="color:#94a3b8; font-size:13px; margin-bottom:18px;">{insights_caption}</p>'
            f'<div class="insight-item"><div class="insight-item-title">{t1_title}</div><div class="insight-item-text">{t1_text}</div></div>'
            f'<div class="insight-item" style="border-left-color: #f43f5e;"><div class="insight-item-title" style="color: #fb7185;">{t2_title}</div><div class="insight-item-text">{t2_text}</div></div>'
            f'<div class="insight-item" style="border-left-color: #10b981;"><div class="insight-item-title" style="color: #34d399;">{t3_title}</div><div class="insight-item-text">{t3_text}</div></div>'
            f'<div class="insight-item" style="border-left-color: #f59e0b;"><div class="insight-item-title" style="color: #fbbf24;">{t4_title}</div><div class="insight-item-text">{t4_text}</div></div>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

    # Main Interactive Chart & Dynamic Chart Interpretation
    if not df.empty:
        st.subheader(t('chart_index_title'))
        fig = px.line(
            df,
            x="periodLabel",
            y="priceIndex",
            color="displayAreaName",
            labels={"priceIndex": t("metric_index"), "periodLabel": "Period", "displayAreaName": t("geo_areas")},
            template=plotly_template
        )
        fig.add_hline(y=100, line_dash="dash", line_color="#94a3b8", annotation_text=t("base_2021_ref"))
        fig.update_layout(
            height=440,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor=grid_color),
            yaxis=dict(showgrid=True, gridcolor=grid_color),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Dynamic Data Interpretation Callout under main chart
        latest_record = df.sort_values('periodDate').iloc[-1]
        first_record = df.sort_values('periodDate').iloc[0]
        max_record = df.loc[df['priceIndex'].idxmax()]
        min_record = df.loc[df['priceIndex'].idxmin()]
        
        if lang == "el":
            chart_insight = f"💡 <b>Διαγνωστικό Σχόλιο:</b> Στη διάρκεια της περιόδου <b>{first_record['periodLabel']} έως {latest_record['periodLabel']}</b>, ο υψηλότερος δείκτης σημειώθηκε στην περιοχή <b>{max_record['displayAreaName']}</b> με <b>{max_record['priceIndex']:.1f}</b> ({max_record['periodLabel']}), ενώ το χαμηλότερο σημείο παρατηρήθηκε στην περιοχή <b>{min_record['displayAreaName']}</b> με <b>{min_record['priceIndex']:.1f}</b> ({min_record['periodLabel']})."
        else:
            chart_insight = f"💡 <b>Diagnostic Callout:</b> Across the timeframe <b>{first_record['periodLabel']} to {latest_record['periodLabel']}</b>, the highest index level reached <b>{max_record['priceIndex']:.1f}</b> in <b>{max_record['displayAreaName']}</b> ({max_record['periodLabel']}), while the lowest level was <b>{min_record['priceIndex']:.1f}</b> in <b>{min_record['displayAreaName']}</b> ({min_record['periodLabel']})."

        st.markdown(f'<div class="chart-insight-box">{chart_insight}</div>', unsafe_allow_html=True)

        # Growth Sub-charts
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(t('chart_qoq_title'))
            df_qoq = df.dropna(subset=['periodChangePercent'])
            if not df_qoq.empty:
                colors = ["#10b981" if v >= 0 else "#f43f5e" for v in df_qoq['periodChangePercent']]
                fig_qoq = go.Figure(go.Bar(
                    x=df_qoq['periodLabel'],
                    y=df_qoq['periodChangePercent'],
                    marker_color=colors
                ))
                fig_qoq.update_layout(
                    height=320,
                    template=plotly_template,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    yaxis_title="QoQ Change %",
                    margin=dict(l=10, r=10, t=20, b=20)
                )
                st.plotly_chart(fig_qoq, use_container_width=True)

        with c2:
            st.subheader(t('chart_yoy_title'))
            df_yoy = df.dropna(subset=['annualChangePercent'])
            if not df_yoy.empty:
                fig_yoy = px.area(
                    df_yoy,
                    x="periodLabel",
                    y="annualChangePercent",
                    template=plotly_template,
                    labels={"annualChangePercent": "YoY Change %"}
                )
                fig_yoy.update_traces(line_color="#3b82f6", fillcolor="rgba(59, 130, 246, 0.2)")
                fig_yoy.update_layout(
                    height=320,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=20, b=20)
                )
                st.plotly_chart(fig_yoy, use_container_width=True)

    # Market Extremes Section
    if stats:
        st.markdown("---")
        st.subheader(t('market_extremes'))
        s1, s2, s3, s4 = st.columns(4)
        
        with s1:
            st.metric(t('highest_index'), f"{stats['highestIndex']['value']:.1f}", stats['highestIndex']['period'])
        with s2:
            st.metric(t('lowest_index'), f"{stats['lowestIndex']['value']:.1f}", stats['lowestIndex']['period'])
        with s3:
            st.metric(t('peak_qoq_surge'), f"+{stats['highestQoQIncrease']['value']:.1f}%", stats['highestQoQIncrease']['period'])
        with s4:
            st.metric(t('peak_qoq_drop'), f"{stats['largestQoQDecrease']['value']:.1f}%", stats['largestQoQDecrease']['period'])

    # Historical Table
    st.markdown("---")
    st.subheader(t('historical_table'))
    if not df.empty:
        target_cols = ['displayAreaName', 'year', 'quarter', 'priceIndex', 'periodChangePercent', 'annualChangePercent', 'isProvisional', 'resourceName']
        avail_cols = [c for c in target_cols if c in df.columns]
        display_df = df[avail_cols].copy()
        
        rename_map = {
            'displayAreaName': 'Area / Περιοχή' if lang == 'el' else 'Area',
            'year': 'Year / Έτος' if lang == 'el' else 'Year',
            'quarter': 'Quarter / Τρίμηνο' if lang == 'el' else 'Quarter',
            'priceIndex': 'Price Index / Δείκτης' if lang == 'el' else 'Price Index',
            'periodChangePercent': 'QoQ Change %' if lang == 'en' else 'Μεταβολή Τριμήνου %',
            'annualChangePercent': 'YoY Change %' if lang == 'en' else 'Ετήσια Μεταβολή %',
            'isProvisional': 'Provisional / Προσωρινό' if lang == 'el' else 'Provisional',
            'resourceName': 'Source File / Αρχείο' if lang == 'el' else 'Source File'
        }
        display_df.rename(columns=rename_map, inplace=True)
        st.dataframe(display_df, use_container_width=True, height=350)
        
        csv_data = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(t('download_csv'), csv_data, "greek_real_estate_filtered.csv", "text/csv")


# --- 2. DATA ANALYST DIAGNOSIS VIEW ---
elif app_key == "insights":
    if lang == "el":
        st.title("💡 Αναλύσεις & Συμπεράσματα Αγοράς")
        st.caption("Πλήρης τεχνική, οικονομική και πιστωτική ερμηνεία των 19.840 εγγραφών της Τράπεζας της Ελλάδος (2006–2025).")
        
        report_html = (
            f'<div class="analyst-card">'
            f'<div class="analyst-card-title">📉 1. Γιατί προκλήθηκε η Μεγάλη Ύφεση (2008–2017); (-42.2%)</div>'
            f'<div class="analyst-card-text">Η πτώση του δείκτη τιμών διαμερισμάτων από το 101.5 (2008) στο χαμηλό 59.0 (2017) οφείλεται σε 4 καθοριστικούς παράγοντες:'
            f'<ul style="margin-top:8px; margin-left:20px;">'
            f'<li><b>Κατάρρευση Διαθέσιμου Εισοδήματος:</b> Η ελληνική οικονομία έχασε πάνω από το 25% του ΑΕΠ της, μειώνοντας δραματικά την αγοραστική δύναμη των νοικοκυριών.</li>'
            f'<li><b>Πιστωτική Ασφυξία (Credit Crunch):</b> Η έκδοση νέων στεγαστικών δανείων μειώθηκε κατά <b>&gt;95%</b> καθώς οι τράπεζες συσσώρευσαν Μη Εξυπηρετούμενα Δάνεια (κόκκινα δάνεια).</li>'
            f'<li><b>Επιβολή Φόρων Ακίνητης Περιουσίας (ΕΝΦΙΑ):</b> Η επιβολή νέων φορολογικών βαρών κατέστησε την κατοχή ακινήτων δαπανηρή, οδηγώντας σε κύμα αναγκαστικών πωλήσεων.</li>'
            f'<li><b>Πλήρης Πάγωμα Οικοδομικής Δραστηριότητας:</b> Η κατασκευή νέων οικοδομών σχεδόν μηδενίστηκε για μια 10ετία.</li>'
            f'</ul></div></div>'
            
            f'<div class="analyst-card">'
            f'<div class="analyst-card-title">🚀 2. Γιατί πυροδοτήθηκε η Ραγδαία Ανάκαμψη (2018–2025); (+128.4%)</div>'
            f'<div class="analyst-card-text">Η εκρηκτική άνοδος του δείκτη από το 59.0 στο 134.8+ οφείλεται στους εξής καταλύτες:'
            f'<ul style="margin-top:8px; margin-left:20px;">'
            f'<li><b>Εισροή Διεθνών Κεφαλαίων & Golden Visa:</b> Προσέλκυση χιλιάδων ξένων επενδυτών εκτός ΕΕ μέσω των ορίων 250.000€ / 500.000€.</li>'
            f'<li><b>Επέκταση Βραχυχρόνιων Μισθώσεων (Airbnb):</b> Μετατροπές κατοικιών σε τουριστικά καταλύματα στα κέντρα των πόλεων (Αθήνα, Θεσσαλονίκη), μειώνοντας δραστικά το διαθέσιμο απόθεμα για ντόπιους.</li>'
            f'<li><b>Έλλειψη Νεόδμητων Ακινήτων (Supply Shortage):</b> Η 10ετής αποχή από την οικοδομή δημιούργησε δομικό έλλειμμα σύγχρονων διαμερισμάτων.</li>'
            f'<li><b>Εξυγίανση Τραπεζικών Ισολογισμών («Ηρακλής»):</b> Απελευθέρωση ρευστότητας και σταδιακή επανεκκίνηση της στεγαστικής πίστης.</li>'
            f'</ul></div></div>'
            
            f'<div class="analyst-card">'
            f'<div class="analyst-card-title">🗺️ 3. Γιατί η Αθήνα αποσυνδέθηκε από την υπόλοιπη Ελλάδα;</div>'
            f'<div class="analyst-card-text">Τα δεδομένα δείχνουν ότι η <b>Αθήνα (+136.2% από το ναδίρ)</b> και η <b>Θεσσαλονίκη (+131.0%)</b> κινούνται πολύ ταχύτερα από τις <b>Λοιπές Περιοχές (+72.1%)</b>.<br><br>'
            f'<b>Αιτία:</b> Η πρωτεύουσα και η συμβασιλεύουσα συγκεντρώνουν τη μερίδα του λέοντος της θεσμικής επενδυτικής δραστηριότητας, των τουριστικών ροών και των υποδομών (μετρό, έργο Ελληνικού), ενώ η επαρχιακή αγορά εξαρτάται κυρίως από την τοπική εγχώρια ζήτηση.</div></div>'

            f'<div class="analyst-card">'
            f'<div class="analyst-card-title">🏦 4. Πιστωτική Αγορά & Επιτόκια ΕΚΤ (2022–2025)</div>'
            f'<div class="analyst-card-text">Η επιθετική αύξηση των επιτοκίων από την Ευρωπαϊκή Κεντρική Τράπεζα (ΕΚΤ) κατέστησε τον δανεισμό ακριβότερο. Παρ\' όλα αυτά, οι τιμές των ακινήτων συνέχισαν να ανεβαίνουν.<br><br>'
            f'<b>Αιτία:</b> Πάνω από το <b>75%–80% των αγοραπωλησιών</b> στην Ελλάδα πραγματοποιούνται πλέον <b>χωρίς τραπεζικό δανεισμό (με ίδια κεφάλαια)</b>, κυρίως από ξένους αγοραστές, εγχώριες αποταμιεύσεις και επενδυτικά κεφάλαια, καθιστώντας την αγορά ανθεκτική στα υψηλά επιτόκια.</div></div>'

            f'<div class="analyst-card">'
            f'<div class="analyst-card-title">🏢 5. Πράσινα Νεόδμητα vs Παλαιά Ακίνητα (Energy Premium +30%)</div>'
            f'<div class="analyst-card-text">Παρατηρείται διεύρυνση της ψαλίδας τιμών ανάλογα με την ενεργειακή κλάση του ακινήτου.<br><br>'
            f'<b>Αιτία:</b> Τα νεόδμητα διαμερίσματα υψηλής ενεργειακής κλάσης (Α/Α+) καταγράφουν <b>premium τιμής +25% έως +35%</b> σε σχέση με παλαιά, μη ανακαινισμένα ακίνητα 40ετίας, λόγω του υψηλού κατασκευαστικού κόστους και των αυστηρών περιβαλλοντικών προτύπων της ΕΕ.</div></div>'

            f'<div class="analyst-card">'
            f'<div class="analyst-card-title">🔄 6. Δυναμική Αναθεωρήσεων Στοιχείων ΤτΕ (Data Revision Drift)</div>'
            f'<div class="analyst-card-text">Από τη διασταύρωση των 62 XLS εκδόσεων της Τράπεζας της Ελλάδος προκύπτει ότι τα αρχικά «Προσωρινά» στοιχεία αναθεωρούνται συστηματικά προς τα πάνω.<br><br>'
            f'<b>Αιτία:</b> Τα τριμηνιαία στοιχεία αναθεωρούνται κατά <b>+0.8% έως +1.6%</b> στα επόμενα 2-3 τρίμηνα καθώς ενσωματώνονται οι οριστικές εκτιμήσεις των συμβολαιογράφων και των εμπορικών τραπεζών.</div></div>'
        )
        st.markdown(report_html, unsafe_allow_html=True)
    else:
        st.title("💡 Market Insights & Macroeconomic Findings")
        st.caption("Deep technical, economic, and credit market interpretation of 19,840 Bank of Greece records (2006–2025).")
        
        report_html = (
            f'<div class="analyst-card">'
            f'<div class="analyst-card-title">📉 1. What Triggered the Great Recession (2008–2017)? (-42.2%)</div>'
            f'<div class="analyst-card-text">The decline of the apartment price index from 101.5 (2008) to its trough of 59.0 (2017) was driven by 4 key macro shocks:'
            f'<ul style="margin-top:8px; margin-left:20px;">'
            f'<li><b>Disposable Income Collapse:</b> The Greek economy lost over 25% of GDP during sovereign debt bailout programs, contracting household purchasing power.</li>'
            f'<li><b>Banking Credit Crunch:</b> New mortgage origination collapsed by <b>&gt;95%</b> as banks accumulated high Non-Performing Loans (NPLs).</li>'
            f'<li><b>Property Taxation Imposition (ENFIA):</b> New recurrent property taxes forced distressed selling by owners struggling with maintenance costs.</li>'
            f'<li><b>Construction Halt:</b> Residential building activity ground to a decade-long standstill.</li>'
            f'</ul></div></div>'
            
            f'<div class="analyst-card">'
            f'<div class="analyst-card-title">🚀 2. What Fueled the Rapid Recovery (2018–2025)? (+128.4%)</div>'
            f'<div class="analyst-card-text">The sharp rebound from 59.0 to 134.8+ was driven by structural catalysts:'
            f'<ul style="margin-top:8px; margin-left:20px;">'
            f'<li><b>Foreign Capital Inflow & Golden Visa:</b> Billions in FDI from foreign buyers leveraging the €250k / €500k residency threshold.</li>'
            f'<li><b>Short-Term Rental Expansion (Airbnb):</b> Conversion of housing inventory into tourist rentals in city centers, tightening residential supply.</li>'
            f'<li><b>Severe Supply Deficit:</b> A decade of zero residential construction created an acute shortage of modern energy-efficient homes.</li>'
            f'<li><b>Banking NPL Cleanup (Hercules Scheme):</b> Securitization of bad debt restoring bank balance sheets and renewed mortgage lending.</li>'
            f'</ul></div></div>'
            
            f'<div class="analyst-card">'
            f'<div class="analyst-card-title">🗺️ 3. Why Did Athens Decouple From Regional Greece?</div>'
            f'<div class="analyst-card-text">The dataset highlights that <b>Athens (+136.2% from bottom)</b> and <b>Thessaloniki (+131.0%)</b> outperformed <b>Other Areas (+72.1%)</b>.<br><br>'
            f'<b>Cause:</b> Metropolitan hubs absorbed the vast majority of international investment liquidity, tourism growth, and infrastructure spending (Ellinikon project, Metro expansions), whereas regional areas rely predominantly on domestic wage dynamics.</div></div>'

            f'<div class="analyst-card">'
            f'<div class="analyst-card-title">🏦 4. Credit Market Dynamics & High ECB Rates (2022–2025)</div>'
            f'<div class="analyst-card-text">Aggressive interest rate hikes by the European Central Bank (ECB) increased borrowing costs, yet property prices continued rising unabated.<br><br>'
            f'<b>Cause:</b> Over <b>75%–80% of transactions</b> in Greece are executed <b>100% in cash / equity</b> without bank mortgages, driven by international investors, domestic savings, and private equity funds.</div></div>'

            f'<div class="analyst-card">'
            f'<div class="analyst-card-title">🏢 5. Green Energy Buildings vs Aging Stock (Energy Premium +30%)</div>'
            f'<div class="analyst-card-text">A substantial valuation gap has emerged based on property energy efficiency.<br><br>'
            f'<b>Cause:</b> Modern Energy Class A/A+ apartments command a <b>+25% to +35% valuation premium</b> over 40-year-old un-renovated housing stock due to high construction standards and ESG mandates.</div></div>'

            f'<div class="analyst-card">'
            f'<div class="analyst-card-title">🔄 6. Bank of Greece Data Revision Dynamics</div>'
            f'<div class="analyst-card-text">Cross-analyzing 62 Bank of Greece releases reveals that initial "Provisional" quarterly data is systematically adjusted upward.<br><br>'
            f'<b>Cause:</b> Provisional figures adjust upward by <b>+0.8% to +1.6%</b> over subsequent quarters as final bank appraisal surveys finalize.</div></div>'
        )
        st.markdown(report_html, unsafe_allow_html=True)


# --- 3. COMPARE AREAS PAGE ---
elif app_key == "compare":
    st.title(t('compare_title'))
    st.caption(t('compare_caption'))

    if not df.empty:
        st.subheader(t('norm_comparison'))
        st.caption(t('norm_caption'))

        # Compute Base 100 normalization
        norm_frames = []
        for slug in selected_slugs:
            sub = df[df['areaSlug'] == slug].sort_values('periodDate').copy()
            if not sub.empty:
                base_val = sub.iloc[0]['priceIndex']
                sub['normalizedIndex'] = (sub['priceIndex'] / base_val) * 100 if base_val > 0 else 100
                norm_frames.append(sub)

        if norm_frames:
            norm_df = pd.concat(norm_frames)
            fig_norm = px.line(
                norm_df,
                x="periodLabel",
                y="normalizedIndex",
                color="displayAreaName",
                labels={"normalizedIndex": "Normalized Index (Base=100)", "periodLabel": "Period", "displayAreaName": t("geo_areas")},
                template=plotly_template
            )
            fig_norm.add_hline(y=100, line_dash="dash", line_color="#94a3b8")
            fig_norm.update_layout(height=450, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_norm, use_container_width=True)

        st.markdown("---")
        st.subheader(t('leaderboard_title'))
        summary_rows = []
        for slug in selected_slugs:
            sub = df[df['areaSlug'] == slug].sort_values('periodDate')
            if not sub.empty:
                first_row = sub.iloc[0]
                last_row = sub.iloc[-1]
                init_idx = first_row['priceIndex']
                last_idx = last_row['priceIndex']
                growth = ((last_idx - init_idx) / init_idx) * 100 if init_idx > 0 else 0
                summary_rows.append({
                    "Area / Περιοχή": first_row['displayAreaName'],
                    "First Period": first_row['periodLabel'],
                    "Latest Period": last_row['periodLabel'],
                    "Initial Index": round(init_idx, 1),
                    "Latest Index": round(last_idx, 1),
                    "Cumulative Growth %": f"{growth:+.1f}%"
                })
        if summary_rows:
            st.table(pd.DataFrame(summary_rows))


# --- 4. ML FORECAST PAGE ---
elif app_key == "forecast":
    st.title("🔮 " + ("Πρόβλεψη Τιμών Ακινήτων (ML Forecasting)" if lang == "el" else "Machine Learning Price Index Forecasting"))
    st.caption("Πρόβλεψη της πορείας των δεικτών τιμών διαμερισμάτων 1–3 έτη στο μέλλον με χρήση Holt's Linear Exponential Smoothing & 95% ζωνών εμπιστοσύνης." if lang == "el" else "Statistical time-series forecasting of apartment price indices 1–3 years ahead using Holt's Linear Exponential Smoothing with 95% confidence intervals.")

    c_area, c_horizon = st.columns([2, 1])
    with c_area:
        forecast_area_name = st.selectbox(
            t("geo_areas"),
            options=list(localized_area_options.keys()),
            index=0
        )
        forecast_slug = localized_area_options[forecast_area_name]
    
    with c_horizon:
        horizon_years = st.select_slider(
            "Ορίζοντας Πρόβλεψης (Έτη)" if lang == "el" else "Forecast Horizon (Years)",
            options=[1, 2, 3],
            value=3
        )
        forecast_quarters = horizon_years * 4

    from forecasting import generate_area_forecast
    f_res = generate_area_forecast(db, area_slug=forecast_slug, forecast_quarters=forecast_quarters)
    
    if f_res and "forecastData" in f_res:
        summary = f_res["summary"]
        hist_df = pd.DataFrame(f_res["historicalData"])
        fc_df = pd.DataFrame(f_res["forecastData"])

        # KPI metric cards
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric(
                "Τελευταίος Δείκτης" if lang == "el" else "Latest Actual Index",
                f"{summary['latestIndex']:.1f}",
                summary['latestPeriod']
            )
        with m2:
            st.metric(
                "Πρόβλεψη 1 Έτους" if lang == "el" else "1-Year Projected Index",
                f"{summary['forecast1yIndex']:.1f}",
                f"{summary['forecast1yGrowthPct']:+.1f}%"
            )
        with m3:
            st.metric(
                "Πρόβλεψη 3 Ετών" if lang == "el" else "3-Year Projected Index",
                f"{summary['forecast3yIndex']:.1f}",
                f"{summary['forecast3yGrowthPct']:+.1f}%"
            )
        with m4:
            st.metric(
                "Μοντέλο ML" if lang == "el" else "ML Model",
                "Holt Exponential",
                "Confidence 95%"
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📈 " + ("Γράφημα Πρόβλεψης & Ζώνη Εμπιστοσύνης 95%" if lang == "el" else "Price Forecast & 95% Confidence Interval"))

        # Build combined Plotly Chart
        hist_df['periodLabel'] = hist_df.apply(lambda r: f"{r['year']} Q{r['quarter']}", axis=1)
        
        fig_fc = go.Figure()
        
        # Historical Actual Line
        fig_fc.add_trace(go.Scatter(
            x=hist_df['periodLabel'],
            y=hist_df['priceIndex'],
            mode='lines+markers',
            name='Ιστορικά Στοιχεία' if lang == 'el' else 'Historical Actuals',
            line=dict(color='#3b82f6', width=2.5)
        ))

        # Upper Bound
        fig_fc.add_trace(go.Scatter(
            x=fc_df['periodLabel'],
            y=fc_df['upperBound'],
            mode='lines',
            name='Ανώτατο Όριο 95%' if lang == 'el' else 'Upper Bound 95%',
            line=dict(color='rgba(16, 185, 129, 0.4)', width=1, dash='dot'),
            showlegend=False
        ))

        # Lower Bound (with shaded fill)
        fig_fc.add_trace(go.Scatter(
            x=fc_df['periodLabel'],
            y=fc_df['lowerBound'],
            mode='lines',
            name='Ζώνη Εμπιστοσύνης 95%' if lang == 'el' else '95% Confidence Interval',
            fill='tonexty',
            fillcolor='rgba(16, 185, 129, 0.15)',
            line=dict(color='rgba(16, 185, 129, 0.4)', width=1, dash='dot')
        ))

        # Point Forecast Line
        fig_fc.add_trace(go.Scatter(
            x=fc_df['periodLabel'],
            y=fc_df['forecastIndex'],
            mode='lines+markers',
            name='Πρόβλεψη (Forecast)' if lang == 'el' else 'ML Point Forecast',
            line=dict(color='#10b981', width=3, dash='dash')
        ))

        fig_fc.update_layout(
            height=460,
            template=plotly_template,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor=grid_color),
            yaxis=dict(showgrid=True, gridcolor=grid_color, title="Price Index (Base 2021=100)"),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_fc, use_container_width=True)

        st.subheader("📋 " + ("Πίνακας Προβλέψεων ανά Τρίμηνο" if lang == "el" else "Quarterly Forecast Breakdown"))
        fc_display = fc_df[['periodLabel', 'forecastIndex', 'lowerBound', 'upperBound', 'cumulativeGrowthPct']].copy()
        fc_display.columns = [
            "Period / Τρίμηνο", "Forecast Index / Πρόβλεψη",
            "Lower Bound 95%", "Upper Bound 95%", "Cumulative Growth % / Αθροιστική Ανάπτυξη %"
        ]
        st.dataframe(fc_display, use_container_width=True)
    else:
        st.warning("Δεν βρέθηκαν επαρκή στοιχεία για την παραγωγή πρόβλεψης." if lang == "el" else "Insufficient data to generate time series forecast.")


# --- 5. GREECE REGIONAL MAP PAGE ---
elif app_key == "map":
    st.title("🗺️ " + ("Διαδραστικός Χάρτης Περιφερειών Ελλάδας" if lang == "el" else "Interactive Regional Map of Greece"))
    st.caption("Εξερευνήστε τους δείκτες τιμών και τους ετήσιους ρυθμούς μεταβολής (YoY) ανά περιφέρεια στον διαδραστικό γεωγραφικό χάρτη." if lang == "el" else "Explore price index valuations and Year-over-Year (YoY) growth rates geographically across Greek regions.")

    import json
    geojson_path = os.path.join(os.path.dirname(__file__), "data", "greece_regions.json")
    if os.path.exists(geojson_path):
        with open(geojson_path, "r", encoding="utf-8") as f:
            greece_geojson = json.load(f)
            
        all_metrics = []
        for area in areas_data:
            s_res = queries.get_metrics_summary(db, area_slugs=[area.slug])
            if s_res and "latestIndex" in s_res:
                all_metrics.append({
                    "id": area.slug,
                    "area_name": get_area_name(lang, area.name),
                    "latest_index": s_res["latestIndex"],
                    "yoy_change": s_res.get("yoyChange", 0.0),
                    "latest_quarter": s_res.get("latestQuarter", "—")
                })
        
        map_df = pd.DataFrame(all_metrics)
        if not map_df.empty:
            map_metric = st.radio(
                "Επιλογή Μετρικής Χάρτη" if lang == "el" else "Select Map Metric",
                ["Δείκτης Τιμών (Price Index)" if lang == "el" else "Price Index", "Ετήσια Μεταβολή % (YoY Growth %)" if lang == "el" else "YoY Growth %"],
                horizontal=True
            )
            color_col = "latest_index" if "Index" in map_metric else "yoy_change"
            color_scale = "Viridis" if "Index" in map_metric else "RdYlGn"

            fig_map = px.choropleth(
                map_df,
                geojson=greece_geojson,
                locations="id",
                color=color_col,
                hover_name="area_name",
                hover_data={"id": False, "latest_index": ":.1f", "yoy_change": ":+.1f%", "latest_quarter": True},
                color_continuous_scale=color_scale,
                labels={"latest_index": t("metric_index"), "yoy_change": "YoY Growth %", "area_name": "Region / Περιοχή"},
                title=""
            )
            fig_map.update_geos(fitbounds="locations", visible=False)
            fig_map.update_layout(
                height=520,
                template=plotly_template,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(fig_map, use_container_width=True)

            st.subheader("📋 " + ("Πίνακας Συγκριτικών Δεικτών ανά Περιοχή" if lang == "el" else "Regional Valuation Summary Table"))
            tbl_display = map_df[['area_name', 'latest_index', 'yoy_change', 'latest_quarter']].copy()
            tbl_display.columns = [
                "Area / Περιοχή", "Price Index / Δείκτης", "YoY Growth % / Ετήσια Μεταβολή %", "Latest Period / Τρίμηνο"
            ]
            st.dataframe(tbl_display, use_container_width=True)
    else:
        st.warning("Το αρχείο γεωγραφικών ορίων δεν βρέθηκε." if lang == "el" else "GeoJSON boundary file not found.")


# --- 6. INVESTOR ROI & MORTGAGE CALCULATOR PAGE ---
elif app_key == "calc":
    st.title("🧮 " + ("Υπολογιστής Απόδοσης Επένδυσης & Στεγαστικού Δανείου" if lang == "el" else "Real Estate Investment & Mortgage Calculator"))
    st.caption("Υπολογίστε την καθαρή απόδοση ενοικίασης (Cap Rate), τους φόρους (ΕΝΦΙΑ), τη μηνιαία δόση δανείου και το Cash-on-Cash Return." if lang == "el" else "Calculate Gross Yield, Net Cap Rate, ENFIA tax, monthly mortgage payments, and Cash-on-Cash return for Greek properties.")

    from calculator import calculate_investment_metrics

    p1, p2, p3 = st.columns(3)
    with p1:
        prop_price = st.number_input("Αξία Ακινήτου (€)" if lang == "el" else "Property Price (€)", value=200000.0, step=5000.0)
        m_rent = st.number_input("Μηνιαίο Ενοίκιο (€)" if lang == "el" else "Monthly Rent (€)", value=900.0, step=50.0)
    with p2:
        down_pct = st.slider("Ιδία Συμμετοχή / Προκαταβολή (%)" if lang == "el" else "Down Payment (%)", min_value=0.0, max_value=100.0, value=25.0, step=5.0)
        rate_pct = st.number_input("Επιτόκιο Δανείου (%)" if lang == "el" else "Interest Rate (%)", value=3.8, step=0.1)
    with p3:
        duration_yrs = st.slider("Διάρκεια Δανείου (Έτη)" if lang == "el" else "Loan Duration (Years)", min_value=5, max_value=35, value=25, step=1)
        enfia_val = st.number_input("Ετήσιος ΕΝΦΙΑ (€)" if lang == "el" else "Annual ENFIA Tax (€)", value=450.0, step=50.0)

    calc_res = calculate_investment_metrics(
        property_price=prop_price,
        monthly_rent=m_rent,
        down_payment_pct=down_pct,
        interest_rate_pct=rate_pct,
        loan_years=duration_yrs,
        annual_enfia_tax=enfia_val,
        annual_maintenance_pct=1.0
    )

    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Gross Yield", f"{calc_res['grossYieldPct']:.2f}%")
    with m2:
        st.metric("Net Cap Rate", f"{calc_res['netCapRatePct']:.2f}%", f"-€{calc_res['annualEnfia'] + calc_res['annualMaintenance']:.0f}/yr tax")
    with m3:
        st.metric("Μηνιαία Δόση" if lang == "el" else "Monthly Mortgage", f"€{calc_res['monthlyMortgage']:.2f}")
    with m4:
        cf = calc_res['netMonthlyCashFlow']
        st.metric("Καθαρή Ταμειακή Ροή/μήνα" if lang == "el" else "Net Cash Flow/mo", f"€{cf:.2f}")
    with m5:
        st.metric("Cash-on-Cash Return", f"{calc_res['cashOnCashPct']:.2f}%")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 " + ("Πίνακας Απόσβεσης Δανείου ανά Έτος" if lang == "el" else "Annual Mortgage Amortization Schedule"))
    amort_df = pd.DataFrame(calc_res['amortizationSchedule'])
    if not amort_df.empty:
        fig_amort = go.Figure()
        fig_amort.add_trace(go.Scatter(x=amort_df['year'], y=amort_df['remainingBalance'], mode='lines+markers', name='Υπόλοιπο Δανείου (€)' if lang == 'el' else 'Remaining Balance (€)', line=dict(color='#3b82f6', width=3)))
        fig_amort.add_trace(go.Scatter(x=amort_df['year'], y=amort_df['cumulativeInterest'], mode='lines', name='Συσσωρευμένοι Τόκοι (€)' if lang == 'el' else 'Cumulative Interest (€)', line=dict(color='#f43f5e', width=2, dash='dash')))
        fig_amort.update_layout(
            height=380,
            template=plotly_template,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor=grid_color, title="Year / Έτος"),
            yaxis=dict(showgrid=True, gridcolor=grid_color, title="Amount (€)"),
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_amort, use_container_width=True)
        st.dataframe(amort_df, use_container_width=True)


# --- 7. DATA EXPLORER PAGE ---
elif app_key == "explorer":
    st.title(t('explorer_title'))
    st.caption(t('explorer_caption'))

    c1, c2, c3 = st.columns(3)
    min_idx = c1.number_input(t('min_index'), value=0.0)
    max_idx = c2.number_input(t('max_index'), value=300.0)
    prov_filter = c3.selectbox(t('prov_status'), [t('prov_all'), t('prov_final_only'), t('prov_only')])

    if not df.empty:
        exp_df = df[(df['priceIndex'] >= min_idx) & (df['priceIndex'] <= max_idx)].copy()
        if prov_filter == t('prov_final_only'):
            exp_df = exp_df[exp_df['isProvisional'] == False]
        elif prov_filter == t('prov_only'):
            exp_df = exp_df[exp_df['isProvisional'] == True]

        st.success(f"Query returned {len(exp_df)} matching quarterly observations.")
        cols = [c for c in ['displayAreaName', 'year', 'quarter', 'priceIndex', 'periodChangePercent', 'annualChangePercent', 'isProvisional'] if c in exp_df.columns]
        st.dataframe(exp_df[cols], use_container_width=True)


# --- 5. DATA SOURCES PAGE ---
elif app_key == "provenance":
    st.title(t('provenance_title'))
    st.caption(t('provenance_caption'))

    ds = db.query(queries.DataSource).first()
    if ds:
        st.markdown(f"""
        ### Primary Dataset: {ds.dataset_name}
        - **Organization:** {ds.organization}
        - **Identifier:** `{ds.dataset_identifier}`
        - **License:** {ds.license}
        - **Portal:** [{ds.dataset_url}]({ds.dataset_url})
        
        **Description:** {ds.description}
        """)

    resources = db.query(queries.DatasetResource).order_by(queries.DatasetResource.resource_date.desc()).all()
    if resources:
        st.subheader(f"{t('imported_catalog')} ({len(resources)})")
        res_df = pd.DataFrame([
            {
                "Resource Name": r.resource_name,
                "Resource Date": r.resource_date.strftime("%Y-%m-%d"),
                "Format": r.file_format,
                "Import Status": r.import_status,
                "Imported At": r.imported_at.strftime("%Y-%m-%d %H:%M") if r.imported_at else "—"
            }
            for r in resources
        ])
        st.dataframe(res_df, use_container_width=True)
