# GreenPath AI

GreenPath AI is a map route visualizer. It compares
the fastest route and the greenest route on a real OpenStreetMap road graph using A*
pathfinding.

The project started as an AI pathfinding assignment and is being refactored into a
polished multimedia web app.

## Current Stack

- Python Flask backend
- Static HTML, CSS, and JavaScript frontend
- Bootstrap 5 via CDN for UI structure
- Leaflet for interactive maps
- OSMnx and NetworkX for road graph processing
- Preprocessed Greater Jakarta graph stored in `data/processed/`

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

## Generate Route Data

The app is standardized around the Greater Jakarta dataset.

```bash
conda activate green_path
python scripts/network_extractor.py large
python scripts/add_pollution_weights.py large
```

This creates:

```txt
data/processed/jakarta_network_processed.pkl
```

For a faster local test only, you can still pass `small`:

```bash
python scripts/network_extractor.py small
python scripts/add_pollution_weights.py small
```

## Run the App

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

## Backend Change Notes

Major changes:

- Backend routes are standardized around `/api/route`, `/api/map-context`, and `/api/health`.
- `/get_route` remains available as a backwards-compatible route alias.
- The route pipeline uses `data/raw/jakarta_network_large.graphml` for Greater Jakarta and writes `data/processed/jakarta_network_processed.pkl`.
- Pollution is modeled as simplified emitted particulate mass: `PM2.5 mg` and `PM10 mg`.

Minor changes:

- The graph loads lazily, so the app can return clear JSON setup errors instead of crashing at import time.
- `pollution_score` remains in API responses as a compatibility alias for `pm25_mg`.
- `scripts/add_pollution_weights.py` now supports `large`, `small`, `2`, and `1` command arguments.
- The processing script now prints the actual processed output path after saving.

## Multimedia Roadmap

The final Multimedia Systems submission should include:

- [x] Text: landing page copy, route stats, comparison summary
- [x] Picture/Image: Leaflet map and generated network map asset
- [x] Audio: user-controlled generated route-complete sound cue
- [x] Video: landing hero looping demo placeholder
- [x] Animation: A* exploration and route display animation

Pollution is displayed as simplified emitted particulate mass: `PM2.5 mg` and
`PM10 mg` for one representative vehicle. It is useful for comparing route
alternatives inside this project, not for ambient air-concentration claims.

Asset folders:

```txt
web/assets/images/
web/assets/audio/
web/assets/video/
```

The current app uses generated placeholders, so missing media files do not break the
interface. Replace them later with final presentation assets if needed.

## Deployment Direction

Recommended phase-one deployment: a single Flask app on Render or Railway.

The included `Procfile` uses:

```txt
web: python src/app.py
```

Before deploying, confirm that the processed graph file is included or generated during
setup. The app can start without the graph, but `/api/route` will return a clear JSON
error until the graph is available.

## Phase One Goal

Phase one focuses on structure, deployment readiness, and clarity:

- Keep the name GreenPath AI
- Keep Flask plus static frontend
- Standardize around Greater Jakarta
- Use Bootstrap as the UI library
- Simplify backend routing
- Add `/api/health`
- Prepare for multimedia UI work in phase two
