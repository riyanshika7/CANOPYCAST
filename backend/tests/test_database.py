import math
from pathlib import Path

import pytest

from app.database import (
    city_mean_temperature,
    get_cell,
    get_cell_by_latlon,
    get_city_grid,
    init_db,
    seed_city,
)
from app.schema import CELL_DEG, GRID_SIZE


@pytest.fixture
def db(tmp_path: Path) -> str:
    path = str(tmp_path / "canopycast.db")
    init_db(path)
    seed_city(path, city="Kolkata", seed=42)
    return path


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy)


def test_init_db_idempotent(tmp_path: Path) -> None:
    path = str(tmp_path / "empty.db")
    init_db(path)
    init_db(path)
    seed_city(path)
    assert len(get_city_grid(path, "Kolkata").cells) == GRID_SIZE * GRID_SIZE


def test_temperature_range_kolkata_summer(db: str) -> None:
    temps = [c.base_temperature for c in get_city_grid(db, "Kolkata").cells]
    assert min(temps) >= 28.0
    assert max(temps) <= 42.0
    assert min(temps) < 32.0
    assert max(temps) > 38.0


def test_temp_canopy_anticorrelated(db: str) -> None:
    cells = get_city_grid(db, "Kolkata").cells
    temps = [c.base_temperature for c in cells]
    canopy = [c.canopy_cover for c in cells]
    assert _pearson(temps, canopy) < -0.5
    assert all(2.0 <= c.canopy_cover <= 100.0 for c in cells)


def test_cell_ids_unique_and_shaped(db: str) -> None:
    cells = get_city_grid(db, "Kolkata").cells
    ids = [c.cell_id for c in cells]
    assert len(ids) == GRID_SIZE * GRID_SIZE
    assert len(set(ids)) == len(ids)
    for cell in cells:
        assert cell.cell_id == f"{cell.x}_{cell.y}"
        assert 0 <= cell.x < GRID_SIZE
        assert 0 <= cell.y < GRID_SIZE


def test_seed_twice_identical(tmp_path: Path) -> None:
    a = str(tmp_path / "a.db")
    b = str(tmp_path / "b.db")
    seed_city(a, city="Kolkata", seed=42)
    seed_city(b, city="Kolkata", seed=42)
    ga = get_city_grid(a, "Kolkata")
    gb = get_city_grid(b, "Kolkata")
    assert ga.cells == gb.cells
    seed_city(a, city="Kolkata", seed=42)
    assert get_city_grid(a, "Kolkata").cells == ga.cells


def test_get_cell_by_latlon_snaps_inside_cell(db: str) -> None:
    target = get_cell(db, "Kolkata", "5_7")
    assert target is not None
    assert get_cell_by_latlon(db, "Kolkata", target.lat, target.lon) == target
    inside_lat = target.lat + CELL_DEG * 0.2
    inside_lon = target.lon - CELL_DEG * 0.2
    snapped = get_cell_by_latlon(db, "Kolkata", inside_lat, inside_lon)
    assert snapped is not None
    assert snapped.cell_id == "5_7"


def test_get_cell_missing(db: str) -> None:
    assert get_cell(db, "Kolkata", "99_99") is None


def test_city_mean_temperature(db: str) -> None:
    grid = get_city_grid(db, "Kolkata")
    mean = city_mean_temperature(db, "Kolkata")
    expected = sum(c.base_temperature for c in grid.cells) / len(grid.cells)
    assert mean == pytest.approx(expected)
    assert mean == pytest.approx(grid.city_mean_temperature)


def test_park_proximity_is_geometric(db: str) -> None:
    cells = get_city_grid(db, "Kolkata").cells
    proximities = [c.park_proximity_km for c in cells]
    assert min(proximities) < 0.5
    assert max(proximities) > 3.0
    assert all(p >= 0.0 for p in proximities)
    by_id = {c.cell_id: c for c in cells}
    # Maidan sits near (6.5, 7.2); that cell must be closer than a far western corner.
    assert by_id["7_7"].park_proximity_km < by_id["0_19"].park_proximity_km
