import { ArrowRight } from "lucide-react";

const phases = [
  { title: "Data Acquisition", steps: ["Sentinel-1 (VV SAR)", "Sentinel-2 (B4, NDWI, NDVI)", "QA60 cloud mask"] },
  { title: "Preprocessing", steps: ["Cloud masking", "NDWI computation", "Normalization", "Patch tiling (64x64)"] },
  { title: "Model Development", steps: ["61-feature extraction", "XGBoost training", "ROC-AUC evaluation"] },
  { title: "Alert Generation", steps: ["Flood probability threshold", "Risk level (Low/Medium/High)", "Alert dispatch"] },
];

export default function WorkflowDiagram() {
  return (
    <div className="grid gap-3 lg:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr]">
      {phases.map((phase, index) => (
        <div key={phase.title} className="contents">
          <div className="card border-teal-200 p-4">
            <h3 className="font-semibold text-flood">{phase.title}</h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-700">
              {phase.steps.map((step) => (
                <li key={step} className="flex gap-2">
                  <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-aqua" />
                  <span>{step}</span>
                </li>
              ))}
            </ul>
          </div>
          {index < phases.length - 1 && (
            <div className="hidden items-center justify-center text-aqua lg:flex">
              <ArrowRight />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
