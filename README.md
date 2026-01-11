# 🗺️ Jakarta Pollution-Aware Pathfinding AI

A college project implementing A* pathfinding algorithm comparing time-optimized vs pollution-optimized routes in Jakarta, Indonesia.

## Project Overview

This AI system provides two route options:
- **Fastest Route** ⚡ - Minimizes travel time
- **Greenest Route** 🌱 - Minimizes pollution/emissions

Uses real Jakarta road network data from OpenStreetMap with custom pollution estimation based on road characteristics.

---

## Project Structure

```
jakarta_pathfinding_ai/
├── src/                              # Backend source code
│   ├── app.py                        # Flask API server
│   ├── pathfinding_algo.py           # A* algorithm implementation
│   └── routes_data.json              # [Generated] Route results
│
├── data/                             # Data directory
│   ├── raw/                          # Raw network data
│   │   ├── jakarta_network_small.graphml
│   │   ├── jakarta_network_large.graphml
│   │   └── network_map_*.png
│   └── processed/                    # Processed data
│       └── jakarta_network_processed.pkl
│
├── web/                              # Frontend
│   ├── index.html                    # Main interface
│   ├── style.css                     # [Optional] Styles
│   └── script.js                     # [Optional] Scripts
│
├── scripts/                          # Setup & processing scripts
│   ├── network_extractor.py          # Download OSM data
│   ├── add_pollution_weights.py      # Add pollution estimates
│   └── cache/                        # OSMnx cache
│
├── environment.yml                   # Conda environment
├── setup_environment.py              # Setup script
├── .gitignore                        # Git ignore rules
└── README.md                         # This file
```

---

## Quick Start

### Prerequisites
- **Conda** (Miniconda or Anaconda) - [Download](https://docs.conda.io/en/latest/miniconda.html)
- **Git** (optional, for cloning)

### Installation

**Step 1: Setup Environment**
```bash
# Run automated setup
python setup_environment.py
```

**Step 2: Activate Environment**
```bash
conda activate green_path
```

**Step 3: Extract Road Network (First time only)**
```bash
cd scripts
python network_extractor.py
```
Takes 3-5 minutes

**Step 4: Add Pollution Weights**
```bash
python add_pollution_weights.py
```
Takes ~30 seconds

**Step 5: Start Server**
```bash
cd ../src
python app.py
```

**Step 6: Open Web Interface**
- Manually open `web/index.html` in your browser

---

## Usage

### Interactive Map
1. **Click** on the map to set **Start Point**
2. **Click** again to set **End Point**
3. Algorithm automatically calculates both routes
4. View comparison in the stats panel

### Controls (Hamburger Menu)
- **Dark Mode** - Toggle neon visualization
- **Route Display** - Show/hide fastest/greenest routes
- **Animation** - Visualize A* algorithm exploration
- **Reset** - Clear map and start over

### Animation Features
- See A* algorithm explore the graph in real-time
- One-by-one animation (time route → pollution route)
- Replay anytime

---

## How It Works

### 1. Road Network Extraction
Uses `osmnx` to download real Jakarta road data from OpenStreetMap.

### 2. Pollution Estimation Model
```
pollution_score = distance × pollution_multiplier × intersection_penalty
```

**Pollution Multipliers by Road Type:**
- Residential: 2.5× (stop-and-go traffic)
- Secondary: 1.8× (moderate traffic)
- Primary: 1.6× (traffic lights)
- Motorway: 1.0× (free-flowing)
- Etc.

**Additional Factors:**
- Intersections: +10% (stop-and-go increases emissions)
- Assumed Average speeds affect time calculation

### 3. A* Pathfinding Algorithm
Runs twice with different cost functions:

**Time Route (Fastest):**
- Cost = travel time (distance ÷ average assumed speed)
- Heuristic = straight-line distance ÷ max speed (80km/h)

**Pollution Route (Greenest):**
- Cost = pollution score
- Heuristic = straight-line distance × min pollution factor (1.0)

### 4. Results Comparison
Shows:
- Distance, time, and pollution for each route
- Extra time needed for green route
- Pollution reduction percentage

---

## Technical Details

### Technologies
- **Backend:** Flask (Python 3.11)
- **Algorithm:** A* with custom heuristics
- **Data:** OpenStreetMap via OSMnx
- **Frontend:** Vanilla HTML/CSS/JS + Leaflet.js
- **Maps:** Leaflet.js with CartoDB tiles

### API Endpoint
```
GET http://localhost:5000/get_route
Parameters:
  - start_lat: float
  - start_lon: float
  - end_lat: float
  - end_lon: float

Returns: JSON with both routes, stats, and explored nodes
```

### Performance
- Small network (~1000 nodes): <1 second per route
- Large network (~10000 nodes): ~5-10 seconds per route
- Animation: ~2ms per edge

---

## Customization

### Change Area Size
In `scripts/network_extractor.py`:
```python
area_size = large #(Jakarta, Indonesia)
# OR
area_size = small #(Central Jakarta, Jakarta, Indonesia) for lighter load on memory
```

### Adjust Pollution Factors
In `scripts/add_pollution_weights.py`:
```python
POLLUTION_FACTORS = {
    'residential': 1.8,  # Modify these values
    'highway': 1.0,
    # ...
}
```

### Animation Speed
In `web/script.js`:
```javascript
const targetAnimationSpeed = 888;
//                            ↑ Change this
```

---

## Environment Management

### Useful Commands
```bash
# Activate environment
conda activate green_path

# Deactivate
conda deactivate

# Update environment
conda env update -f environment.yml --prune

# Export environment
conda env export > environment_backup.yml

# Remove environment
conda env remove -n green_path

# List environments
conda env list
```

---

## Troubleshooting

### "Conda not found"
- Install Miniconda: https://docs.conda.io/en/latest/miniconda.html
- Restart terminal after installation

### "Network data not found"
```bash
cd scripts
python network_extractor.py
python add_pollution_weights.py
```

### "No route found"
- Click points closer to actual roads
- Try different start/end locations
- Ensure points are within Jakarta bounds

### "Flask server not starting"
```bash
# Check if environment is activated
conda activate green_path

# Check if in correct directory
cd src
python app.py
```

### "Animation not working"
- Check browser console for errors
- Ensure Flask server is running
- Verify `explored_edges` data exists in API response

### Network download fails
- Check internet connection
- OpenStreetMap might be slow, retry later
- Try smaller area first

---

## Dependencies

### Core Libraries
- `osmnx` - Road network extraction
- `networkx` - Graph algorithms
- `geopandas` - Geospatial data
- `flask` - Web server
- `flask-cors` - Cross-origin requests

### Visualization
- `matplotlib` - Network visualization
- `folium` - Web maps
- Leaflet.js - Interactive maps

### Scientific
- `numpy` - Numerical computing
- `pandas` - Data manipulation
- `scikit-learn` - ML utilities

Full list in `environment.yml`

---

## Educational Value

This project demonstrates:
- **Graph Algorithms:** A* with custom heuristics
- **Real-world Data:** OpenStreetMap integration
- **Multi-objective Optimization:** Time vs environment
- **Full-stack Development:** Backend + Frontend
- **API Design:** RESTful Flask API
- **Geospatial Computing:** Working with coordinates & projections

---


## License

This is a college project for Artificial Intelligence Class in BINUS University. Free to use and modify for educational purposes.

---

## Credits

- **OpenStreetMap** - Road network data
- **OSMnx** - Network extraction library
- **Leaflet.js** - Web mapping
- **CartoDB** - Map tiles
- **Jakarta Government** - City data

---

## Contributors

- Kenneth Raymond
- Richson Limec
- Jonathan Gho
- Project: Assurance of Learning
- Course: AI
- University: Bina Nusantara University
- Semester: 3

---

## Support


### Common Workflows

**First Time:**
```bash
python setup_environment.py
conda activate green_path
cd scripts
python network_extractor.py
python add_pollution_weights.py
cd ../src
python app.py
```

**Daily Use:**
```bash
conda activate green_path
python app.py
```

**Clean Restart:**
```bash
# Remove generated files
del data\raw\*.graphml data\processed\*.pkl
# Or on Mac/Linux:
rm data/raw/*.graphml data/processed/*.pkl

# Regenerate
cd scripts
python network_extractor.py
python add_pollution_weights.py
```

---

**Created for Assurance of Learning - Artificial Intelligence Project**  
**Focus:** Transportation Emissions in Major Cities
**Environment:** `green_path` conda environment  
**Python Version:** 3.11