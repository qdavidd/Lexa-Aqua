"""
HYDROSAFE — Real-time water quality alerts for irrigation farmers.
CASSINI Hackathon 11 demo dashboard.
"""
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(
    page_title="HYDROSAFE",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #065A82;
        margin-bottom: 0;
    }
    .tagline {
        font-style: italic;
        color: #1C7293;
        font-size: 1.2rem;
        margin-top: 0;
    }
    .alert-high {
        background-color: #FEE2E2;
        border-left: 4px solid #DC2626;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .alert-med {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .alert-ok {
        background-color: #D1FAE5;
        border-left: 4px solid #059669;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .sms-bubble {
        background: #065A82;
        color: white;
        padding: 1rem 1.2rem;
        border-radius: 1rem;
        font-family: -apple-system, sans-serif;
        margin: 0.5rem 0;
    }
    .sms-header {
        color: #01BAEF;
        font-weight: bold;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    .sms-meta {
        color: #94A3B8;
        font-size: 0.75rem;
        margin-top: 0.5rem;
        text-align: center;
    }
    div[data-testid="stMetricValue"] {
        color: #065A82;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# --- Mock data ---
@st.cache_data
def get_pump_points():
    return pd.DataFrame([
        {"id": "PP001", "fermier": "Cooperativa Brăila Sud",
         "sector": "Dunăre km 165", "lat": 45.27, "lng": 27.97,
         "risk": "HIGH", "score": 87, "chl_a": 42.1, "spm": 38,
         "last_alert": "2024-05-18 06:14"},
        {"id": "PP002", "fermier": "Asociația Galați Est",
         "sector": "Dunăre km 145", "lat": 45.43, "lng": 28.03,
         "risk": "HIGH", "score": 81, "chl_a": 38.5, "spm": 41,
         "last_alert": "2024-05-18 06:14"},
        {"id": "PP003", "fermier": "Ferma BIO Tulcea",
         "sector": "Dunăre km 80 (Brațul Sf. Gheorghe)",
         "lat": 45.18, "lng": 28.79,
         "risk": "MEDIUM", "score": 58, "chl_a": 22.0, "spm": 19,
         "last_alert": "2024-05-15 11:20"},
        {"id": "PP004", "fermier": "Ion Petrescu (individual)",
         "sector": "Mureș km 320", "lat": 46.55, "lng": 24.55,
         "risk": "HIGH", "score": 91, "chl_a": 51.0, "spm": 45,
         "last_alert": "2024-05-17 08:42"},
        {"id": "PP005", "fermier": "Cooperativa Aiud-Mureș",
         "sector": "Mureș km 280", "lat": 46.31, "lng": 23.72,
         "risk": "MEDIUM", "score": 62, "chl_a": 25.3, "spm": 22,
         "last_alert": "2024-05-16 14:00"},
        {"id": "PP006", "fermier": "Ferma Argeș Vest",
         "sector": "Argeș km 45", "lat": 44.65, "lng": 25.45,
         "risk": "OK", "score": 18, "chl_a": 8.2, "spm": 7,
         "last_alert": None},
        {"id": "PP007", "fermier": "Asociația Olt Sud",
         "sector": "Olt km 110", "lat": 44.21, "lng": 24.42,
         "risk": "MEDIUM", "score": 55, "chl_a": 19.1, "spm": 18,
         "last_alert": "2024-05-16 09:15"},
        {"id": "PP008", "fermier": "Cooperativa Călărași",
         "sector": "Dunăre km 380", "lat": 44.20, "lng": 27.33,
         "risk": "OK", "score": 22, "chl_a": 9.5, "spm": 8,
         "last_alert": None},
        {"id": "PP009", "fermier": "Ferma Siret Pașcani",
         "sector": "Siret km 215", "lat": 47.25, "lng": 26.73,
         "risk": "OK", "score": 15, "chl_a": 7.0, "spm": 6,
         "last_alert": None},
        {"id": "PP010", "fermier": "Cooperativa Crișana",
         "sector": "Crișul Repede km 88", "lat": 47.05, "lng": 21.95,
         "risk": "OK", "score": 27, "chl_a": 11.2, "spm": 10,
         "last_alert": None},
    ])


def risk_color(level):
    return {"HIGH": "#DC2626", "MEDIUM": "#F59E0B", "OK": "#059669"}[level]


def make_history(pump_id, current_chl):
    """Generate 30-day chl-a history with a spike near the end for HIGH risk."""
    rng = np.random.RandomState(hash(pump_id) % 2**31)
    days = pd.date_range(end=datetime(2024, 5, 18), periods=30)
    base = rng.normal(8, 3, 30).clip(2, None)
    if current_chl > 30:
        base[-5:] = base[-5:] + np.linspace(5, current_chl - 8, 5)
    elif current_chl > 18:
        base[-3:] = base[-3:] + np.linspace(3, current_chl - 8, 3)
    return pd.DataFrame({"data": days, "chl_a": base})


# --- Header ---
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown("# 💧")
with col_title:
    st.markdown('<p class="main-header">HYDROSAFE</p>',
                unsafe_allow_html=True)
    st.markdown('<p class="tagline">Apă curată pentru fiecare recoltă.</p>',
                unsafe_allow_html=True)

st.divider()

# --- Sidebar ---
with st.sidebar:
    st.markdown("### Filtre")
    river = st.selectbox(
        "Râu",
        ["Toate", "Dunăre", "Mureș", "Argeș", "Olt", "Siret", "Crișul Repede"]
    )
    risk_filter = st.multiselect(
        "Nivel risc",
        ["HIGH", "MEDIUM", "OK"],
        default=["HIGH", "MEDIUM", "OK"]
    )
    date = st.date_input("Data analiză", datetime(2024, 5, 18))

    st.divider()
    st.markdown("### Date Sentinel")
    st.markdown("**Sursă:** Sentinel-3 OLCI · Sentinel-2 MSI")
    st.markdown("**Update:** la 12 ore")
    st.markdown("**Acoperire:** 8 râuri principale RO")

    st.divider()
    st.markdown("### Despre")
    st.caption(
        "HYDROSAFE detectează în timp real evenimente de poluare pe râurile "
        "din care fermierii pompează apă pentru irigație. Folosește exclusiv "
        "date Copernicus publice și gratuite."
    )
    st.caption(
        "Demo CASSINI Hackathon 11 — Space for Water (24-26 Aprilie 2026)"
    )

# --- KPI metrics ---
df = get_pump_points()
df_filtered = df[df["risk"].isin(risk_filter)].copy()
if river != "Toate":
    df_filtered = df_filtered[df_filtered["sector"].str.contains(river)]

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Pump points active", len(df), delta="+12 săpt. trecută")
with c2:
    high_count = len(df[df["risk"] == "HIGH"])
    st.metric("HIGH risk azi", high_count, delta=f"-3 vs ieri",
              delta_color="inverse")
with c3:
    st.metric("SMS trimise săpt.", "1.842", delta="+218")
with c4:
    st.metric("Recolte salvate (est.)", "€ 47.300",
              delta="+€ 8.200")

st.divider()

# --- Map + alerts side by side ---
col_map, col_alerts = st.columns([2, 1])

with col_map:
    st.subheader("Hartă pump points monitorizate")

    m = folium.Map(location=[45.9, 25.5], zoom_start=6, tiles="cartodbpositron")

    for _, row in df_filtered.iterrows():
        color = risk_color(row["risk"])
        popup_html = f"""
        <div style='font-family: sans-serif; min-width: 220px;'>
            <h4 style='margin:0; color:{color};'>{row['risk']}</h4>
            <p style='margin:4px 0;'><b>{row['sector']}</b></p>
            <p style='margin:4px 0; font-size: 0.85em;'>{row['fermier']}</p>
            <hr style='margin:6px 0;'>
            <p style='margin:2px 0;'>Score risc: <b>{row['score']}/100</b></p>
            <p style='margin:2px 0;'>Chl-a: <b>{row['chl_a']:.1f} mg/m³</b></p>
            <p style='margin:2px 0;'>SPM: <b>{row['spm']} mg/L</b></p>
        </div>
        """
        folium.CircleMarker(
            location=[row["lat"], row["lng"]],
            radius=10,
            popup=folium.Popup(popup_html, max_width=300),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.8,
            weight=2,
            tooltip=f"{row['sector']} — {row['risk']}",
        ).add_to(m)

    # Major Romanian rivers — geographically accurate paths
    rivers_geom = {
        "Dunăre": {
            "color": "#065A82", "weight": 4,
            "path": [
                [44.62, 22.66], [44.31, 22.69], [44.15, 22.93],
                [43.99, 22.94], [43.78, 23.95], [43.74, 24.50],
                [43.66, 25.37], [43.90, 25.97], [44.08, 26.63],
                [44.20, 27.33], [44.34, 28.03], [44.69, 27.95],
                [45.27, 27.97], [45.43, 28.04], [45.18, 28.79],
                [45.15, 29.66]
            ]
        },
        "Mureș": {
            "color": "#1C7293", "weight": 3,
            "path": [
                [46.92, 25.36], [46.78, 24.71], [46.55, 24.55],
                [46.31, 23.72], [46.07, 23.58], [45.88, 22.91],
                [46.09, 21.69], [46.18, 21.32]
            ]
        },
        "Olt": {
            "color": "#1C7293", "weight": 3,
            "path": [
                [45.82, 25.79], [45.65, 24.97], [45.10, 24.37],
                [44.43, 24.36], [44.02, 24.36], [43.74, 24.50]
            ]
        },
        "Argeș": {
            "color": "#1C7293", "weight": 3,
            "path": [
                [45.21, 24.69], [44.84, 24.94], [44.65, 25.45],
                [44.40, 25.83], [44.42, 26.10], [44.08, 26.63]
            ]
        },
        "Siret": {
            "color": "#1C7293", "weight": 3,
            "path": [
                [47.62, 26.10], [47.25, 26.73], [46.92, 26.93],
                [46.55, 26.92], [46.05, 26.92], [45.65, 27.45],
                [45.43, 28.04]
            ]
        },
        "Crișul Repede": {
            "color": "#1C7293", "weight": 3,
            "path": [
                [46.91, 22.99], [47.05, 21.95], [47.07, 21.50],
                [47.04, 21.39]
            ]
        },
    }
    for rname, rinfo in rivers_geom.items():
        folium.PolyLine(
            rinfo["path"],
            color=rinfo["color"], weight=rinfo["weight"], opacity=0.55,
            tooltip=rname
        ).add_to(m)

    st_folium(m, width=None, height=480, returned_objects=[])

with col_alerts:
    st.subheader("Alerte active")

    high_pumps = df_filtered[df_filtered["risk"] == "HIGH"]
    med_pumps = df_filtered[df_filtered["risk"] == "MEDIUM"]

    for _, row in high_pumps.iterrows():
        st.markdown(
            f"""
            <div class='alert-high'>
                <b style='color: #DC2626;'>🚨 HIGH — {row['sector']}</b><br>
                <span style='font-size: 0.9em;'>{row['fermier']}</span><br>
                <span style='font-size: 0.8em; color: #6B7280;'>
                    Score: {row['score']}/100 · Alert trimis: {row['last_alert']}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    for _, row in med_pumps.iterrows():
        st.markdown(
            f"""
            <div class='alert-med'>
                <b style='color: #B45309;'>⚠️ MEDIUM — {row['sector']}</b><br>
                <span style='font-size: 0.9em;'>{row['fermier']}</span><br>
                <span style='font-size: 0.8em; color: #6B7280;'>
                    Score: {row['score']}/100 · Monitorizat
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

st.divider()

# --- Detail section: chart + SMS preview ---
st.subheader("Detaliu sector")
selected = st.selectbox(
    "Selectează un sector pentru analiză",
    df["sector"].tolist(),
    index=3,  # Mureș km 320 (HIGH)
)
selected_row = df[df["sector"] == selected].iloc[0]

c5, c6 = st.columns([2, 1])

with c5:
    st.markdown(f"**{selected_row['fermier']}** — Score risc: "
                f"**{selected_row['score']}/100** ({selected_row['risk']})")
    history = make_history(selected_row["id"], selected_row["chl_a"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=history["data"], y=history["chl_a"],
        mode="lines+markers",
        line=dict(color="#065A82", width=3),
        marker=dict(size=6, color="#01BAEF"),
        name="Clorofila-a",
    ))
    fig.add_hline(y=20, line_dash="dot", line_color="#F59E0B",
                  annotation_text="Prag MEDIUM", annotation_position="right")
    fig.add_hline(y=30, line_dash="dot", line_color="#DC2626",
                  annotation_text="Prag HIGH", annotation_position="right")
    fig.update_layout(
        title="Evoluția clorofilei-a (30 zile) — Sentinel-3 OLCI",
        xaxis_title="Data",
        yaxis_title="Chl-a (mg/m³)",
        height=350,
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#E5E7EB")
    fig.update_yaxes(showgrid=True, gridcolor="#E5E7EB")
    st.plotly_chart(fig, use_container_width=True)

with c6:
    st.markdown("**Mesaj SMS generat**")
    if selected_row["risk"] == "HIGH":
        sms_text = (
            f"ALERTĂ: Risc MARE de poluare pe "
            f"{selected_row['sector']}.<br><br>"
            f"Detectat val poluare amonte (Chl-a: "
            f"{selected_row['chl_a']:.1f} mg/m³, peste pragul HIGH).<br><br>"
            f"NU pompa în 72h. Vom reveni cu update."
        )
    elif selected_row["risk"] == "MEDIUM":
        sms_text = (
            f"Atenție: poluare moderată pe {selected_row['sector']}.<br><br>"
            f"Chl-a: {selected_row['chl_a']:.1f} mg/m³.<br><br>"
            f"Recomandare: amână pomparea 24-48h dacă poți."
        )
    else:
        sms_text = (
            f"OK: apa pe {selected_row['sector']} e în parametri.<br><br>"
            f"Chl-a: {selected_row['chl_a']:.1f} mg/m³.<br><br>"
            f"Pompare sigură."
        )

    st.markdown(
        f"""
        <div class='sms-bubble'>
            <div class='sms-header'>HYDROSAFE</div>
            {sms_text}
        </div>
        <div class='sms-meta'>
            Astăzi · {datetime.now().strftime("%H:%M")} · +40 7XX XXX XXX
        </div>
        """,
        unsafe_allow_html=True
    )

# --- Footer ---
st.divider()
st.caption(
    "💧 HYDROSAFE — Demo CASSINI Hackathon 11 · Space for Water · "
    "Date: Copernicus Sentinel-2/-3 (CC-BY) · Surse: EEA, ANIF, ANAR · "
    "Realizat cu Streamlit + Folium + Plotly"
)
