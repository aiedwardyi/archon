import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

const params = new URLSearchParams(window.location.search);
const urlToken = params.get("token");
if (urlToken) {
  localStorage.setItem("archon_token", urlToken);
  window.history.replaceState({}, "", window.location.pathname);
}

createRoot(document.getElementById("root")!).render(<App />);
