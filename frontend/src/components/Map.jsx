import React from "react";
import {
  MapContainer,
  TileLayer,
  Polygon,
  CircleMarker,
  Popup,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";

// ======================================================
// 1. KOLKATA CENTER
// ======================================================

const KOLKATA_CENTER = [22.5726, 88.3639];

// ======================================================
// 2. TEMPORARY GRID DATA
// ======================================================

const GRID = [
  {
    id: 1,
    lat: 22.5726,
    lon: 88.3639,
    temperature: 40,
    canopy_cover: 12,
    population_density: 8500,
  },
  {
    id: 2,
    lat: 22.5756,
    lon: 88.3639,
    temperature: 38,
    canopy_cover: 18,
    population_density: 7200,
  },
  {
    id: 3,
    lat: 22.5786,
    lon: 88.3639,
    temperature: 31,
    canopy_cover: 42,
    population_density: 4000,
  },
  {
    id: 4,
    lat: 22.5726,
    lon: 88.3689,
    temperature: 39,
    canopy_cover: 15,
    population_density: 8100,
  },
  {
    id: 5,
    lat: 22.5756,
    lon: 88.3689,
    temperature: 36,
    canopy_cover: 25,
    population_density: 6500,
  },
  {
    id: 6,
    lat: 22.5786,
    lon: 88.3689,
    temperature: 30,
    canopy_cover: 48,
    population_density: 3500,
  },
  {
    id: 7,
    lat: 22.5726,
    lon: 88.3739,
    temperature: 41,
    canopy_cover: 10,
    population_density: 9000,
  },
  {
    id: 8,
    lat: 22.5756,
    lon: 88.3739,
    temperature: 37,
    canopy_cover: 20,
    population_density: 7000,
  },
  {
    id: 9,
    lat: 22.5786,
    lon: 88.3739,
    temperature: 32,
    canopy_cover: 35,
    population_density: 5000,
  },
];

// ======================================================
// 3. TEMPERATURE COLOR
// ======================================================

function getCellColor(temperature) {
  if (temperature >= 38) {
    return "#ef4444";
  }

  if (temperature >= 32) {
    return "#f59e0b";
  }

  return "#10b981";
}

// ======================================================
// 4. CREATE GRID SQUARE
// ======================================================

function createSquare(lat, lon) {
  const size = 0.0013;

  return [
    [lat - size, lon - size],
    [lat - size, lon + size],
    [lat + size, lon + size],
    [lat + size, lon - size],
  ];
}

// ======================================================
// 5. MAP COMPONENT
// ======================================================

export default function Map({ onCellClick, recommendations }) {
  return (
    <div className="w-full h-full rounded-xl overflow-hidden border border-slate-200 shadow-sm">
      
      <MapContainer
        center={KOLKATA_CENTER}
        zoom={14}
        scrollWheelZoom={true}
        style={{ width: "100%", height: "100%" }}
      >

        {/* ==================================================
            OPENSTREETMAP BASE LAYER
        ================================================== */}

        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* ==================================================
            TEMPERATURE GRID
        ================================================== */}

        {GRID.map((cell) => (
          <Polygon
            key={cell.id}
            positions={createSquare(cell.lat, cell.lon)}
            pathOptions={{
              color: getCellColor(cell.temperature),
              fillColor: getCellColor(cell.temperature),
              fillOpacity: 0.55,
              weight: 1,
            }}
            eventHandlers={{
              click: () => onCellClick(cell),
            }}
          >
            <Popup>
              <div>
                <strong>CanopyCast Grid Cell</strong>

                <p>
                  🌡️ Temperature:{" "}
                  <strong>{cell.temperature}°C</strong>
                </p>

                <p>
                  🌳 Canopy Cover:{" "}
                  <strong>{cell.canopy_cover}%</strong>
                </p>

                <p>
                  👥 Population Density:{" "}
                  <strong>{cell.population_density}</strong>
                </p>

                <p className="text-xs text-gray-500">
                  Click this cell to analyze it.
                </p>
              </div>
            </Popup>
          </Polygon>
        ))}

        {/* ==================================================
            OPTIMIZER RECOMMENDATIONS
        ================================================== */}

        {recommendations?.map((rec, index) => (
          <CircleMarker
            key={index}
            center={[rec.lat, rec.lon]}
            radius={10}
            pathOptions={{
              color: "#166534",
              fillColor: "#22c55e",
              fillOpacity: 0.9,
            }}
          >
            <Popup>
              <strong>🌱 Recommended Planting Site</strong>

              <p>
                Latitude: {rec.lat.toFixed(4)}
              </p>

              <p>
                Longitude: {rec.lon.toFixed(4)}
              </p>
            </Popup>
          </CircleMarker>
        ))}

      </MapContainer>
    </div>
  );
}