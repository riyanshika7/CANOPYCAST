"""Synthetic city grid stored in SQLite. Kolkata is built from named spatial features."""
import math
import random
import sqlite3

from .schema import CELL_DEG, CITY_CENTRES, GRID_SIZE, Cell, CityGrid

# Background summer air temp; hotspots and parks are signed offsets from this.
_BASE_TEMP_C = 34.2
_TEMP_JITTER_C = 0.35
_KM_PER_DEG_LAT = 111.32

# (x, y, amplitude_C, sigma_cells). (0, 0) is the SW cell.
_HOTSPOTS = (
    (10.2, 10.4, 7.0, 2.8),  # CBD / Esplanade: dense concrete
    (8.0, 14.0, 5.8, 2.3),  # Burrabazar market district
    (3.2, 9.0, 5.2, 2.2),  # western industrial / Howrah-facing
)
_GREENS = (
    (6.5, 7.2, 6.2, 2.7),  # Maidan
    (10.5, 2.8, 5.4, 2.0),  # south lake
    (17.2, 8.8, 6.8, 3.1),  # East Kolkata Wetlands
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cells (
    city TEXT NOT NULL,
    cell_id TEXT NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    base_temperature REAL NOT NULL,
    canopy_cover REAL NOT NULL,
    population_density TEXT NOT NULL
        CHECK (population_density IN ('Low', 'Medium', 'High')),
    park_proximity_km REAL NOT NULL,
    PRIMARY KEY (city, cell_id)
);
"""


def _origin(city: str) -> tuple[float, float]:
    if city not in CITY_CENTRES:
        raise ValueError(f"unknown city: {city!r}")
    clat, clon = CITY_CENTRES[city]
    half = GRID_SIZE * CELL_DEG / 2.0
    return clat - half, clon - half


def _centre_latlon(x: float, y: float, origin_lat: float, origin_lon: float) -> tuple[float, float]:
    return origin_lat + (y + 0.5) * CELL_DEG, origin_lon + (x + 0.5) * CELL_DEG


def _euclidean_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    mid = math.radians((lat1 + lat2) / 2.0)
    dy = (lat1 - lat2) * _KM_PER_DEG_LAT
    dx = (lon1 - lon2) * _KM_PER_DEG_LAT * math.cos(mid)
    return math.hypot(dx, dy)


def _gaussian_field(x: float, y: float, features: tuple) -> float:
    total = 0.0
    for fx, fy, amp, sigma in features:
        d = math.hypot(x - fx, y - fy)
        total += amp * math.exp(-0.5 * (d / sigma) ** 2)
    return total


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_cell(row: sqlite3.Row) -> Cell:
    return Cell(
        cell_id=row["cell_id"],
        x=row["x"],
        y=row["y"],
        lat=row["lat"],
        lon=row["lon"],
        base_temperature=row["base_temperature"],
        canopy_cover=row["canopy_cover"],
        population_density=row["population_density"],
        park_proximity_km=row["park_proximity_km"],
    )


def _density(min_core_d: float, min_green_d: float) -> str:
    # Parks and wetlands are not residential even when they sit near a core.
    if min_green_d < 1.6:
        return "Low"
    if min_core_d < 2.4:
        return "High"
    if min_core_d < 6.0:
        return "Medium"
    return "Low"


def _generate_cells(city: str, rng: random.Random) -> list[tuple]:
    origin_lat, origin_lon = _origin(city)
    green_latlon = [_centre_latlon(gx, gy, origin_lat, origin_lon) for gx, gy, *_ in _GREENS]
    rows: list[tuple] = []
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            lat, lon = _centre_latlon(x, y, origin_lat, origin_lon)
            heat = _gaussian_field(x, y, _HOTSPOTS)
            cool = _gaussian_field(x, y, _GREENS)
            temp = _BASE_TEMP_C + heat - cool + rng.uniform(-_TEMP_JITTER_C, _TEMP_JITTER_C)
            temp = max(28.1, min(41.7, temp))
            # Hot pavement is bare; residual noise keeps the map from looking painted.
            frac = (temp - 28.0) / 14.0
            canopy = 80.0 - 70.0 * frac + rng.gauss(0.0, 5.5)
            canopy = max(2.0, min(92.0, canopy))
            min_core = min(math.hypot(x - hx, y - hy) for hx, hy, *_ in _HOTSPOTS)
            min_green = min(math.hypot(x - gx, y - gy) for gx, gy, *_ in _GREENS)
            park_km = min(_euclidean_km(lat, lon, glat, glon) for glat, glon in green_latlon)
            rows.append(
                (
                    city,
                    f"{x}_{y}",
                    x,
                    y,
                    lat,
                    lon,
                    temp,
                    canopy,
                    _density(min_core, min_green),
                    park_km,
                )
            )
    return rows


def init_db(db_path: str) -> None:
    conn = _connect(db_path)
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def seed_city(db_path: str, city: str = "Kolkata", seed: int = 42) -> None:
    init_db(db_path)
    rng = random.Random(seed)
    rows = _generate_cells(city, rng)
    conn = _connect(db_path)
    try:
        conn.execute("DELETE FROM cells WHERE city = ?", (city,))
        conn.executemany(
            """
            INSERT INTO cells (
                city, cell_id, x, y, lat, lon,
                base_temperature, canopy_cover, population_density, park_proximity_km
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def get_city_grid(db_path: str, city: str) -> CityGrid:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "SELECT * FROM cells WHERE city = ? ORDER BY y, x",
            (city,),
        )
        cells = [_row_to_cell(row) for row in cur]
    finally:
        conn.close()
    mean = (
        sum(c.base_temperature for c in cells) / len(cells) if cells else 0.0
    )
    return CityGrid(
        city=city,
        grid_size=GRID_SIZE,
        cell_deg=CELL_DEG,
        city_mean_temperature=mean,
        cells=cells,
    )


def get_cell(db_path: str, city: str, cell_id: str) -> Cell | None:
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM cells WHERE city = ? AND cell_id = ?",
            (city, cell_id),
        ).fetchone()
    finally:
        conn.close()
    return _row_to_cell(row) if row is not None else None


def get_cell_by_latlon(db_path: str, city: str, lat: float, lon: float) -> Cell | None:
    origin_lat, origin_lon = _origin(city)
    x = math.floor((lon - origin_lon) / CELL_DEG)
    y = math.floor((lat - origin_lat) / CELL_DEG)
    x = max(0, min(GRID_SIZE - 1, x))
    y = max(0, min(GRID_SIZE - 1, y))
    return get_cell(db_path, city, f"{x}_{y}")


def city_mean_temperature(db_path: str, city: str) -> float:
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT AVG(base_temperature) FROM cells WHERE city = ?",
            (city,),
        ).fetchone()
    finally:
        conn.close()
    if row is None or row[0] is None:
        raise ValueError(f"no cells for city {city!r}")
    return float(row[0])


if __name__ == "__main__":
    db_path = "./canopycast.db"
    init_db(db_path)
    seed_city(db_path, city="Kolkata", seed=42)
