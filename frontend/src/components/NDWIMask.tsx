import { useEffect, useRef } from "react";

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

function drawPanel(canvas: HTMLCanvasElement, masked: boolean) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const size = 256;
  canvas.width = size;
  canvas.height = size;
  const image = ctx.createImageData(size, size);
  let i = 0;
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const basinA = Math.hypot((x - 72) / 70, (y - 92) / 44);
      const basinB = Math.hypot((x - 184) / 52, (y - 166) / 78);
      const river = Math.abs(y - 148 - Math.sin(x / 25) * 34) / 42;
      const texture = valueNoise(x, y, 24, 18) * 0.45 + valueNoise(x, y, 91, 46) * 0.55;
      const ndwi = Math.max(1.05 - basinA, 1.0 - basinB, 0.72 - river) + texture * 0.52 - 0.42;
      const water = ndwi > 0;
      const landTone = 88 + valueNoise(x, y, 44, 11) * 68;
      const waterTone = 124 + valueNoise(x, y, 51, 19) * 58;
      const color = masked
        ? water
          ? [0, 124 + valueNoise(x, y, 61, 15) * 48, 230 + valueNoise(x, y, 17, 9) * 25]
          : [124 + texture * 36, 132 + texture * 32, 136 + texture * 30]
        : water
          ? [32 + texture * 16, 82 + texture * 42, waterTone]
          : [landTone + 16, landTone, 52 + texture * 28];
      image.data[i++] = color[0];
      image.data[i++] = color[1];
      image.data[i++] = color[2];
      image.data[i++] = 255;
    }
  }
  ctx.putImageData(image, 0, 0);
}

export default function NDWIMask() {
  const raw = useRef<HTMLCanvasElement>(null);
  const mask = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (raw.current) drawPanel(raw.current, false);
    if (mask.current) drawPanel(mask.current, true);
  }, []);

  return (
    <div>
      <div className="grid gap-4 md:grid-cols-2">
        <figure className="card p-3">
          <canvas ref={raw} className="aspect-square w-full rounded-md" />
          <figcaption className="mt-2 text-center text-sm font-medium text-slate-700">Diagnostic satellite-style view</figcaption>
        </figure>
        <figure className="card p-3">
          <canvas ref={mask} className="aspect-square w-full rounded-md" />
          <figcaption className="mt-2 text-center text-sm font-medium text-slate-700">NDWI feature response</figcaption>
        </figure>
      </div>
      <p className="mt-3 text-sm text-slate-600">NDWI is computed during preprocessing and audited separately from UNOSAT validation labels.</p>
      <div className="mt-3 h-3 rounded-full bg-gradient-to-r from-slate-400 to-blue-500" />
      <div className="mt-1 flex justify-between text-xs text-slate-500"><span>Non-water</span><span>Water/flooded</span></div>
    </div>
  );
}
