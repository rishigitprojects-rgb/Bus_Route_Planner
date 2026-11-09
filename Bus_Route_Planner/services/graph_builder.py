import pandas as pd
import networkx as nx
import os

def load_transit_data():
    """Loads bus stops and routes from CSV datasets."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stops_path = os.path.join(base_dir, 'data', 'bus_stops.csv')
    routes_path = os.path.join(base_dir, 'data', 'bus_routes.csv')
    
    stops_df = pd.read_csv(stops_path)
    routes_df = pd.read_csv(routes_path)
    return stops_df, routes_df

def build_transit_graph(weight_metric='base_time_mins'):
    """
    Builds a NetworkX MultiDiGraph representing the Trichy bus network.
    weight_metric can be 'base_time_mins', 'distance_km', or 'fare_rs'.
    """
    stops_df, routes_df = load_transit_data()
    
    # Create a Directed Graph that allows multiple edges between the same stops (different buses)
    G = nx.MultiDiGraph()
    
    # Add nodes (Bus Stops) with attributes
    for _, row in stops_df.iterrows():
        G.add_node(
            row['stop_id'],
            stop_name=row['stop_name'],
            latitude=row['latitude'],
            longitude=row['longitude'],
            zone=row['zone'],
            is_sheltered=row['is_sheltered']
        )
        
    # Add edges (Bus Routes) with weights
    for _, row in routes_df.iterrows():
        G.add_edge(
            row['from_stop_id'],
            row['to_stop_id'],
            route_id=row['route_id'],
            bus_number=str(row['bus_number']),
            weight=float(row[weight_metric]),
            distance_km=float(row['distance_km']),
            base_time_mins=float(row['base_time_mins']),
            fare_rs=float(row['fare_rs']),
            govt_free_pass_allowed=int(row['govt_free_pass_allowed'])
        )
        
    return G, stops_df