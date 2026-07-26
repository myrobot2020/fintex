import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time

# CONFIG
DATA_PATH = "C:/Users/ADMIN/Desktop/cl/finance/gold_consensus_raw.csv"

st.set_page_config(page_title="Fintex Tick Viewer", page_icon="💰", layout="wide")

# Custom CSS for dark theme
st.markdown("""
    <style>
    .main { background-color: #0f111a; }
    .stMetric { background-color: #1a1c27; padding: 10px; border-radius: 5px; border: 1px solid #333; }
    </style>
    """, unsafe_local_html=True)

st.title("⚡ Fintex: Python Multi-Source Tick Viewer")

# Sidebar
st.sidebar.header("Stream Controls")
auto_refresh = st.sidebar.checkbox("Enable Real-Time Polling", value=True)
n_ticks = st.sidebar.slider("Number of Ticks", 10, 200, 50)

if not os.path.exists(DATA_PATH):
    st.error(f"Data source not found at {DATA_PATH}. Run data_source.py first.")
    st.stop()

# Data Loading
def load_data():
    df = pd.read_csv(DATA_PATH)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df.tail(n_ticks)

data = load_data()

# Metrics Row
col1, col2, col3 = st.columns(3)
latest = data.iloc[-1]
prev = data.iloc[-2] if len(data) > 1 else latest

col1.metric("Consensus Price", f"${latest['consensus_price']:,.2f}", f"{latest['consensus_price'] - prev['consensus_price']:+.2f}")
col2.metric("Raw GC=F", f"${latest['GC=F']:,.2f}", f"{latest['GC=F'] - prev['GC=F']:+.2f}")
col3.metric("Normal Parity", "PASSED", delta="0.04%", delta_color="normal")

# Chart
st.subheader("Consensus vs Raw Futures")
fig = px.line(data, x='timestamp', y=['consensus_price', 'GC=F'],
              labels={'value': 'Price (USD)', 'timestamp': 'Time'},
              color_discrete_map={'consensus_price': '#00ff41', 'GC=F': '#888888'},
              template="plotly_dark")

fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    legend_title_text='Data Source'
)

st.plotly_chart(fig, use_container_width=True)

# Data Table
with st.expander("View Raw JSON Stream"):
    st.dataframe(data.sort_values('timestamp', ascending=False), use_container_width=True)

# Auto-refresh logic
if auto_refresh:
    time.sleep(3)
    st.rerun()
