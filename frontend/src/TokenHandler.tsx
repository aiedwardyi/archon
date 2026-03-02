import { useEffect } from "react";

export default function TokenHandler() {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    const theme = params.get("theme");
    if (token) {
      localStorage.setItem("archon_token", token);
      localStorage.setItem("archon_active_tab", "projects");
      if (theme) {
        localStorage.setItem("theme", theme);
      } else if (!localStorage.getItem("theme")) {
        localStorage.setItem("theme", "dark");
      }
      window.history.replaceState({}, "", "/");
    }
  }, []);
  return null;
}
