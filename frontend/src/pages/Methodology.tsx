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
  ["dataset", "Table 2"], ["roc", "Fig. 5"], ["metrics", "Table A1"], ["validation", "Validation"], ["references", "References"], ["audit", "Audit"], ["modularity", "Modularity"], ["ablation", "Table 3"], ["findings", "Findings"],
];

function Section({ id, title, caption, children }: { id: string; title: string; caption?: string; children: ReactNode }) {
  return (
    <section id={id} className="card scroll-mt-6 p-5">
      <h2 className="section-title">{title}</h2>
      {caption && <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{caption}</p>}
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
        <nav className="sticky top-4 space-y-1 rounded-lg border border-slate-200 bg-white p-3 text-sm dark:border-slate-800 dark:bg-slate-900">
          {anchors.map(([id, label]) => <a key={id} href={`#${id}`} className="block rounded px-2 py-1.5 text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">{label}</a>)}
        </nav>
      </aside>
      <div className="space-y-5">
        <Section id="abstract" title="Abstract Summary">
          <p className="text-slate-700 dark:text-slate-300">The paper proposes a binary flood detection framework for central Bangladesh that fuses Sentinel-2 optical features (B4, NDVI, NDWI) with Sentinel-1 VV SAR data. A 50 km Dhaka buffer, cloud masking, NDWI water features, 64x64 patch extraction, and 61 engineered features support XGBoost classification with ROC-AUC 0.9985 on the original August 2024 test set. External validation now uses UNOSAT flood extents as labels instead of NDWI-derived labels.</p>
        </Section>
        <Section id="workflow" title="Fig. 1: Workflow Diagram" caption="Overview of the proposed flood monitoring workflow."><WorkflowDiagram /></Section>
        <Section id="ndwi" title="Fig. 2: NDWI Water Features" caption="NDWI is retained as a model feature; external validation labels come from independent flood maps."><NDWIMask /></Section>
        <Section id="patches" title="Fig. 3: Patch Grid" caption="Examples of extracted image patches showing flood and non-flood regions used for supervised classification."><PatchGrid /></Section>
        <Section id="distribution" title="Fig. 4: Pixel Distribution Chart" caption="Pixel value distribution used for NDWI threshold selection and flood discrimination."><PixelDistribution /></Section>
        <Section id="dataset" title="Table 2: Dataset Summary"><DatasetTable rows={data.dataset_stats} /></Section>
        <Section id="roc" title="Fig. 5: ROC Curve Chart" caption="ROC curve comparison of evaluated flood detection models."><ROCCurveChart /></Section>
        <Section id="metrics" title="Table A1: Full Model Performance"><ModelMetricsTable rows={data.model_metrics} /></Section>
        <Section id="validation" title="Independent Validation Source">
          <div className="grid gap-4 md:grid-cols-[1fr_220px]">
            <div className="space-y-2 text-sm text-slate-700 dark:text-slate-300">
              <p className="font-semibold text-slate-900 dark:text-slate-100">{data.independent_validation.source.name}: {data.independent_validation.source.title}</p>
              <p>Sensor: {data.independent_validation.source.sensor}. Acquisition window: {data.independent_validation.source.acquisition_window}. Published: {data.independent_validation.source.published}.</p>
              <p>{data.independent_validation.metric_note}</p>
              {data.independent_validation.operational_fallback_audit && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-amber-900">
                  <p className="font-semibold">Operational fallback audit</p>
                  <p>{data.independent_validation.operational_fallback_audit.sample}</p>
                  <p>
                    AUC {data.independent_validation.operational_fallback_audit.model_probability_metrics.roc_auc.toFixed(4)};
                    recall {data.independent_validation.operational_fallback_audit.model_probability_metrics.recall.toFixed(1)};
                    F1 {data.independent_validation.operational_fallback_audit.model_probability_metrics.f1.toFixed(1)}.
                  </p>
                  <p>{data.independent_validation.operational_fallback_audit.verdict}</p>
                </div>
              )}
              <p className="text-xs text-slate-500 dark:text-slate-400">{data.independent_validation.source.caveat}</p>
              <div className="flex flex-wrap gap-2 pt-1">
                <a className="rounded bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white" href={data.independent_validation.source.source_url} target="_blank" rel="noreferrer">UNOSAT product</a>
                <a className="rounded border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:border-slate-700 dark:text-slate-200" href={data.independent_validation.source.shapefile_url} target="_blank" rel="noreferrer">Shapefile</a>
              </div>
            </div>
            <dl className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-800 dark:bg-slate-950">
              <dt className="text-slate-500 dark:text-slate-400">Patch labels</dt>
              <dd className="text-2xl font-bold text-slate-900 dark:text-slate-100">{data.independent_validation.ground_truth.patches}</dd>
              <dt className="mt-3 text-slate-500 dark:text-slate-400">Flooded patches</dt>
              <dd className="text-2xl font-bold text-blue-700 dark:text-cyan-300">{data.independent_validation.ground_truth.flooded_patches}</dd>
              <dt className="mt-3 text-slate-500 dark:text-slate-400">Flooded share</dt>
              <dd className="text-2xl font-bold text-blue-700 dark:text-cyan-300">{data.independent_validation.ground_truth.flooded_percent}%</dd>
            </dl>
          </div>
        </Section>
        <Section id="references" title="Methodology References" caption="External papers used to frame forecasting, uncertainty, and validation language.">
          <div className="space-y-3">
            {data.methodology_references.map((reference) => (
              <article key={reference.key} className="rounded-lg border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-950">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h3 className="font-semibold text-slate-900 dark:text-slate-100">{reference.title}</h3>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">{reference.authors} ({reference.year}). {reference.venue}.</p>
                  </div>
                  <a className="rounded border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:border-slate-700 dark:text-slate-200" href={`https://doi.org/${reference.doi}`} target="_blank" rel="noreferrer">DOI</a>
                </div>
                <p className="mt-3 text-slate-700 dark:text-slate-300">{reference.relevance}</p>
                <div className="mt-3 rounded border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
                  <p className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Copy-ready APA citation</p>
                  <p className="mt-1 text-slate-800 dark:text-slate-200">{reference.citation}</p>
                </div>
              </article>
            ))}
          </div>
        </Section>
        <Section id="audit" title="Numerical Consistency Audit">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-slate-900 text-white">
              <tr>{["Item", "Resolved", "Status", "Note"].map((h) => <th key={h} className="p-3">{h}</th>)}</tr>
            </thead>
            <tbody>
              {data.metric_audit.map((row) => (
              <tr key={row.item} className="border-b border-slate-200 odd:bg-white even:bg-slate-50 dark:border-slate-800 dark:odd:bg-slate-950 dark:even:bg-slate-900">
                <td className="p-3 font-semibold">{row.item}</td>
                <td className="p-3">{row.resolved_value?.toFixed(4) ?? "Documented"}</td>
                <td className="p-3">{row.status.replace(/_/g, " ")}</td>
                <td className="p-3 text-slate-600 dark:text-slate-300">{row.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
        <Section id="modularity" title="Modularity Evidence">
          <ul className="grid gap-3 text-sm text-slate-700 dark:text-slate-300 md:grid-cols-3">
            {data.modularity_evidence.map((item) => <li key={item} className="rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-950">{item}</li>)}
          </ul>
        </Section>
        <Section id="ablation" title="Table 3: Ablation Study"><AblationTable rows={data.ablation_results} /></Section>
        <Section id="findings" title="Key Findings And Limitations">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h3 className="font-semibold text-slate-800 dark:text-slate-100">Key findings</h3>
              <ul className="mt-2 space-y-2 text-sm text-slate-700 dark:text-slate-300">
                <li>XGBoost is the best structured-feature baseline.</li>
                <li>NDWI_p95 is the top-ranked feature.</li>
                <li>Water fraction is powerful but raises label circularity concerns.</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-slate-800 dark:text-slate-100">Future work</h3>
              <ul className="mt-2 space-y-2 text-sm text-slate-700 dark:text-slate-300">
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
