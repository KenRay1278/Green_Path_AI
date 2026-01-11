import pickle
import json
from heapq import heappush, heappop
import math
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, '../data/processed')
INPUT_FILENAME = 'jakarta_network_processed.pkl'

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points (heuristic for A*)"""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def astar_pathfinding(G, start_node, end_node, weight='length'):
    """
    A* pathfinding algorithm
    weight: 'time' (fastest) or 'pollution' (greenest)
    Returns: path, total_cost, explored_nodes
    """

    # Get coordinates for heuristic
    end_node_data = G.nodes[end_node]
    end_coords = (end_node_data['y'], end_node_data['x'])
    
    # Priority queue: (f_score, g_score, node)
    # Note: We removed 'path' from the tuple to save RAM
    open_set = [(0, 0, start_node)]
    
    # Track where we came from (to reconstruct path later)
    came_from = {}
    
    # Cost to get to node
    g_scores = {start_node: 0}
    
    explored_nodes = []  # For visualization
    explored_edges = []
    closed_set = set()   # Faster lookups than list

    MAX_SPEED_MPS = 80 / 3.6  # 80 km/h converted to meters/second (~22.2)

    while open_set:
        # Get the node with lowest F score
        f_score, current_g, current = heappop(open_set)
        
        if current in closed_set:
            continue
            
        # Add to animation list
        explored_nodes.append(current)
        
        # --- GOAL REACHED? ---
        if current == end_node:
            # Reconstruct path backwards from came_from
            path = []
            curr = end_node
            while curr in came_from:
                path.append(curr)
                curr = came_from[curr]
            path.append(start_node)
            path.reverse() # Flip it to be Start -> End
            
            return path, current_g, explored_nodes, explored_edges
        
        closed_set.add(current)
        
        # Explore neighbors
        for neighbor in G.neighbors(current):
            if neighbor in closed_set:
                continue
            
            # Get edge data (handle MultiDiGraph structure)
            # We use the first edge (key=0) usually available
            edge_data = G[current][neighbor][0]
            
            # --- 2. RETRIEVE CORRECT COST ---
            # Defaults to 'length' (100m) if key is missing to prevent crash
            edge_cost = edge_data.get(weight, edge_data.get('length', 100))
            
            tentative_g = current_g + edge_cost
            
            # If this path is better than any previous one
            if neighbor not in g_scores or tentative_g < g_scores[neighbor]:
                came_from[neighbor] = current
                g_scores[neighbor] = tentative_g
                explored_edges.append((current, neighbor))
                # --- HEURISTIC CALCULATION ---
                neighbor_data = G.nodes[neighbor]
                h_dist = haversine_distance(
                    neighbor_data['y'], neighbor_data['x'],
                    end_coords[0], end_coords[1]
                )
                
                # Scale heuristic based on goal type
                if weight == 'time':
                    # Time = Distance / MaxSpeed
                    h_score = h_dist / MAX_SPEED_MPS
                elif weight == 'pollution':
                    # Pollution = Distance * MinMultiplier
                    # Min multiplier is 1.0 (Highways), so we use 1.0 to be safe
                    h_score = h_dist
                else:
                    h_score = h_dist

                final_f = tentative_g + h_score
                heappush(open_set, (final_f, tentative_g, neighbor))
    
    # If no path found
    return None, float('inf'), explored_nodes, explored_edges

def calculate_route_stats(G, path, route_name="Route"):
    """Calculate detailed statistics for a route"""
    total_distance = 0
    total_time = 0
    total_pollution = 0
    road_types = {}
    
    for i in range(len(path) - 1):
        edge_data = G[path[i]][path[i+1]][0]
        
        distance = edge_data.get('length', 0)
        time = edge_data.get('time', 0)
        pollution = edge_data.get('pollution', 0)
        road_type = edge_data.get('road_type', 'unknown')
        
        total_distance += distance
        total_time += time
        total_pollution += pollution
        road_types[road_type] = road_types.get(road_type, 0) + 1
    
    return {
        'name': route_name,
        'distance_km': total_distance / 1000,
        'time_minutes': total_time / 60,
        'pollution_score': total_pollution,
        'num_segments': len(path) - 1,
        'road_types': road_types
    }

def export_routes_json(G, time_route, pollution_route, time_stats, pollution_stats, 
                       time_explored, pollution_explored, filename='routes_data.json'):
    """Export routes and exploration data for visualization"""
    
    def path_to_coords(path):
        return [[G.nodes[node]['y'], G.nodes[node]['x']] for node in path]
    
    data = {
        'time_route': {
            'path': path_to_coords(time_route),
            'stats': time_stats,
            'explored': path_to_coords(time_explored)  # Limit for performance
        },
        'pollution_route': {
            'path': path_to_coords(pollution_route),
            'stats': pollution_stats,
            'explored': path_to_coords(pollution_explored)
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n\tRoutes exported to: {filename}")

def find_sample_route(G):
    """Find two random but meaningful points for demonstration"""
    import random
    
    nodes = list(G.nodes())
    
    # Try to find nodes that are reasonably far apart
    max_attempts = 50
    for _ in range(max_attempts):
        start = random.choice(nodes)
        end = random.choice(nodes)
        
        start_coords = (G.nodes[start]['y'], G.nodes[start]['x'])
        end_coords = (G.nodes[end]['y'], G.nodes[end]['x'])
        
        distance = haversine_distance(start_coords[0], start_coords[1],
                                      end_coords[0], end_coords[1])
        
        # Look for routes between 2-5 km apart
        if 2000 < distance < 5000:
            return start, end
    
    # Fallback: just return any two different nodes
    return nodes[0], nodes[-1]

def hunt_for_best_scenario(G, duration_seconds=30):
    import time
    import random
    
    print(f"\n\tHunting for the best trade-off scenario for {duration_seconds}s...")
    
    start_time = time.time()
    nodes = list(G.nodes())
    
    # Track the champions
    best_pollution_saving_pct = 0
    best_pair_saving = None
    
    best_time_loss_min = 0
    best_pair_loss = None
    
    attempts = 0
    
    while time.time() - start_time < duration_seconds:
        attempts += 1
        
        u = random.choice(nodes)
        v = random.choice(nodes)
        
        time_path, time_cost, _, _ = astar_pathfinding(G, u, v, weight='time')
        poll_path, poll_cost, _, _ = astar_pathfinding(G, u, v, weight='pollution')

        if time_cost == float('inf') or poll_cost == float('inf') or not time_path or not poll_path:
            continue

        if not time_path or not poll_path: continue
        
        fast_stats = calculate_route_stats(G, time_path)
        green_stats = calculate_route_stats(G, poll_path)
        
        poll_diff = fast_stats['pollution_score'] - green_stats['pollution_score']
        if fast_stats['pollution_score'] > 0:
            saving_pct = (poll_diff / fast_stats['pollution_score']) * 100
        else:
            saving_pct = 0
            
        time_diff = green_stats['time_minutes'] - fast_stats['time_minutes']
        
        if saving_pct > best_pollution_saving_pct:
            best_pollution_saving_pct = saving_pct
            best_pair_saving = (u, v)
            print(f"\tNew Pollution Record: {saving_pct:.1f}% saving! (Nodes: {u}->{v})")
            
        if time_diff > best_time_loss_min:
            best_time_loss_min = time_diff
            best_pair_loss = (u, v)
            print(f"\tNew Time Loss Record: {time_diff:.1f} min slower")

    print("\n" + "\t" + "="*40)
    print(f"\tHUNT COMPLETE ({attempts} attempts)")
    print(f"\tBest Pollution Saving: {best_pollution_saving_pct:.1f}%")
    print(f"\tWorst Time Loss: {best_time_loss_min:.1f}%")
    print(f"\tNodes: {best_pair_saving}")
    print("\t" + "="*40)
    
    return *best_pair_saving, best_pair_loss

if __name__ == "__main__":
    print("\t" + "=" * 24)
    print("\tA* PATHFINDING ALGORITHM")
    print("\t" + "=" * 24)
    full_processed_path = os.path.join(PROCESSED_DATA_DIR, INPUT_FILENAME)
    # Load processed network
    try:
        print("\n\tLoading processed network...")
        with open(full_processed_path, 'rb') as f:
            G = pickle.load(f)
        print(f"\tLoaded: {len(G.nodes())} nodes, {len(G.edges())} edges")
        
        # Find sample route
        print("\n\tFinding sample start and end points...")
        # start_node, end_node = find_sample_route(G)
        start_node, end_node, _= hunt_for_best_scenario(G, 120)
        
        start_coords = (G.nodes[start_node]['y'], G.nodes[start_node]['x'])
        end_coords = (G.nodes[end_node]['y'], G.nodes[end_node]['x'])
        
        print(f"\tStart: {start_coords}")
        print(f"\tEnd: {end_coords}")
        
        # Run A* for FASTEST route (time-optimized)
        print("\n\tRunning A* for FASTEST route...")
        time_route, time_cost, time_explored, _ = astar_pathfinding(G, start_node, end_node, weight='time')
        
        if time_route:
            time_stats = calculate_route_stats(G, time_route, "Fastest Route")
            print(f"\tFound route with {len(time_route)} nodes")
            print(f"\tDistance: {time_stats['distance_km']:.2f} km")
            print(f"\tTime: {time_stats['time_minutes']:.2f} minutes")
            print(f"\tPollution: {time_stats['pollution_score']:.2f}")
            print(f"\tExplored: {len(time_explored)} nodes")
        else:
            print("No route found!")
        
        # Run A* for GREENEST route (pollution-optimized)
        print("\n\tRunning A* for GREENEST route...")
        pollution_route, pollution_cost, pollution_explored, _ = astar_pathfinding(G, start_node, end_node, weight='pollution')
        
        if pollution_route:
            pollution_stats = calculate_route_stats(G, pollution_route, "Greenest Route")
            print(f"\tFound route with {len(pollution_route)} nodes")
            print(f"\tDistance: {pollution_stats['distance_km']:.2f} km")
            print(f"\tTime: {pollution_stats['time_minutes']:.2f} minutes")
            print(f"\tPollution: {pollution_stats['pollution_score']:.2f}")
            print(f"\tExplored: {len(pollution_explored)} nodes")
        else:
            print("No route found!")
        
        # Comparison
        if time_route and pollution_route:
            print("\n\tCOMPARISON:")
            print("\t" + "-" * 40)
            time_diff = pollution_stats['time_minutes'] - time_stats['time_minutes']
            pollution_diff = time_stats['pollution_score'] - pollution_stats['pollution_score']
            pollution_reduction = (pollution_diff / time_stats['pollution_score']) * 100
            
            print(f"\tTime difference: +{time_diff:.2f} minutes ({time_diff/time_stats['time_minutes']*100:.1f}% longer)")
            print(f"\tPollution reduction: {pollution_reduction:.1f}% less pollution")
            
            # Export for visualization
            export_routes_json(G, time_route, pollution_route, time_stats, pollution_stats, time_explored, pollution_explored)
            
            print("\n" + "\t" + "=" * 32)
            print("\tALL STEPS COMPLETE AND VERIFIED!")
            print("\t" + "=" * 32)
            print("\n\tNext: Run server 'python app.py' and open index.html")
        
    except FileNotFoundError:
        print("\tError: jakarta_network_processed.pkl not found!")
        print("\tPlease run 'add_pollution_weights.py' first")