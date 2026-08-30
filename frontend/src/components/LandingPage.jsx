import React, { useState, useEffect } from 'react';
import { 
  ArrowRight, Thermometer, Leaf, Network, Sparkles, 
  Users, Milestone, ChevronRight, Activity, ArrowUpRight 
} from 'lucide-react';

export default function LandingPage({ setView }) {
  // 1. Heat Island drag comparison state
  const [sliderVal, setSliderVal] = useState(50);
  
  // 2. Interactive algorithm simulator weights
  const [weights, setWeights] = useState({
    heat: 80,
    canopy: 70,
    population: 90,
    corridor: 60
  });

  const getScore = () => {
    const sum = weights.heat + weights.canopy + weights.population + weights.corridor;
    return Math.round((sum / 400) * 100);
  };

  // 3. Simulated city-map visual updates (pulsing highlights)
  const [activeCell, setActiveCell] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveCell(prev => (prev + 1) % 6);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-nature-bg min-h-screen text-nature-text pt-24 overflow-x-hidden">
      
      {/* ==================================================
          1. HERO SECTION
      ================================================== */}
      <header id="overview" className="relative max-w-7xl mx-auto px-6 pt-8 pb-16 md:py-24 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        
        {/* Subtle Map Contour/Contour Background lines */}
        <div className="absolute inset-0 -z-10 opacity-30 select-none pointer-events-none">
          <svg className="w-full h-full text-nature-300" viewBox="0 0 100 100" preserveAspectRatio="none">
            <path d="M 0,40 Q 25,60 50,40 T 100,40" fill="none" stroke="currentColor" strokeWidth="0.1" />
            <path d="M 0,60 Q 25,40 50,60 T 100,60" fill="none" stroke="currentColor" strokeWidth="0.1" />
            <path d="M 0,80 Q 25,70 50,80 T 100,80" fill="none" stroke="currentColor" strokeWidth="0.1" />
          </svg>
        </div>

        {/* Text Area */}
        <div className="lg:col-span-6 space-y-6 text-left">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold text-nature-800 bg-nature-100 border border-nature-300 uppercase tracking-widest">
            <Sparkles className="w-3 h-3 text-nature-800 animate-pulse" />
            AI-Powered Urban Climate Planning
          </span>
          
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-nature-text tracking-tight leading-[1.05]">
            Cooler streets.<br />
            Connected <span className="text-nature-800">canopies</span>.<br />
            Resilient cities.
          </h1>

          <p className="text-sm md:text-base text-nature-secText max-w-lg leading-relaxed">
            CanopyCast identifies where trees can create the greatest cooling, ecological, and community impact — block by block.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <button
              onClick={() => setView('planner')}
              className="flex items-center justify-center gap-1 bg-nature-800 hover:bg-nature-900 text-white font-bold text-xs py-3.5 px-7 rounded-full shadow-md hover:shadow-lg transition-custom group"
            >
              <span>Explore the Planner</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              onClick={() => {
                document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="flex items-center justify-center gap-1 border border-nature-800/20 hover:border-nature-800/40 text-nature-text bg-white font-bold text-xs py-3.5 px-7 rounded-full transition-custom"
            >
              <span>See How It Works</span>
            </button>
          </div>
        </div>

        {/* Hero Visual: Simulated City Map Preview */}
        <div className="lg:col-span-6 flex justify-center">
          <div className="relative w-full max-w-[500px] h-[360px] bg-white rounded-2xl shadow-xl border border-nature-800/10 p-4 flex flex-col justify-between overflow-hidden transition-custom hover:shadow-2xl">
            {/* Street Grid Mock */}
            <div className="absolute inset-0 p-4 opacity-75">
              <div className="w-full h-full rounded-xl border border-slate-100 bg-slate-50/50 relative overflow-hidden">
                {/* Simulated Street Grid Line SVGs */}
                <svg className="w-full h-full text-slate-200" stroke="currentColor" strokeWidth="2">
                  <line x1="20%" y1="0" x2="20%" y2="100%" />
                  <line x1="55%" y1="0" x2="55%" y2="100%" />
                  <line x1="80%" y1="0" x2="80%" y2="100%" />
                  <line x1="0" y1="35%" x2="100%" y2="35%" />
                  <line x1="0" y1="70%" x2="100%" y2="70%" />
                </svg>

                {/* Simulated Grid Blocks */}
                <div className={`absolute top-[4%] left-[4%] w-[12%] h-[27%] rounded-md border border-red-200 bg-red-500/10 flex items-center justify-center transition-all duration-700 ${activeCell === 0 ? 'bg-red-500/20 border-red-400 scale-[1.02]' : ''}`}>
                  <span className="text-[9px] font-bold text-red-600">41.8°C</span>
                </div>
                <div className={`absolute top-[4%] left-[24%] w-[27%] h-[27%] rounded-md border border-amber-200 bg-amber-500/10 flex items-center justify-center transition-all duration-700 ${activeCell === 1 ? 'bg-amber-500/20 border-amber-400 scale-[1.02]' : ''}`}>
                  <span className="text-[9px] font-bold text-amber-600">36.2°C</span>
                </div>
                <div className={`absolute top-[4%] left-[59%] w-[17%] h-[27%] rounded-md border border-emerald-200 bg-emerald-500/10 flex items-center justify-center transition-all duration-700 ${activeCell === 2 ? 'bg-emerald-500/20 border-emerald-400 scale-[1.02]' : ''}`}>
                  <span className="text-[9px] font-bold text-emerald-600">31.4°C</span>
                </div>
                <div className={`absolute top-[39%] left-[4%] w-[47%] h-[27%] rounded-md border border-red-200 bg-red-500/10 flex items-center justify-center transition-all duration-700 ${activeCell === 3 ? 'bg-red-500/20 border-red-400 scale-[1.02]' : ''}`}>
                  <span className="text-[9px] font-bold text-red-600">39.5°C</span>
                </div>
                <div className={`absolute top-[39%] left-[59%] w-[37%] h-[27%] rounded-md border border-emerald-200 bg-emerald-500/10 flex items-center justify-center transition-all duration-700 ${activeCell === 4 ? 'bg-emerald-500/20 border-emerald-400 scale-[1.02]' : ''}`}>
                  <span className="text-[9px] font-bold text-emerald-600">30.8°C</span>
                </div>
              </div>
            </div>

            {/* Top Row: Floating Title & Priority Capsule */}
            <div className="flex justify-between items-start z-10">
              <div className="bg-white/95 backdrop-blur-md py-2 px-3 border border-nature-800/10 shadow-sm rounded-xl">
                <p className="text-[10px] text-nature-secText font-bold">Kolkata Urban Core</p>
                <p className="text-[8px] text-nature-mutedText">Land Surface Temp Grid</p>
              </div>
              <div className="bg-emerald-800 text-white font-extrabold text-[9px] uppercase tracking-wider py-1.5 px-3.5 rounded-full shadow-sm">
                Priority Index
              </div>
            </div>

            {/* Bottom Row: Animated Floating Metrics Pill */}
            <div className="flex justify-between items-end z-10">
              <div className="bg-white/95 backdrop-blur-md p-3 border border-nature-800/10 shadow-md rounded-xl space-y-1 transform translate-y-1 animate-bounce [animation-duration:4s]">
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-red-500"></span>
                  <span className="text-[10px] font-bold text-slate-700">39.5°C Heat Zone</span>
                </div>
                <div className="flex justify-between gap-6 text-[8px] text-slate-500 font-semibold uppercase">
                  <span>Canopy: 8%</span>
                  <span className="text-emerald-600">Cool Potential: +2.1°C</span>
                </div>
              </div>

              <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 shadow-md rounded-xl space-y-0.5 text-right">
                <span className="text-[10px] font-black block">Site Recommender</span>
                <span className="text-[8px] font-bold text-emerald-600 block">Plant: Neem (Azadirachta indica)</span>
              </div>
            </div>
          </div>
        </div>

      </header>

      {/* ==================================================
          2. LIVE IMPACT STRIP
      ================================================== */}
      <section className="bg-white border-y border-nature-800/10 shadow-sm py-10">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-4 text-center">
          <div>
            <p className="text-3xl md:text-4xl font-extrabold text-nature-800 tracking-tight">-1.8°C</p>
            <p className="text-[10px] md:text-xs text-nature-secText font-bold uppercase tracking-wider mt-1">Local Heat Reduction</p>
          </div>
          <div>
            <p className="text-3xl md:text-4xl font-extrabold text-nature-800 tracking-tight">+37%</p>
            <p className="text-[10px] md:text-xs text-nature-secText font-bold uppercase tracking-wider mt-1">Canopy Connectivity</p>
          </div>
          <div>
            <p className="text-3xl md:text-4xl font-extrabold text-nature-800 tracking-tight">3.2×</p>
            <p className="text-[10px] md:text-xs text-nature-secText font-bold uppercase tracking-wider mt-1">Planting Impact Multiplier</p>
          </div>
          <div>
            <p className="text-3xl md:text-4xl font-extrabold text-nature-800 tracking-tight">Block-Level</p>
            <p className="text-[10px] md:text-xs text-nature-secText font-bold uppercase tracking-wider mt-1">Resolution Granularity</p>
          </div>
        </div>
      </section>

      {/* ==================================================
          3. PROBLEM STORYTELLING SECTION
      ================================================== */}
      <section className="max-w-7xl mx-auto px-6 py-16 md:py-24 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        
        {/* Left Explanation */}
        <div className="lg:col-span-5 text-left space-y-6">
          <h2 className="text-3xl md:text-4xl font-black text-nature-text tracking-tight leading-tight">
            Cities are getting hotter — but not equally.
          </h2>
          <p className="text-xs md:text-sm text-nature-secText leading-relaxed">
            Concrete structures, highways, and steel roofs absorb radiation and trap hot air. Without the evapotranspiration of trees, concrete blocks act as heat cookers, making high-density neighborhoods up to 8°C warmer than nearby parks.
          </p>
          <p className="text-xs md:text-sm text-nature-secText leading-relaxed">
            This creates extreme Urban Heat Islands (UHI) that disproportionately impact vulnerable populations. Expanding the canopy is crucial, but planting trees randomly produces negligible cooling.
          </p>
        </div>

        {/* Right Comparison Slider */}
        <div className="lg:col-span-7 flex flex-col justify-center">
          <div className="bg-white border border-nature-800/10 rounded-2xl p-6 shadow-md space-y-6 w-full max-w-[580px] mx-auto">
            <h3 className="text-sm font-bold text-nature-text text-left">Microclimate Contrast Simulator</h3>
            
            <div className="grid grid-cols-2 gap-4">
              {/* Concrete Block */}
              <div className="p-4 bg-red-50/50 border border-red-100 rounded-xl space-y-3">
                <p className="text-[10px] font-bold text-red-500 uppercase tracking-wider">Concrete Core</p>
                <div>
                  <p className="text-3xl font-black text-red-700">
                    {(30 + (sliderVal / 100) * 10).toFixed(1)}°C
                  </p>
                  <p className="text-[9px] text-slate-400 mt-1 font-semibold">Canopy Cover: {Math.max(0, Math.round(15 - (sliderVal / 10)))}%</p>
                </div>
              </div>

              {/* Tree Cover Block */}
              <div className="p-4 bg-emerald-50/50 border border-emerald-100 rounded-xl space-y-3">
                <p className="text-[10px] font-bold text-emerald-500 uppercase tracking-wider">Urban Forestry</p>
                <div>
                  <p className="text-3xl font-black text-emerald-700">
                    {(28 + (sliderVal / 100) * 4).toFixed(1)}°C
                  </p>
                  <p className="text-[9px] text-slate-400 mt-1 font-semibold">Canopy Cover: {Math.min(100, Math.round(10 + (sliderVal / 1.2)))}%</p>
                </div>
              </div>
            </div>

            {/* Slider */}
            <div className="space-y-2">
              <div className="flex justify-between text-[10px] font-bold text-nature-secText">
                <span>Sparse Canopy (Deficit)</span>
                <span>Dense Reforestation</span>
              </div>
              <input 
                type="range" 
                min="0" 
                max="100" 
                value={sliderVal}
                onChange={(e) => setSliderVal(Number(e.target.value))}
                className="w-full h-1 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-emerald-800"
              />
            </div>
          </div>
        </div>

      </section>

      {/* ==================================================
          4. HOW CANOPYCAST WORKS
      ================================================== */}
      <section id="how-it-works" className="bg-nature-surface border-y border-nature-800/10 py-16 md:py-24">
        <div className="max-w-7xl mx-auto px-6 text-center space-y-12">
          <div className="space-y-2">
            <h2 className="text-3xl font-black text-nature-text tracking-tight">How CanopyCast Works</h2>
            <p className="text-xs text-nature-secText max-w-md mx-auto">
              Connecting spatial data layers to actionable urban green paths in three easy phases.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto relative">
            {/* Steps */}
            {[
              { num: "01", title: "Map the City Grid", text: "We divide urban spaces into local planning grids containing thermal surface profiles, population density, and current foliage cover." },
              { num: "02", title: "Optimize Planting Coordinates", text: "Our multi-objective engine calculates where planting new saplings will maximize local cooling and close connectivity gaps." },
              { num: "03", title: "Recommend Species (RAG)", text: "Our AI Canopy Assistant answers queries grounded in local municipal guides, suggesting the exact native species to plant." }
            ].map((step, idx) => (
              <div key={idx} className="bg-white border border-nature-800/10 p-6 rounded-2xl text-left shadow-sm space-y-4 hover:shadow-md transition-custom relative z-10">
                <span className="text-3xl font-black text-nature-300 block">{step.num}</span>
                <h3 className="text-sm font-bold text-nature-text">{step.title}</h3>
                <p className="text-xs text-nature-secText leading-relaxed">{step.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ==================================================
          5. INTERACTIVE ALGORITHM SECTION
      ================================================== */}
      <section className="max-w-7xl mx-auto px-6 py-16 md:py-24 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        
        {/* Title */}
        <div className="lg:col-span-5 text-left space-y-5">
          <h2 className="text-3xl md:text-4xl font-black text-nature-text tracking-tight leading-tight">
            One score.<br />Multiple urban priorities.
          </h2>
          <p className="text-xs md:text-sm text-nature-secText leading-relaxed">
            Many city planners plant trees where space is empty. CanopyCast targets the sweet spots. Our priority scoring balances heat stress indices, canopy deficits, and demographic vulnerability.
          </p>
          <p className="text-xs md:text-sm text-nature-secText leading-relaxed">
            The connectivity term computes distance vectors to existing parks. It ensures we prioritize boundaries that can bridge green spaces together, creating vital corridors for urban biodiversity.
          </p>
        </div>

        {/* Weights visualizer */}
        <div className="lg:col-span-7 flex justify-center">
          <div className="bg-white border border-nature-800/10 rounded-2xl p-6 shadow-md space-y-5 w-full max-w-[500px]">
            <div className="flex justify-between items-center pb-2 border-b border-slate-100">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Priority Weight Tuner</span>
              <span className="text-emerald-800 font-extrabold text-xs bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
                Score: {getScore()}/100
              </span>
            </div>

            {/* Sliders */}
            {Object.keys(weights).map((key) => (
              <div key={key} className="space-y-1">
                <div className="flex justify-between text-xs text-slate-600 capitalize">
                  <span>{key} Weight</span>
                  <span className="font-bold">{weights[key]}%</span>
                </div>
                <input 
                  type="range"
                  min="10"
                  max="100"
                  value={weights[key]}
                  onChange={(e) => setWeights(prev => ({ ...prev, [key]: Number(e.target.value) }))}
                  className="w-full h-1 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-emerald-800"
                />
              </div>
            ))}
          </div>
        </div>

      </section>

      {/* ==================================================
          6. URBAN INTELLIGENCE FEATURES
      ================================================== */}
      <section id="intelligence" className="bg-nature-surface border-y border-nature-800/10 py-16 md:py-24">
        <div className="max-w-7xl mx-auto px-6 text-center space-y-12">
          <div className="space-y-2">
            <h2 className="text-3xl font-black text-nature-text tracking-tight">Urban Intelligence Grid</h2>
            <p className="text-xs text-nature-secText max-w-md mx-auto">
              Our core technological modules designed for smart, climate-aware community coordination.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto text-left">
            {[
              { icon: Thermometer, title: "Heat Indexing", desc: "Identify hyper-local thermal exposures and surface temperature pockets." },
              { icon: Leaf, title: "Canopy Deficit", desc: "Locate blocks that lack critical canopy cover to mitigate solar load." },
              { icon: Network, title: "Connectivity Vector", desc: "Formulate migratory linkages between isolated parks and green sanctuaries." },
              { icon: Sparkles, title: "AI Species Advisor", desc: "Consult native manuals zero-shot to select trees matching local soil and temperatures." }
            ].map((feat, idx) => (
              <div key={idx} className="bg-white border border-nature-800/10 p-6 rounded-2xl shadow-sm space-y-4 hover:shadow-md transition-custom hover:-translate-y-0.5">
                <div className="w-10 h-10 rounded-xl bg-nature-100 flex items-center justify-center border border-nature-300">
                  <feat.icon className="w-5 h-5 text-nature-800" />
                </div>
                <h3 className="text-sm font-bold text-nature-text">{feat.title}</h3>
                <p className="text-xs text-nature-secText leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ==================================================
          7. GREEN CORRIDOR VISUALIZATION
      ================================================== */}
      <section id="impact" className="max-w-6xl mx-auto px-6 py-16 md:py-24 text-center space-y-8">
        <div className="max-w-2xl mx-auto space-y-4">
          <h2 className="text-3xl font-black text-nature-text tracking-tight">
            Cooling cities shouldn't come at the cost of biodiversity.
          </h2>
          <p className="text-xs md:text-sm text-nature-secText leading-relaxed">
            CanopyCast prioritizes locations that can cool neighborhoods while reconnecting fragmented urban ecosystems.
          </p>
        </div>

        {/* Visual Connectivity Pipeline */}
        <div className="bg-white border border-nature-800/10 rounded-2xl p-6 md:p-10 shadow-md max-w-3xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 md:gap-4">
            
            {/* Park A */}
            <div className="p-4 bg-emerald-800 text-white rounded-xl text-center w-full md:w-32 shadow-sm font-bold text-xs uppercase tracking-wider">
              Reserve Park A
            </div>
            
            {/* Connectivity bridge */}
            <div className="flex-1 flex items-center justify-center gap-2">
              <span className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse border border-emerald-600"></span>
              <div className="h-0.5 bg-dashed border-t-2 border-dashed border-emerald-300 flex-1 min-w-[40px]"></div>
              <span className="w-3.5 h-3.5 rounded-full bg-emerald-600 border border-emerald-700 animate-bounce"></span>
              <div className="h-0.5 bg-dashed border-t-2 border-dashed border-emerald-300 flex-1 min-w-[40px]"></div>
              <span className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse border border-emerald-600"></span>
            </div>

            {/* Park B */}
            <div className="p-4 bg-emerald-800 text-white rounded-xl text-center w-full md:w-32 shadow-sm font-bold text-xs uppercase tracking-wider">
              Reserve Park B
            </div>

          </div>
          
          <div className="mt-6 text-[10px] text-nature-mutedText uppercase font-bold tracking-widest">
            Simulated Corridor Bridge Connected
          </div>
        </div>

        <div className="pt-4">
          <button
            onClick={() => setView('planner')}
            className="inline-flex items-center gap-1.5 bg-nature-800 hover:bg-nature-900 text-white font-extrabold text-xs py-3.5 px-8 rounded-full shadow-md transition-custom"
          >
            <span>Launch Planner Portal</span>
            <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>
      </section>

    </div>
  );
}
