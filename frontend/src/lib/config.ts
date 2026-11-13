/**
 * Single source of truth for the backend URL.
 *
 * NEXT_PUBLIC_BACKEND_URL is inlined at BUILD time by Next.js, so on Railway it must be
 * set as a variable of the frontend service before the build runs.
 * Local development falls back to http://localhost:8000; production never silently
 * falls back to localhost (that would only ever fail in the user's browser).
 */
const raw = (process.env.NEXT_PUBLIC_BACKEND_URL || "").trim();

export const BACKEND_URL: string = (
  raw || (process.env.NODE_ENV === "production" ? "" : "http://localhost:8000")
).replace(/\/+$/, "");

export const BACKEND_CONFIGURED = BACKEND_URL !== "";

export function apiUrl(path: string): string {
  if (!BACKEND_CONFIGURED) {
    throw new Error(
      "NEXT_PUBLIC_BACKEND_URL is not set for this build, so the app does not know where the Sagarvani backend is."
    );
  }
  return `${BACKEND_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

/** Pull a human-readable message out of a failed backend response. */
export async function readApiError(res: Response): Promise<string> {
  const body = await res.json().catch(() => null);
  const detail = body && (typeof body.detail === "string" ? body.detail : null);
  const rid = body?.request_id ? ` (ref ${body.request_id})` : "";
  return `${detail || `Request failed with HTTP ${res.status}`}${rid}`;
}
