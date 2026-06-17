# Agent Instructions: GreenPath AI

## Project Summary

GreenPath AI is a Multimedia Systems project built from a previous AI pathfinding assignment.
The app compares fastest and greenest routes across Greater Jakarta using a Flask backend,
a preprocessed OpenStreetMap road graph, and a static Leaflet frontend.

The project is intentionally not a React or Node app at this stage. Keep the deployment
path simple unless the user explicitly asks for a frontend framework migration.

## Current Stack

- Backend: Python Flask
- Frontend: static HTML, CSS, and JavaScript
- UI library: Bootstrap via CDN, plus custom CSS
- Map rendering: Leaflet
- Data source: preprocessed Greater Jakarta road graph
- Algorithm: A* pathfinding with two weights:
  - fastest route, using estimated travel time
  - greenest route, using estimated pollution score

## Product Goal

The final app should be a polished, deployable multimedia route visualizer:

- Landing page
- Actual interactive map page
- Clean route controls
- Fastest vs greenest route comparison
- Smooth route and exploration animation
- Text, picture, audio, video, and animation elements
- Strong user experience suitable for classroom presentation

The backend is a supporting layer. Do not rewrite the core pathfinding algorithm unless
it is necessary for reliability, deployment, or frontend integration.

## Phase One Scope

Focus on structure, deployment readiness, and project clarity:

1. Keep the app name as GreenPath AI.
2. Keep Flask as the only backend.
3. Keep static frontend files under `web/`.
4. Use Bootstrap for faster UI improvement without adding Node tooling.
5. Refactor backend routes to:
   - `/` landing page
   - `/app` map app
   - `/api/route` route calculation
   - `/api/health` backend/data health check
6. Keep `/get_route` only as a backwards-compatible alias if useful.
7. Standardize the app around Greater Jakarta data.
8. Make startup safer for deployment:
   - app should not crash just because the graph file is missing
   - API should return clear JSON errors
   - port should come from the `PORT` environment variable
9. Clean broken text encoding in visible UI.
10. Do not attempt a full visual redesign yet.

## Multimedia Requirements

The final submission must visibly include all five multimedia elements:

1. Text
   - App explanation
   - A* explanation
   - Route result summaries
   - Fastest vs greenest comparison

2. Picture/Image
   - Map imagery
   - Route/legend visuals
   - Optional screenshots or generated city/map graphics

3. Audio
   - User-controlled audio only
   - No aggressive autoplay
   - Possible features: route success sound, narration, ambient toggle

4. Video
   - Tutorial/demo panel or modal
   - Local placeholder acceptable at first
   - Must not block the main route workflow

5. Animation
   - Route drawing
   - Exploration replay
   - Loading state
   - Optional moving marker

## Frontend Guidance

- The map page is the main product experience.
- The landing page should introduce the app and link to the map.
- Avoid overexplaining inside the interface.
- Prioritize responsive, readable, non-laggy UI.
- Keep controls obvious and accessible.
- Prefer CSS and Leaflet-native animation before adding dependencies.
- Add placeholder multimedia assets safely if real assets are not ready.

Suggested future asset folders:

```txt
web/assets/images/
web/assets/audio/
web/assets/video/
```

## Backend Guidance

- Preserve existing route response shape where possible.
- Keep route calculation in `/api/route`.
- Keep graph loading centralized and cached.
- Return JSON errors for invalid input, missing graph data, or route failures.
- Do not add a separate Node/Express backend.
- Do not hardcode deployment-only URLs.

## Deployment Direction

Recommended first deployment target:

- Single Flask app on Render or Railway
- Flask serves both static frontend and API
- Include preprocessed graph data if the hosting size limit allows it

Avoid Docker unless deployment requires it.

## Definition of Done

Phase one is complete when:

- Flask routes are clean and deployment-friendly.
- The app serves a landing page and map page.
- The map calls `/api/route`.
- `/api/health` reports graph/data readiness.
- Greater Jakarta is treated as the standard app dataset.
- Bootstrap is available for UI work.
- The project brief and README match the real stack.

The final project is complete when:

- Existing pathfinding still works.
- UI is polished and responsive.
- All five multimedia elements are present.
- Animation is smooth enough for presentation.
- Missing assets are handled gracefully.
- README explains setup, media replacement, and deployment.
