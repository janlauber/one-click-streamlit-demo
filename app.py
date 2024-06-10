import time
from concurrent.futures import ThreadPoolExecutor

import folium
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from streamlit_folium import folium_static

# Constants
API_URL = "https://aareguru.existenz.ch/v2018/current"
APP_NAME = "my.app.ch"
APP_VERSION = "1.0.42"
CITIES = ["bern", "thun", "biel", "solothurn", "aarau", "brugg", "augsburg", "konstanz"]
CITY_COORDINATES = {
    "bern": [46.94809, 7.44744],
    "thun": [46.75736, 7.62798],
    "biel": [47.13236, 7.24411],
    "solothurn": [47.20883, 7.53298],
    "aarau": [47.39254, 8.04422],
    "brugg": [47.48413, 8.20826],
    "augsburg": [48.37054, 10.89779],
    "konstanz": [47.66374, 9.17582]
}

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
st.title("Aare River Real-time Monitoring Dashboard")
st.write("Monitor real-time conditions of the Aare river across multiple cities.")

# Sidebar for city selection and date input
st.sidebar.title("Select a City")

# Display loading animation while fetching data
with st.spinner("Fetching data... 🌊💧"):
    data = fetch_all_data(CITIES)

# Alerts for specific conditions
alert_temp_threshold = st.sidebar.number_input("Set temperature alert threshold (°C)", value=18)
alert_flow_threshold = st.sidebar.number_input("Set flow rate alert threshold (m³/s)", value=150)

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

# Display alerts at the top
st.header("Alerts")
if temperature_alerts or flow_rate_alerts:
    if temperature_alerts:
        st.subheader("Temperature Alerts")
        for alert in temperature_alerts:
            st.warning(f"Temperature alert in {alert[0]}: {alert[1]} °C", icon="🔥")
    if flow_rate_alerts:
        st.subheader("Flow Rate Alerts")
        for alert in flow_rate_alerts:
            st.error(f"Flow rate alert in {alert[0]}: {alert[1]} m³/s", icon="🌊")
else:
    st.write("No alerts")

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

# Display alerts on the map
m = folium.Map(location=[46.8182, 8.2275], zoom_start=8, tiles='cartodb positron')  # Centered on Switzerland, using a modern tile layer

# Function to determine the marker color
def get_marker_color(city, temperature, flow_rate):
    if (city.capitalize(), temperature) in temperature_alerts:
        return 'orange'
    elif (city.capitalize(), flow_rate) in flow_rate_alerts:
        return 'red'
    else:
        return 'blue'

for city in CITIES:
    city_data = data.get(city)
    if city_data:
        temperature = city_data.get("aare", {}).get("temperature", "N/A")
        flow_rate = city_data.get("aare", {}).get("flow", "N/A")
        marker_color = get_marker_color(city, temperature, flow_rate)
        folium.Marker(
            CITY_COORDINATES[city],
            popup=folium.Popup(html=f"<b>{city.capitalize()}</b><br>Temp: {temperature} °C<br>Flow: {flow_rate} m³/s", max_width=200),
            icon=folium.Icon(color=marker_color, icon='info-sign')
        ).add_to(m)

# Optimize map for mobile
st.subheader("Alerts Map")
folium_static(m, width=800, height=400)
