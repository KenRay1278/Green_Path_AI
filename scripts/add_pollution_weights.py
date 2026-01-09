import osmnx as ox
import networkx as nx
import pickle
import os
from sys import argv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(BASE_DIR, '../data/raw')
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, '../data/processed')
OUTPUT_FILENAME = 'jakarta_network_processed.pkl'

#estimated pollution multipliers based on road characteristics
POLLUTION_FACTORS = {
    'living_street': 3.0, #gang (jalan tikus)
    'busway': 20.0, #illegal routing

    #local small roads
    'residential': 2.5, #jalan perumahan
    'unclassified': 2.2, #penghubung kecil
    
    #city streets
    'primary': 1.6, #jalan utama
    'primary_link': 1.7,

    'secondary': 1.8, #jalan raya kecamatan
    'secondary_link': 1.9,
    
    'tertiary': 2.0, #jalan raya kelurahan
    'tertiary_link': 2.1,
    
    #arteries
    'motorway': 1.0, #jalan tol
    'motorway_link': 1.5, #jalan masuk tol
    
    'trunk': 1.2, #jalan arteri
    'trunk_link': 1.5, #jalan masuk jalan arteri
    
    # Default
    'default': 1.8
}

# Assume speeds: motorway=80km/h, primary=50km/h, residential=30km/h
speed_limits_kmh = {
    'living_street': 10, #gang (jalan tikus)
    'busway': 1, #illegal routing

    #local small roads
    'residential': 20, #jalan perumahan
    'unclassified': 20, #penghubung kecil
    
    #city streets
    'primary': 40, #jalan utama
    'primary_link': 20,

    'secondary': 30, #jalan raya kecamatan
    'secondary_link': 20,
    
    'tertiary': 25, #jalan raya kelurahan
    'tertiary_link': 15,
    
    #arteries
    'motorway': 80, #jalan tol
    'motorway_link': 40, #jalan masuk tol
    
    'trunk': 60, #jalan arteri
    'trunk_link': 30, #jalan masuk jalan arteri
    
    # Default
    'default': 30
}

def add_pollution_weights(G):
    
    #adds pollution weights to each edge in the graph

    """
    Formula: pollution = base_distance * pollution_multiplier * intersection penalty
    """
    print("\tAdding pollution weights to network...")
    
    edges_processed = 0
    
    for u, v, key, data in G.edges(keys=True, data=True):
        # Get road type
        highway = data.get('highway', 'default')
        if isinstance(highway, list):
            highway = highway[0]
        
        # Get base distance (in meters)
        length = data.get('length', 100)
        
        # Get pollution multiplier based on road type
        pollution_multiplier = POLLUTION_FACTORS.get(highway, POLLUTION_FACTORS['default'])
        
        # Count intersections (nodes with degree > 2 indicate intersections)
        # More intersections = more stop-and-go = more pollution
        intersection_penalty = 1.0
        if G.degree(u) > 2 or G.degree(v) > 2:
            intersection_penalty = 1.1
        
        # Calculate pollution score
        # Higher score = more pollution
        pollution_score = length * pollution_multiplier * intersection_penalty
        
        # Add to edge data
        G[u][v][key]['pollution'] = pollution_score
        G[u][v][key]['pollution_multiplier'] = pollution_multiplier
        G[u][v][key]['road_type'] = highway
        
        # Time weight (for fastest route) - based on speed limits
        road_speed = speed_limits_kmh.get(highway, speed_limits_kmh['default'])
        # Time in seconds = (distance in km) / (speed in km/h) * 3600
        time_seconds = (length / 1000) / road_speed * 3600
        G[u][v][key]['time'] = time_seconds
        
        edges_processed += 1
    
    print(f"Processed {edges_processed} edges")
    return G

def save_processed_network(G):
    """Save the processed network with pollution weights"""
    print("\nSaving processed network...")
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    full_processed_path = os.path.join(PROCESSED_DATA_DIR, OUTPUT_FILENAME)
    with open(full_processed_path, 'wb') as f:
        pickle.dump(G, f)
    print(f"Saved to: {filename}")

def display_sample_edges(G, n=5):
    """Display sample edges with their weights"""
    print(f"\n📋 Sample edges with weights (first {n}):")
    print("-" * 80)
    
    for i, (u, v, key, data) in enumerate(G.edges(keys=True, data=True)):
        if i >= n:
            break
        
        print(f"\n\tEdge {i+1}:")
        print(f"\tRoad type: {data.get('road_type', 'unknown')}")
        print(f"\tLength: {data.get('length', 0):.2f}m")
        print(f"\tTime: {data.get('time', 0):.2f}s")
        print(f"\tPollution score: {data.get('pollution', 0):.2f}")
        print(f"\tPollution multiplier: {data.get('pollution_multiplier', 0):.2f}x")

if __name__ == "__main__":
    
    selected_mode = None
    if len(argv) > 1:
        if argv[1] in ['1', '2']:
            selected_mode = argv[1]
        else:
            print(f"Argument '{argv[1]}' invalid. Ignoring.")
    else:
        print("\n\n\t" + "=" * 24)
        print("\tADDING POLLUTION WEIGHTS")
        print("\t" + "=" * 30 + "\n")
        print("\tMode 1: Simple (Central Jakarta)")
        print("\tMode 2: Complete (Greater Jakarta)")
        while selected_mode not in ['1', '2']:
            selected_mode = input("\n\tChoose mode (1/2): ")

    size_key = 'small' if selected_mode == '1' else 'large'
    filename = f'jakarta_network_{size_key}.graphml'
    full_raw_path = os.path.join(RAW_DATA_DIR, filename)
    # Load the network
    try:        
        print("\n\tLoading network...")
        G = ox.load_graphml(full_raw_path)
        print(f"\tLoaded: {len(G.nodes())} nodes, {len(G.edges())} edges")
        
        #Add pollution weights
        G = add_pollution_weights(G)
        
        # Display samples
        display_sample_edges(G)
        
        # Save processed network
        save_processed_network(G)
        
        print("\n\t" + "=" * 16)
        print("\tSTEP 2 COMPLETE!")
        print("\t"+ "=" * 16)
        print("\n\tNext: cd ../src ; Run 'python app.py' or Test 'python pathfinding_algo.py'")
        
    except FileNotFoundError:
        print(f"\tError: jakarta_network_{size_key}.graphml not found!")
        print(f"\tEnsure you are choosing the correct mode or run 'network_extractor.py {selected_mode}' first!\n")
    except Exception as e:
        print(f"\n\tUnexpected Error: {e}")