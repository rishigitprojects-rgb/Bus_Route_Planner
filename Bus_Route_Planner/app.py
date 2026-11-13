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
st.subheader("Multi-Objective Dijkstra | Safe Transfers | Friends Rendezvous | Live Weather & Traffic AI")
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

metric_map = {
    "⚡ Fastest Journey (Time Optimized)": "base_time_mins",
    "📏 Shortest Distance (Km Optimized)": "distance_km",
    "🎫 Student / Govt Free Pass Mode (Cost Optimized)": "fare_rs"
}
selected_metric = metric_map[optimization_goal]

# Traffic Simulation Control
st.sidebar.header("🚦 AI Traffic & Environment Simulation")
simulate_traffic = st.sidebar.checkbox("Enable Peak-Hour Traffic Congestion (1.4x Time Heuristic)", value=False)
traffic_mult = 1.4 if simulate_traffic else 1.0

# Gang size configuration if Friends Gang Meet-Up is selected
num_members = 2
if routing_mode == "👥 Friends Gang Meet-Up (Multi-Source Convergence)":
    num_members = st.sidebar.slider("👥 Gang Size (Members):", min_value=2, max_value=5, value=2, step=1)

st.sidebar.markdown("---")
st.sidebar.markdown("### 👨‍💻 Project Team / Developed By")
st.sidebar.markdown(
    "**ROHITH A**  \n"
    "**RISHI ARAVINDH L**  \n"
    "**SAKTHI VIGNESH**"
)
st.sidebar.caption("ADI1221 – Principles of Artificial Intelligence")
st.sidebar.caption("Department of AI & DS")
st.sidebar.caption("K. Ramakrishnan College of Engineering")

st.markdown("---")

if routing_mode == "👤 Single Commuter (A to B)":
    st.markdown("### 📍 Select Journey Points")
    col_s1, col_s2 = st.columns(2)

    with col_s1:
        source_name = st.selectbox("Starting Bus Stop:", list(stop_options.keys()), index=0)
    with col_s2:
        destination_default_index = 2 if len(stop_options) > 2 else 0
        target_name = st.selectbox("Destination Bus Stop:", list(stop_options.keys()), index=destination_default_index)

    source_id = stop_options[source_name]
    target_id = stop_options[target_name]

    current_inputs = ('single', source_id, target_id, selected_metric, traffic_mult)

    if 'last_inputs' not in st.session_state or st.session_state.last_inputs != current_inputs:
        if source_id == target_id:
            st.session_state.route_result = {
                'success': False, 
                'error': 'Starting location and destination cannot be the same. Please select different stops.'
            }
        else:
            st.session_state.route_result = find_optimal_route(source_id, target_id, optimization_metric=selected_metric, traffic_multiplier=traffic_mult)
        st.session_state.last_inputs = current_inputs

    result = st.session_state.get('route_result', None)

    if result and result['success']:
        st.success(f"✅ Optimal Path Found Successfully using Dijkstra's Algorithm ({optimization_goal})!")
        
        total_time_calc = result.get('total_time_mins', sum(s['time_mins'] for s in result['route_details']))
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
            route_map = create_route_map(stops_df, result['route_details'], result['path_nodes'], member_starts=[source_id])
            st_folium(route_map, width=650, height=450, returned_objects=[])
    else:
        err_msg = result['error'] if result else "Please select valid distinct stops."
        st.warning(f"⚠️ {err_msg}")

else:
    # Friends Gang Meet-Up Mode
    st.markdown(f"### 📍 Configure Gang Meet-Up (Total Members: {num_members})")
    
    target_name = st.selectbox("🎯 Select Common Meet-Up Destination Stop:", list(stop_options.keys()), index=2)
    target_id = stop_options[target_name]
    
    st.markdown("#### 👤 Select Starting Stop for Each Member:")
    member_sources = []
    
    cols = st.columns(min(num_members, 3))
    for i in range(num_members):
        col_idx = i % 3
        with cols[col_idx]:
            m_name = st.selectbox(f"Member {i+1} Start:", list(stop_options.keys()), index=(i * 2) % len(stop_options), key=f"member_{i+1}_start")
            member_sources.append(stop_options[m_name])

    current_inputs = ('gang', tuple(member_sources), target_id, selected_metric, traffic_mult)

    if 'last_inputs' not in st.session_state or st.session_state.last_inputs != current_inputs:
        gang_results = []
        has_error = False
        err_message = ""
        
        for idx, src_id in enumerate(member_sources):
            if src_id == target_id:
                has_error = True
                err_message = f"Member {idx+1}'s starting stop cannot be the same as the meet-up destination."
                break
            res = find_optimal_route(src_id, target_id, optimization_metric=selected_metric, traffic_multiplier=traffic_mult)
            if not res['success']:
                has_error = True
                err_message = f"No route found for Member {idx+1}: {res['error']}"
                break
            gang_results.append(res)
            
        if has_error:
            st.session_state.gang_result = {'success': False, 'error': err_message}
        else:
            st.session_state.gang_result = {'success': True, 'results': gang_results}
        st.session_state.last_inputs = current_inputs

    gang_res = st.session_state.get('gang_result', None)

    if gang_res and gang_res['success']:
        st.success(f"✅ All {num_members} Gang Members Routes Calculated Successfully to **{target_name}**!")
        
        total_gang_fare = sum(r['total_fare_rs'] for r in gang_res['results'])
        max_gang_time = max(r.get('total_time_mins', sum(s['time_mins'] for s in r['route_details'])) for r in gang_res['results'])
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Longest Travel Time", f"{max_gang_time} mins")
        with m2:
            st.metric("Total Combined Fare", f"₹ {total_gang_fare}")
        with m3:
            st.metric("Meet-Up Destination", target_name)
            
        st.markdown("---")
        
        col_left, col_right = st.columns([1, 1.2])
        
        with col_left:
            st.subheader("📋 Member-wise Boarding Guides")
            for idx, r in enumerate(gang_res['results'], 1):
                st.markdown(f"#### 👤 Member {idx} Route:")
                for s_idx, step in enumerate(r['route_details'], 1):
                    pass_badge = "🟢 Govt Free Pass OK" if step['govt_free_pass'] else "🔴 Paid Private Bus"
                    st.markdown(
                        f"""
                        * **Step {s_idx}: Board Bus `{step['bus_number']}`** ({step['from_stop_name']} ➔ {step['to_stop_name']})  
                          🕒 {step['time_mins']} mins | 🛣️ {step['distance_km']} km | 💵 ₹{step['fare_rs']} | {pass_badge}
                        """
                    )
                st.markdown("---")
                
        with col_right:
            st.subheader("🗺️ Convergence Route Map")
            combined_path_nodes = []
            combined_route_details = []
            for r in gang_res['results']:
                combined_route_details.extend(r['route_details'])
                for node in r['path_nodes']:
                    if node not in combined_path_nodes:
                        combined_path_nodes.append(node)
                                
            route_map = create_route_map(stops_df, combined_route_details, combined_path_nodes, member_starts=member_sources)
            st_folium(route_map, width=650, height=450, returned_objects=[])
    else:
        err_msg = gang_res['error'] if gang_res else "Please configure all member starting points."
        st.warning(f"⚠️ {err_msg}")

st.markdown("---")
footer_left, footer_center, footer_right = st.columns([1, 2, 1])
with footer_center:
    st.markdown("### 👨‍💻 Project Team / Developed By")
    st.markdown(
        "**ROHITH A**  \n"
        "**RISHI ARAVINDH L**  \n"
        "**SAKTHI VIGNESH**"
    )
    st.caption("ADI1221 – Principles of Artificial Intelligence")
    st.caption("Department of AI & DS · K. Ramakrishnan College of Engineering")
