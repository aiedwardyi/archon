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
    if (!PUBLIC_ROUTES.includes(pathname) && !authService.isLoggedIn()) {
      router.replace("/login");
    } else {
      setChecked(true);
    }
  }, [pathname, router]);

  if (!PUBLIC_ROUTES.includes(pathname) && !checked) return null;
  return <>{children}</>;
}
