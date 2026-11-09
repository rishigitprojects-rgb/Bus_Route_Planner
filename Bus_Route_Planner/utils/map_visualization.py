import folium
import requests
from collections import defaultdict

def get_osrm_road_path(lat1, lon1, lat2, lon2):
    """
    Fetches real road routing geometry from the public OSRM API.
    """
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "routes" in data and len(data["routes"]) > 0:
                coords = data["routes"][0]["geometry"]["coordinates"]
                return [[c[1], c[0]] for c in coords]
    except Exception:
        pass
    
    return [[lat1, lon1], [lat2, lon2]]

def create_route_map(stops_df, route_details, path_nodes, member_starts=None):
    """
    Creates an interactive Folium map marking individual gang members (up to 5)
    using professional custom HTML numbered badges and destination flag.
    """
    trichy_lat = 10.8305
    trichy_lon = 78.6821
    
    m = folium.Map(location=[trichy_lat, trichy_lon], zoom_start=12, tiles="OpenStreetMap")
    
    full_road_coords = []
    
    # Fetch road geometries segment by segment along the exact path nodes
    for i in range(len(path_nodes) - 1):
        u = path_nodes[i]
        v = path_nodes[i + 1]
        
        u_row = stops_df[stops_df['stop_id'] == u]
        v_row = stops_df[stops_df['stop_id'] == v]
        
        if not u_row.empty and not v_row.empty:
            lat1, lon1 = float(u_row['latitude'].values[0]), float(u_row['longitude'].values[0])
            lat2, lon2 = float(v_row['latitude'].values[0]), float(v_row['longitude'].values[0])
            
            segment_coords = get_osrm_road_path(lat1, lon1, lat2, lon2)
            full_road_coords.extend(segment_coords)

    # Map stop_id to list of member numbers
    member_starts = member_starts or []
    stop_to_members = defaultdict(list)
    for idx, m_id in enumerate(member_starts):
        stop_to_members[m_id].append(idx + 1)

    # Distinct vibrant colors for members 1 to 5
    member_colors = {
        1: '#16a34a',  # Green
        2: '#ea580c',  # Orange
        3: '#9333ea',  # Purple
        4: '#0284c7',  # Blue
        5: '#dc2626'   # Red/Darkred
    }

    # Place custom markers for all stops along the path
    for idx, stop_id in enumerate(path_nodes):
        stop_row = stops_df[stops_df['stop_id'] == stop_id]
        if not stop_row.empty:
            lat = float(stop_row['latitude'].values[0])
            lon = float(stop_row['longitude'].values[0])
            name = stop_row['stop_name'].values[0]
            zone = stop_row['zone'].values[0]
            shelter = "Yes (Sheltered)" if int(stop_row['is_sheltered'].values[0]) == 1 else "No (Open Stop)"
            
            if stop_id == path_nodes[-1]:
                # Destination Flag Pin
                folium.Marker(
                    location=[lat, lon],
                    popup=f"<b>🎯 MEET-UP DESTINATION</b><br><b>Stop:</b> {name}<br><b>Zone:</b> {zone}",
                    icon=folium.Icon(color='red', icon='flag', prefix='glyphicon')
                ).add_to(m)
            elif stop_id in stop_to_members:
                members_list = stop_to_members[stop_id]
                m_str = ", ".join(map(str, members_list))
                first_m = members_list[0]
                bg_color = member_colors.get(first_m, '#2563eb')
                
                # Professional HTML Circular Badge for Members
                html_icon = f"""
                <div style="
                    background-color: {bg_color};
                    color: white;
                    border-radius: 50%;
                    width: 32px;
                    height: 32px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    font-size: 14px;
                    border: 2px solid white;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                ">M{m_str}</div>
                """
                folium.Marker(
                    location=[lat, lon],
                    popup=f"<b>👤 GANG MEMBER(S) {m_str} START</b><br><b>Stop:</b> {name}<br><b>Zone:</b> {zone}",
                    icon=folium.DivIcon(html=html_icon, icon_size=(32, 32), icon_anchor=(16, 16))
                ).add_to(m)
            else:
                # Intermediate transit stops
                folium.Marker(
                    location=[lat, lon],
                    popup=f"<b>🚏 TRANSIT STOP</b><br><b>Stop:</b> {name}<br><b>Zone:</b> {zone}",
                    icon=folium.Icon(color='blue', icon='bus', prefix='fa')
                ).add_to(m)
            
    # Draw the accurate road polyline
    if len(full_road_coords) > 1:
        folium.PolyLine(
            full_road_coords,
            color='#2563eb',
            weight=5,
            opacity=0.85,
            tooltip="Gang Convergence Route"
        ).add_to(m)
        
    return m