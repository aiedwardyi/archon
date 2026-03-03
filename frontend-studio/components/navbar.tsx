"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useState } from "react"
import {
  LayoutDashboard,
  Play,
  Clock,
  FileCode2,
  Hexagon,
  ChevronRight,
  Coins,
} from "lucide-react"
import { AvatarDropdown } from "@/components/avatar-dropdown"
import { useLanguage } from "@/contexts/LanguageContext"

import type { TranslationKey } from "@/lib/i18n"

const navItems: { href: string; labelKey: TranslationKey; icon: typeof LayoutDashboard }[] = [
  { href: "/", labelKey: "projects", icon: LayoutDashboard },
  { href: "/pipeline", labelKey: "pipeline", icon: Play },
  { href: "/versions", labelKey: "versions", icon: Clock },
  { href: "/artifacts", labelKey: "artifacts", icon: FileCode2 },
]

export function Navbar() {
  const pathname = usePathname()
  const { language, toggleLanguage, t } = useLanguage()
  const [projectName, setProjectName] = useState<string | null>(null)
  const [version, setVersion] = useState<string | null>(null)
  const [creditsRemaining, setCreditsRemaining] = useState<number | null>(null)

  useEffect(() => {
    const load = () => {
      const token = localStorage.getItem("archon_token")
      fetch("http://localhost:5000/api/credits/balance", {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      })
        .then(r => r.json())
        .then(d => setCreditsRemaining(d.credits_remaining))
        .catch(() => {})
    }
    load()
    const interval = setInterval(load, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const readStorage = () => {
      const pname = sessionStorage.getItem("archon_project_name")
      // Pipeline page: always show the current build version
      // All other pages (Versions, Artifacts, etc.): prefer the user-selected version
      const isPipelinePage = window.location.pathname.startsWith("/pipeline")
      const ver = isPipelinePage
        ? (sessionStorage.getItem("archon_current_version") || sessionStorage.getItem("archon_selected_version"))
        : (sessionStorage.getItem("archon_selected_version") || sessionStorage.getItem("archon_current_version"))
      setProjectName(pname)
      setVersion(ver)
    }

    const onVersionChange = (e: Event) => {
      const v = (e as CustomEvent).detail?.version
      if (v != null) setVersion(String(v))
    }

    readStorage()
    window.addEventListener("storage", readStorage)
    window.addEventListener("archon:version-change", onVersionChange)
    return () => {
      window.removeEventListener("storage", readStorage)
      window.removeEventListener("archon:version-change", onVersionChange)
    }
  }, [pathname])

  return (
    <header className="flex items-center justify-between h-14 border-b border-border bg-card px-6">
      <div className="flex items-center gap-8">
        <Link href="/" className="flex items-center gap-2">
          <Hexagon className="h-5 w-5 text-primary" strokeWidth={2.5} />
          <span className="text-foreground font-semibold text-base tracking-tight">Archon</span>
        </Link>
        <nav className="flex items-center gap-1">
          {navItems.map((item) => {
            const isActive = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href)
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors ${
                  isActive
                    ? "bg-accent text-accent-foreground font-medium"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                <item.icon className="h-4 w-4" />
                {t(item.labelKey)}
              </Link>
            )
          })}
        </nav>
      </div>
      <div className="flex items-center gap-3 min-w-0 shrink">
        {projectName && (
          <span className="hidden md:flex items-center text-xs text-muted-foreground font-mono max-w-[160px] truncate">
            {projectName}
            {version && (
              <>
                <ChevronRight className="h-3 w-3 mx-0.5" />
                <span className="text-foreground">v{version}</span>
              </>
            )}
          </span>
        )}
        <div className="flex items-center gap-2">
          <div className="hidden md:flex items-center rounded-md border border-border overflow-hidden">
            <button
              onClick={toggleLanguage}
              className={`px-2 py-1 text-xs font-medium transition-colors ${
                language === "en"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              EN
            </button>
            <button
              onClick={toggleLanguage}
              className={`px-2 py-1 text-xs font-medium transition-colors ${
                language === "ko"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              KO
            </button>
          </div>
          <span className="hidden md:flex items-center gap-1 text-xs text-muted-foreground font-medium">
            <Coins className="h-3.5 w-3.5 text-amber-500" />
            {creditsRemaining !== null ? creditsRemaining.toLocaleString() : "—"}
          </span>
          <AvatarDropdown />
        </div>
      </div>
    </header>
  )
}





