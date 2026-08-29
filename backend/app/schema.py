"""Shared API contract. Every module and the frontend agree on these shapes.

Owned by main.py's author. Workers read this and do not edit it.
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field

Density = Literal["Low", "Medium", "High"]

CITY_CENTRES = {"Kolkata": (22.5726, 88.3639)}

GRID_SIZE = 20
CELL_DEG = 0.0045  # ~500m per cell at Kolkata's latitude


class Cell(BaseModel):
    cell_id: str = Field(description="stable id, 'x_y' in grid coordinates")
    x: int
    y: int
    lat: float
    lon: float
    base_temperature: float = Field(description="surface temp, degrees C")
    canopy_cover: float = Field(description="percent tree cover, 0-100")
    population_density: Density
    park_proximity_km: float = Field(description="km to nearest major green space")


class CityGrid(BaseModel):
    city: str
    grid_size: int
    cell_deg: float
    city_mean_temperature: float
    cells: list[Cell]


class ImpactProjection(BaseModel):
    estimated_cooling_effect_c: float
    co2_sequestration_kg_per_year: float
    stormwater_litres_diverted_per_year: float
    trees_recommended: int


class PlantingSite(BaseModel):
    cell_id: str
    lat: float
    lon: float
    priority_score: float
    # per-term contributions, so the sidebar can explain WHY a site won
    score_breakdown: dict[str, float]
    rationale: str
    impact: ImpactProjection


class OptimizeRequest(BaseModel):
    city: str = "Kolkata"
    selected_cell_id: Optional[str] = None
    top_n: int = 5


class OptimizeResponse(BaseModel):
    city: str
    sites: list[PlantingSite]
    aggregate_impact: ImpactProjection


class Citation(BaseModel):
    doc_title: str
    page: int
    snippet: str


class ChatRequest(BaseModel):
    message: str
    session_id: str
    city: str = "Kolkata"
    selected_cell: Optional[Cell] = None


class ChatResponse(BaseModel):
    response: str
    citations: list[Citation]
