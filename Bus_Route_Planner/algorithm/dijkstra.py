import networkx as nx
from services.graph_builder import build_transit_graph

def find_optimal_route(source_id, target_id, optimization_metric='base_time_mins', traffic_multiplier=1.0):
    """
    Finds the optimal path using Dijkstra's algorithm with optional live traffic congestion multiplier.
    """
    G, stops_df = build_transit_graph(weight_metric=optimization_metric)
    
    # If traffic simulation is enabled, dynamically adjust edge weights for time-based metrics
    if traffic_multiplier > 1.0 and optimization_metric == 'base_time_mins':
        for u, v, data in G.edges(data=True):
            G[u][v]['weight'] = data['base_time_mins'] * traffic_multiplier
            
    try:
        path_nodes = nx.shortest_path(G, source=source_id, target=target_id, weight='weight')
        path_length = nx.shortest_path_length(G, source=source_id, target=target_id, weight='weight')
        
        route_details = []
        total_distance = 0.0
        total_fare = 0.0
        actual_time = 0.0
        
        for i in range(len(path_nodes) - 1):
            u = path_nodes[i]
            v = path_nodes[i + 1]
            
            edge_data = G.get_edge_data(u, v)
            best_edge_key = min(edge_data, key=lambda k: edge_data[k]['weight'])
            edge = edge_data[best_edge_key]
            
            from_name = stops_df.loc[stops_df['stop_id'] == u, 'stop_name'].values[0]
            to_name = stops_df.loc[stops_df['stop_id'] == v, 'stop_name'].values[0]
            
            segment_time = edge['base_time_mins'] * traffic_multiplier if optimization_metric == 'base_time_mins' else edge['base_time_mins']
            
            route_details.append({
                'from_stop_id': u,
                'from_stop_name': from_name,
                'to_stop_id': v,
                'to_stop_name': to_name,
                'bus_number': edge['bus_number'],
                'distance_km': edge['distance_km'],
                'time_mins': round(segment_time, 1),
                'fare_rs': edge['fare_rs'],
                'govt_free_pass': bool(edge['govt_free_pass_allowed'])
            })
            
            total_distance += edge['distance_km']
            total_fare += edge['fare_rs']
            actual_time += segment_time
            
        return {
            'success': True,
            'path_nodes': path_nodes,
            'total_cost': round(path_length, 1),
            'total_distance_km': round(total_distance, 2),
            'total_fare_rs': round(total_fare, 2),
            'total_time_mins': round(actual_time, 1),
            'route_details': route_details
        }
        
    except nx.NetworkXNoPath:
        return {
            'success': False,
            'error': 'No bus route found connecting these specific stops.'
        }
    except nx.NodeNotFound:
        return {
            'success': False,
            'error': 'One or both selected stops are invalid.'
        }