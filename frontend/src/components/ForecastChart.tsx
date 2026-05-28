import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ForecastDay } from "../api/client";

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
          <Bar yAxisId="left" dataKey="likelihood_pct" fill="#0077b6" name="Flood likelihood %" radius={[4, 4, 0, 0]} />
          <Bar yAxisId="right" dataKey="precipitation_mm" fill="#00a6a6" name="Precipitation mm" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
