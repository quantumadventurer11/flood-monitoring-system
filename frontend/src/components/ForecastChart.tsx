import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ForecastDay } from "../api/client";

const colorForRisk = (risk: string) => risk === "High" ? "#dc2626" : risk === "Medium" ? "#d97706" : "#16a34a";

export default function ForecastChart({ data }: { data: ForecastDay[] }) {
  const rows = data.map((day) => ({ ...day, likelihood_pct: Math.round(day.flood_likelihood * 100) }));
  return (
    <div className="h-80">
      <ResponsiveContainer>
        <BarChart data={rows} margin={{ top: 20, right: 20, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.45)" />
          <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 12 }} />
          <YAxis yAxisId="left" tick={{ fill: "#64748b", fontSize: 12 }} label={{ value: "Likelihood %", angle: -90, position: "insideLeft", fill: "#64748b" }} />
          <YAxis yAxisId="right" orientation="right" tick={{ fill: "#64748b", fontSize: 12 }} label={{ value: "Precip mm", angle: 90, position: "insideRight", fill: "#64748b" }} />
          <Tooltip
            formatter={(value, name) => [`${value}${name === "Flood likelihood %" ? "%" : " mm"}`, name]}
            contentStyle={{ background: "#0f172a", border: "1px solid #334155", color: "#f8fafc", borderRadius: 8 }}
            labelStyle={{ color: "#f8fafc" }}
          />
          <Bar yAxisId="left" dataKey="likelihood_pct" name="Flood likelihood %" radius={[5, 5, 0, 0]}>
            {rows.map((row) => <Cell key={row.date} fill={colorForRisk(row.risk_level)} />)}
          </Bar>
          <Bar yAxisId="right" dataKey="precipitation_mm" fill="#38bdf8" name="Precipitation mm" radius={[5, 5, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
