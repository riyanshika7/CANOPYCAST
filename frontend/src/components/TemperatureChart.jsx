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
  if (!selectedCell) return null;

  const cellTemperature = selectedCell.temperature ?? selectedCell.temp ?? 0;
  const cityAverage = 34;

  const data = [
    {
      name: "Selected Block",
      temperature: cellTemperature,
      fill: cellTemperature >= 38 ? "#EF4444" : cellTemperature >= 32 ? "#FACC15" : "#22C55E"
    },
    {
      name: "City Average",
      temperature: cityAverage,
      fill: "#166534"
    },
  ];

  return (
    <div className="bg-white border border-nature-800/10 rounded-xl p-4 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xs font-bold text-nature-text">
            Temperature Delta
          </h3>
          <p className="text-[9px] text-nature-mutedText font-semibold mt-0.5">
            Selected location vs city average
          </p>
        </div>

        <div className="text-right">
          <p className="text-[10px] text-nature-mutedText font-semibold uppercase">
            Difference
          </p>
          <p className={`text-xs font-black ${cellTemperature >= cityAverage ? "text-red-600" : "text-emerald-700"}`}>
            {cellTemperature >= cityAverage ? "+" : ""}
            {(cellTemperature - cityAverage).toFixed(1)}°C
          </p>
        </div>
      </div>

      <div className="w-full h-40">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{
              top: 5,
              right: 5,
              left: -35,
              bottom: 0,
            }}
          >
            <CartesianGrid stroke="#f1f7f2" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 9, fill: "#647067", fontWeight: 600 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={[20, 45]}
              tick={{ fontSize: 9, fill: "#647067", fontWeight: 600 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              cursor={{ fill: 'rgba(22, 101, 52, 0.03)' }}
              contentStyle={{ 
                backgroundColor: '#ffffff', 
                border: '1px solid rgba(22, 101, 52, 0.1)', 
                borderRadius: '8px',
                fontSize: '10px',
                fontWeight: 600,
                color: '#17231B',
                boxShadow: '0 4px 12px rgba(22, 101, 52, 0.05)'
              }}
              formatter={(value) => [`${value}°C`, "Temperature"]}
            />
            <Bar
              dataKey="temperature"
              radius={[4, 4, 0, 0]}
              barSize={32}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}