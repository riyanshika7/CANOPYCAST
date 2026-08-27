import React from 'react';

export default function Dashboard({ selectedCell, onRunOptimizer }) {
  return (
    <div className="w-full h-full bg-white p-6 border-r border-slate-200 flex flex-col justify-between">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 mb-2">CanopyCast</h1>
        <p className="text-sm text-slate-500 mb-6">Urban Heat Island & Green-Corridor Planner</p>
        
        {selectedCell ? (
          <div className="space-y-4">
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Selected Location</p>
              <p className="text-sm text-slate-700 font-bold">({selectedCell.lat.toFixed(4)}, {selectedCell.lon.toFixed(4)})</p>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-red-50 border border-red-100 rounded-lg">
                <p className="text-xs text-red-500 font-medium">Temperature</p>
                <p className="text-xl font-bold text-red-700">{selectedCell.temp}°C</p>
              </div>
              <div className="p-3 bg-green-50 border border-green-100 rounded-lg">
                <p className="text-xs text-green-500 font-medium">Canopy Cover</p>
                <p className="text-xl font-bold text-green-700">{selectedCell.canopy}%</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-10 bg-slate-50 border border-dashed border-slate-200 rounded-lg">
            <p className="text-sm text-slate-400">Click a neighborhood block on the map to view hyper-local climate stats.</p>
          </div>
        )}
      </div>
      
      <button 
        onClick={onRunOptimizer}
        className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-4 rounded-lg shadow-md transition-colors"
      >
        Optimize Canopy cover
      </button>
    </div>
  );
}
