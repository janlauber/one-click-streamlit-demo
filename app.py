from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# Constants
API_URL = "https://aareguru.existenz.ch/v2018/current"
APP_NAME = "my.app.ch"
APP_VERSION = "1.0.42"
CITIES = ["bern", "thun", "biel", "solothurn", "aarau", "brugg", "augsburg", "konstanz"]

# Set page configuration
st.set_page_config(
    page_title="Aare Monitoring Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>

"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Function to fetch Aare river data
def fetch_aare_data(city):
    params = {
        "city": city,
        "app": APP_NAME,
        "version": APP_VERSION
    }
    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        return {city: response.json()}
    else:
        return {city: None}

# Fetch data for all cities using multithreading
@st.cache_data(ttl=600)
def fetch_all_data(cities):
    data = {}
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(fetch_aare_data, cities))
        for result in results:
            data.update(result)
    return data

# Title and description
st.title("Aare Real-time Monitoring Dashboard Test")
st.write("Monitor real-time conditions of the Aare river across multiple cities powered by aare.guru.")

# Sidebar for city selection and date input
# st.sidebar.title("Select a City")

# Display loading animation while fetching data
with st.spinner("Fetching data... 🌊💧"):
    data = fetch_all_data(CITIES)

# Alerts for specific conditions
alert_temp_threshold = st.sidebar.number_input("Set temperature alert threshold (°C)", value=18)
alert_flow_threshold = st.sidebar.number_input("Set flow rate alert threshold (m³/s)", value=180)

temperature_alerts = []
flow_rate_alerts = []
current_data = []
for city in CITIES:
    city_data = data.get(city)
    if city_data:
        temperature = city_data.get("aare", {}).get("temperature", "N/A")
        flow_rate = city_data.get("aare", {}).get("flow", "N/A")
        current_data.append({"City": city.capitalize(), "Temperature (°C)": temperature, "Flow Rate (m³/s)": flow_rate})
        if temperature != "N/A" and temperature > alert_temp_threshold:
            temperature_alerts.append((city.capitalize(), temperature))
        if flow_rate != "N/A" and flow_rate > alert_flow_threshold:
            flow_rate_alerts.append((city.capitalize(), flow_rate))
            
st.sidebar.header("Alerts")
if temperature_alerts or flow_rate_alerts:
    if temperature_alerts:
        st.sidebar.subheader("Temperature Alerts")
        for alert in temperature_alerts:
            st.sidebar.warning(f"{alert[0]}: {alert[1]} °C", icon="🔥")
    if flow_rate_alerts:
        st.sidebar.subheader("Flow Rate Alerts")
        for alert in flow_rate_alerts:
            st.sidebar.info(f"{alert[0]}: {alert[1]} m³/s", icon="🌊")

# Display charts instead of table
current_df = pd.DataFrame(current_data)

# Temperature comparison chart
st.subheader("Temperature Comparison")
fig_temp = px.bar(current_df, x="City", y="Temperature (°C)", color="City", title="Current Temperature Comparison")
st.plotly_chart(fig_temp, use_container_width=True)

# Flow rate comparison chart
st.subheader("Flow Rate Comparison")
fig_flow = px.bar(current_df, x="City", y="Flow Rate (m³/s)", color="City", title="Current Flow Rate Comparison")
st.plotly_chart(fig_flow, use_container_width=True)

# Historical data line chart
st.subheader("Historical Data Comparison")
fig_hist = px.line(current_df, x="City", y=["Temperature (°C)", "Flow Rate (m³/s)"], title="Historical Data Comparison", markers=True)
st.plotly_chart(fig_hist, use_container_width=True)
