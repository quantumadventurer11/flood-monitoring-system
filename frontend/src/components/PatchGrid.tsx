import { useEffect, useRef } from "react";

function rand(seed: number) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function smoothstep(t: number) {
  return t * t * (3 - 2 * t);
}

function hashNoise(x: number, y: number, seed: number) {
  const n = Math.sin(x * 127.1 + y * 311.7 + seed * 74.7) * 43758.5453;
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
  const top = a + (b - a) * tx;
  const bottom = c + (d - c) * tx;
  return top + (bottom - top) * ty;
}

function drawPatch(canvas: HTMLCanvasElement, flooded: boolean, seed: number) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const size = 64;
  canvas.width = size;
  canvas.height = size;
  const img = ctx.createImageData(size, size);
  const random = rand(seed);
  const blobs = Array.from({ length: flooded ? 4 : 2 }, () => ({
    x: random() * size,
    y: random() * size,
    rx: 10 + random() * (flooded ? 18 : 8),
    ry: 7 + random() * (flooded ? 16 : 7),
    angle: random() * Math.PI,
  }));
  const fieldAngle = random() * Math.PI;
  const fieldFrequency = 0.12 + random() * 0.08;
  let p = 0;
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const terrain = valueNoise(x, y, seed, 9) * 0.55 + valueNoise(x, y, seed + 17, 23) * 0.45;
      const cropLine = Math.sin((Math.cos(fieldAngle) * x + Math.sin(fieldAngle) * y) * fieldFrequency + seed * 0.01);
      const waterMask = blobs.some((blob) => {
        const dx = x - blob.x;
        const dy = y - blob.y;
        const ca = Math.cos(blob.angle);
        const sa = Math.sin(blob.angle);
        const px = (dx * ca + dy * sa) / blob.rx;
        const py = (-dx * sa + dy * ca) / blob.ry;
        return px * px + py * py < 1 + terrain * 0.45;
      });
      const water = flooded && waterMask;
      const r = water ? 20 + terrain * 20 : 82 + terrain * 58 + cropLine * 7;
      const g = water ? 88 + terrain * 32 : 116 + terrain * 58 + cropLine * 14;
      const b = water ? 146 + terrain * 76 : 58 + terrain * 38;
      img.data[p++] = r;
      img.data[p++] = g;
      img.data[p++] = b;
      img.data[p++] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
}

function Patch({ flooded, index }: { flooded: boolean; index: number }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    if (ref.current) drawPatch(ref.current, flooded, 143 + index * 79);
  }, [flooded, index]);
  return (
    <div className="relative overflow-hidden rounded-md border border-slate-200">
      <canvas ref={ref} className="w-full [image-rendering:pixelated]" />
      <span className={`absolute left-1 top-1 rounded px-1.5 py-0.5 text-[10px] font-bold text-white ${flooded ? "bg-blue-600" : "bg-green-700"}`}>
        {flooded ? "FLOOD" : "NO-FLOOD"}
      </span>
    </div>
  );
}

export default function PatchGrid() {
  return (
    <div>
      <h3 className="mb-3 text-base font-semibold text-slate-800">Extracted image patches - flood vs. non-flood regions</h3>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {Array.from({ length: 16 }, (_, i) => <Patch key={i} flooded={i < 8} index={i} />)}
      </div>
    </div>
  );
}
