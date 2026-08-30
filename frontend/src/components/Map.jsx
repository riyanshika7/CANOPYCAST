import React, { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Polygon,
  CircleMarker,
  Popup,
  useMap
} from "react-leaflet";

import "leaflet/dist/leaflet.css";

// CITY CENTER COORDINATES
const CITY_CENTERS = {
  Kolkata: [22.5726, 88.3639],
  Delhi: [28.6139, 77.2090],
  Goa: [15.4909, 73.8278],
};

// RELATIVE OFFSETS TO BUILD GRID TILES ARROUND SELECTED CITY CENTER
const GRID_OFFSETS = [
  { id: 1, latOff: 0, lonOff: 0, temperature: 40, canopy_cover: 12, population_density: "High", park_proximity: 0.8 },
  { id: 2, latOff: 0.003, lonOff: 0, temperature: 38, canopy_cover: 18, population_density: "High", park_proximity: 1.1 },
  { id: 3, latOff: 0.006, lonOff: 0, temperature: 31, canopy_cover: 42, population_density: "Low", park_proximity: 0.3 },
  { id: 4, latOff: 0, lonOff: 0.005, temperature: 39, canopy_cover: 15, population_density: "High", park_proximity: 1.4 },
  { id: 5, latOff: 0.003, lonOff: 0.005, temperature: 36, canopy_cover: 25, population_density: "Medium", park_proximity: 1.2 },
  { id: 6, latOff: 0.006, lonOff: 0.005, temperature: 30, canopy_cover: 48, population_density: "Low", park_proximity: 0.4 },
  { id: 7, latOff: 0, lonOff: 0.010, temperature: 41, canopy_cover: 10, population_density: "High", park_proximity: 1.6 },
  { id: 8, latOff: 0.003, lonOff: 0.010, temperature: 37, canopy_cover: 20, population_density: "Medium", park_proximity: 1.5 },
  { id: 9, latOff: 0.006, lonOff: 0.010, temperature: 32, canopy_cover: 35, population_density: "Medium", park_proximity: 0.7 },
];

// Dynamically center map view on prop change
function ChangeMapView({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, 14);
    }
  }, [center, map]);
  return null;
}

// 3. MULTI-LAYER CELL COLOR FACTORY
function getCellColor(cell, activeLayers) {
  if (!activeLayers.heat && !activeLayers.canopy && !activeLayers.population && !activeLayers.corridors) {
    return "#e2e8f0";
  }

  // 1. Heat Overlay Color
  if (activeLayers.heat) {
    if (cell.temperature >= 38) return "#ef4444"; // Hot
    if (cell.temperature >= 34) return "#f59e0b"; // Warm
    return "#10b981"; // Cool
  }

  // 2. Canopy Cover Overlay Color
  if (activeLayers.canopy) {
    if (cell.canopy_cover >= 40) return "#15803d"; // Good cover
    if (cell.canopy_cover >= 20) return "#eab308"; // Moderate
    return "#dc2626"; // Critical deficit
  }

  // 3. Population Vulnerability Overlay
  if (activeLayers.population) {
    if (cell.population_density === "High") return "#991b1b"; // High
    if (cell.population_density === "Medium") return "#f97316"; // Medium
    return "#22c55e"; // Low
  }

  // 4. Biodiversity Corridor Linkages
  if (activeLayers.corridors) {
    if (cell.park_proximity <= 0.5) return "#065f46"; // Anchor
    if (cell.park_proximity <= 1.2) return "#34d399"; // Transition
    return "#fbbf24"; // Isolation gap
  }

  return "#e2e8f0";
}

// 4. CELL BOUNDS CREATOR
function createSquare(lat, lon) {
  const size = 0.0013;
  return [
    [lat - size, lon - size],
    [lat - size, lon + size],
    [lat + size, lon + size],
    [lat + size, lon - size],
  ];
}

export default function Map({ onCellClick, recommendations, activeLayers, selectedCity }) {
  const center = CITY_CENTERS[selectedCity] || CITY_CENTERS.Kolkata;

  // Generate grid relative to selected city coordinates
  const localGrid = GRID_OFFSETS.map(cell => ({
    ...cell,
    lat: center[0] + cell.latOff,
    lon: center[1] + cell.lonOff
  }));

  return (
    <div className="w-full h-full rounded-2xl overflow-hidden border border-nature-800/10 shadow-md bg-white">
      <MapContainer
        center={center}
        zoom={14}
        scrollWheelZoom={true}
        style={{ width: "100%", height: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Dynamic panning handler */}
        <ChangeMapView center={center} />

        {/* Dynamic Grid Overlay */}
        {localGrid.map((cell) => {
          const color = getCellColor(cell, activeLayers);
          return (
            <Polygon
              key={cell.id}
              positions={createSquare(cell.lat, cell.lon)}
              pathOptions={{
                color: color,
                fillColor: color,
                fillOpacity: 0.35,
                weight: 1.5,
              }}
              eventHandlers={{
                click: () => onCellClick(cell),
              }}
            >
              <Popup>
                <div className="space-y-1 text-xs">
                  <strong className="text-nature-text font-black block border-b pb-1 mb-1.5 border-slate-100">CanopyCast Index Block</strong>
                  <p className="flex justify-between gap-4 text-slate-600">
                    <span>🌡️ Temperature:</span>
                    <strong className="text-slate-800">{cell.temperature}°C</strong>
                  </p>
                  <p className="flex justify-between gap-4 text-slate-600">
                    <span>🌳 Canopy Cover:</span>
                    <strong className="text-slate-800">{cell.canopy_cover}%</strong>
                  </p>
                  <p className="flex justify-between gap-4 text-slate-600">
                    <span>👥 Population:</span>
                    <strong className="text-slate-800">{cell.population_density}</strong>
                  </p>
                  <p className="flex justify-between gap-4 text-slate-600">
                    <span>📍 Proximity:</span>
                    <strong className="text-slate-800">{cell.park_proximity} km</strong>
                  </p>
                  <p className="text-[10px] text-emerald-700 font-bold mt-2 text-center uppercase tracking-wide">
                    Click to select coordinates
                  </p>
                </div>
              </Popup>
            </Polygon>
          );
        })}

        {/* Recommended Tree-Planting Markers */}
        {recommendations?.map((rec, index) => {
          // Relocate recommendation markers relative to active city center
          const recLat = center[0] + (rec.lat - CITY_CENTERS.Kolkata[0]);
          const recLon = center[1] + (rec.lon - CITY_CENTERS.Kolkata[1]);

          return (
            <CircleMarker
              key={index}
              center={[recLat, recLon]}
              radius={8}
              pathOptions={{
                color: "#166534",
                fillColor: "#4ade80",
                fillOpacity: 0.95,
                weight: 2,
              }}
            >
              <Popup>
                <div className="text-xs space-y-1">
                  <strong className="text-emerald-800 block border-b pb-1 mb-1 border-emerald-100">🌱 Recommended Planting Coordinates</strong>
                  <p className="text-slate-600">Priority Score: <strong className="text-slate-800">{rec.score || 90}/100</strong></p>
                  <p className="text-slate-600">Lat: {recLat.toFixed(5)}</p>
                  <p className="text-slate-600">Lon: {recLon.toFixed(5)}</p>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}