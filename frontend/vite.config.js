import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies the Django backend so the app is same-origin in dev too
// (no CORS setup needed). Override with VITE_PROXY_TARGET if Django runs elsewhere.
const target = process.env.VITE_PROXY_TARGET || "http://127.0.0.1:8000";
const proxied = Object.fromEntries(
  ["/api", "/media", "/admin", "/static"].map((p) => [p, { target, changeOrigin: true }]),
);

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: proxied },
  preview: { port: 4173, proxy: proxied },
  build: { outDir: "dist", sourcemap: false },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.js",
    css: false,
    // Tests talk to a real Django server when E2E=1 (see src/test/e2e.test.jsx).
    env: { VITE_API_BASE: process.env.TEST_API_BASE || "http://127.0.0.1:8000/api/v1" },
  },
});
