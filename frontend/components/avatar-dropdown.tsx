"use client"

import { useState, useRef, useEffect } from "react"
import { usePathname, useRouter } from "next/navigation"
import { useTheme } from "next-themes"
import {
  Sun, Moon, LogOut, Settings, BookOpen,
  User, DollarSign, Coins, Zap, ExternalLink,
  Building2, Paintbrush,
} from "lucide-react"
import { ProfileModal, SettingsModal, PricingModal } from "@/components/account-modals"
import { authService } from "@/lib/auth"
import { useLanguage } from "@/contexts/LanguageContext"

export function AvatarDropdown() {
  const [open, setOpen] = useState(false)
  const [modal, setModal] = useState<"profile" | "settings" | "pricing" | null>(null)
  const { resolvedTheme, setTheme } = useTheme()
  const pathname = usePathname()
  const router = useRouter()
  const ref = useRef<HTMLDivElement>(null)
  const { language, t } = useLanguage()

  function handleSignOut() {
    authService.logout()
    setOpen(false)
    router.push("/login")
  }

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  const isDark = resolvedTheme === "dark"
  const openModal = (m: "profile" | "settings" | "pricing") => {
    setOpen(false)
    setModal(m)
  }

  return (
    <>
      {modal === "profile" && <ProfileModal onClose={() => setModal(null)} />}
      {modal === "settings" && <SettingsModal onClose={() => setModal(null)} />}
      {modal === "pricing" && <PricingModal onClose={() => setModal(null)} />}

      <div className="relative" ref={ref}>
        <button
          onClick={() => setOpen((o) => !o)}
          className="h-7 w-7 rounded-full bg-primary flex items-center justify-center hover:opacity-80 transition-opacity focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1"
        >
          <span className="text-primary-foreground text-xs font-semibold select-none">JD</span>
        </button>

        {open && (
          <div className="absolute right-0 top-9 w-64 rounded-xl border border-border bg-popover shadow-xl z-50 overflow-hidden">

            <div className="px-3 py-3 border-b border-border">
              <p className="text-xs text-muted-foreground">{t("signedInAs")}</p>
              <p className="text-sm font-semibold text-foreground truncate mt-0.5">archon@archon.dev</p>
            </div>

            <div className="py-1">
              <button
                onClick={() => openModal("profile")}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-foreground hover:bg-accent transition-colors"
              >
                <User className="h-4 w-4 text-muted-foreground shrink-0" />
                {t("profile")}
              </button>
              <button
                onClick={() => openModal("settings")}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-foreground hover:bg-accent transition-colors"
              >
                <Settings className="h-4 w-4 text-muted-foreground shrink-0" />
                {t("settings")}
              </button>
              <button
                onClick={() => openModal("pricing")}
                className="w-full flex items-center justify-between px-3 py-2 text-sm text-foreground hover:bg-accent transition-colors"
              >
                <span className="flex items-center gap-2.5">
                  <DollarSign className="h-4 w-4 text-muted-foreground shrink-0" />
                  {t("pricing")}
                </span>
                <ExternalLink className="h-3 w-3 text-muted-foreground/60" />
              </button>
              <a
                href="https://docs.archon.dev"
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => setOpen(false)}
                className="w-full flex items-center justify-between px-3 py-2 text-sm text-foreground hover:bg-accent transition-colors"
              >
                <span className="flex items-center gap-2.5">
                  <BookOpen className="h-4 w-4 text-muted-foreground shrink-0" />
                  {t("documentation")}
                </span>
                <ExternalLink className="h-3 w-3 text-muted-foreground/60" />
              </a>
            </div>

            <div className="border-t border-border px-3 py-2.5">
              <p className="text-xs text-muted-foreground mb-2 font-medium">{t("theme")}</p>
              <div className="flex items-center gap-1 bg-muted rounded-lg p-1">
                <button
                  onClick={() => setTheme("light")}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-md text-xs font-medium transition-all ${!isDark ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
                >
                  <Sun className="h-3.5 w-3.5" />
                  {t("light")}
                </button>
                <button
                  onClick={() => setTheme("dark")}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-md text-xs font-medium transition-all ${isDark ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
                >
                  <Moon className="h-3.5 w-3.5" />
                  {t("dark")}
                </button>
              </div>
            </div>

            <div className="border-t border-border px-3 py-2.5">
              <p className="text-xs text-muted-foreground mb-2 font-medium">{t("design")}</p>
              <div className="flex items-center gap-1 bg-muted rounded-lg p-1">
                <button
                  onClick={() => {
                    console.log('[studio] raw pathname:', pathname);
                    const pathToTab: Record<string, string> = { '/': 'projects', '/pipeline': 'pipeline', '/versions': 'versions', '/artifacts': 'artifacts' };
                    const tab = pathToTab[pathname] || 'projects';
                    console.log('[studio] switching to enterprise, pathname:', pathname, 'mapped tab:', tab);
                    const storedPid = sessionStorage.getItem("archon_current_project_id");
                    const params = new URLSearchParams();
                    params.set("tab", tab);
                    if (storedPid) params.set("projectId", storedPid);
                    if (language === "ko") params.set("lang", "ko");
                    window.location.href = `http://localhost:8080?${params.toString()}`;
                  }}
                  className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-md text-xs font-medium transition-all text-muted-foreground hover:text-foreground"
                >
                  <Building2 className="h-3.5 w-3.5" />
                  {t("enterprise")}
                </button>
                <button
                  onClick={() => setOpen(false)}
                  className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-md text-xs font-medium transition-all bg-card text-foreground shadow-sm"
                >
                  <Paintbrush className="h-3.5 w-3.5" />
                  {t("studio")}
                </button>
              </div>
            </div>

            <div className="border-t border-border px-3 py-2.5">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm text-foreground">
                  <Coins className="h-4 w-4 text-amber-500" />
                  {t("credits")}
                </span>
                <span className="text-sm font-semibold text-foreground">1,250</span>
              </div>
            </div>

            <div className="border-t border-border p-2">
              <button
                onClick={() => openModal("pricing")}
                className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
              >
                <Zap className="h-3.5 w-3.5" />
                {t("upgradeToPro")}
              </button>
            </div>

            <div className="border-t border-border py-1">
              <button
                onClick={handleSignOut}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-destructive hover:bg-accent transition-colors"
              >
                <LogOut className="h-4 w-4" />
                {t("signOut")}
              </button>
            </div>

          </div>
        )}
      </div>
    </>
  )
}
