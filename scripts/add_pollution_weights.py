import ast
import os
import pickle
from sys import argv

import osmnx as ox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(BASE_DIR, '../data/raw')
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, '../data/processed')
OUTPUT_FILENAME = 'jakarta_network_processed.pkl'

# Simplified emitted particulate mass factors for one representative vehicle.
# These values are for route comparison, not ambient air-concentration claims.
PM25_FACTORS = {
    'motorway': {'base_pm25_mg_per_km': 6, 'traffic_multiplier': 1.8},
    'motorway_link': {'base_pm25_mg_per_km': 6, 'traffic_multiplier': 1.8},
    'trunk': {'base_pm25_mg_per_km': 8, 'traffic_multiplier': 1.6},
    'trunk_link': {'base_pm25_mg_per_km': 8, 'traffic_multiplier': 1.6},
    'primary': {'base_pm25_mg_per_km': 12, 'traffic_multiplier': 1.5},
    'primary_link': {'base_pm25_mg_per_km': 12, 'traffic_multiplier': 1.5},
    'secondary': {'base_pm25_mg_per_km': 16, 'traffic_multiplier': 1.3},
    'secondary_link': {'base_pm25_mg_per_km': 16, 'traffic_multiplier': 1.3},
    'tertiary': {'base_pm25_mg_per_km': 18, 'traffic_multiplier': 1.1},
    'tertiary_link': {'base_pm25_mg_per_km': 18, 'traffic_multiplier': 1.1},
    'residential': {'base_pm25_mg_per_km': 22, 'traffic_multiplier': 0.8},
    'unclassified': {'base_pm25_mg_per_km': 22, 'traffic_multiplier': 0.8},
    'living_street': {'base_pm25_mg_per_km': 28, 'traffic_multiplier': 0.6},
    'busway': {'base_pm25_mg_per_km': 10000, 'traffic_multiplier': 1.0},
    'default': {'base_pm25_mg_per_km': 16, 'traffic_multiplier': 1.0},
}

speed_limits_kmh = {
    'living_street': 10,
    'busway': 1,
    'residential': 20,
    'unclassified': 20,
    'primary': 40,
    'primary_link': 20,
    'secondary': 30,
    'secondary_link': 20,
    'tertiary': 25,
    'tertiary_link': 15,
    'motorway': 80,
    'motorway_link': 40,
    'trunk': 60,
    'trunk_link': 30,
    'default': 30,
}


def normalize_highway(highway):
    if isinstance(highway, list):
        return highway[0] if highway else 'default'
    if isinstance(highway, str) and highway.startswith('['):
        try:
            parsed = ast.literal_eval(highway)
            if isinstance(parsed, list) and parsed:
                return parsed[0]
        except (SyntaxError, ValueError):
            pass
    return highway or 'default'


def add_pollution_weights(G):
    """Add time, PM2.5, and PM10 weights to each edge in the graph."""
    print("\tAdding PM2.5/PM10 route weights to network...")
    edges_processed = 0

    for u, v, key, data in G.edges(keys=True, data=True):
        highway = normalize_highway(data.get('highway', 'default'))
        length = float(data.get('length', 100))
        length_km = length / 1000
        factor = PM25_FACTORS.get(highway, PM25_FACTORS['default'])
        stop_go_multiplier = 1.15 if G.degree(u) > 2 or G.degree(v) > 2 else 1.0

        pm25_mg = (
            length_km
            * factor['base_pm25_mg_per_km']
            * factor['traffic_multiplier']
            * stop_go_multiplier
        )
        pm10_mg = pm25_mg * 2.5

        G[u][v][key]['pm25_mg'] = pm25_mg
        G[u][v][key]['pm10_mg'] = pm10_mg
        G[u][v][key]['pollution'] = pm25_mg
        G[u][v][key]['pollution_multiplier'] = factor['traffic_multiplier'] * stop_go_multiplier
        G[u][v][key]['pollution_unit'] = 'mg'
        G[u][v][key]['road_type'] = highway

        road_speed = speed_limits_kmh.get(highway, speed_limits_kmh['default'])
        G[u][v][key]['time'] = (length / 1000) / road_speed * 3600

        edges_processed += 1

    print(f"Processed {edges_processed} edges")
    return G


def save_processed_network(G):
    """Save the processed network with route weights."""
    print("\nSaving processed network...")
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    full_processed_path = os.path.join(PROCESSED_DATA_DIR, OUTPUT_FILENAME)
    with open(full_processed_path, 'wb') as f:
        pickle.dump(G, f)
    print(f"Saved to: {full_processed_path}")


def display_sample_edges(G, n=5):
    """Display sample edges with their weights."""
    print(f"\nSample edges with weights (first {n}):")
    print("-" * 80)

    for i, (u, v, key, data) in enumerate(G.edges(keys=True, data=True)):
        if i >= n:
            break

        print(f"\n\tEdge {i + 1}:")
        print(f"\tRoad type: {data.get('road_type', 'unknown')}")
        print(f"\tLength: {data.get('length', 0):.2f}m")
        print(f"\tTime: {data.get('time', 0):.2f}s")
        print(f"\tPM2.5: {data.get('pm25_mg', data.get('pollution', 0)):.2f} mg")
        print(f"\tPM10: {data.get('pm10_mg', 0):.2f} mg")
        print(f"\tPollution multiplier: {data.get('pollution_multiplier', 0):.2f}x")


def resolve_size_key(args):
    if len(args) > 1:
        if args[1] in ['1', 'small']:
            return 'small'
        if args[1] in ['2', 'large']:
            return 'large'
        print(f"Argument '{args[1]}' invalid. Using Greater Jakarta.")
        return 'large'

    print("\n\n\t" + "=" * 24)
    print("\tADDING POLLUTION WEIGHTS")
    print("\t" + "=" * 30 + "\n")
    print("\tMode 1: Simple (Central Jakarta)")
    print("\tMode 2: Complete (Greater Jakarta)")
    selected_mode = None
    while selected_mode not in ['1', '2']:
        selected_mode = input("\n\tChoose mode (1/2): ")
    return 'small' if selected_mode == '1' else 'large'


if __name__ == "__main__":
    size_key = resolve_size_key(argv)
    filename = f'jakarta_network_{size_key}.graphml'
    full_raw_path = os.path.join(RAW_DATA_DIR, filename)

    try:
        print("\n\tLoading network...")
        print(f"\tRaw graph: {full_raw_path}")
        G = ox.load_graphml(full_raw_path)
        print(f"\tLoaded: {len(G.nodes())} nodes, {len(G.edges())} edges")

        G = add_pollution_weights(G)
        display_sample_edges(G)
        save_processed_network(G)

        print("\n\t" + "=" * 16)
        print("\tSTEP 2 COMPLETE!")
        print("\t" + "=" * 16)
        print("\n\tNext: cd ../src ; run 'python app.py' or test 'python pathfinding_algo.py'")

    except FileNotFoundError:
        print(f"\tError: jakarta_network_{size_key}.graphml not found!")
        print(f"\tExpected path: {full_raw_path}")
        print(f"\tRun 'python network_extractor.py {size_key}' first.\n")
    except Exception as e:
        print(f"\n\tUnexpected Error: {e}")
