# ⏱️ CanopyCast: 3-Day Action Plan & GitHub Setup

With exactly 3 days remaining, you must work in parallel to avoid bottlenecks. This document provides the repository structure, day-by-day tasks, and direct messages to copy-paste to your teammates.

---

## 📂 1. GitHub Repository Structure

Create a single repository named `canopycast`. Set up these two root directories immediately to keep frontend and backend development isolated and prevent Git merge conflicts.

```text
canopycast/
├── backend/            # Chirag's Domain (FastAPI + SQL + LLM)
│   ├── app/
│   │   ├── main.py     # API endpoints
│   │   ├── database.py # SQLite synthetic grid generator
│   │   ├── optimize.py # Core UHI scoring algorithm
│   │   └── rag.py      # LangChain + ChromaDB for tree matching
│   ├── documents/      # Put 2-3 urban forestry PDFs here
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/           # Riyanshika & Nitesh's Domain (React + Leaflet + Tailwind)
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Map.jsx       # Leaflet Map grid overlays (Nitesh)
│   │   │   ├── Dashboard.jsx # Charts & stats (Riyanshika)
│   │   │   └── Chatbot.jsx   # AI Canopy Chat panel (Riyanshika)
│   │   ├── App.jsx
│   │   └── index.css
│   ├── package.json
│   └── tailwind.config.js
│
└── README.md           # Project presentation and setup instructions
```

---

## 🛠️ 2. Work Division & 3-Day Timeline

```
Day 1: Scaffolding (APIs + Maps) ➔ Day 2: Core Features (Optimization + RAG) ➔ Day 3: Polish & Pitch Video
```

### 📅 Day 1: Scaffolding & Setup
*   **Chirag:**
    1. Initialize FastAPI backend and requirements.
    2. Write the SQLite script to auto-generate a $20 \times 20$ grid of coordinate data for a chosen city (e.g. Kolkata) with random/semi-structured attributes (`base_temperature`, `canopy_cover`, `population_density`, `park_proximity`).
    3. Expose `GET /api/city-grid` (returns the full grid) and `GET /api/cell-stats?lat=...&lon=...`.
*   **Nitesh:**
    1. Initialize the React app with Tailwind CSS.
    2. Install `react-leaflet` or `leaflet`. Render the base map centered on the chosen city coordinates.
    3. Overlay a visual grid of square polygons matching the coordinates returned by Chirag's `GET /api/city-grid`.
*   **Riyanshika:**
    1. Create the general UI layout (Sidebar dashboard + main map area).
    2. Mock the UI sidebar panel that will display the selected cell statistics once Nitesh captures a grid click.

### 📅 Day 2: Core Algorithm, Charts & Chatbot
*   **Chirag:**
    1. Implement `POST /api/optimize` which takes the bounding box and executes the multi-objective priority score. Returns the top 5 coordinates for planting.
    2. Implement RAG using LangChain and a local ChromaDB folder. Feed in 2-3 PDF forestry manuals to recommend tree species. Expose `POST /api/chat` and `GET /api/recommend-trees`.
*   **Nitesh:**
    1. Connect the grid-click action to set the selected coordinates in React state.
    2. When Chirag's optimization API returns planting locations, overlay highlighted green circle markers at those coordinates.
*   **Riyanshika:**
    1. Install `recharts` and build responsive charts to display the selected cell's temperature compared to the city average.
    2. Connect the Chatbot component to Chirag's `/api/chat` endpoint to enable live conversational planning.

### 📅 Day 3: Integration, Deployment & Video Pitch
*   **Team (All):**
    1. Hook the frontend endpoints to point to the live backend.
    2. Deploy the backend (to Render or Railway) and the frontend (to Vercel).
    3. **The Submission Video:** Record a 3-minute screen share highlighting:
       * Selecting a hot red zone in the city.
       * Running the optimizer and seeing green planting zones pop up on the map.
       * Asking the chatbot what tree to plant at those exact coordinates, and showing the RAG engine retrieve local regulatory advice.
       * A walkthrough of the charts showing the projected cooling effect.

---
