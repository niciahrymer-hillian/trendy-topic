import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// During dev, proxy /api to the FastAPI backend so the browser sees one origin
// (no CORS friction) and we never hardcode the backend host in the app code.
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            "/api": "http://localhost:8000",
        },
    },
});
