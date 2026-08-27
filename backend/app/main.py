from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CanopyCast API")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to CanopyCast API"}

@app.get("/api/city-grid")
def get_city_grid(city: str = "Kolkata"):
    # TODO: Fetch synthetic grid data from SQLite
    return {
        "city": city,
        "grid": [
            {"lat": 22.5726, "lon": 88.3639, "temp": 38.5, "canopy": 12.0},
            {"lat": 22.5800, "lon": 88.3700, "temp": 39.1, "canopy": 8.0},
        ]
    }

@app.get("/api/cell-stats")
def get_cell_stats(lat: float, lon: float):
    # TODO: Return specific statistics for the clicked cell
    return {
        "latitude": lat,
        "longitude": lon,
        "temperature": 38.5,
        "canopy_cover_percentage": 12.0,
        "population_density": "High",
        "nearest_park_distance_km": 1.4
    }

@app.post("/api/optimize")
def run_optimization(bounds: dict):
    # TODO: Implement priority score calculations and return top planting sites
    return {
        "recommendations": [
            {"lat": 22.5750, "lon": 88.3660, "priority_score": 94.2},
            {"lat": 22.5790, "lon": 88.3720, "priority_score": 88.7}
        ]
    }

@app.post("/api/chat")
def chatbot_interaction(message: dict):
    # TODO: Implement RAG query to return tree recommendations
    return {
        "response": "For this area, planting Neem (Azadirachta indica) is highly recommended. It has an average mature crown radius of 5 meters and excellent heat tolerance."
    }
