import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During dev, proxy /api to the FastAPI backend so the browser sees one origin
// (no CORS friction) and we never hardcode the backend host in the app code.
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.indexOf("node_modules") < 0) return;

          if (
            id.indexOf("/node_modules/three/") >= 0
            || id.indexOf("three/build/") >= 0
            || id.indexOf("three/src/") >= 0
            || id.indexOf("three.module") >= 0
          ) {
            return "three-vendor";
          }

          if (
            id.indexOf("globe.gl") >= 0
            || id.indexOf("three-globe") >= 0
            || id.indexOf("d3-") >= 0
          ) {
            return "globe-vendor";
          }

          if (id.indexOf("echarts") >= 0 || id.indexOf("zrender") >= 0) {
            return "echarts-vendor";
          }

          if (id.indexOf("react") >= 0 || id.indexOf("scheduler") >= 0 || id.indexOf("react-router") >= 0) {
            return "react-vendor";
          }
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
