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
} from "lucide-react"
import { AvatarDropdown } from "@/components/avatar-dropdown"

const navItems = [
  { href: "/", label: "Projects", icon: LayoutDashboard },
  { href: "/pipeline", label: "Pipeline", icon: Play },
  { href: "/versions", label: "Versions", icon: Clock },
  { href: "/artifacts", label: "Artifacts", icon: FileCode2 },
]

export function Navbar() {
  const pathname = usePathname()
  const [projectName, setProjectName] = useState<string | null>(null)
  const [version, setVersion] = useState<string | null>(null)

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
                {item.label}
              </Link>
            )
          })}
        </nav>
      </div>
      <div className="flex items-center gap-3">
        {projectName && (
          <span className="hidden md:flex items-center text-xs text-muted-foreground font-mono">
            {projectName}
            {version && (
              <>
                <ChevronRight className="h-3 w-3 mx-0.5" />
                <span className="text-foreground">v{version}</span>
              </>
            )}
          </span>
        )}
        <AvatarDropdown />
      </div>
    </header>
  )
}



