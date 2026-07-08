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
          <p className="text-slate-700 dark:text-slate-300">The current validation pass tests Bangladesh 2024 flood detection against independent UNOSAT FL20240825BGD labels. The XGBoost model now excludes NDWI-derived inputs and uses 45 non-NDWI Sentinel features; NDWI water fraction is retained only as an audited score for comparison, not as a training input or label source.</p>
        </Section>
        <Section id="workflow" title="Fig. 1: Workflow Diagram" caption="Overview of the proposed flood monitoring workflow."><WorkflowDiagram /></Section>
        <Section id="ndwi" title="Fig. 2: NDWI Water Features" caption="NDWI is audited as a water signal; external validation labels come from independent UNOSAT flood maps."><NDWIMask /></Section>
        <Section id="patches" title="Fig. 3: Patch Grid" caption="Examples of extracted image patches showing flood and non-flood regions used for supervised classification."><PatchGrid /></Section>
        <Section id="distribution" title="Fig. 4: Pixel Distribution Chart" caption="Pixel value distribution used for NDWI threshold selection and flood discrimination."><PixelDistribution /></Section>
        <Section id="dataset" title="Table 2: Dataset Summary"><DatasetTable rows={data.dataset_stats} /></Section>
        <Section id="roc" title="Fig. 5: ROC Curve Chart" caption="Synthetic comparison curves retained for context only; not publishable validation evidence."><ROCCurveChart /></Section>
        <Section id="metrics" title="Table A1: Full Model Performance"><ModelMetricsTable rows={data.model_metrics} /></Section>
        <Section id="validation" title="Independent Validation Source">
          <div className="grid gap-4 md:grid-cols-[1fr_220px]">
            <div className="space-y-2 text-sm text-slate-700 dark:text-slate-300">
              <p className="font-semibold text-slate-900 dark:text-slate-100">{data.independent_validation.source.name}: {data.independent_validation.source.title}</p>
              {data.independent_validation.first_principles_note && (
                <p className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-blue-900 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-100">{data.independent_validation.first_principles_note}</p>
              )}
              {data.independent_validation.evidence_tiers && (
                <div className="grid gap-2 md:grid-cols-3">
                  {data.independent_validation.evidence_tiers.map((tier) => (
                    <div key={tier.tier} className="rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-950">
                      <p className="font-semibold text-slate-900 dark:text-slate-100">{tier.tier}</p>
                      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{tier.source}</p>
                      <p className="mt-2 text-xs font-semibold text-blue-700 dark:text-cyan-300">{tier.role}</p>
                    </div>
                  ))}
                </div>
              )}
              <p>Sensor: {data.independent_validation.source.sensor}. Acquisition window: {data.independent_validation.source.acquisition_window}. Published: {data.independent_validation.source.published}.</p>
              <p>{data.independent_validation.metric_note}</p>
              {data.independent_validation.model_probability_metrics && (
                <div className="grid gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-emerald-950 md:grid-cols-5">
                  <div><p className="text-xs font-semibold">AUC ROC</p><p className="text-lg font-bold">{data.independent_validation.model_probability_metrics.roc_auc.toFixed(4)}</p></div>
                  <div><p className="text-xs font-semibold">Accuracy</p><p className="text-lg font-bold">{data.independent_validation.model_probability_metrics.accuracy.toFixed(4)}</p></div>
                  <div><p className="text-xs font-semibold">Precision</p><p className="text-lg font-bold">{data.independent_validation.model_probability_metrics.precision.toFixed(4)}</p></div>
                  <div><p className="text-xs font-semibold">Recall</p><p className="text-lg font-bold">{data.independent_validation.model_probability_metrics.recall.toFixed(4)}</p></div>
                  <div><p className="text-xs font-semibold">F1</p><p className="text-lg font-bold">{data.independent_validation.model_probability_metrics.f1.toFixed(4)}</p></div>
                </div>
              )}
              {data.independent_validation.patch_audit_artifact && (
                <p className="rounded border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300">Patch-level audit artifact: {data.independent_validation.patch_audit_artifact}</p>
              )}
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
        <Section id="ablation" title="UNOSAT Label-Margin Ablation"><AblationTable rows={data.ablation_results} /></Section>
        <Section id="findings" title="Key Findings And Limitations">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <h3 className="font-semibold text-slate-800 dark:text-slate-100">Key findings</h3>
              <ul className="mt-2 space-y-2 text-sm text-slate-700 dark:text-slate-300">
                <li>The current NDWI-free XGBoost pass is real but weak: AUC ROC 0.3681 and F1 0.0629.</li>
                <li>The dominant failure case is over-prediction: 953 false positives at the default threshold.</li>
                <li>NDWI water fraction is now separated from the model input and audited against UNOSAT labels.</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-slate-800 dark:text-slate-100">Future work</h3>
              <ul className="mt-2 space-y-2 text-sm text-slate-700 dark:text-slate-300">
                <li>Retrain on real labeled multi-region data, not synthetic first-run data.</li>
                <li>Add land-cover evidence to test built-up and dense-vegetation failure hypotheses.</li>
                <li>Replace simulated comparison curves with real ROC points from scored validation folds.</li>
              </ul>
            </div>
          </div>
        </Section>
      </div>
    </div>
  );
}
