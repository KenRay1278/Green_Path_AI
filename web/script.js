let map;
let lightTileLayer;
let darkTileLayer;
let routeLayer;
let animationLayer;
let visitedLayer;
let frontierLayer;
let markersLayer;
let boundaryLayer;
let routeLabelLayer;
let routeRenderer;
let startMarker = null;
let endMarker = null;
let routesData = null;
let mapContext = null;
let animationRunning = false;
let isDarkMode = false;
let routeMode = "compare";
let soundEnabled = true;
let soundVolume = 0.7;
let animationSpeed = "normal";
let particleQuality = "low";
let audioContext = null;
let statsManuallyClosed = false;

const jakartaBounds = [
    [-6.380, 106.680],
    [-5.950, 106.980],
];

const colors = {
    fastest: "#007ACC",
    greenest: "#25D366",
    overlapBlue: "#007ACC",
    overlapGreen: "#25D366",
    mutedBlue: "#5f8fc2",
    mutedGreen: "#65b887",
};

function initMap() {
    map = L.map("map", {
        center: [-6.2088, 106.8456],
        zoom: 11,
        minZoom: 11,
        maxZoom: 17,
        maxBounds: jakartaBounds,
        maxBoundsViscosity: 1.0,
        preferCanvas: true,
        zoomControl: false,
        attributionControl: false,
    });

    L.control.zoom({ position: "bottomleft" }).addTo(map);
    routeRenderer = L.svg({ padding: 0.5 });

    lightTileLayer = L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
        attribution: "&copy; OpenStreetMap contributors &copy; CARTO",
        subdomains: "abcd",
    });

    darkTileLayer = L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        attribution: "&copy; OpenStreetMap contributors &copy; CARTO",
        subdomains: "abcd",
    });

    boundaryLayer = L.layerGroup().addTo(map);
    visitedLayer = L.layerGroup().addTo(map);
    frontierLayer = L.layerGroup().addTo(map);
    animationLayer = L.layerGroup().addTo(map);
    routeLayer = L.layerGroup().addTo(map);
    routeLabelLayer = L.layerGroup().addTo(map);
    markersLayer = L.layerGroup().addTo(map);

    drawFallbackBoundary();
    lightTileLayer.addTo(map);
    loadMapContext();
    wireControls();
    applyInitialResponsiveState();
    map.fitBounds(jakartaBounds, { padding: [28, 28] });
    map.on("click", onMapClick);
}

function wireControls() {
    document.querySelectorAll("[data-route-mode]").forEach((button) => {
        button.addEventListener("click", () => setRouteMode(button.dataset.routeMode));
    });
    document.querySelectorAll("[data-animation-speed]").forEach((button) => {
        button.addEventListener("click", () => setAnimationSpeed(button.dataset.animationSpeed));
    });
    document.querySelectorAll("[data-particle-quality]").forEach((button) => {
        button.addEventListener("click", () => setParticleQuality(button.dataset.particleQuality));
    });
    document.getElementById("soundVolume").addEventListener("input", (event) => {
        soundVolume = Number(event.target.value) / 100;
        soundEnabled = soundVolume > 0;
    });
    document.getElementById("aboutModal").addEventListener("click", (event) => {
        if (event.target.id === "aboutModal") closeAboutModal();
    });
    wirePressFeedback();
    updateThemeToggle();
}

function wirePressFeedback() {
    document.querySelectorAll("button, .home-link").forEach((control) => {
        control.addEventListener("click", () => {
            control.classList.remove("tap-feedback");
            void control.offsetWidth;
            control.classList.add("tap-feedback");
        });
        control.addEventListener("animationend", () => {
            control.classList.remove("tap-feedback");
        });
    });
}

function applyInitialResponsiveState() {
    if (window.matchMedia("(max-width: 560px)").matches) {
        const panel = document.getElementById("hudPanel");
        const button = panel?.querySelector(".hud-collapse-btn");
        const icon = panel?.querySelector(".hud-collapse-icon");
        panel?.classList.add("collapsed");
        button?.setAttribute("aria-label", "Expand route information");
        if (icon) icon.textContent = "+";
    }
}

async function loadMapContext() {
    try {
        const response = await fetch("/api/map-context");
        if (!response.ok) return;
        mapContext = await response.json();
        drawMapContext(mapContext);
    } catch (error) {
        console.warn("Map context unavailable", error);
    }
}

function drawFallbackBoundary() {
    boundaryLayer.clearLayers();
    L.rectangle(jakartaBounds, {
        color: "#f59e0b",
        weight: 2,
        opacity: 0.75,
        fillColor: "#f59e0b",
        fillOpacity: 0.035,
        dashArray: "8 8",
        interactive: false,
    }).addTo(boundaryLayer);
}

function drawMapContext(context) {
    boundaryLayer.clearLayers();

    if (Array.isArray(context.mask) && context.mask.length >= 2) {
        const maskPolygon = buildViewportMask(context.mask[1] || context.boundary, context.bounds) || context.mask;
        L.polygon(maskPolygon, {
            color: "transparent",
            weight: 0,
            fillColor: isDarkMode ? "#020617" : "#f8fafc",
            fillOpacity: isDarkMode ? 0.62 : 0.56,
            fillRule: "evenodd",
            interactive: false,
        }).addTo(boundaryLayer);
    }

    if (Array.isArray(context.network_lines) && context.network_lines.length) {
        L.polyline(context.network_lines, {
            color: isDarkMode ? "#94a3b8" : "#64748b",
            weight: 1,
            opacity: isDarkMode ? 0.08 : 0.06,
            interactive: false,
        }).addTo(boundaryLayer);
    }

    if (Array.isArray(context.boundary) && context.boundary.length > 2) {
        L.polygon(context.boundary, {
            color: "#64748b",
            weight: 1.75,
            opacity: isDarkMode ? 0.62 : 0.56,
            fillColor: "#64748b",
            fillOpacity: 0.008,
            interactive: false,
        }).addTo(boundaryLayer);

        map.fitBounds(context.boundary, { padding: [44, 44], maxZoom: 12 });
    }

    if (Array.isArray(context.bounds) && context.bounds.length === 2) {
        map.setMaxBounds(context.bounds);
    }
}

function buildViewportMask(boundary, bounds) {
    if (!Array.isArray(boundary) || boundary.length < 3 || !Array.isArray(bounds) || bounds.length !== 2) {
        return null;
    }
    const [[south, west], [north, east]] = bounds;
    const latPad = Math.max((north - south) * 2.4, 0.12);
    const lngPad = Math.max((east - west) * 2.4, 0.12);
    const outer = [
        [south - latPad, west - lngPad],
        [south - latPad, east + lngPad],
        [north + latPad, east + lngPad],
        [north + latPad, west - lngPad],
        [south - latPad, west - lngPad],
    ];
    return [outer, boundary];
}

function showToast(message, tone = "info") {
    const toast = document.getElementById("toast-notification");
    toast.textContent = message;
    toast.dataset.tone = tone;
    toast.classList.add("show");

    window.clearTimeout(showToast.hideTimer);
    showToast.hideTimer = window.setTimeout(() => {
        toast.classList.remove("show");
    }, 2600);
}

function setStatus(message) {
    document.getElementById("routeStatus").textContent = message;
}

function makeRouteIcon(type) {
    const label = type === "start" ? "Start" : "End";
    return L.divIcon({
        html: `<div class="route-marker ${type}"><span class="marker-pin" aria-hidden="true"></span><span class="marker-text">${label}</span></div>`,
        className: "",
        iconSize: [92, 34],
        iconAnchor: [18, 30],
        popupAnchor: [0, -28],
    });
}

function onMapClick(e) {
    ensureAudioContext();
    if (!isInsidePlayableArea(e.latlng)) {
        setStatus("Choose a point inside the available route area.");
        showToast("Choose a point inside the available route area.", "error");
        return;
    }

    if (!startMarker) {
        startMarker = L.marker(e.latlng, { icon: makeRouteIcon("start") }).addTo(markersLayer);
        setStatus("Start selected. Now choose a destination.");
        playPinSound("start");
        showToast("Start point set");
        return;
    }

    if (!endMarker) {
        endMarker = L.marker(e.latlng, { icon: makeRouteIcon("end") }).addTo(markersLayer);
        setStatus("Calculating fastest and greenest routes...");
        playPinSound("end");
        getRoutes(startMarker.getLatLng(), endMarker.getLatLng());
        return;
    }

    resetMap();
    onMapClick(e);
}

function isInsidePlayableArea(latlng) {
    if (!mapContext || !Array.isArray(mapContext.boundary) || mapContext.boundary.length < 3) {
        return true;
    }
    return isPointInPolygon([latlng.lat, latlng.lng], mapContext.boundary);
}

function isPointInPolygon(point, polygon) {
    const [lat, lng] = point;
    let inside = false;

    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i, i += 1) {
        const [latI, lngI] = polygon[i];
        const [latJ, lngJ] = polygon[j];
        const intersects = ((lngI > lng) !== (lngJ > lng))
            && (lat < ((latJ - latI) * (lng - lngI) / ((lngJ - lngI) || Number.EPSILON) + latI));
        if (intersects) inside = !inside;
    }

    return inside;
}

async function getRoutes(start, end) {
    setLoading(true);
    document.getElementById("statsCard").classList.remove("show");
    routeLayer.clearLayers();
    routeLabelLayer.clearLayers();
    clearAnimationLayers();

    try {
        const url = `/api/route?start_lat=${start.lat}&start_lon=${start.lng}&end_lat=${end.lat}&end_lon=${end.lng}`;
        const response = await fetch(url);

        if (!response.ok) {
            const errorPayload = await response.json().catch(() => ({}));
            throw new Error(errorPayload.details || errorPayload.error || "API Error");
        }

        routesData = await response.json();
        statsManuallyClosed = false;

        if (document.getElementById("enableAnimation").checked) {
            await runAnimation();
        }

        displayRoutes({ fit: true });
        displayStats();
        playSuccessSound();
        setStatus("Routes ready. Switch modes or replay the animation.");
        showToast("Routes calculated", "success");
    } catch (error) {
        console.error(error);
        setStatus("Route calculation failed. Try points closer to major roads.");
        showToast(error.message || "Error calculating route", "error");
    } finally {
        setLoading(false);
    }
}

function setLoading(isLoading) {
    document.getElementById("loadingIndicator").classList.toggle("show", isLoading);
}

async function runAnimation() {
    if (!routesData || animationRunning) return;

    animationRunning = true;
    routeLayer.clearLayers();
    routeLabelLayer.clearLayers();
    clearAnimationLayers();

    try {
        playSearchPulse();
        const routeNodeKeys = getRouteNodeKeys();
        if (routeMode !== "greenest") {
            await animateExploration(routesData.time_route.explored_edges || [], colors.mutedBlue, routeNodeKeys);
        }
        if (routeMode !== "fastest") {
            await animateExploration(routesData.pollution_route.explored_edges || [], colors.mutedGreen, routeNodeKeys);
        }

        await animateRouteDraw();
        clearAnimationLayers();
    } finally {
        animationRunning = false;
    }
}

async function animateExploration(edges, color, routeNodeKeys) {
    const isMobile = window.innerWidth < 720;
    const config = getAnimationConfig();
    const sampledEdges = sampleEdges(edges, isMobile ? config.mobileMaxEdges : config.maxEdges);
    const batchSize = isMobile ? config.mobileBatchSize : config.batchSize;
    const frontierWindow = isMobile ? 2 : 3;
    const recentBatches = [];

    for (let i = 0; i < sampledEdges.length; i += batchSize) {
        const batch = sampledEdges.slice(i, i + batchSize);
        const classified = classifyExplorationBatch(batch, routeNodeKeys);
        if (classified.faint.length) {
            L.polyline(classified.faint, {
                color,
                weight: isMobile ? 1 : 1.25,
                opacity: isMobile ? 0.11 : 0.15,
                interactive: false,
            }).addTo(visitedLayer);
        }

        recentBatches.push(classified);
        if (recentBatches.length > frontierWindow) recentBatches.shift();

        frontierLayer.clearLayers();
        const frontierFaint = recentBatches.flatMap((item) => item.faint);
        const frontierHot = recentBatches.flatMap((item) => item.hot);

        if (frontierFaint.length) {
            L.polyline(frontierFaint, {
                color: color === colors.mutedGreen ? colors.greenest : colors.fastest,
                weight: isMobile ? 2 : 2.75,
                opacity: isMobile ? 0.46 : 0.55,
                interactive: false,
            }).addTo(frontierLayer);
        }

        if (frontierHot.length) {
            L.polyline(frontierHot, {
                color: "#f8fafc",
                weight: isMobile ? 2.5 : 3.25,
                opacity: 0.62,
                interactive: false,
            }).addTo(frontierLayer);
        }

        if (i % (batchSize * 3) === 0) {
            playSearchPulse();
        }
        await nextFrame(config.frameDelay);
    }
}

function getAnimationConfig() {
    const configs = {
        slow: {
            maxEdges: 900,
            mobileMaxEdges: 360,
            batchSize: 22,
            mobileBatchSize: 14,
            routeFramesMax: 84,
            routeStepDivisor: 3,
            frameDelay: 72,
        },
        normal: {
            maxEdges: 900,
            mobileMaxEdges: 360,
            batchSize: 56,
            mobileBatchSize: 34,
            routeFramesMax: 34,
            routeStepDivisor: 7,
            frameDelay: 18,
        },
        fast: {
            maxEdges: 900,
            mobileMaxEdges: 360,
            batchSize: 140,
            mobileBatchSize: 82,
            routeFramesMax: 12,
            routeStepDivisor: 18,
            frameDelay: 0,
        },
    };
    const particleScales = {
        low: 0.28,
        medium: 1,
        high: 3.2,
    };
    const selected = configs[animationSpeed] || configs.normal;
    const scale = particleScales[particleQuality] || particleScales.low;
    return {
        ...selected,
        maxEdges: Math.max(160, Math.round(selected.maxEdges * scale)),
        mobileMaxEdges: Math.max(90, Math.round(selected.mobileMaxEdges * scale)),
    };
}

function classifyExplorationBatch(batch, routeNodeKeys) {
    const faint = [];
    const hot = [];

    batch.forEach(([from, to]) => {
        const target = routeNodeKeys.has(coordKey(from)) || routeNodeKeys.has(coordKey(to)) ? hot : faint;
        target.push([from, to]);
    });

    return { faint, hot };
}

function sampleEdges(edges, maxEdges) {
    if (!Array.isArray(edges) || edges.length <= maxEdges) return edges || [];
    const step = Math.ceil(edges.length / maxEdges);
    return edges.filter((_, index) => index % step === 0);
}

async function animateRouteDraw() {
    const paths = getVisiblePaths();
    const longest = Math.max(...paths.map((path) => path.length), 0);
    const config = getAnimationConfig();
    const frames = Math.min(config.routeFramesMax, Math.max(10, Math.ceil(longest / config.routeStepDivisor)));

    for (let frame = 1; frame <= frames; frame++) {
        routeLayer.clearLayers();
        const ratio = frame / frames;
        drawVisibleRoutes(ratio);
        await nextFrame(config.frameDelay);
    }
}

function nextFrame(delay = 0) {
    return new Promise((resolve) => {
        requestAnimationFrame(() => {
            if (delay > 0) {
                window.setTimeout(resolve, delay);
            } else {
                resolve();
            }
        });
    });
}

function clearAnimationLayers() {
    if (visitedLayer) visitedLayer.clearLayers();
    if (frontierLayer) frontierLayer.clearLayers();
    if (animationLayer) animationLayer.clearLayers();
}

function setRouteMode(mode) {
    routeMode = mode;
    statsManuallyClosed = false;
    document.querySelectorAll("[data-route-mode]").forEach((button) => {
        button.classList.toggle("active", button.dataset.routeMode === mode);
    });
    displayRoutes();
    displayStats();
}

function displayRoutes(options = {}) {
    routeLayer.clearLayers();
    routeLabelLayer.clearLayers();
    if (!routesData) return;

    drawVisibleRoutes(1);
    drawRouteLabels();

    if (options.fit) {
        const allCoords = [
            ...(routesData.time_route.path || []),
            ...(routesData.pollution_route.path || []),
        ];
        if (allCoords.length > 0) {
            map.fitBounds(allCoords, {
                paddingTopLeft: [390, 120],
                paddingBottomRight: [80, 180],
                maxZoom: 15,
            });
        }
    }
}

function drawVisibleRoutes(progress = 1) {
    if (!routesData) return;

    const timePath = trimPath(routesData.time_route.path || [], progress);
    const greenPath = trimPath(routesData.pollution_route.path || [], progress);

    if (routeMode === "fastest") {
        drawPath(timePath, colors.fastest, 5, 0.95);
        return;
    }

    if (routeMode === "greenest") {
        drawPath(greenPath, colors.greenest, 5, 0.95);
        return;
    }

    drawComparedRoutes(timePath, greenPath);
}

function trimPath(path, progress) {
    if (progress >= 1 || path.length <= 2) return path;
    const visibleLength = Math.max(2, Math.ceil(path.length * progress));
    return path.slice(0, visibleLength);
}

function drawComparedRoutes(timePath, greenPath) {
    const timeSegments = getSegments(timePath);
    const greenSegments = getSegments(greenPath);
    const greenKeys = new Set(greenSegments.map((segment) => segment.key));
    const sharedKeys = new Set(timeSegments.filter((segment) => greenKeys.has(segment.key)).map((segment) => segment.key));

    drawSegments(timeSegments.filter((segment) => !sharedKeys.has(segment.key)), colors.fastest, 5, 0.92);
    drawSegments(greenSegments.filter((segment) => !sharedKeys.has(segment.key)), colors.greenest, 5, 0.92);
    drawOverlapSegments(timeSegments.filter((segment) => sharedKeys.has(segment.key)));
}

function drawPath(path, color, weight, opacity) {
    if (path.length < 2) return;
    L.polyline(path, {
        color,
        weight: weight + 3,
        opacity: 0.1,
        lineCap: "round",
        lineJoin: "round",
        renderer: routeRenderer,
        interactive: false,
    }).addTo(routeLayer);
    L.polyline(path, {
        color,
        weight,
        opacity,
        lineCap: "round",
        lineJoin: "round",
        renderer: routeRenderer,
        interactive: false,
    }).addTo(routeLayer);
}

function drawSegments(segments, color, weight, opacity) {
    if (!segments.length) return;
    L.polyline(segments.map((segment) => [segment.from, segment.to]), {
        color,
        weight,
        opacity,
        lineCap: "round",
        lineJoin: "round",
        renderer: routeRenderer,
        interactive: false,
    }).addTo(routeLayer);
}

function drawOverlapSegments(segments) {
    if (!segments.length) return;
    segments.forEach((segment) => {
        const coords = [segment.from, segment.to];
        L.polyline(coords, {
            color: "#e2e8f0",
            weight: 7,
            opacity: 0.34,
            lineCap: "butt",
            renderer: routeRenderer,
            interactive: false,
        }).addTo(routeLayer);
        L.polyline(coords, {
            color: colors.overlapGreen,
            weight: 5,
            opacity: 0.92,
            lineCap: "butt",
            renderer: routeRenderer,
            interactive: false,
        }).addTo(routeLayer);
        L.polyline(coords, {
            color: colors.overlapBlue,
            weight: 5,
            opacity: 0.98,
            dashArray: "7 7",
            dashOffset: "0",
            lineCap: "butt",
            renderer: routeRenderer,
            interactive: false,
        }).addTo(routeLayer);
        L.polyline(coords, {
            color: "#f8fafc",
            weight: 1.5,
            opacity: 0.5,
            dashArray: "2 12",
            dashOffset: "6",
            lineCap: "butt",
            renderer: routeRenderer,
            interactive: false,
        }).addTo(routeLayer);
    });
}

function getSegments(path) {
    const segments = [];
    for (let i = 0; i < path.length - 1; i += 1) {
        segments.push({
            from: path[i],
            to: path[i + 1],
            key: segmentKey(path[i], path[i + 1]),
        });
    }
    return segments;
}

function segmentKey(a, b) {
    const first = coordKey(a);
    const second = coordKey(b);
    return first < second ? `${first}|${second}` : `${second}|${first}`;
}

function coordKey(coord) {
    return `${Number(coord[0]).toFixed(6)},${Number(coord[1]).toFixed(6)}`;
}

function getVisiblePaths() {
    if (!routesData) return [];
    if (routeMode === "fastest") return [routesData.time_route.path || []];
    if (routeMode === "greenest") return [routesData.pollution_route.path || []];
    return [routesData.time_route.path || [], routesData.pollution_route.path || []];
}

function getRouteNodeKeys() {
    const keys = new Set();
    getVisiblePaths().forEach((path) => {
        path.forEach((coord) => keys.add(coordKey(coord)));
    });
    return keys;
}

function displayStats() {
    if (!routesData) return;

    const timeStats = routesData.time_route.stats;
    const pollutionStats = routesData.pollution_route.stats;
    const timeDiff = pollutionStats.time_minutes - timeStats.time_minutes;
    const timePm25 = getPm25(timeStats);
    const greenPm25 = getPm25(pollutionStats);
    const pollutionDiff = timePm25 - greenPm25;
    const pollutionReduction = timePm25
        ? (pollutionDiff / timePm25 * 100)
        : 0;

    document.getElementById("fastestStats").innerHTML = statsMarkup([
        ["Distance", `${timeStats.distance_km.toFixed(2)} km`],
        ["Time", `${timeStats.time_minutes.toFixed(1)} min`],
        ["PM2.5", formatMass(timePm25)],
        ["PM10", formatMass(getPm10(timeStats))],
    ]);

    document.getElementById("greenestStats").innerHTML = statsMarkup([
        ["Distance", `${pollutionStats.distance_km.toFixed(2)} km`],
        ["Time", `${pollutionStats.time_minutes.toFixed(1)} min`],
        ["PM2.5", formatMass(greenPm25)],
        ["PM10", formatMass(getPm10(pollutionStats))],
    ]);

    document.getElementById("comparisonStats").innerHTML = statsMarkup([
        ["Extra time", `${timeDiff >= 0 ? "+" : ""}${timeDiff.toFixed(1)} min`],
        ["PM2.5 saved", `${formatMass(pollutionDiff)} (${pollutionReduction.toFixed(1)}%)`],
    ]);

    document.getElementById("fastestCard").classList.toggle("hidden", routeMode === "greenest");
    document.getElementById("greenestCard").classList.toggle("hidden", routeMode === "fastest");
    document.getElementById("comparisonCard").classList.toggle("hidden", routeMode !== "compare");
    document.getElementById("statsCard").dataset.mode = routeMode;
    applyStatsVisibility();
}

function drawRouteLabels() {
    if (!routesData) return;

    if (routeMode === "fastest") {
        addRouteLabel(routesData.time_route, "fastest", 0.5);
        return;
    }

    if (routeMode === "greenest") {
        addRouteLabel(routesData.pollution_route, "greenest", 0.5);
        return;
    }

    addRouteLabel(routesData.time_route, "fastest", 0.62);
    addRouteLabel(routesData.pollution_route, "greenest", 0.38);
}

function addRouteLabel(route, type, positionRatio = 0.5) {
    const path = route?.path || [];
    const stats = route?.stats;
    if (path.length < 2 || !stats) return;

    const labelIndex = Math.min(
        path.length - 1,
        Math.max(0, Math.round((path.length - 1) * positionRatio)),
    );
    const label = type === "fastest" ? "Fastest" : "Greenest";
    const icon = L.divIcon({
        className: "",
        html: `
            <div class="route-chip ${type}">
                <strong>${label}</strong>
                <span>${stats.distance_km.toFixed(1)} km · ${stats.time_minutes.toFixed(0)} min</span>
            </div>
        `,
        iconSize: [146, 42],
        iconAnchor: type === "fastest" ? [8, 34] : [138, 8],
    });

    L.marker(path[labelIndex], {
        icon,
        interactive: false,
        keyboard: false,
    }).addTo(routeLabelLayer);
}

function statsMarkup(rows) {
    return rows.map(([label, value]) => `
        <div class="stat-item">
            <span>${label}</span>
            <span class="stat-value">${value}</span>
        </div>
    `).join("");
}

function getPm25(stats) {
    return Number(stats.pm25_mg ?? stats.pollution_score ?? 0);
}

function getPm10(stats) {
    return Number(stats.pm10_mg ?? getPm25(stats) * 2.5);
}

function formatMass(value) {
    const absValue = Math.abs(value);
    const formatted = absValue >= 100 ? value.toFixed(0) : value.toFixed(1);
    return `${formatted} mg`;
}

function modeLabel(mode) {
    if (mode === "fastest") return "Fastest only";
    if (mode === "greenest") return "Greenest only";
    return "Compare";
}

function toggleMenu() {
    document.getElementById("controlPanel").classList.toggle("open");
}

function toggleDarkMode() {
    isDarkMode = !isDarkMode;
    document.body.classList.toggle("dark-mode", isDarkMode);

    if (isDarkMode) {
        if (map.hasLayer(lightTileLayer)) map.removeLayer(lightTileLayer);
        darkTileLayer.addTo(map);
    } else {
        if (map.hasLayer(darkTileLayer)) map.removeLayer(darkTileLayer);
        lightTileLayer.addTo(map);
    }

    if (mapContext) drawMapContext(mapContext);
    updateThemeToggle();
}

function updateThemeToggle() {
    const icon = document.getElementById("themeToggleIcon");
    const button = document.getElementById("themeToggle");
    if (!icon || !button) return;
    icon.textContent = isDarkMode ? "🌙" : "☀";
    button.setAttribute("aria-label", isDarkMode ? "Switch to light mode" : "Switch to dark mode");
}

function setAnimationSpeed(speed) {
    animationSpeed = ["slow", "normal", "fast"].includes(speed) ? speed : "normal";
    document.querySelectorAll("[data-animation-speed]").forEach((button) => {
        button.classList.toggle("active", button.dataset.animationSpeed === animationSpeed);
    });
    showToast(`Animation speed: ${animationSpeed}`);
}

function setParticleQuality(quality) {
    particleQuality = ["low", "medium", "high"].includes(quality) ? quality : "low";
    document.querySelectorAll("[data-particle-quality]").forEach((button) => {
        button.classList.toggle("active", button.dataset.particleQuality === particleQuality);
    });
    showToast(`Particle quantity: ${particleQuality}`);
}

function toggleLegend() {
    const isVisible = document.getElementById("showLegend").checked;
    document.querySelector(".legend-grid").classList.toggle("hidden", !isVisible);
}

function toggleRouteComparison() {
    statsManuallyClosed = false;
    applyStatsVisibility();
}

function applyStatsVisibility() {
    const statsCard = document.getElementById("statsCard");
    const shouldShow = Boolean(routesData && document.getElementById("showComparison").checked && !statsManuallyClosed);
    statsCard.classList.toggle("show", shouldShow);
}

function closeStatsCard() {
    statsManuallyClosed = true;
    applyStatsVisibility();
}

function toggleHudPanel() {
    const panel = document.getElementById("hudPanel");
    const isCollapsed = panel.classList.toggle("collapsed");
    const button = panel.querySelector(".hud-collapse-btn");
    const icon = panel.querySelector(".hud-collapse-icon");
    button.setAttribute("aria-label", isCollapsed ? "Expand route information" : "Collapse route information");
    icon.textContent = isCollapsed ? "+" : "−";
}

function openAboutModal() {
    const modal = document.getElementById("aboutModal");
    modal.classList.add("show");
    modal.setAttribute("aria-hidden", "false");
}

function closeAboutModal() {
    const modal = document.getElementById("aboutModal");
    modal.classList.remove("show");
    modal.setAttribute("aria-hidden", "true");
}

function ensureAudioContext() {
    if (!audioContext) {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (AudioContextClass) audioContext = new AudioContextClass();
    }
    if (audioContext && audioContext.state === "suspended") {
        audioContext.resume();
    }
}

function playSuccessSound() {
    if (!soundEnabled) return;
    ensureAudioContext();
    if (!audioContext) return;

    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(520, audioContext.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(840, audioContext.currentTime + 0.16);
    gain.gain.setValueAtTime(0.0001, audioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.13 * soundVolume, audioContext.currentTime + 0.03);
    gain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + 0.22);
    oscillator.connect(gain).connect(audioContext.destination);
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.24);
}

function playPinSound(type) {
    if (!soundEnabled) return;
    ensureAudioContext();
    if (!audioContext) return;

    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    oscillator.type = "triangle";
    oscillator.frequency.setValueAtTime(type === "start" ? 420 : 620, audioContext.currentTime);
    gain.gain.setValueAtTime(0.0001, audioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.11 * soundVolume, audioContext.currentTime + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + 0.14);
    oscillator.connect(gain).connect(audioContext.destination);
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.16);
}

function playSearchPulse() {
    if (!soundEnabled) return;
    ensureAudioContext();
    if (!audioContext) return;

    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    oscillator.type = "sawtooth";
    oscillator.frequency.setValueAtTime(160, audioContext.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(260, audioContext.currentTime + 0.08);
    gain.gain.setValueAtTime(0.0001, audioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.05 * soundVolume, audioContext.currentTime + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + 0.1);
    oscillator.connect(gain).connect(audioContext.destination);
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.11);
}

async function replayAnimation() {
    if (!routesData) {
        showToast("Calculate a route first");
        return;
    }

    statsManuallyClosed = false;
    await runAnimation();
    displayRoutes();
    displayStats();
}

function resetMap() {
    startMarker = null;
    endMarker = null;
    routesData = null;
    animationRunning = false;
    statsManuallyClosed = false;
    markersLayer.clearLayers();
    routeLayer.clearLayers();
    routeLabelLayer.clearLayers();
    clearAnimationLayers();
    document.getElementById("statsCard").classList.remove("show");
    setStatus("Choose a start point, then choose a destination.");
    showToast("Map reset");
}

initMap();
