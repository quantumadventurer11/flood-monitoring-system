import { createReadStream, existsSync } from "node:fs";
import { stat } from "node:fs/promises";
import { createServer, request as httpRequest } from "node:http";
import { extname, join, normalize, resolve } from "node:path";

const port = Number(process.env.PORT ?? 3005);
const apiTarget = new URL(process.env.API_TARGET ?? "http://localhost:8000");
const distDir = resolve(process.env.DIST_DIR ?? join(process.cwd(), "frontend", "dist"));

const mimeTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
};

function send(res, statusCode, body, contentType = "text/plain; charset=utf-8") {
  res.writeHead(statusCode, { "content-type": contentType });
  res.end(body);
}

function proxyApi(req, res) {
  const path = req.url.replace(/^\/api/, "") || "/";
  const upstream = httpRequest(
    {
      hostname: apiTarget.hostname,
      port: apiTarget.port || 80,
      path,
      method: req.method,
      headers: { ...req.headers, host: apiTarget.host },
    },
    (upstreamRes) => {
      res.writeHead(upstreamRes.statusCode ?? 502, upstreamRes.headers);
      upstreamRes.pipe(res);
    },
  );
  upstream.on("error", (error) => send(res, 502, `API proxy failed: ${error.message}`));
  req.pipe(upstream);
}

async function serveStatic(req, res) {
  const pathname = decodeURIComponent(new URL(req.url, "http://localhost").pathname);
  const requested = normalize(pathname).replace(/^(\.\.[/\\])+/, "");
  let filePath = resolve(join(distDir, requested));
  if (!filePath.startsWith(distDir) || !existsSync(filePath)) filePath = join(distDir, "index.html");
  const info = await stat(filePath);
  if (info.isDirectory()) filePath = join(distDir, "index.html");
  res.writeHead(200, { "content-type": mimeTypes[extname(filePath)] ?? "application/octet-stream" });
  createReadStream(filePath).pipe(res);
}

createServer((req, res) => {
  if (req.url?.startsWith("/api/") || req.url === "/api") {
    proxyApi(req, res);
    return;
  }
  serveStatic(req, res).catch((error) => send(res, 500, error.message));
}).listen(port, "0.0.0.0", () => {
  console.log(`Public demo server listening on http://localhost:${port}`);
  console.log(`Proxying /api to ${apiTarget.href}`);
});
