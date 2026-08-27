import React from 'react';

export default function Map({ onCellClick, recommendations }) {
  return (
    <div className="w-full h-full bg-slate-100 flex items-center justify-center border border-slate-200 rounded-lg relative overflow-hidden">
      <div className="text-center p-6">
        <p className="text-slate-500 font-semibold mb-2">Leaflet Interactive Map Area</p>
        <p className="text-xs text-slate-400">Grid cells color-coded by temperature will render here.</p>
      </div>
      
      {/* Recommended Coordinates overlay preview */}
      {recommendations && recommendations.length > 0 && (
        <div className="absolute bottom-4 right-4 bg-white p-3 shadow-md rounded-md text-xs border border-slate-100">
          <p className="font-bold text-green-600 mb-1">Recommended Planting Coordinates:</p>
          <ul>
            {recommendations.map((rec, i) => (
              <li key={i}>Site {i+1}: ({rec.lat.toFixed(4)}, {rec.lon.toFixed(4)})</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
