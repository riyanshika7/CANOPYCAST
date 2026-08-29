import React, { useState } from 'react';
import Map from './components/Map';
import Dashboard from './components/Dashboard';
import Chatbot from './components/Chatbot';

export default function App() {
  const [selectedCell, setSelectedCell] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [isOptimizing, setIsOptimizing] = useState(false);

  const handleCellClick = (cell) => {
    setSelectedCell(cell);
  };

  const handleRunOptimizer = async () => {
    if (isOptimizing) return;
    setIsOptimizing(true);
       setTimeout(() => {
      setRecommendations([
        { lat: 22.5750, lon: 88.3660 },
        { lat: 22.5790, lon: 88.3720 }
      ]);
      setIsOptimizing(false);
    }, 1500);
  };

  return (
    <div className="flex h-screen w-screen bg-slate-100 overflow-hidden font-sans">
      {/* Sidebar - Dashboard Display */}
      <div className="w-80 min-w-[320px] max-w-[360px] h-full shrink-0">
        <Dashboard 
          selectedCell={selectedCell} 
          onRunOptimizer={handleRunOptimizer}
          isOptimizing={isOptimizing}
          recommendations={recommendations}
        />
      </div>

      {/* Main Area - Map & Chatbot */}
      <div className="flex-1 flex flex-col p-6 gap-6 h-full overflow-hidden">
        {/* Map Header Title */}
        <div className="flex justify-between items-center bg-white p-4 rounded-2xl shadow-sm border border-slate-200 shrink-0">
          <div>
            <h2 className="text-base font-bold text-slate-800">Urban Canopy Planner</h2>
            <p className="text-[11px] text-slate-400">Click cells on the grid layer to analyze local surface temperatures and run optimizer.</p>
          </div>
          <div className="flex gap-4 text-[10px] font-semibold text-slate-500">
            <span className="flex items-center gap-1.5"><span className="w-3.5 h-3.5 bg-red-500 rounded-md border border-red-600"></span> Hot Island (&gt;38°C)</span>
            <span className="flex items-center gap-1.5"><span className="w-3.5 h-3.5 bg-emerald-500 rounded-md border border-emerald-600"></span> Cool Space (&lt;32°C)</span>
          </div>
        </div>

        {/* Map Display area */}
        <div className="flex-1 min-h-[250px] relative">
          <Map 
            onCellClick={handleCellClick} 
            recommendations={recommendations} 
          />
        </div>

        {/* Interactive Chatbot */}
        <div className="h-80 shrink-0">
          <Chatbot />
        </div>
      </div>
    </div>
  );
}
