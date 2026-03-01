import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

const params = new URLSearchParams(window.location.search);
const urlToken = params.get("token");
if (urlToken) {
  localStorage.setItem("archon_token", urlToken);
  params.delete("token");
  const remaining = params.toString();
  window.history.replaceState({}, "", remaining ? `${window.location.pathname}?${remaining}` : window.location.pathname);
}

createRoot(document.getElementById("root")!).render(<App />);
