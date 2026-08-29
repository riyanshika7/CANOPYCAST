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
    # Bounded: an unbounded top_n returned all 400 cells as one response.
    top_n: int = Field(default=5, ge=1, le=25)


class OptimizeResponse(BaseModel):
    city: str
    sites: list[PlantingSite]
    aggregate_impact: ImpactProjection


class Citation(BaseModel):
    doc_title: str
    page: int
    snippet: str


class TreeRecommendation(BaseModel):
    """One species suggestion, structured so the sidebar can render a card.

    Distinct from the chat answer on purpose: chat is prose for a human reading
    it, this is fields the dashboard lays out.
    """
    common_name: str
    botanical_name: Optional[str] = None
    crown_shape: Optional[str] = Field(
        default=None, description="roundish, umbrella, or columnar"
    )
    mature_height_ft: Optional[float] = None
    why_here: str = Field(description="one line tying the species to this cell")
    caution: Optional[str] = Field(
        default=None, description="storm risk, litter, root spread, if the source says so"
    )
    citations: list["Citation"] = Field(default_factory=list)


class RecommendResponse(BaseModel):
    city: str
    cell_id: Optional[str] = None
    recommendations: list[TreeRecommendation]
    sources: list["Citation"] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str
    session_id: str
    city: str = "Kolkata"
    selected_cell: Optional[Cell] = None


class ChatResponse(BaseModel):
    response: str
    citations: list[Citation]
