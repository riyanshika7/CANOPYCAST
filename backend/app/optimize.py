"""Multi-objective planting optimizer for urban heat island mitigation."""

from __future__ import annotations

import math
from collections import deque

from .schema import (
    Cell,
    CityGrid,
    ImpactProjection,
    OptimizeResponse,
    PlantingSite,
)

# Default weights for the four scoring terms.
DEFAULT_WEIGHTS: dict[str, float] = {
    "heat": 0.35,
    "deficit": 0.20,
    "people": 0.25,
    "corridor": 0.20,
}

# Canopy cover threshold (%) to classify a cell as "green" for anchor detection.
GREEN_CANOPY_THRESHOLD: float = 45

# Minimum Chebyshev distance between selected sites to enforce spatial spread.
MIN_SEPARATION: int = 2

# Approximate cell side length in metres (~500 m based on CELL_DEG at Kolkata latitude).
CELL_METRES: float = 500.0

# Fraction of an urban cell realistically available for tree planting (order-of-magnitude
# estimate for dense Kolkata neighbourhoods; most area is buildings and roads).
URBAN_PLANTABLE_FRACTION: float = 0.10

# West Bengal TPOFA recommended spacing: 2.5 m x 2.5 m = 6.25 m^2 per tree.
TREE_SPACING_M2: float = 6.25

# Average CO2 sequestered per urban tree per year in kg (order-of-magnitude estimate).
CO2_PER_TREE_KG_YEAR: float = 22.0

# Average stormwater intercepted per tree per year in litres (order-of-magnitude estimate).
STORMWATER_PER_TREE_LITRES_YEAR: float = 15000.0

# Cooling effect per percentage point of canopy deficit, in degrees C
# (order-of-magnitude estimate calibrated so a fully bare cell approaches MAX_COOLING_C).
COOLING_PER_CANOPY_DEFICIT_PCT: float = 0.025

# Maximum cooling effect achievable for any single site, degrees C.
MAX_COOLING_C: float = 2.5


def score_cell(
    cell: Cell,
    grid_stats: dict,
    weights: dict[str, float] | None = None,
) -> tuple[float, dict[str, float]]:
    """Return (weighted_total, breakdown) for a single cell.

    grid_stats must contain:
        grid_min_temp, grid_max_temp,
        corridor_min, corridor_max, corridor_scores (dict cell_id -> raw score)
    """
    w = weights or DEFAULT_WEIGHTS

    # Heat: min-max normalised across grid temperatures.
    temp_range = grid_stats["grid_max_temp"] - grid_stats["grid_min_temp"]
    heat = (cell.base_temperature - grid_stats["grid_min_temp"]) / temp_range if temp_range > 0 else 0.0

    # Canopy deficit: 0 when fully covered, 1 when bare.
    deficit = (100.0 - cell.canopy_cover) / 100.0

    # Population density mapped to 0..1.
    people_map = {"Low": 0.0, "Medium": 0.5, "High": 1.0}
    people = people_map[cell.population_density]

    # Corridor: raw score looked up from pre-computed grid stats, min-max normalised.
    raw_corridor = grid_stats["corridor_scores"].get(cell.cell_id, 0.0)
    c_range = grid_stats["corridor_max"] - grid_stats["corridor_min"]
    corridor = (raw_corridor - grid_stats["corridor_min"]) / c_range if c_range > 0 else 0.0

    breakdown = {
        "heat": heat * w["heat"],
        "deficit": deficit * w["deficit"],
        "people": people * w["people"],
        "corridor": corridor * w["corridor"],
    }
    return sum(breakdown.values()), breakdown


# ---------------------------------------------------------------------------
# Corridor scoring internals
# ---------------------------------------------------------------------------

def _cluster_green_anchors(cells: list[Cell], threshold: float) -> list[list[Cell]]:
    """Cluster contiguous green cells into distinct anchors via BFS flood-fill.

    Two cells are neighbours if Chebyshev distance == 1 (8-connected grid).
    """
    green = {(c.x, c.y): c for c in cells if c.canopy_cover > threshold}
    visited: set[tuple[int, int]] = set()
    anchors: list[list[Cell]] = []

    for pos in green:
        if pos in visited:
            continue
        cluster: list[Cell] = []
        queue = deque([pos])
        visited.add(pos)
        while queue:
            cx, cy = queue.popleft()
            cluster.append(green[(cx, cy)])
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nb = (cx + dx, cy + dy)
                    if nb in green and nb not in visited:
                        visited.add(nb)
                        queue.append(nb)
        anchors.append(cluster)

    return anchors


def _anchor_centroid(anchor: list[Cell]) -> tuple[float, float]:
    """Centroid of an anchor in grid coordinates."""
    n = len(anchor)
    return sum(c.x for c in anchor) / n, sum(c.y for c in anchor) / n


def _chebyshev(a: tuple[float, float], b: tuple[float, float]) -> float:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _euclidean(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _compute_corridor_scores(
    cells: list[Cell],
    canopy_threshold: float = GREEN_CANOPY_THRESHOLD,
) -> dict[str, float]:
    """Compute raw corridor bridging score for every cell.

    A cell scores highest when it lies roughly between two separate green anchors
    and its own canopy is low, indicating it bridges them into a wildlife corridor.

    The score is: bridging_factor * proximity_factor * greenness_penalty

    bridging_factor:
        d_anchor_pair / (d_to_anchor1 + d_to_anchor2).  By the triangle inequality
        this is <= 1, and equals 1 when the cell sits exactly on the line between
        the two nearest anchor centroids.

    proximity_factor:
        max(0, 1 - (d1 + d2) / (2 * grid_diagonal)).  Decays toward zero as the
        cell moves farther from the anchor pair.  Planting in the middle of nowhere
        links nothing.

    greenness_penalty:
        1 - canopy_cover / 100.  A cell already covered by trees contributes nothing
        new to corridor connectivity.

    Three key cases:
    - Inside-green: anchor cells are skipped entirely (score 0).  Non-anchor cells
      with high canopy get a penalty near 0 via greenness_penalty.
    - Isolated-far: large d1+d2 drives both bridging and proximity toward 0.
    - In-the-gap: cell between two anchors with low canopy gives the highest score.
    """
    anchors = _cluster_green_anchors(cells, canopy_threshold)

    # Need at least 2 anchors to form a corridor.
    if len(anchors) < 2:
        return {c.cell_id: 0.0 for c in cells}

    centroids = [_anchor_centroid(a) for a in anchors]

    # Set of cells that belong to a green anchor (get score 0).
    anchor_cell_set: set[tuple[int, int]] = set()
    for a in anchors:
        for c in a:
            anchor_cell_set.add((c.x, c.y))

    # Pre-compute pairwise distances between anchor centroids.
    anchor_pair_dists: dict[tuple[int, int], float] = {}
    for i in range(len(anchors)):
        for j in range(i + 1, len(anchors)):
            anchor_pair_dists[(i, j)] = _euclidean(centroids[i], centroids[j])

    # Grid diagonal for proximity normalisation.
    max_coord = max(max(c.x for c in cells), max(c.y for c in cells))
    grid_diagonal = math.hypot(max_coord, max_coord) if max_coord > 0 else 1.0

    scores: dict[str, float] = {}
    for cell in cells:
        if (cell.x, cell.y) in anchor_cell_set:
            scores[cell.cell_id] = 0.0
            continue

        pos = (float(cell.x), float(cell.y))

        # Two nearest distinct anchors by Euclidean distance to centroid.
        dists = sorted(
            (_euclidean(pos, centroids[i]), i) for i in range(len(anchors))
        )
        d1, idx1 = dists[0]
        d2, idx2 = dists[1]

        pair_key = (min(idx1, idx2), max(idx1, idx2))
        d_pair = anchor_pair_dists[pair_key]

        denom = d1 + d2
        bridging = min(d_pair / denom, 1.0) if denom > 0 else 1.0

        proximity = max(0.0, 1.0 - denom / (2.0 * grid_diagonal))

        greenness = 1.0 - cell.canopy_cover / 100.0

        scores[cell.cell_id] = bridging * proximity * greenness

    return scores


# ---------------------------------------------------------------------------
# Grid-wide stats
# ---------------------------------------------------------------------------

def _build_grid_stats(cells: list[Cell]) -> dict:
    """Pre-compute grid-wide statistics needed by score_cell."""
    temps = [c.base_temperature for c in cells]
    corridor_scores = _compute_corridor_scores(cells)
    c_vals = list(corridor_scores.values())
    return {
        "grid_min_temp": min(temps),
        "grid_max_temp": max(temps),
        "corridor_scores": corridor_scores,
        "corridor_min": min(c_vals) if c_vals else 0.0,
        "corridor_max": max(c_vals) if c_vals else 0.0,
    }


# ---------------------------------------------------------------------------
# Impact projection
# ---------------------------------------------------------------------------

def _compute_impact(cell: Cell) -> ImpactProjection:
    """Impact projection for planting a single cell, with defensible constants."""
    cell_area_m2 = CELL_METRES * CELL_METRES
    canopy_deficit_pct = max(0.0, 100.0 - cell.canopy_cover)

    # Only the unplanted share of the plantable area is available. Without this
    # the tree count is a constant and every site reports identical impact,
    # which reads as a hardcoded number on the dashboard.
    plantable_m2 = cell_area_m2 * URBAN_PLANTABLE_FRACTION * (canopy_deficit_pct / 100.0)
    trees = int(plantable_m2 / TREE_SPACING_M2)

    cooling = min(canopy_deficit_pct * COOLING_PER_CANOPY_DEFICIT_PCT, MAX_COOLING_C)

    co2 = trees * CO2_PER_TREE_KG_YEAR
    stormwater = trees * STORMWATER_PER_TREE_LITRES_YEAR

    return ImpactProjection(
        trees_recommended=trees,
        estimated_cooling_effect_c=round(cooling, 2),
        co2_sequestration_kg_per_year=round(co2, 1),
        stormwater_litres_diverted_per_year=round(stormwater, 1),
    )


# ---------------------------------------------------------------------------
# Rationale
# ---------------------------------------------------------------------------

def _dominant_term(breakdown: dict[str, float]) -> str:
    return max(breakdown, key=breakdown.get)


def _make_rationale(cell: Cell, breakdown: dict[str, float]) -> str:
    """One-sentence plain-English rationale naming the dominant term."""
    dominant = _dominant_term(breakdown)
    templates = {
        "heat": f"{cell.base_temperature:.1f} C with only {cell.canopy_cover:.0f} percent canopy",
        "deficit": f"only {cell.canopy_cover:.0f} percent canopy cover despite high heat exposure",
        "people": (
            f"high population density with {cell.canopy_cover:.0f} percent canopy and "
            f"{cell.base_temperature:.1f} C surface temp"
        ),
        "corridor": (
            f"low canopy ({cell.canopy_cover:.0f} percent) bridging two separate green areas"
        ),
    }
    core = templates.get(dominant, "scored highest overall")
    return f"{core}, prioritized for greening."


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def optimise(
    grid: CityGrid,
    top_n: int = 5,
    weights: dict[str, float] | None = None,
) -> OptimizeResponse:
    """Return the top_n planting sites with spatial spread enforcement.

    Greedy selection: pick the highest-scoring cell, suppress its Chebyshev
    neighbours within MIN_SEPARATION, repeat.  If suppression reduces candidates
    below top_n, relax the constraint and fill from the remaining pool.
    """
    cells = grid.cells
    if not cells:
        return OptimizeResponse(
            city=grid.city,
            sites=[],
            aggregate_impact=ImpactProjection(
                trees_recommended=0,
                estimated_cooling_effect_c=0.0,
                co2_sequestration_kg_per_year=0.0,
                stormwater_litres_diverted_per_year=0.0,
            ),
        )

    grid_stats = _build_grid_stats(cells)
    w = weights or DEFAULT_WEIGHTS

    scored: list[tuple[float, dict[str, float], Cell]] = []
    for cell in cells:
        total, breakdown = score_cell(cell, grid_stats, w)
        scored.append((total, breakdown, cell))
    scored.sort(key=lambda x: x[0], reverse=True)

    # Greedy selection with Chebyshev spread enforcement.
    selected: list[tuple[float, dict[str, float], Cell]] = []
    suppressed: set[str] = set()
    remaining = list(scored)

    while remaining and len(selected) < top_n:
        total, breakdown, cell = remaining.pop(0)
        if cell.cell_id in suppressed:
            continue
        selected.append((total, breakdown, cell))
        for _, _, other in remaining:
            if _chebyshev((cell.x, cell.y), (other.x, other.y)) < MIN_SEPARATION:
                suppressed.add(other.cell_id)

    # Relax spatial constraint if we still need more sites.
    if len(selected) < top_n:
        selected_ids = {s[2].cell_id for s in selected}
        for total, breakdown, cell in scored:
            if len(selected) >= top_n:
                break
            if cell.cell_id not in selected_ids:
                selected.append((total, breakdown, cell))
                selected_ids.add(cell.cell_id)

    sites: list[PlantingSite] = []
    for total, breakdown, cell in selected:
        impact = _compute_impact(cell)
        sites.append(
            PlantingSite(
                cell_id=cell.cell_id,
                lat=cell.lat,
                lon=cell.lon,
                priority_score=round(total, 4),
                score_breakdown={k: round(v, 4) for k, v in breakdown.items()},
                rationale=_make_rationale(cell, breakdown),
                impact=impact,
            )
        )

    agg = ImpactProjection(
        trees_recommended=sum(s.impact.trees_recommended for s in sites),
        # Cooling is local to each site and does not add across the city. Summing
        # it would claim the whole city drops 11 C, which is indefensible. This is
        # the mean cooling a planted site sees.
        estimated_cooling_effect_c=(
            round(sum(s.impact.estimated_cooling_effect_c for s in sites) / len(sites), 2)
            if sites else 0.0
        ),
        co2_sequestration_kg_per_year=round(sum(s.impact.co2_sequestration_kg_per_year for s in sites), 1),
        stormwater_litres_diverted_per_year=round(sum(s.impact.stormwater_litres_diverted_per_year for s in sites), 1),
    )

    return OptimizeResponse(city=grid.city, sites=sites, aggregate_impact=agg)
