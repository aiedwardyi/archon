import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    watch: {
      // Ignore public directory to prevent HMR on runtime artifact changes
      ignored: ["**/public/**"]
    }
  }
});
