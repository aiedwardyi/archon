"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useTheme } from "next-themes"
import {
  LayoutDashboard,
  Play,
  Clock,
  FileCode2,
  Hexagon,
  Sun,
  Moon,
  ChevronRight,
} from "lucide-react"

const navItems = [
  { href: "/", label: "Projects", icon: LayoutDashboard },
  { href: "/pipeline", label: "Pipeline", icon: Play },
  { href: "/versions", label: "Versions", icon: Clock },
  { href: "/artifacts", label: "Artifacts", icon: FileCode2 },
]

export function Navbar() {
  const pathname = usePathname()
  const { resolvedTheme, setTheme } = useTheme()

  return (
    <header className="flex items-center justify-between h-14 border-b border-border bg-card px-6">
      <div className="flex items-center gap-8">
        <Link href="/" className="flex items-center gap-2">
          <Hexagon className="h-5 w-5 text-primary" strokeWidth={2.5} />
          <span className="text-foreground font-semibold text-base tracking-tight">
            Archon
          </span>
        </Link>
        <nav className="flex items-center gap-1">
          {navItems.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href)
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
        <span className="hidden md:flex items-center text-xs text-muted-foreground font-mono">
          checkout-service
          <ChevronRight className="h-3 w-3 mx-0.5" />
          <span className="text-foreground">v14</span>
        </span>
        <button
          onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
          className="p-1.5 rounded-md hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
          aria-label="Toggle dark mode"
        >
          <Sun className="h-4 w-4 hidden dark:block" />
          <Moon className="h-4 w-4 block dark:hidden" />
        </button>
        <div className="h-7 w-7 rounded-full bg-primary flex items-center justify-center">
          <span className="text-primary-foreground text-xs font-medium">
            JD
          </span>
        </div>
      </div>
    </header>
  )
}
