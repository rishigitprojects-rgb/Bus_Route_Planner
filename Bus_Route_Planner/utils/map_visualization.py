import folium
import requests

def get_osrm_road_path(lat1, lon1, lat2, lon2):
    """
    Fetches real road routing geometry from the public OSRM API 
    so the line follows actual roads instead of drawing a straight line.
    """
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "routes" in data and len(data["routes"]) > 0:
                coords = data["routes"][0]["geometry"]["coordinates"]
                # OSRM returns [lon, lat], Folium needs [lat, lon]
                return [[c[1], c[0]] for c in coords]
    except Exception:
        pass
    
    # Fallback to straight line if API fails or offline
    return [[lat1, lon1], [lat2, lon2]]

def create_route_map(stops_df, route_details, path_nodes):
    """
    Creates an interactive Folium map centered on Trichy, 
    marking bus stops and drawing the OSRM real road path.
    """
    trichy_lat = 10.8305
    trichy_lon = 78.6821
    
    m = folium.Map(location=[trichy_lat, trichy_lon], zoom_start=13, tiles="OpenStreetMap")
    
    full_road_coords = []
    
    for i in range(len(path_nodes) - 1):
        u = path_nodes[i]
        v = path_nodes[i + 1]
        
        u_row = stops_df[stops_df['stop_id'] == u]
        v_row = stops_df[stops_df['stop_id'] == v]
        
        if not u_row.empty and not v_row.empty:
            lat1, lon1 = float(u_row['latitude'].values[0]), float(u_row['longitude'].values[0])
            lat2, lon2 = float(v_row['latitude'].values[0]), float(v_row['longitude'].values[0])
            
            # Fetch real road path segment between consecutive stops
            segment_coords = get_osrm_road_path(lat1, lon1, lat2, lon2)
            full_road_coords.extend(segment_coords)

    # Place Markers for all stops in the path
    for stop_id in path_nodes:
        stop_row = stops_df[stops_df['stop_id'] == stop_id]
        if not stop_row.empty:
            lat = float(stop_row['latitude'].values[0])
            lon = float(stop_row['longitude'].values[0])
            name = stop_row['stop_name'].values[0]
            zone = stop_row['zone'].values[0]
            shelter = "Yes (Sheltered)" if int(stop_row['is_sheltered'].values[0]) == 1 else "No (Open Stop)"
            
            if stop_id == path_nodes[0]:
                color = 'green'
                icon_type = 'play'
                popup_title = 'START LOCATION'
            elif stop_id == path_nodes[-1]:
                color = 'red'
                icon_type = 'stop'
                popup_title = 'DESTINATION'
            else:
                color = 'blue'
                icon_type = 'info-sign'
                popup_title = 'TRANSIT STOP'
                
            folium.Marker(
                location=[lat, lon],
                popup=f"<b>{popup_title}</b><br>{name}<br>Zone: {zone}<br>Shelter: {shelter}",
                icon=folium.Icon(color=color, icon=icon_type, prefix='glyphicon')
            ).add_to(m)
            
    # Draw the accurate road polyline
    if len(full_road_coords) > 1:
        folium.PolyLine(
            full_road_coords,
            color='#2563eb',  # Professional blue road line
            weight=6,
            opacity=0.85,
            tooltip="OSRM Real Road Bus Route"
        ).add_to(m)
        
    return m