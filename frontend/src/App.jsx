import React, { useState } from 'react';
import Map from './components/Map';
import Dashboard from './components/Dashboard';
import Chatbot from './components/Chatbot';

export default function App() {
  const [selectedCell, setSelectedCell] = useState(null);
  const [recommendations, setRecommendations] = useState([]);

  const handleCellClick = (cell) => {
    setSelectedCell(cell);
  };

  const handleRunOptimizer = async () => {
    // Simulated optimizer call
    setRecommendations([
      { lat: 22.5750, lon: 88.3660 },
      { lat: 22.5790, lon: 88.3720 }
    ]);
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      {/* Sidebar - Dashboard */}
      <div className="w-1/4 min-w-[320px]">
        <Dashboard 
          selectedCell={selectedCell} 
          onRunOptimizer={handleRunOptimizer} 
        />
      </div>

      {/* Main Area - Map & Chatbot */}
      <div className="flex-1 flex flex-col p-6 gap-6 overflow-hidden">
        {/* Map Header */}
        <div className="flex justify-between items-center bg-white p-4 rounded-lg shadow-sm border border-slate-100">
          <div>
            <h2 className="text-lg font-bold text-slate-800">Kolkata City Heat Island Index</h2>
            <p className="text-xs text-slate-400">Click cells on the grid layer to analyze local surface temperatures.</p>
          </div>
          <div className="flex gap-4 text-xs font-semibold">
            <span className="flex items-center gap-1"><span className="w-3 h-3 bg-red-500 rounded-sm"></span> Hot Zone (&gt;38°C)</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 bg-blue-500 rounded-sm"></span> Cool Zone (&lt;32°C)</span>
          </div>
        </div>

        {/* Map visualization area */}
        <div className="flex-1 min-h-[300px]">
          <Map 
            onCellClick={handleCellClick} 
            recommendations={recommendations} 
          />
        </div>

        {/* Chatbot footer panel */}
        <div className="h-96">
          <Chatbot />
        </div>
      </div>
    </div>
  );
}
