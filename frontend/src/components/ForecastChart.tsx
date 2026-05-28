import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ForecastDay } from "../api/client";

const colorForRisk = (risk: string) => risk === "High" ? "#dc2626" : risk === "Medium" ? "#d97706" : "#16a34a";

export default function ForecastChart({ data }: { data: ForecastDay[] }) {
  const rows = data.map((day) => ({ ...day, likelihood_pct: Math.round(day.flood_likelihood * 100) }));
  return (
    <div className="h-80">
      <ResponsiveContainer>
        <BarChart data={rows} margin={{ top: 20, right: 20, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis yAxisId="left" label={{ value: "Likelihood %", angle: -90, position: "insideLeft" }} />
          <YAxis yAxisId="right" orientation="right" label={{ value: "Precip mm", angle: 90, position: "insideRight" }} />
          <Tooltip />
          <Bar yAxisId="left" dataKey="likelihood_pct" name="Flood likelihood %" radius={[4, 4, 0, 0]}>
            {rows.map((row) => <Cell key={row.date} fill={colorForRisk(row.risk_level)} />)}
          </Bar>
          <Bar yAxisId="right" dataKey="precipitation_mm" fill="#00a6a6" name="Precipitation mm" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
