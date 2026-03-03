"use client";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { authService } from "@/lib/auth";

const PUBLIC_ROUTES = ["/login", "/register", "/forgot-password"];

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get("token");
    const isSwitch = params.get("switch") === "1";

    // Save token synchronously FIRST before anything else runs
    if (urlToken && isSwitch) {
      localStorage.setItem("archon_token", urlToken);
    }

    const cleanAndCheck = () => {
      params.delete("token");
      params.delete("switch");
      const remaining = params.toString();
      const cleanUrl = window.location.pathname + (remaining ? `?${remaining}` : "");
      window.history.replaceState({}, "", cleanUrl);
    };

    if (urlToken && isSwitch) {
      fetch("http://localhost:5000/api/auth/me", {
        headers: { Authorization: `Bearer ${urlToken}` },
      })
        .then((r) => r.json())
        .then((user) => {
          if (user?.id) {
            localStorage.setItem("archon_user", JSON.stringify(user));
          }
        })
        .catch(() => {})
        .finally(() => {
          cleanAndCheck();
          if (!PUBLIC_ROUTES.includes(pathname) && !authService.isLoggedIn()) {
            router.replace("/login");
          } else {
            setChecked(true);
          }
        });
    } else {
      if (!PUBLIC_ROUTES.includes(pathname) && !authService.isLoggedIn()) {
        router.replace("/login");
      } else {
        setChecked(true);
      }
    }
  }, [pathname, router]);

  if (!PUBLIC_ROUTES.includes(pathname) && !checked) return null;
  return <>{children}</>;
}
