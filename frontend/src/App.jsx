import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import LandingPage from './components/LandingPage';
import Map from './components/Map';
import Dashboard from './components/Dashboard';
import Chatbot from './components/Chatbot';

export default function App() {
  // Navigation view: 'landing' or 'planner'
  const [currentView, setView] = useState('landing');
  
  // Selected map coordinates/cell details
  const [selectedCell, setSelectedCell] = useState(null);
  
  // Array of coordinates optimized for tree planting
  const [recommendations, setRecommendations] = useState([]);
  
  // Active city selector
  const [selectedCity, setSelectedCity] = useState("Kolkata");
  
  // Optimizer calculating animation state
  const [isOptimizing, setIsOptimizing] = useState(false);
  
  // Active map display layers toggles
  const [activeLayers, setActiveLayers] = useState({
    heat: true,
    canopy: false,
    population: false,
    corridors: false
  });

  const handleCityChange = (city) => {
    setSelectedCity(city);
    setSelectedCell(null);
    setRecommendations([]);
  };

  const handleCellClick = (cell) => {
    setSelectedCell(cell);
  };

  const handleRunOptimizer = async () => {
    if (isOptimizing) return;
    setIsOptimizing(true);
    
    // Simulate API fetch delay (GET /api/optimize)
    setTimeout(() => {
      setRecommendations([
        { lat: 22.5756, lon: 88.3639, score: 94 },
        { lat: 22.5726, lon: 88.3689, score: 88 },
        { lat: 22.5786, lon: 88.3689, score: 82 }
      ]);
      setIsOptimizing(false);
    }, 1800);
  };

  const toggleLayer = (layerName) => {
    setActiveLayers(prev => ({
      ...prev,
      [layerName]: !prev[layerName]
    }));
  };

  return (
    <div className="min-h-screen bg-nature-bg flex flex-col font-sans">
      {/* Sticky Translucent Header */}
      <Navbar currentView={currentView} setView={setView} />

      {/* Main Content Router */}
      {currentView === 'landing' ? (
        <>
          <LandingPage setView={setView} />
          <Footer setView={setView} />
        </>
      ) : (
        /* Planner Workspace View */
        <div className="flex-1 pt-[73px] h-screen flex flex-col overflow-hidden">
          
          {/* Top Control Bar */}
          <div className="bg-white border-b border-nature-800/10 py-3 px-6 flex flex-col sm:flex-row justify-between items-center gap-4 shrink-0 shadow-sm z-20">
            <div className="flex items-center gap-3">
              <span className="text-xs font-bold text-nature-secText uppercase tracking-wider">City Selector</span>
              <select 
                value={selectedCity}
                onChange={(e) => handleCityChange(e.target.value)}
                className="border border-nature-800/15 rounded-lg py-1.5 px-3.5 text-xs text-nature-text font-bold focus:outline-none focus:ring-1 focus:ring-nature-800 bg-nature-bg"
              >
                <option value="Kolkata">Kolkata, WB</option>
                <option value="Delhi">Delhi, NCT</option>
                <option value="Goa">Goa, GA</option>
              </select>
            </div>
            
            <button
              onClick={handleRunOptimizer}
              disabled={isOptimizing}
              className="bg-nature-800 hover:bg-nature-900 disabled:bg-nature-300 text-white font-bold text-xs py-2.5 px-6 rounded-full shadow-sm hover:shadow-md transition-all flex items-center gap-1.5"
            >
              {isOptimizing ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Analyzing Urban Grid...</span>
                </>
              ) : (
                <>
                  <span>Optimize Green Canopy</span>
                </>
              )}
            </button>
          </div>

          {/* Main Map Workspace Layout */}
          <div className="flex-1 flex overflow-hidden relative">
            
            {/* Left Layer Panel Toolbar */}
            <div className="w-48 bg-white border-r border-nature-800/10 p-4 space-y-5 flex flex-col justify-start shrink-0 z-10">
              <h3 className="text-[10px] font-black text-nature-secText uppercase tracking-wider">Map Layers</h3>
              
              <div className="space-y-3">
                {Object.keys(activeLayers).map((layer) => (
                  <button
                    key={layer}
                    onClick={() => toggleLayer(layer)}
                    className={`w-full flex items-center justify-between p-2.5 rounded-lg text-xs font-bold transition-all border ${
                      activeLayers[layer] 
                        ? 'bg-nature-100 border-nature-300 text-nature-800 shadow-sm' 
                        : 'bg-white border-slate-100 text-nature-secText hover:bg-slate-50'
                    }`}
                  >
                    <span className="capitalize">{layer}</span>
                    <span className={`w-2 h-2 rounded-full ${activeLayers[layer] ? 'bg-nature-800 animate-pulse' : 'bg-slate-300'}`}></span>
                  </button>
                ))}
              </div>
            </div>

            {/* Center Map View (Dominant component) */}
            <div className="flex-1 min-h-0 relative">
              <div className="absolute inset-0">
                <Map 
                  onCellClick={handleCellClick} 
                  recommendations={recommendations}
                  activeLayers={activeLayers}
                  selectedCity={selectedCity}
                />
              </div>
            </div>

            {/* Right Sidebar Dashboard Metrics */}
            <div className="w-80 border-l border-nature-800/10 h-full shrink-0 z-10">
              <Dashboard 
                selectedCell={selectedCell} 
                onRunOptimizer={handleRunOptimizer}
                isOptimizing={isOptimizing}
                recommendations={recommendations}
                selectedCity={selectedCity}
              />
            </div>
          </div>

        </div>
      )}

      {/* Floating Expandable Chatbot Panel */}
      {currentView === 'planner' && <Chatbot selectedCell={selectedCell} selectedCity={selectedCity} />}
    </div>
  );
}