import React from "react";

import {
  ShieldAlert,
  Leaf,
  Users,
  MapPin,
  Activity,
  HelpCircle,
  Thermometer,
} from "lucide-react";

import TemperatureChart from "./TemperatureChart";

export default function Dashboard({
  selectedCell,
  onRunOptimizer,
  isOptimizing,
  recommendations,
}) {
  // ======================================================
  // TEMPERATURE COLOR
  // ======================================================

  const getTempColor = (temperature) => {
    if (temperature >= 38) {
      return "text-red-600 bg-red-50 border-red-100";
    }

    if (temperature >= 32) {
      return "text-amber-600 bg-amber-50 border-amber-100";
    }

    return "text-emerald-600 bg-emerald-50 border-emerald-100";
  };

  // ======================================================
  // CANOPY COLOR
  // ======================================================

  const getCanopyColor = (canopy) => {
    if (canopy < 15) {
      return "bg-red-500";
    }

    if (canopy < 30) {
      return "bg-amber-500";
    }

    return "bg-emerald-500";
  };

  return (
    <div className="w-full h-full bg-slate-50 border-r border-slate-200 flex flex-col justify-between overflow-y-auto">

      {/* ==================================================
          HEADER
      ================================================== */}

      <div className="p-6 bg-gradient-to-r from-emerald-800 to-teal-900 text-white shadow-sm">

        <div className="flex items-center gap-2 mb-1">

          <Leaf className="w-6 h-6 text-emerald-300" />

          <h1 className="text-xl font-bold tracking-tight">
            CanopyCast
          </h1>

        </div>

        <p className="text-xs text-emerald-100 opacity-90 font-medium">
          Urban Heat & Green-Corridor Planner
        </p>

      </div>


      {/* ==================================================
          MAIN DASHBOARD AREA
      ================================================== */}

      <div className="flex-1 p-5 space-y-6">

        {selectedCell ? (

          <div className="space-y-5">

            {/* ==================================================
                LOCATION
            ================================================== */}

            <div className="flex items-center gap-3 p-4 bg-white rounded-xl shadow-sm border border-slate-100">

              <MapPin className="w-5 h-5 text-emerald-600 shrink-0" />

              <div>

                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  Target Coordinates
                </p>

                <p className="text-sm text-slate-700 font-bold">

                  {selectedCell.lat.toFixed(5)}° N,{" "}

                  {selectedCell.lon.toFixed(5)}° E

                </p>

              </div>

            </div>


            {/* ==================================================
                CLIMATE CARDS
            ================================================== */}

            <div className="grid grid-cols-2 gap-4">

              {/* ================= TEMPERATURE ================= */}

              <div
                className={`p-4 rounded-xl border flex flex-col justify-between ${getTempColor(
                  selectedCell.temperature
                )}`}
              >

                <div className="flex items-center gap-1">

                  <Thermometer className="w-4 h-4" />

                  <p className="text-xs font-semibold opacity-90">
                    Surface Temp
                  </p>

                </div>

                <p className="text-2xl font-black mt-2">
                  {selectedCell.temperature}°C
                </p>

              </div>


              {/* ================= CANOPY ================= */}

              <div className="p-4 bg-white border border-slate-100 rounded-xl flex flex-col justify-between shadow-sm">

                <p className="text-xs font-semibold text-slate-500">
                  Canopy Cover
                </p>

                <div className="mt-2">

                  <p className="text-2xl font-black text-slate-800">
                    {selectedCell.canopy_cover}%
                  </p>

                  <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">

                    <div
                      className={`h-1.5 rounded-full transition-all duration-500 ${getCanopyColor(
                        selectedCell.canopy_cover
                      )}`}
                      style={{
                        width: `${Math.min(
                          selectedCell.canopy_cover,
                          100
                        )}%`,
                      }}
                    />

                  </div>

                </div>

              </div>

            </div>


            {/* ==================================================
                TEMPERATURE COMPARISON CHART
            ================================================== */}

            <TemperatureChart
              selectedCell={selectedCell}
            />


            {/* ==================================================
                POPULATION & PARK DETAILS
            ================================================== */}

            <div className="bg-white border border-slate-100 rounded-xl p-4 space-y-3 shadow-sm">

              {/* ================= POPULATION ================= */}

              <div className="flex items-center justify-between">

                <div className="flex items-center gap-2 text-xs text-slate-500">

                  <Users className="w-4 h-4 text-slate-400" />

                  <span>
                    Population Density
                  </span>

                </div>

                <span className="text-xs font-bold text-slate-700 bg-slate-100 px-2 py-1 rounded-md">

                  {selectedCell.population_density}

                </span>

              </div>


              {/* ================= PARK PROXIMITY ================= */}

              <div className="flex items-center justify-between border-t border-slate-100 pt-3">

                <div className="flex items-center gap-2 text-xs text-slate-500">

                  <Activity className="w-4 h-4 text-slate-400" />

                  <span>
                    Park Proximity
                  </span>

                </div>

                <span className="text-xs font-bold text-slate-700">

                  {selectedCell.nearest_park_distance_km
                    ? `${selectedCell.nearest_park_distance_km} km`
                    : "1.2 km"}

                </span>

              </div>

            </div>


            {/* ==================================================
                PROJECTED ENVIRONMENTAL IMPACT
            ================================================== */}

            {recommendations && recommendations.length > 0 && (

              <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4 space-y-3">

                <h3 className="text-xs font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1.5">

                  <ShieldAlert className="w-4 h-4" />

                  Projected Environmental Impact

                </h3>


                <div className="grid grid-cols-3 gap-2 pt-1 text-center">

                  {/* ================= COOLING ================= */}

                  <div className="p-2 bg-white rounded-lg border border-emerald-100">

                    <p className="text-[10px] text-slate-400 font-semibold uppercase">
                      Cooling
                    </p>

                    <p className="text-sm font-extrabold text-emerald-700 mt-0.5">
                      -1.6°C
                    </p>

                  </div>


                  {/* ================= CO2 ================= */}

                  <div className="p-2 bg-white rounded-lg border border-emerald-100">

                    <p className="text-[10px] text-slate-400 font-semibold uppercase">
                      CO2 Abs
                    </p>

                    <p className="text-sm font-extrabold text-emerald-700 mt-0.5">
                      140kg/y
                    </p>

                  </div>


                  {/* ================= RUNOFF ================= */}

                  <div className="p-2 bg-white rounded-lg border border-emerald-100">

                    <p className="text-[10px] text-slate-400 font-semibold uppercase">
                      Runoff
                    </p>

                    <p className="text-sm font-extrabold text-emerald-700 mt-0.5">
                      -4k gal
                    </p>

                  </div>

                </div>

              </div>

            )}

          </div>

        ) : (

          /* ==================================================
             NO CELL SELECTED
          ================================================== */

          <div className="h-48 border-2 border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center p-6 text-center bg-slate-50">

            <HelpCircle className="w-8 h-8 text-slate-300 mb-2" />

            <p className="text-xs font-semibold text-slate-500">
              No block selected
            </p>

            <p className="text-[10px] text-slate-400 mt-1 max-w-[200px]">
              Click a grid tile on the map to display hyper-local climate
              statistics.
            </p>

          </div>

        )}

      </div>


      {/* ==================================================
          OPTIMIZER BUTTON
      ================================================== */}

      <div className="p-5 border-t border-slate-100 bg-white shadow-md">

        <button
          onClick={onRunOptimizer}
          disabled={isOptimizing}
          className="w-full bg-emerald-700 hover:bg-emerald-800 disabled:bg-emerald-300 text-white font-bold py-3 px-4 rounded-xl shadow-md transition-colors text-sm tracking-wide shrink-0 flex items-center justify-center gap-2"
        >

          {isOptimizing ? (

            <>

              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />

              Calculating Canopy Pathways...

            </>

          ) : (

            "Optimize Green Canopy"

          )}

        </button>

      </div>

    </div>
  );
}