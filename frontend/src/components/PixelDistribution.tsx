import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const data = Array.from({ length: 41 }, (_, i) => {
  const x = -0.5 + i * 0.025;
  const land = Math.exp(-((x + 0.2) ** 2) / 0.012);
  const water = Math.exp(-((x - 0.15) ** 2) / 0.008);
  return {
    ndwi: Number(x.toFixed(3)),
    June: Math.round(2600 * land + 1450 * water),
    July: Math.round(2300 * land + 520 * water),
    August: Math.round(2100 * land + 145 * water),
  };
});

export default function PixelDistribution() {
  return (
    <div className="h-80">
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 16, right: 20, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="ndwi" type="number" domain={[-0.5, 0.5]} label={{ value: "NDWI value", position: "insideBottom", offset: -4 }} />
          <YAxis label={{ value: "Pixel count", angle: -90, position: "insideLeft" }} />
          <Tooltip />
          <Legend />
          <ReferenceLine x={0} stroke="#dc2626" strokeDasharray="5 5" label="Threshold (NDWI > 0.0)" />
          <Line type="monotone" dataKey="June" stroke="#2563eb" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="July" stroke="#f97316" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="August" stroke="#16a34a" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
