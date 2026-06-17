import ast
import os
import pickle

import osmnx as ox
from flask import Flask, abort, jsonify, request, send_from_directory
from flask_cors import CORS

from pathfinding_algo import astar_pathfinding, calculate_route_stats

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, '../web')
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, '../data/processed')
INPUT_FILENAME = os.getenv('GREENPATH_GRAPH_FILE', 'jakarta_network_processed.pkl')
APP_AREA_NAME = 'Greater Jakarta'

app = Flask(__name__)
CORS(app)

G = None
GRAPH_LOAD_ERROR = None
MAP_CONTEXT = None

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

POLLUTION_UNIT = 'mg'
POLLUTION_UNIT_LABEL = 'Estimated emitted particulate mass'


def get_graph():
    """Load the processed graph once and return JSON-friendly errors if missing."""
    global G, GRAPH_LOAD_ERROR, MAP_CONTEXT

    if G is not None:
        return G

    graph_path = os.path.join(PROCESSED_DATA_DIR, INPUT_FILENAME)
    if not os.path.exists(graph_path):
        GRAPH_LOAD_ERROR = (
            f"Processed graph not found: {graph_path}. "
            "Run scripts/add_pollution_weights.py large after generating jakarta_network_large.graphml."
        )
        return None

    try:
        print(f"Loading {APP_AREA_NAME} network graph from {graph_path}...")
        with open(graph_path, 'rb') as f:
            G = pickle.load(f)
        apply_runtime_pollution_model(G)
        MAP_CONTEXT = build_map_context(G)
        GRAPH_LOAD_ERROR = None
        print("Network loaded!")
        return G
    except Exception as exc:
        GRAPH_LOAD_ERROR = f"Failed to load processed graph: {exc}"
        G = None
        MAP_CONTEXT = None
        return None


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


def apply_runtime_pollution_model(graph):
    """Keep old processed files compatible by applying the PM model at load time."""
    for u, v, key, data in graph.edges(keys=True, data=True):
        highway = normalize_highway(data.get('highway', data.get('road_type', 'default')))
        length = float(data.get('length', 100))
        length_km = length / 1000
        factor = PM25_FACTORS.get(highway, PM25_FACTORS['default'])
        stop_go_multiplier = 1.15 if graph.degree(u) > 2 or graph.degree(v) > 2 else 1.0

        pm25_mg = (
            length_km
            * factor['base_pm25_mg_per_km']
            * factor['traffic_multiplier']
            * stop_go_multiplier
        )
        pm10_mg = pm25_mg * 2.5

        data['pm25_mg'] = pm25_mg
        data['pm10_mg'] = pm10_mg
        data['pollution'] = pm25_mg
        data['pollution_multiplier'] = factor['traffic_multiplier'] * stop_go_multiplier
        data['pollution_unit'] = POLLUTION_UNIT
        data['road_type'] = highway


def path_to_coords(graph, path):
    return [[graph.nodes[node]['y'], graph.nodes[node]['x']] for node in path]


def build_map_context(graph, max_lines=1400):
    points = [
        (float(data['x']), float(data['y']))
        for _, data in graph.nodes(data=True)
        if 'x' in data and 'y' in data
    ]
    hull = graph_boundary(points)
    hull_latlng = [[lat, lon] for lon, lat in hull]
    if hull_latlng and hull_latlng[0] != hull_latlng[-1]:
        hull_latlng.append(hull_latlng[0])

    source_for_bounds = hull if hull else points
    bounds = []
    if source_for_bounds:
        min_lon = min(lon for lon, _ in source_for_bounds)
        max_lon = max(lon for lon, _ in source_for_bounds)
        min_lat = min(lat for _, lat in source_for_bounds)
        max_lat = max(lat for _, lat in source_for_bounds)
        pad_lon = max((max_lon - min_lon) * 0.04, 0.004)
        pad_lat = max((max_lat - min_lat) * 0.04, 0.004)
        bounds = [
            [min_lat - pad_lat, min_lon - pad_lon],
            [max_lat + pad_lat, max_lon + pad_lon],
        ]

    mask = []
    if hull_latlng and source_for_bounds:
        outer_pad_lon = max((max_lon - min_lon) * 0.45, 0.05)
        outer_pad_lat = max((max_lat - min_lat) * 0.45, 0.05)
        outer = [
            [min_lat - outer_pad_lat, min_lon - outer_pad_lon],
            [min_lat - outer_pad_lat, max_lon + outer_pad_lon],
            [max_lat + outer_pad_lat, max_lon + outer_pad_lon],
            [max_lat + outer_pad_lat, min_lon - outer_pad_lon],
            [min_lat - outer_pad_lat, min_lon - outer_pad_lon],
        ]
        mask = [outer, hull_latlng]

    network_lines = []
    edge_count = graph.number_of_edges()
    step = max(1, edge_count // max_lines)
    for index, (u, v, _) in enumerate(graph.edges(keys=True)):
        if index % step != 0:
            continue
        u_data = graph.nodes[u]
        v_data = graph.nodes[v]
        network_lines.append([
            [float(u_data['y']), float(u_data['x'])],
            [float(v_data['y']), float(v_data['x'])],
        ])
        if len(network_lines) >= max_lines:
            break

    return {
        'area': APP_AREA_NAME,
        'bounds': bounds,
        'boundary': hull_latlng,
        'mask': mask,
        'network_lines': network_lines,
    }


def graph_boundary(points):
    """Return a graph-hugging hull if Shapely supports it, else a convex hull."""
    try:
        from shapely import concave_hull
        from shapely.geometry import MultiPoint, MultiPolygon, Polygon

        geometry = concave_hull(MultiPoint(points), ratio=0.18, allow_holes=False)
        if isinstance(geometry, MultiPolygon):
            geometry = max(geometry.geoms, key=lambda item: item.area)
        if isinstance(geometry, Polygon) and not geometry.is_empty:
            return list(geometry.exterior.coords)
    except Exception as exc:
        print(f"Concave hull unavailable, falling back to convex hull: {exc}")

    return convex_hull(points)


def convex_hull(points):
    unique = sorted(set(points))
    if len(unique) <= 1:
        return unique

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)

    upper = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)

    return lower[:-1] + upper[:-1]


@app.route('/api/health', methods=['GET'])
def health():
    graph = get_graph()
    is_ready = graph is not None
    return jsonify({
        'ok': is_ready,
        'app': 'GreenPath AI',
        'area': APP_AREA_NAME,
        'graph_file': INPUT_FILENAME,
        'nodes': len(graph.nodes()) if graph else 0,
        'edges': len(graph.edges()) if graph else 0,
        'error': GRAPH_LOAD_ERROR,
    }), 200 if is_ready else 503


@app.route('/api/map-context', methods=['GET'])
def map_context():
    graph = get_graph()
    if graph is None:
        return jsonify({
            'error': 'Map data is not ready',
            'details': GRAPH_LOAD_ERROR,
        }), 503
    return jsonify(MAP_CONTEXT)


@app.route('/api/route', methods=['GET'])
@app.route('/get_route', methods=['GET'])
def get_route():
    graph = get_graph()
    if graph is None:
        return jsonify({
            'error': 'Route data is not ready',
            'details': GRAPH_LOAD_ERROR,
        }), 503

    try:
        start_lat = float(request.args.get('start_lat'))
        start_lon = float(request.args.get('start_lon'))
        end_lat = float(request.args.get('end_lat'))
        end_lon = float(request.args.get('end_lon'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid coordinates'}), 400

    start_node = ox.nearest_nodes(graph, start_lon, start_lat)
    end_node = ox.nearest_nodes(graph, end_lon, end_lat)

    time_route, _, time_explored, time_edges = astar_pathfinding(graph, start_node, end_node, weight='time')
    poll_route, _, poll_explored, poll_edges = astar_pathfinding(graph, start_node, end_node, weight='pollution')

    if not time_route or not poll_route:
        return jsonify({'error': 'No route found'}), 404

    time_stats = calculate_route_stats(graph, time_route, "Fastest Route")
    poll_stats = calculate_route_stats(graph, poll_route, "Greenest Route")

    response = {
        'time_route': {
            'path': path_to_coords(graph, time_route),
            'stats': time_stats,
            'explored': path_to_coords(graph, time_explored),
            'explored_edges': [[path_to_coords(graph, [u])[0], path_to_coords(graph, [v])[0]] for u, v in time_edges],
        },
        'pollution_route': {
            'path': path_to_coords(graph, poll_route),
            'stats': poll_stats,
            'explored': path_to_coords(graph, poll_explored),
            'explored_edges': [[path_to_coords(graph, [u])[0], path_to_coords(graph, [v])[0]] for u, v in poll_edges],
        },
        'pollution_unit': POLLUTION_UNIT,
        'pollution_unit_label': POLLUTION_UNIT_LABEL,
        'pollution_note': 'PM estimates are simplified emitted particulate mass for one representative vehicle, not ambient concentration.',
    }

    return jsonify(response)


@app.route('/')
def landing():
    return send_from_directory(WEB_DIR, 'index.html')


@app.route('/app')
def map_app():
    return send_from_directory(WEB_DIR, 'app.html')


@app.route('/<path:filename>')
def web_static(filename):
    if '..' in filename or filename in {'get_route', 'api'}:
        abort(404)
    return send_from_directory(WEB_DIR, filename)


if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    print(f"Server running on http://localhost:{port}/")
    print(f"  Landing: http://localhost:{port}/")
    print(f"  Map app: http://localhost:{port}/app")
    print(f"  Health: http://localhost:{port}/api/health")
    app.run(debug=False, host='0.0.0.0', port=port)
