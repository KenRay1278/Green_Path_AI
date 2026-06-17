# GreenPath AI

GreenPath AI is an interactive route-comparison app for exploring tradeoffs between
fast travel and lower-emission route choices. It combines A* pathfinding, map-based
visualization, route statistics, and simplified particulate-emission estimates in a
single Flask web app.

The app currently ships with a preprocessed sample road graph so deployment does not
need to fetch or process map data at runtime. The pipeline is designed so other map
areas can be prepared and swapped in later.

## Current Stack

- Python Flask backend
- Static HTML, CSS, and JavaScript frontend
- Bootstrap 5 via CDN for UI structure
- Leaflet for interactive maps
- OSMnx and NetworkX for road graph processing
- Preprocessed route graph stored in `data/processed/`

There is no React, Vite, or Node build step in the current app.

## App Routes

| Route | Purpose |
|---|---|
| `/` | Landing page |
| `/app` | Interactive map app |
| `/api/route` | Route calculation API |
| `/api/map-context` | Graph boundary and sampled network-line context |
| `/api/health` | Backend and graph-data readiness check |
| `/get_route` | Backwards-compatible route API alias |

## Project Structure

```txt
Green_Path_AI/
  src/
    app.py
    pathfinding_algo.py
  web/
    index.html
    app.html
    landing.css
    style.css
    script.js
    assets/
      images/
      audio/
      video/
  scripts/
    network_extractor.py
    add_pollution_weights.py
    cache/
  data/
    raw/
    processed/
  environment.yml
  requirements.txt
  setup_environment.py
  Procfile
  .env.example
```

## Local Setup

Create or update the conda environment:

```bash
python setup_environment.py
```

Or manually:

```bash
conda env update -n green_path -f environment.yml --prune
conda activate green_path
```

If Flask or OSMnx is missing inside the activated environment, repair it with:

```bash
conda env update -n green_path -f environment.yml --prune
```

## Route Data

The deployed app uses a preprocessed graph file:

```txt
data/processed/jakarta_network_processed.pkl
```

For this phase, the processed graph is committed so hosting providers can run the
app directly without live Overpass fetching or preprocessing. To regenerate data
locally, use the scripts in `scripts/` and keep the processed output filename aligned
with `GREENPATH_GRAPH_FILE`.

Example local regeneration:

```bash
conda activate green_path
python scripts/network_extractor.py large
python scripts/add_pollution_weights.py large
```

For a faster local test only, you can still pass `small`:

```bash
python scripts/network_extractor.py small
python scripts/add_pollution_weights.py small
```

## Run The App

```bash
conda activate green_path
python src/app.py
```

Open:

```txt
http://localhost:5000/
```

Health check:

```txt
http://localhost:5000/api/health
```

## Environment Variables

Copy `.env.example` if your hosting provider supports environment files.

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `5000` | Flask server port |
| `GREENPATH_GRAPH_FILE` | `jakarta_network_processed.pkl` | Processed graph filename |

## Backend Notes

Major behavior:

- Backend routes are standardized around `/api/route`, `/api/map-context`, and `/api/health`.
- `/get_route` remains available as a backwards-compatible route API alias.
- The app reads a preprocessed graph from `data/processed/` rather than fetching road data at startup.
- Pollution is modeled as simplified emitted particulate mass: `PM2.5 mg` and `PM10 mg`.

Compatibility details:

- The graph loads lazily, so the app can return clear JSON setup errors instead of crashing at import time.
- `pollution_score` remains in API responses as a compatibility alias for `pm25_mg`.
- `scripts/add_pollution_weights.py` supports `large`, `small`, `2`, and `1` command arguments.
- The processing script prints the processed output path after saving.

## Product Notes

GreenPath AI uses text, map visuals, route animation, audio cues, and a landing-page
video background to make route comparison easier to understand. These media elements
support the app experience rather than defining the product scope.

PM values are simplified emitted particulate-mass estimates for one representative
vehicle. They are useful for comparing route alternatives inside this app, not for
official air-quality or ambient-concentration claims.

## Deployment Direction

Recommended phase-one deployment: a single Flask app on Railway, Render, or a similar
Python web host.

The included `Procfile` uses:

```txt
web: python src/app.py
```

Before deploying, confirm that the processed graph file is included. The app can start
without the graph, but `/api/route` will return a clear JSON error until the graph is
available.

## Phase One Goal

Phase one focuses on structure, deployment readiness, and clarity:

- Keep the name GreenPath AI
- Keep Flask plus a static frontend
- Use a preprocessed road graph for reliable deployment
- Use Bootstrap as the UI library
- Keep backend routing simple and documented
- Provide a polished route-comparison flow for users
