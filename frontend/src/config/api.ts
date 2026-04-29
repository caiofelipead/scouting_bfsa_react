/**
 * API URL routing configuration.
 *
 * To minimise Vercel Origin Transfer cost, analytics endpoints (large JSON
 * payloads) bypass the Vercel proxy and hit Render directly. Asset endpoints
 * (logos, faces, image proxy, config) stay on relative paths so the Vercel
 * edge cache keeps absorbing the load.
 */

export const RENDER_BACKEND = "https://scouting-bfsa-react.onrender.com";

/** Path prefixes that remain on Vercel-rewritten relative URLs (edge-cached). */
export const VERCEL_PROXIED_PREFIXES = [
  "/api/team-logo/",
  "/api/player-face/",
  "/api/image-proxy",
  "/api/config/",
];

/**
 * Returns the URL that the browser should request for `path`.
 * - For prefixes listed in VERCEL_PROXIED_PREFIXES → keep relative (Vercel proxy + edge cache).
 * - Otherwise → absolute Render URL (no Origin Transfer through Vercel).
 *
 * Absolute URLs (http(s)://...) and data:/blob: URIs are returned unchanged.
 */
export function apiUrl(path: string): string {
  if (!path) return path;
  if (/^(https?:|data:|blob:)/i.test(path)) return path;

  const normalized = path.startsWith("/") ? path : `/${path}`;
  const useProxy = VERCEL_PROXIED_PREFIXES.some((prefix) =>
    normalized.startsWith(prefix),
  );
  return useProxy ? normalized : `${RENDER_BACKEND}${normalized}`;
}

export const API_BASE = RENDER_BACKEND;
