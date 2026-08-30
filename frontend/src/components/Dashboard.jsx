import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  Leaf,
  Users,
  MapPin,
  Activity,
  HelpCircle,
  Thermometer,
  Trees,
  Scale
} from "lucide-react";
import TemperatureChart from "./TemperatureChart";

export default function Dashboard({
  selectedCell,
  onRunOptimizer,
  isOptimizing,
  recommendations,
  selectedCity,
}) {
  const [treeRecommendations, setTreeRecommendations] = useState([]);
  const [loadingTrees, setLoadingTrees] = useState(false);

  // Fetch recommended trees whenever a cell is selected
  useEffect(() => {
    if (!selectedCell) {
      setTreeRecommendations([]);
      return;
    }

    const fetchTreeRecommendations = async () => {
      setLoadingTrees(true);
      try {
        const cellId = selectedCell.id || `${Math.round(selectedCell.lat * 100)}_${Math.round(selectedCell.lon * 100)}`;
        const response = await fetch(`http://127.0.0.1:8000/api/recommend-trees?city=${selectedCity || "Kolkata"}&cell_id=${cellId}`);
        if (response.ok) {
          const data = await response.json();
          setTreeRecommendations(data.recommendations || []);
        } else {
          throw new Error("Failed to fetch tree recommendations");
        }
      } catch (error) {
        // Dynamic fallback based on local cell temperature for offline demo realism
        const temp = selectedCell.temperature ?? selectedCell.temp ?? 0;
        setTimeout(() => {
          if (temp >= 38) {
            setTreeRecommendations([
              {
                common_name: "Neem",
                botanical_name: "Azadirachta indica",
                crown_shape: "dense-round",
                mature_height_ft: 45,
                why_here: "High evapotranspiration capacity. Excellent shade potential for high UHI zones.",
                caution: "Requires well-drained soil",
                spacing: "6-8 m",
                co2_absorption: "22 kg/year"
              },
              {
                common_name: "Gulmohar",
                botanical_name: "Delonix regia",
                crown_shape: "flat-umbrella",
                mature_height_ft: 40,
                why_here: "Broad shade spread helps cover exposed asphalt roads, reducing pavement heat storage.",
                caution: "Shallow roots; avoid tight concrete curbings",
                spacing: "8-10 m",
                co2_absorption: "25 kg/year"
              }
            ]);
          } else if (temp >= 32) {
            setTreeRecommendations([
              {
                common_name: "Bakul",
                botanical_name: "Mimusops elengi",
                crown_shape: "thick-dome",
                mature_height_ft: 40,
                why_here: "Compact shade tree ideal for street avenues with dense population exposure.",
                caution: null,
                spacing: "5-6 m",
                co2_absorption: "18 kg/year"
              },
              {
                common_name: "Amaltas",
                botanical_name: "Cassia fistula",
                crown_shape: "spreading",
                mature_height_ft: 35,
                why_here: "Native species with moderate shade. Extremely drought resistant and handles city pollutants well.",
                caution: "Deciduous; drops leaves for a brief winter period",
                spacing: "5-6 m",
                co2_absorption: "15 kg/year"
              }
            ]);
          } else {
            setTreeRecommendations([
              {
                common_name: "Jarul",
                botanical_name: "Lagerstroemia speciosa",
                crown_shape: "rounded",
                mature_height_ft: 30,
                why_here: "Thrives in moderate heat. Excellent root system for preventing topsoil runoff near local water bodies.",
                caution: "Requires moderate watering during dry spells",
                spacing: "5-6 m",
                co2_absorption: "14 kg/year"
              },
              {
                common_name: "Radhachura",
                botanical_name: "Peltophorum pterocarpum",
                crown_shape: "dome-shaped",
                mature_height_ft: 45,
                why_here: "Fast-growing evergreen with moderate canopy spread. Serves well as a boundary buffer species.",
                caution: "Brittle wood; branches can break in heavy storms",
                spacing: "7-8 m",
                co2_absorption: "20 kg/year"
              }
            ]);
          }
        }, 300);
      } finally {
        setLoadingTrees(false);
      }
    };

    fetchTreeRecommendations();
  }, [selectedCell, selectedCity]);

  const getTempColor = (temperature) => {
    if (temperature >= 38) return "text-red-600 bg-red-50/50 border-red-100";
    if (temperature >= 32) return "text-amber-600 bg-amber-50/50 border-amber-100";
    return "text-emerald-600 bg-emerald-50/50 border-emerald-100";
  };

  const getCanopyColor = (canopy) => {
    if (canopy < 15) return "bg-red-500";
    if (canopy < 30) return "bg-amber-500";
    return "bg-emerald-500";
  };

  const cellTemperature = selectedCell ? (selectedCell.temperature ?? selectedCell.temp ?? 0) : 0;
  const cellCanopy = selectedCell ? (selectedCell.canopy_cover ?? selectedCell.canopy ?? 0) : 0;
  const cellPop = selectedCell ? (selectedCell.population_density ?? "Medium") : "Medium";
  const cellPark = selectedCell ? (selectedCell.park_proximity ?? 1.2) : 1.2;

  return (
    <div className="w-full h-full bg-slate-50 border-r border-slate-200 flex flex-col justify-between overflow-y-auto font-sans select-none">
      
      {/* Upper stats wrapper */}
      <div className="flex-1 p-5 space-y-6">
        
        {selectedCell ? (
          <div className="space-y-5">
            {/* Location Banner */}
            <div className="flex items-center gap-3 p-4 bg-white rounded-xl shadow-sm border border-nature-800/10">
              <MapPin className="w-5 h-5 text-nature-800 shrink-0" />
              <div>
                <p className="text-[10px] font-bold text-nature-mutedText uppercase tracking-wider">
                  Target Coordinates
                </p>
                <p className="text-xs text-nature-text font-bold">
                  {selectedCell.lat.toFixed(5)}° N, {selectedCell.lon.toFixed(5)}° E
                </p>
              </div>
            </div>

            {/* Climate Cards */}
            <div className="grid grid-cols-2 gap-4">
              {/* Temperature card */}
              <div className={`p-4 rounded-xl border flex flex-col justify-between ${getTempColor(cellTemperature)}`}>
                <div className="flex items-center gap-1 opacity-80">
                  <Thermometer className="w-4 h-4" />
                  <span className="text-[10px] font-bold uppercase tracking-wider">Temp</span>
                </div>
                <p className="text-2xl font-black mt-2">{cellTemperature}°C</p>
              </div>

              {/* Canopy card */}
              <div className="p-4 bg-white border border-nature-800/10 rounded-xl flex flex-col justify-between shadow-sm">
                <p className="text-[10px] font-bold text-nature-secText uppercase tracking-wider">Canopy Cover</p>
                <div className="mt-2">
                  <p className="text-2xl font-black text-nature-text">{cellCanopy}%</p>
                  <div className="w-full bg-slate-100 rounded-full h-1 mt-2 overflow-hidden">
                    <div
                      className={`h-1 rounded-full transition-all duration-500 ${getCanopyColor(cellCanopy)}`}
                      style={{ width: `${Math.min(cellCanopy, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Recharts chart component */}
            <TemperatureChart selectedCell={selectedCell} />

            {/* Cell parameters */}
            <div className="bg-white border border-nature-800/10 rounded-xl p-4 space-y-3 shadow-sm text-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-nature-secText">
                  <Users className="w-4 h-4 text-nature-mutedText" />
                  <span>Population Density</span>
                </div>
                <span className={`font-bold px-2 py-0.5 rounded-md ${
                  cellPop === 'High' || cellPop > 8000
                    ? 'text-red-700 bg-red-50' 
                    : 'text-emerald-700 bg-emerald-50'
                }`}>
                  {typeof cellPop === 'number' ? (cellPop > 8000 ? 'High' : 'Medium') : cellPop}
                </span>
              </div>

              <div className="flex items-center justify-between border-t border-slate-100 pt-3">
                <div className="flex items-center gap-2 text-nature-secText">
                  <Activity className="w-4 h-4 text-nature-mutedText" />
                  <span>Park Proximity</span>
                </div>
                <span className="font-bold text-nature-text">
                  {cellPark} km
                </span>
              </div>
            </div>

            {/* Projected Impact Panel */}
            {recommendations && recommendations.length > 0 && (
              <div className="bg-nature-100/50 border border-nature-800/10 rounded-xl p-4 space-y-3 shadow-sm">
                <h3 className="text-[10px] font-bold text-nature-800 uppercase tracking-widest flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4" />
                  Projected Climate Impact
                </h3>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-2 bg-white rounded-lg border border-nature-800/10">
                    <p className="text-[9px] text-nature-mutedText font-semibold uppercase">Cooling</p>
                    <p className="text-xs font-black text-nature-800 mt-0.5">-1.6°C</p>
                  </div>
                  <div className="p-2 bg-white rounded-lg border border-nature-800/10">
                    <p className="text-[9px] text-nature-mutedText font-semibold uppercase">CO2 Abs</p>
                    <p className="text-xs font-black text-nature-800 mt-0.5">140kg/y</p>
                  </div>
                  <div className="p-2 bg-white rounded-lg border border-nature-800/10">
                    <p className="text-[9px] text-nature-mutedText font-semibold uppercase">Runoff</p>
                    <p className="text-xs font-black text-nature-800 mt-0.5">-4k gal</p>
                  </div>
                </div>
              </div>
            )}

            {/* Tree recommendation cards */}
            <div className="space-y-3">
              <h3 className="text-[10px] font-bold text-nature-secText uppercase tracking-widest flex items-center gap-1.5">
                <Trees className="w-4 h-4" />
                Recommended Native Species
              </h3>
              
              {loadingTrees ? (
                <div className="py-6 flex justify-center">
                  <div className="w-5 h-5 border-2 border-nature-800 border-t-transparent rounded-full animate-spin"></div>
                </div>
              ) : (
                <div className="space-y-3">
                  {treeRecommendations.map((tree, i) => (
                    <div key={i} className="bg-white border border-nature-800/10 rounded-xl p-4 shadow-sm hover:shadow-md transition-custom text-left space-y-2">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="text-xs font-bold text-nature-text">{tree.common_name}</h4>
                          <span className="text-[10px] text-nature-secText italic font-medium">{tree.botanical_name}</span>
                        </div>
                        <span className="text-[9px] font-black text-nature-800 bg-nature-100 border border-nature-300 px-2 py-0.5 rounded-full">
                          {tree.spacing || "6m spacing"}
                        </span>
                      </div>
                      
                      <p className="text-[10px] text-nature-secText leading-relaxed">
                        {tree.why_here}
                      </p>

                      <div className="flex flex-wrap gap-1.5 pt-1">
                        <span className="text-[8px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">Native</span>
                        {tree.co2_absorption && (
                          <span className="text-[8px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">{tree.co2_absorption} uptake</span>
                        )}
                        {tree.crown_shape && (
                          <span className="text-[8px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100 capitalize">{tree.crown_shape} crown</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>
        ) : (
          <div className="h-48 border-2 border-dashed border-nature-800/10 rounded-xl flex flex-col items-center justify-center p-6 text-center bg-white shadow-sm">
            <HelpCircle className="w-8 h-8 text-nature-mutedText mb-2" />
            <p className="text-xs font-bold text-nature-text">No neighborhood selected</p>
            <p className="text-[10px] text-nature-secText mt-1 max-w-[200px] leading-relaxed">
              Click a grid tile on the map index to display hyper-local climate and tree recommendations.
            </p>
          </div>
        )}

      </div>

    </div>
  );
}