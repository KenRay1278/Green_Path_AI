from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import osmnx as ox
import os
from pathfinding_algo import astar_pathfinding, calculate_route_stats

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, '../data/processed')
INPUT_FILENAME = 'jakarta_network_processed.pkl'

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

print("Loading network graph... (this may take a moment)")
data_path = os.path.join(PROCESSED_DATA_DIR, INPUT_FILENAME)

with open(data_path, 'rb') as f:
    G = pickle.load(f)
print("Network loaded!")

def path_to_coords(path):
    #Helper to convert node IDs to [lat, lon] for Leaflet
    return [[G.nodes[node]['y'], G.nodes[node]['x']] for node in path]

@app.route('/get_route', methods=['GET'])
def get_route():
    # 1. Get coordinates from frontend query parameters
    try:
        start_lat = float(request.args.get('start_lat'))
        start_lon = float(request.args.get('start_lon'))
        end_lat = float(request.args.get('end_lat'))
        end_lon = float(request.args.get('end_lon'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid coordinates'}), 400

    # 2. Find nearest graph nodes to the clicked coordinates
    start_node = ox.nearest_nodes(G, start_lon, start_lat)
    end_node = ox.nearest_nodes(G, end_lon, end_lat)

    # 3. Run A* Algorithm (Fastest)
    time_route, _, time_explored, time_edges = astar_pathfinding(G, start_node, end_node, weight='time')
    
    # 4. Run A* Algorithm (Greenest)
    poll_route, _, poll_explored, poll_edges = astar_pathfinding(G, start_node, end_node, weight='pollution')

    if not time_route or not poll_route:
        return jsonify({'error': 'No route found'}), 404

    # 5. Calculate Stats
    time_stats = calculate_route_stats(G, time_route, "Fastest Route")
    poll_stats = calculate_route_stats(G, poll_route, "Greenest Route")

    # 6. Construct Response (matching your original JSON structure)
    response = {
        'time_route': {
            'path': path_to_coords(time_route),
            'stats': time_stats,
            'explored': path_to_coords(time_explored),
            'explored_edges': [[path_to_coords([u])[0], path_to_coords([v])[0]] for u, v in time_edges]
        },
        'pollution_route': {
            'path': path_to_coords(poll_route),
            'stats': poll_stats,
            'explored': path_to_coords(poll_explored),
            'explored_edges': [[path_to_coords([u])[0], path_to_coords([v])[0]] for u, v in poll_edges]
        }
    }
    
    return jsonify(response)

if __name__ == '__main__':
    print("!Server running on http://localhost:5000!")
    app.run(debug=True, port=5000)