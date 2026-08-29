import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function TemperatureChart({ selectedCell }) {
  if (!selectedCell) {
    return (
      <div className="bg-white border border-slate-100 rounded-xl p-5 shadow-sm">
        <h3 className="text-sm font-bold text-slate-700">
          Temperature Comparison
        </h3>

        <p className="text-xs text-slate-400 mt-3">
          Select a grid cell on the map to view temperature comparison.
        </p>
      </div>
    );
  }

  const cellTemperature =
    selectedCell.temperature ?? selectedCell.temp ?? 0;

  // Temporary Kolkata average.
  // Later this can come from Chirag's backend.
  const cityAverage = 34;

  const data = [
    {
      name: "Selected Cell",
      temperature: cellTemperature,
    },
    {
      name: "Kolkata Avg.",
      temperature: cityAverage,
    },
  ];

  return (
    <div className="bg-white border border-slate-100 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-800">
            Temperature Comparison
          </h3>

          <p className="text-[10px] text-slate-400 mt-1">
            Selected location vs Kolkata average
          </p>
        </div>

        <div className="text-right">
          <p className="text-[10px] text-slate-400 uppercase">
            Difference
          </p>

          <p className="text-sm font-bold text-red-600">
            {cellTemperature >= cityAverage ? "+" : ""}
            {(cellTemperature - cityAverage).toFixed(1)}°C
          </p>
        </div>
      </div>

      <div className="w-full h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{
              top: 10,
              right: 10,
              left: -20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis
              dataKey="name"
              tick={{ fontSize: 10 }}
            />

            <YAxis
              domain={["dataMin - 2", "dataMax + 2"]}
              tick={{ fontSize: 10 }}
            />

            <Tooltip
              formatter={(value) => [`${value}°C`, "Temperature"]}
            />

            <Bar
              dataKey="temperature"
              radius={[6, 6, 0, 0]}
              fill="#059669"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}