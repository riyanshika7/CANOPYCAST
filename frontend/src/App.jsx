import React, { useState } from "react";
import Map from "./components/Map";
import Dashboard from "./components/Dashboard";
import Chatbot from "./components/Chatbot";

export default function App() {
  // ======================================================
  // STATE
  // ======================================================

  // Stores the grid cell selected by the user
  const [selectedCell, setSelectedCell] = useState(null);

  // Stores optimizer's recommended planting locations
  const [recommendations, setRecommendations] = useState([]);

  // Controls optimizer loading state
  const [isOptimizing, setIsOptimizing] = useState(false);

  // ======================================================
  // HANDLE MAP CELL CLICK
  // ======================================================

  const handleCellClick = (cell) => {
    setSelectedCell(cell);
  };

  // ======================================================
  // TEMPORARY GREEN CANOPY OPTIMIZER
  // ======================================================

  const handleRunOptimizer = () => {
    // Prevent multiple clicks while optimizer is running
    if (isOptimizing) return;

    setIsOptimizing(true);

    // Temporary simulation of backend/AI calculation
    setTimeout(() => {
      setRecommendations([
        {
          lat: 22.5750,
          lon: 88.3660,
        },
        {
          lat: 22.5790,
          lon: 88.3720,
        },
      ]);

      setIsOptimizing(false);
    }, 1500);
  };

  // ======================================================
  // APPLICATION UI
  // ======================================================

  return (
    <div className="flex h-screen w-screen bg-slate-100 overflow-hidden font-sans">

      {/* ==================================================
          LEFT SIDEBAR
      ================================================== */}

      <div className="w-80 min-w-[320px] max-w-[360px] h-full shrink-0">
        <Dashboard
          selectedCell={selectedCell}
          onRunOptimizer={handleRunOptimizer}
          isOptimizing={isOptimizing}
          recommendations={recommendations}
        />
      </div>

      {/* ==================================================
          RIGHT MAIN AREA
      ================================================== */}

      <div className="flex-1 min-w-0 h-full flex flex-col p-6 gap-6 overflow-hidden">

        {/* ==================================================
            MAP HEADER
        ================================================== */}

        <div className="flex justify-between items-center bg-white p-4 rounded-2xl shadow-sm border border-slate-200 shrink-0">

          <div>
            <h2 className="text-base font-bold text-slate-800">
              Urban Canopy Planner
            </h2>

            <p className="text-[11px] text-slate-400">
              Click cells on the grid layer to analyze local surface
              temperatures and run optimizer.
            </p>
          </div>

          {/* Temperature Legend */}

          <div className="flex gap-4 text-[10px] font-semibold text-slate-500">

            <span className="flex items-center gap-1.5">
              <span className="w-3.5 h-3.5 bg-red-500 rounded-md border border-red-600"></span>
              Hot Island (&gt;38°C)
            </span>

            <span className="flex items-center gap-1.5">
              <span className="w-3.5 h-3.5 bg-emerald-500 rounded-md border border-emerald-600"></span>
              Cool Space (&lt;32°C)
            </span>

          </div>
        </div>

        {/* ==================================================
            MAP CONTAINER
        ================================================== */}

        <div className="flex-1 min-h-0 relative">

          {/* 
            This wrapper gives Leaflet a definite width and height.
            This is important because Leaflet maps need an actual
            rendered height.
          */}

          <div className="absolute inset-0">

            <Map
              onCellClick={handleCellClick}
              recommendations={recommendations}
            />

          </div>

        </div>

        {/* ==================================================
            CHATBOT
        ================================================== */}

        <div className="h-80 shrink-0">

          <Chatbot />

        </div>

      </div>
    </div>
  );
}