import streamlit as st
import pandas as pd
from streamlit_folium import st_folium

from services.graph_builder import load_transit_data
from algorithm.dijkstra import find_optimal_route
from utils.map_visualization import create_route_map

# 1. Page Configuration
st.set_page_config(
    page_title="Trichy AI Bus Route & Rendezvous Planner",
    page_icon="🚌",
    layout="wide"
)

# 2. Main Header
st.title("🚌 Trichy Context-Aware AI Bus Route Planner")
st.subheader("Multi-Objective Dijkstra | Safe Transfers | Friends Rendezvous | Live Weather AI")
st.markdown("---")

# Load Stops Data for Dropdowns
stops_df, _ = load_transit_data()
stop_options = {row['stop_name']: row['stop_id'] for _, row in stops_df.iterrows()}

# 3. Sidebar Controls
st.sidebar.header("⚙️ AI Routing Controls")
routing_mode = st.sidebar.radio(
    "Select Commuter Mode:",
    [
        "👤 Single Commuter (A to B)",
        "👥 Friends Gang Meet-Up (Multi-Source Convergence)"
    ]
)

optimization_goal = st.sidebar.selectbox(
    "AI Optimization Priority:",
    [
        "⚡ Fastest Journey (Time Optimized)",
        "📏 Shortest Distance (Km Optimized)",
        "🎫 Student / Govt Free Pass Mode (Cost Optimized)"
    ]
)

# Map optimization metric selection
metric_map = {
    "⚡ Fastest Journey (Time Optimized)": "base_time_mins",
    "📏 Shortest Distance (Km Optimized)": "distance_km",
    "🎫 Student / Govt Free Pass Mode (Cost Optimized)": "fare_rs"
}
selected_metric = metric_map[optimization_goal]

st.markdown("### 📍 Select Journey Points")
col_s1, col_s2 = st.columns(2)

with col_s1:
    source_name = st.selectbox("Starting Bus Stop:", list(stop_options.keys()), index=0)
with col_s2:
    destination_default_index = 2 if len(stop_options) > 2 else 0
    target_name = st.selectbox("Destination Bus Stop:", list(stop_options.keys()), index=destination_default_index)

source_id = stop_options[source_name]
target_id = stop_options[target_name]

# 4. Automatic Route Calculation on Input Change
current_inputs = (source_id, target_id, selected_metric)

if 'last_inputs' not in st.session_state or st.session_state.last_inputs != current_inputs:
    if source_id == target_id:
        st.session_state.route_result = {
            'success': False, 
            'error': 'Starting location and destination cannot be the same. Please select different stops.'
        }
    else:
        st.session_state.route_result = find_optimal_route(source_id, target_id, optimization_metric=selected_metric)
    st.session_state.last_inputs = current_inputs

# 5. Display Results
result = st.session_state.get('route_result', None)

if result and result['success']:
    st.success(f"✅ Optimal Path Found Successfully using Dijkstra's Algorithm ({optimization_goal})!")
    
    # Metrics Dashboard
    total_time_calc = sum(s['time_mins'] for s in result['route_details'])
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Estimated Time", f"{total_time_calc} mins")
    with m2:
        st.metric("Total Distance", f"{result['total_distance_km']} km")
    with m3:
        st.metric("Estimated Total Fare", f"₹ {result['total_fare_rs']}")
    with m4:
        st.metric("Stops Count", f"{len(result['path_nodes'])} Stops")
        
    st.markdown("---")
    
    # Two-column layout: Route details table & Interactive Map
    col_left, col_right = st.columns([1, 1.2])
    
    with col_left:
        st.subheader("📋 Step-by-Step Boarding Guide")
        for idx, step in enumerate(result['route_details'], 1):
            pass_badge = "🟢 Govt Free Pass OK" if step['govt_free_pass'] else "🔴 Paid Private Bus"
            st.markdown(
                f"""
                **Step {idx}: Board Bus `{step['bus_number']}`**  
                * From: **{step['from_stop_name']}**  
                * To: **{step['to_stop_name']}**  
                * 🕒 {step['time_mins']} mins | 🛣️ {step['distance_km']} km | 💵 ₹{step['fare_rs']}  
                * *Status:* {pass_badge}
                """
            )
            st.markdown("---")
            
    with col_right:
        st.subheader("🗺️ Interactive Route Map (OpenStreetMap)")
        route_map = create_route_map(stops_df, result['route_details'], result['path_nodes'])
        st_folium(route_map, width=650, height=450, returned_objects=[])
else:
    err_msg = result['error'] if result else "Please select valid distinct stops."
    st.warning(f"⚠️ {err_msg}")