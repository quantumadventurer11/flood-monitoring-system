import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const xs = [0, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.4, 0.7, 1];
const curve = (power: number) => xs.map((fpr) => ({ fpr, tpr: Math.min(1, 1 - (1 - fpr) ** power) }));
const data = xs.map((fpr, i) => ({
  fpr,
  "XGBoost (AUC=0.9985)": curve(920)[i].tpr,
  "Simple CNN (AUC=0.9982)": curve(780)[i].tpr,
  "Logistic Reg (AUC=0.9978)": curve(620)[i].tpr,
  "Random Forest (AUC=0.9976)": curve(560)[i].tpr,
  "SVM RBF (AUC=0.9908)": curve(115)[i].tpr,
  "ResNet-18 (AUC=0.9848)": curve(68)[i].tpr,
  "Random baseline": fpr,
}));

export default function ROCCurveChart() {
  const colors = ["#0f766e", "#2563eb", "#7c3aed", "#16a34a", "#f97316", "#dc2626", "#94a3b8"];
  return (
    <div>
      <div className="mb-3 inline-flex rounded bg-red-100 px-2 py-1 text-xs font-bold text-red-800">SIMULATED / NOT PUBLISHABLE CURVES</div>
      <div className="h-96">
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 12, right: 24, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="fpr" type="number" domain={[0, 1]} label={{ value: "False Positive Rate", position: "insideBottom", offset: -4 }} />
          <YAxis domain={[0, 1]} label={{ value: "True Positive Rate", angle: -90, position: "insideLeft" }} />
          <Tooltip />
          <Legend />
          {Object.keys(data[0]).filter((k) => k !== "fpr").map((key, i) => (
            <Line key={key} type="monotone" dataKey={key} stroke={colors[i]} dot={false} strokeWidth={key === "Random baseline" ? 1.5 : 2.2} strokeDasharray={key === "Random baseline" ? "5 5" : undefined} />
          ))}
        </LineChart>
      </ResponsiveContainer>
      </div>
    </div>
  );
}
