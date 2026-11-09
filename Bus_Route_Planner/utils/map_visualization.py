import folium

def create_route_map(stops_df, route_details, path_nodes):
    """
    Creates an interactive Folium map centered on Trichy, 
    marking bus stops and drawing the optimal Dijkstra path.
    """
    # Center map on Trichy (approximate center from our stops)
    trichy_lat = 10.8305
    trichy_lon = 78.6821
    
    m = folium.Map(location=[trichy_lat, trichy_lon], zoom_start=13, tiles="OpenStreetMap")
    
    # Extract coordinates for the path
    path_coords = []
    
    for stop_id in path_nodes:
        stop_row = stops_df[stops_df['stop_id'] == stop_id]
        if not stop_row.empty:
            lat = float(stop_row['latitude'].values[0])
            lon = float(stop_row['longitude'].values[0])
            name = stop_row['stop_name'].values[0]
            zone = stop_row['zone'].values[0]
            shelter = "Yes (Sheltered)" if int(stop_row['is_sheltered'].values[0]) == 1 else "No (Open Stop)"
            
            path_coords.append([lat, lon])
            
            # Determine marker color
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
            
    # Draw polyline connecting the optimal path
    if len(path_coords) > 1:
        folium.PolyLine(
            path_coords,
            color='purple',
            weight=5,
            opacity=0.8,
            tooltip="Optimal Dijkstra Bus Route"
        ).add_to(m)
        
    return m