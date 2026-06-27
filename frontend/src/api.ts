/**
 * API client for the decent-visualizer backend.
 *
 * In local dev: VITE_API_URL is unset → calls are relative (vite proxy handles /api/*).
 * In production (Cloudflare Pages): VITE_API_URL = "http://<GCE_IP>" →
 *   calls go directly to the backend.
 *
 * Set VITE_API_URL in .env.local for dev, or via Terraform / deploy script for production.
 */

const API_BASE = import.meta.env.VITE_API_URL ?? "";

export function apiRequest(path: string, init?: RequestInit) {
  return fetch(`${API_BASE}${path}`, { credentials: "include", ...init });
}

export const api = {
  get: (path: string, init?: RequestInit) => apiRequest(path, init),
  post: (path: string, body?: unknown) =>
    apiRequest(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    }),
  patch: (path: string, body?: unknown) =>
    apiRequest(path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    }),
  delete: (path: string) =>
    apiRequest(path, { method: "DELETE" }),
  upload: (path: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return apiRequest(path, { method: "POST", body: form });
  },
};
