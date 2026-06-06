/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Backend API base URL. Unset in local dev (vite proxy handles /api/*).
   *  Set to "http://<GCE_IP>" in production builds. */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
