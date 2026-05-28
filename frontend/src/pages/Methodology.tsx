import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { api, type PaperResults } from "../api/client";
import AblationTable from "../components/AblationTable";
import DatasetTable from "../components/DatasetTable";
import ModelMetricsTable from "../components/ModelMetricsTable";
import NDWIMask from "../components/NDWIMask";
import PatchGrid from "../components/PatchGrid";
import PixelDistribution from "../components/PixelDistribution";
import ROCCurveChart from "../components/ROCCurveChart";
import WorkflowDiagram from "../components/WorkflowDiagram";

const anchors = [
  ["abstract", "Abstract"], ["workflow", "Fig. 1"], ["ndwi", "Fig. 2"], ["patches", "Fig. 3"], ["distribution", "Fig. 4"],
  ["dataset", "Table 2"], ["roc", "Fig. 5"], ["metrics", "Table A1"], ["ablation", "Table 3"], ["findings", "Findings"],
];

function Section({ id, title, caption, children }: { id: string; title: string; caption?: string; children: ReactNode }) {
  return (
    <section id={id} className="card scroll-mt-6 p-5">
      <h2 className="section-title">{title}</h2>
      {caption && <p className="mt-1 text-sm text-slate-600">{caption}</p>}
      <div className="mt-4 overflow-x-auto">{children}</div>
    </section>
  );
}

export default function Methodology() {
  const [data, setData] = useState<PaperResults | null>(null);
  useEffect(() => { api.paperResults().then(setData); }, []);
  if (!data) return <div className="card p-5">Loading paper results...</div>;

  return (
    <div className="grid gap-5 lg:grid-cols-[190px_1fr]">
      <aside className="hidden lg:block">
        <nav className="sticky top-4 space-y-1 rounded-lg border border-slate-200 bg-white p-3 text-sm">
          {anchors.map(([id, label]) => <a key={id} href={`#${id}`} className="block rounded px-2 py-1.5 text-slate-700 hover:bg-slate-100">{label}</a>)}
        </nav>
      </aside>
      <div className="space-y-5">
        <Section id="abstract" title="Abstract Summary">
          <p className="text-slate-700">The paper proposes a binary flood detection framework for central Bangladesh that fuses Sentinel-2 optical features (B4, NDVI, NDWI) with Sentinel-1 VV SAR data. A 50 km Dhaka buffer, cloud masking, NDWI water detection, 64x64 patch extraction, and 61 engineered features support XGBoost classification with ROC-AUC 0.9985 on the August 2024 test set.</p>
        </Section>
        <Section id="workflow" title="Fig. 1: Workflow Diagram" caption="Overview of the proposed flood monitoring workflow."><WorkflowDiagram /></Section>
        <Section id="ndwi" title="Fig. 2: NDWI Water Masking" caption="NDWI-based water masking used to enhance flooded regions during preprocessing."><NDWIMask /></Section>
        <Section id="patches" title="Fig. 3: Patch Grid" caption="Examples of extracted image patches showing flood and non-flood regions used for supervised classification."><PatchGrid /></Section>
        <Section id="distribution" title="Fig. 4: Pixel Distribution Chart" caption="Pixel value distribution used for NDWI threshold selection and flood discrimination."><PixelDistribution /></Section>
        <Section id="dataset" title="Table 2: Dataset Summary"><DatasetTable rows={data.dataset_stats} /></Section>
        <Section id="roc" title="Fig. 5: ROC Curve Chart" caption="ROC curve comparison of evaluated flood detection models."><ROCCurveChart /></Section>
        <Section id="metrics" title="Table A1: Full Model Performance"><ModelMetricsTable rows={data.model_metrics} /></Section>
        <Section id="ablation" title="Table 3: Ablation Study"><AblationTable rows={data.ablation_results} /></Section>
        <Section id="findings" title="Key Findings And Limitations">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h3 className="font-semibold text-slate-800">Key findings</h3>
              <ul className="mt-2 space-y-2 text-sm text-slate-700">
                <li>XGBoost is the best structured-feature baseline.</li>
                <li>NDWI_p95 is the top-ranked feature.</li>
                <li>Water fraction is powerful but raises label circularity concerns.</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-slate-800">Future work</h3>
              <ul className="mt-2 space-y-2 text-sm text-slate-700">
                <li>Validate across additional flood regions and seasons.</li>
                <li>Separate label-generation signals from model features.</li>
                <li>Replace simulated fallback visuals with live Sentinel tiles when available.</li>
              </ul>
            </div>
          </div>
        </Section>
      </div>
    </div>
  );
}
