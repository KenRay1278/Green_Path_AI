let map, timeLayer, pollutionLayer, timeAnimationLayer, pollAnimationLayer, markersLayer;
let startMarker = null, endMarker = null;
let routesData = null;
let animationRunning = false;
let isDarkMode = false;
let lightTileLayer, darkTileLayer;

// Jakarta bounds
const jakartaBounds = [
    [-6.368997, 106.674902], // Southwest
    [-6.082293, 106.998752]   // Northeast
];

function showToast(message, color = null) {
    const toast = document.getElementById('toast-notification');
    toast.textContent = message;
    
    // Optional: match text color to the route color
    if (color) toast.style.color = color;
    
    toast.classList.add('show');
    
    // Hide automatically after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
    }, 1000);
}

function initMap() {
    map = L.map('map', {
        center: [-6.2088, 106.8456],
        zoom: 12,
        maxBounds: jakartaBounds,
        maxBoundsViscosity: 1.0,
        minZoom: 11,
        maxZoom: 18
    });
    
    // Light tile layer
    lightTileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap contributors',
        subdomains: 'abcd'
    }).addTo(map);
    
    // Dark tile layer (neon style)
    darkTileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap contributors',
        subdomains: 'abcd'
    });
    
    // Initialize layers
    timeLayer = L.layerGroup().addTo(map);
    pollutionLayer = L.layerGroup().addTo(map);
    timeAnimationLayer = L.layerGroup().addTo(map);
    pollAnimationLayer = L.layerGroup().addTo(map);
    markersLayer = L.layerGroup().addTo(map);
    
    map.on('click', onMapClick);
}

function onMapClick(e) {
    if (!startMarker) {
        startMarker = L.marker(e.latlng).addTo(markersLayer);
        startMarker.bindPopup("Start Point").openPopup();
    } else if (!endMarker) {
        endMarker = L.marker(e.latlng).addTo(markersLayer);
        endMarker.bindPopup("End Point").openPopup();
        getRoutes(startMarker.getLatLng(), endMarker.getLatLng());
    } else {
        resetMap();
        onMapClick(e);
    }
}

async function getRoutes(start, end) {
    document.getElementById('loadingIndicator').classList.add('show');
    document.getElementById('statsCard').classList.remove('show');
    
    try {
        const url = `http://localhost:5000/get_route?start_lat=${start.lat}&start_lon=${start.lng}&end_lat=${end.lat}&end_lon=${end.lng}`;
        const response = await fetch(url);
        
        if (!response.ok) throw new Error('API Error');
        
        routesData = await response.json();
        
        const animationEnabled = document.getElementById('enableAnimation').checked;
        
        if (animationEnabled) {
            await runAnimation();
        }
        
        displayRoutes();
        displayStats();
        
    } catch (error) {
        console.error(error);
        alert('Error calculating route. Try points closer to roads.');
    } finally {
        document.getElementById('loadingIndicator').classList.remove('show');
    }
}

async function runAnimation() {
    timeAnimationLayer.clearLayers();
    pollAnimationLayer.clearLayers();
    timeLayer.clearLayers();
    pollutionLayer.clearLayers();
    
    const animateTime = document.getElementById('animateTime').checked;
    const animatePollution = document.getElementById('animatePollution').checked;
    const timeColor = isDarkMode ? '#00d9ff' : '#3b82f6';
    const pollColor = isDarkMode ? '#00ff88' : '#10b981';
    animationRunning = true;    

    if (animateTime && routesData.time_route.explored) {
        await animateExploration('#00d9ff', 'time');
        showToast("⚡ Fastest Route Found!", timeColor);
    }

    timeAnimationLayer.eachLayer(l => l.setStyle({ opacity: 0.2 }));
    L.polyline(routesData.time_route.path, {
        color: timeColor,
        weight: 3,
        opacity: 1,
    }).addTo(timeLayer);
    
    if (animatePollution && routesData.pollution_route.explored) {
        await animateExploration('#00ff88', 'pollution');
        showToast("🌱 Greenest Route Found!", pollColor);
    }
    
    animationRunning = false;
    timeAnimationLayer.clearLayers();
    pollAnimationLayer.clearLayers();
    timeLayer.clearLayers();
}

async function animateExploration(color, type) {
    const edges = (type === 'time') ? routesData.time_route.explored_edges : routesData.pollution_route.explored_edges;
    const layer = (type === 'time') ? timeAnimationLayer : pollAnimationLayer;
    const targetAnimationSpeed = 888;
    const timeToAnimate = Math.max(1, Math.ceil(edges.length / targetAnimationSpeed));
    for (let i = 0; i < edges.length; i ++) {
        const [parentCoord, childCoord] = edges[i];
        // const marker = L.circleMarker(explored[i], {
        //     radius: isDarkMode ? 3 : 2,
        //     color: color,
        //     fillColor: color,
        //     fillOpacity: opacity,
        //     weight: 0
        // }).addTo(exploredLayer);
        L.polyline([parentCoord, childCoord], {
            color: color,
            weight: 2,
            opacity: 0.4,
        }).addTo(layer);
        
        if (i % timeToAnimate === 0) { 
            await new Promise(resolve => setTimeout(resolve, 0)); 
        }
    }
}

function displayRoutes() {
    timeLayer.clearLayers();
    pollutionLayer.clearLayers();
    
    const showFastest = document.getElementById('showFastest').checked;
    const showGreenest = document.getElementById('showGreenest').checked;
    
    if (showFastest) {
        const timeColor = isDarkMode ? '#00d9ff' : '#3b82f6';
        L.polyline(routesData.time_route.path, {
            color: timeColor,
            weight: 3,
            opacity: 1,
        }).addTo(timeLayer);
    }
    
    if (showGreenest) {
        const greenColor = isDarkMode ? '#00ff88' : '#10b981';
        L.polyline(routesData.pollution_route.path, {
            color: greenColor,
            weight: 3,
            opacity: 1,
        }).addTo(pollutionLayer);
    }
    
    const allCoords = [...routesData.time_route.path, ...routesData.pollution_route.path];
    if (allCoords.length > 0) map.fitBounds(allCoords);
}

function displayStats() {
    const timeStats = routesData.time_route.stats;
    const pollutionStats = routesData.pollution_route.stats;
    
    document.getElementById('fastestStats').innerHTML = `
        <div class="stat-item">
            <span class="stat-label">Distance</span>
            <span class="stat-value">${timeStats.distance_km.toFixed(2)} km</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Time</span>
            <span class="stat-value">${timeStats.time_minutes.toFixed(1)} min</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Pollution Score</span>
            <span class="stat-value">${timeStats.pollution_score.toFixed(0)}</span>
        </div>
    `;
    
    document.getElementById('greenestStats').innerHTML = `
        <div class="stat-item">
            <span class="stat-label">Distance</span>
            <span class="stat-value">${pollutionStats.distance_km.toFixed(2)} km</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Time</span>
            <span class="stat-value">${pollutionStats.time_minutes.toFixed(1)} min</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Pollution Score</span>
            <span class="stat-value">${pollutionStats.pollution_score.toFixed(0)}</span>
        </div>
    `;
    
    const timeDiff = pollutionStats.time_minutes - timeStats.time_minutes;
    const pollutionDiff = timeStats.pollution_score - pollutionStats.pollution_score;
    const pollutionReduction = (pollutionDiff / timeStats.pollution_score * 100).toFixed(1);
    
    document.getElementById('comparisonStats').innerHTML = `
        <div class="stat-item">
            <span class="stat-label">Extra Time</span>
            <span class="stat-value" style="color: #f59e0b;">+${timeDiff.toFixed(1)} min</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Pollution Saved</span>
            <span class="stat-value" style="color: #10b981;">${pollutionReduction}%</span>
        </div>
    `;
    
    document.getElementById('statsCard').classList.add('show');
}

function toggleMenu() {
    document.getElementById('controlPanel').classList.toggle('open');
}

function toggleDarkMode() {
    isDarkMode = document.getElementById('darkMode').checked;
    document.body.classList.toggle('dark-mode', isDarkMode);
    
    if (isDarkMode) {
        map.removeLayer(lightTileLayer);
        darkTileLayer.addTo(map);
    } else {
        map.removeLayer(darkTileLayer);
        lightTileLayer.addTo(map);
    }
    
    if (routesData) {
        displayRoutes();
    }
}

function toggleRoute(type) {
    if (routesData) {
        displayRoutes();
    }
}

async function replayAnimation() {
    if (!routesData) {
        alert('Please calculate a route first!');
        return;
    }
    
    if (animationRunning) return;
    
    await runAnimation();
    displayRoutes();
}

function resetMap() {
    startMarker = null;
    endMarker = null;
    routesData = null;
    markersLayer.clearLayers();
    timeLayer.clearLayers();
    pollutionLayer.clearLayers();
    timeAnimationLayer.clearLayers();
    pollAnimationLayer.clearLayers();
    document.getElementById('statsCard').classList.remove('show');
}

initMap();