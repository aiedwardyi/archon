"use client"

import { useState, useRef, useEffect } from "react"
import { useTheme } from "next-themes"
import {
  Sun,
  Moon,
  LogOut,
  Settings,
  BookOpen,
  User,
  DollarSign,
  Coins,
  Zap,
  ExternalLink,
} from "lucide-react"

export function AvatarDropdown() {
  const [open, setOpen] = useState(false)
  const { resolvedTheme, setTheme } = useTheme()
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  const isDark = resolvedTheme === "dark"

  return (
    <div className="relative" ref={ref}>
      {/* Avatar button */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="h-7 w-7 rounded-full bg-primary flex items-center justify-center hover:opacity-80 transition-opacity focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1"
      >
        <span className="text-primary-foreground text-xs font-semibold select-none">JD</span>
      </button>

      {open && (
        <div className="absolute right-0 top-9 w-64 rounded-xl border border-border bg-popover shadow-xl z-50 overflow-hidden">

          {/* Email header */}
          <div className="px-3 py-3 border-b border-border">
            <p className="text-xs text-muted-foreground">Signed in as</p>
            <p className="text-sm font-semibold text-foreground truncate mt-0.5">archon@archon.dev</p>
          </div>

          {/* Nav links */}
          <div className="py-1">
            {[
              { label: "Profile", icon: User },
              { label: "Settings", icon: Settings },
            ].map(({ label, icon: Icon }) => (
              <button
                key={label}
                onClick={() => setOpen(false)}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-foreground hover:bg-accent transition-colors"
              >
                <Icon className="h-4 w-4 text-muted-foreground shrink-0" />
                {label}
              </button>
            ))}

            {/* Pricing & Docs with external link icon */}
            {[
              { label: "Pricing", icon: DollarSign },
              { label: "Documentation", icon: BookOpen },
            ].map(({ label, icon: Icon }) => (
              <button
                key={label}
                onClick={() => setOpen(false)}
                className="w-full flex items-center justify-between px-3 py-2 text-sm text-foreground hover:bg-accent transition-colors"
              >
                <span className="flex items-center gap-2.5">
                  <Icon className="h-4 w-4 text-muted-foreground shrink-0" />
                  {label}
                </span>
                <ExternalLink className="h-3 w-3 text-muted-foreground/60" />
              </button>
            ))}
          </div>

          {/* Theme toggle row */}
          <div className="border-t border-border px-3 py-2.5">
            <p className="text-xs text-muted-foreground mb-2 font-medium">Theme</p>
            <div className="flex items-center gap-1 bg-muted rounded-lg p-1">
              <button
                onClick={() => setTheme("light")}
                className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-md text-xs font-medium transition-all group ${
                  !isDark
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Sun className="h-3.5 w-3.5 transition-transform duration-500 group-hover:rotate-90" />
                Light
              </button>
              <button
                onClick={() => setTheme("dark")}
                className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-md text-xs font-medium transition-all group ${
                  isDark
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Moon className="h-3.5 w-3.5 transition-transform duration-500 group-hover:-rotate-12" />
                Dark
              </button>
            </div>
          </div>

          {/* Credits */}
          <div className="border-t border-border px-3 py-2.5">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-sm text-foreground">
                <Coins className="h-4 w-4 text-amber-500" />
                Credits
              </span>
              <span className="text-sm font-semibold text-foreground">1,250</span>
            </div>
          </div>

          {/* Upgrade */}
          <div className="border-t border-border p-2">
            <button
              onClick={() => setOpen(false)}
              className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              <Zap className="h-3.5 w-3.5" />
              Upgrade to Pro
            </button>
          </div>

          {/* Sign out */}
          <div className="border-t border-border py-1">
            <button
              onClick={() => setOpen(false)}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-destructive hover:bg-accent transition-colors"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>

        </div>
      )}
    </div>
  )
}
