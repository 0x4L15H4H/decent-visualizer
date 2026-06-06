import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  // In local dev the vite proxy forwards /api/* to the backend.
  // When VITE_API_URL is set (production build), the proxy is disabled.
  const proxyTarget = env.VITE_API_URL || "http://localhost:8000";

  return {
    plugins: [react(), tailwindcss()],
    server: {
      proxy: env.VITE_API_URL
        ? undefined
        : {
            "/api": {
              target: proxyTarget,
              changeOrigin: true,
            },
          },
    },
  };
});
