import { useEffect, useRef, useState } from "react";

type Panel = "green" | "nir" | "ndwi" | "mask";

function smoothstep(t: number) {
  return t * t * (3 - 2 * t);
}

function hashNoise(x: number, y: number, seed: number) {
  const n = Math.sin(x * 127.1 + y * 311.7 + seed * 61.3) * 43758.5453;
  return n - Math.floor(n);
}

function valueNoise(x: number, y: number, seed: number, scale: number) {
  const gx = x / scale;
  const gy = y / scale;
  const x0 = Math.floor(gx);
  const y0 = Math.floor(gy);
  const tx = smoothstep(gx - x0);
  const ty = smoothstep(gy - y0);
  const a = hashNoise(x0, y0, seed);
  const b = hashNoise(x0 + 1, y0, seed);
  const c = hashNoise(x0, y0 + 1, seed);
  const d = hashNoise(x0 + 1, y0 + 1, seed);
  return (a + (b - a) * tx) * (1 - ty) + (c + (d - c) * tx) * ty;
}

function syntheticBands(x: number, y: number) {
  const basinA = Math.hypot((x - 72) / 70, (y - 92) / 44);
  const basinB = Math.hypot((x - 184) / 52, (y - 166) / 78);
  const river = Math.abs(y - 148 - Math.sin(x / 25) * 34) / 42;
  const texture = valueNoise(x, y, 24, 18) * 0.45 + valueNoise(x, y, 91, 46) * 0.55;
  const water = Math.max(1.05 - basinA, 1.0 - basinB, 0.72 - river) + texture * 0.52 - 0.42 > 0;
  const green = water ? 0.62 + texture * 0.2 : 0.24 + texture * 0.18;
  const nir = water ? 0.18 + texture * 0.1 : 0.52 + texture * 0.22;
  const ndwi = (green - nir) / Math.max(0.001, green + nir);
  return { green, nir, ndwi, water };
}

function colorRamp(ndwi: number) {
  const t = Math.max(0, Math.min(1, (ndwi + 0.5) / 1.0));
  if (t < 0.5) {
    const k = t / 0.5;
    return [150 + k * 70, 118 + k * 70, 54 + k * 50];
  }
  const k = (t - 0.5) / 0.5;
  return [70 - k * 46, 168 + k * 42, 190 + k * 45];
}

function drawPanel(canvas: HTMLCanvasElement, panel: Panel) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const size = 256;
  canvas.width = size;
  canvas.height = size;
  const image = ctx.createImageData(size, size);
  let i = 0;
  let waterPixels = 0;
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const { green, nir, ndwi, water } = syntheticBands(x, y);
      if (water) waterPixels += 1;
      let color: number[];
      if (panel === "green") {
        const v = Math.round(green * 255);
        color = [36, v, 88];
      } else if (panel === "nir") {
        const v = Math.round(nir * 255);
        color = [v, 64 + v * 0.35, 56];
      } else if (panel === "mask") {
        color = ndwi > 0 ? [0, 145, 230] : [126, 134, 141];
      } else {
        color = colorRamp(ndwi);
      }
      image.data[i++] = color[0];
      image.data[i++] = color[1];
      image.data[i++] = color[2];
      image.data[i++] = 255;
    }
  }
  ctx.putImageData(image, 0, 0);
  canvas.dataset.waterFraction = String(Math.round((waterPixels / (size * size)) * 100));
}

function FigurePanel({ title, subtitle, panel }: { title: string; subtitle: string; panel: Panel }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    if (ref.current) drawPanel(ref.current, panel);
  }, [panel]);
  return (
    <figure className="rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-950">
      <canvas ref={ref} className="aspect-square w-full rounded-md" />
      <figcaption className="mt-2">
        <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">{title}</p>
        <p className="text-xs text-slate-600 dark:text-slate-400">{subtitle}</p>
      </figcaption>
    </figure>
  );
}

export default function NDWIMask() {
  const [waterFraction] = useState(39);
  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm text-blue-950 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-100">
        <p className="font-semibold">NDWI = (Green - NIR) / (Green + NIR)</p>
        <p className="mt-1">Pixels with NDWI &gt; 0.0 are treated as water-feature pixels for feature extraction. UNOSAT labels remain the independent validation source.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <FigurePanel title="Green band" subtitle="Water reflects more green light." panel="green" />
        <FigurePanel title="NIR band" subtitle="Water suppresses near-infrared response." panel="nir" />
        <FigurePanel title="Continuous NDWI" subtitle="Brown/gray = low, cyan/blue = high." panel="ndwi" />
        <FigurePanel title="Thresholded mask" subtitle="Blue pixels are NDWI > 0.0." panel="mask" />
      </div>
      <div className="grid gap-4 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950 md:grid-cols-[1fr_220px] md:items-center">
        <div>
          <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Patch-level feature summary</p>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">The water fraction feature is the percentage of 64x64 patch pixels where NDWI exceeds the water threshold.</p>
        </div>
        <div>
          <div className="flex items-center justify-between text-xs font-semibold text-slate-600 dark:text-slate-400">
            <span>0%</span>
            <span>{waterFraction}% water-feature pixels</span>
          </div>
          <div className="mt-2 h-3 rounded-full bg-slate-200 dark:bg-slate-800">
            <div className="h-3 rounded-full bg-blue-500" style={{ width: `${waterFraction}%` }} />
          </div>
        </div>
      </div>
    </div>
  );
}
