import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The frontend only ever calls same-origin /api and /media; whoever serves it supplies
// the proxy. Vite does it here for `dev` and `preview`, vercel.json does it in
// production. That keeps a hard-coded backend host out of the built bundle, which would
// otherwise send every visitor's requests to their own machine.
const API_TARGET = process.env.VITE_PROXY_TARGET || "http://127.0.0.1:8000";
const proxy = {
  "/api": { target: API_TARGET, changeOrigin: true },
  "/media": { target: API_TARGET, changeOrigin: true },
};

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy,
  },
  preview: {
    port: 4173,
    strictPort: true,
    proxy,
  },
  // Vitest transforms with esbuild rather than the React plugin's Babel pass, and
  // esbuild's default classic runtime left every .test.jsx file throwing
  // "React is not defined". The automatic runtime needs no React in scope.
  esbuild: { jsx: "automatic" },
  build: {
    outDir: "dist",
    // Maps would publish the un-minified sources alongside the bundle and slow the
    // first download; the dev server still gives readable stack traces locally.
    sourcemap: false,
    chunkSizeWarningLimit: 900,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.js",
  },
});
