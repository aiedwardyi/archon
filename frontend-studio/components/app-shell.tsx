"use client"

import { useEffect, useRef } from "react"
import { Navbar } from "@/components/navbar"
import { useNotificationSound } from "@/hooks/useNotificationSound"

const API_BASE = "http://localhost:5000"
const POLL_INTERVAL_MS = 4000

export function AppShell({ children }: { children: React.ReactNode }) {
  const { playSuccess, playFailure } = useNotificationSound()
  const prevExecutionStatusRef = useRef<"RUNNING" | "COMPLETED" | "FAILED" | null>(null)

  useEffect(() => {
    let mounted = true

    const pollExecutionStatus = async () => {
      if (!mounted) return

      const pid = sessionStorage.getItem("archon_current_project_id")
      const pipelineStatus = sessionStorage.getItem("archon_pipeline_status")
      if (!pid || pipelineStatus !== "running") {
        prevExecutionStatusRef.current = null
        return
      }

      try {
        const res = await fetch(`${API_BASE}/api/execution-status?project_id=${pid}`)
        if (!res.ok) return
        const data = await res.json()

        if (!data.project_id || Number(data.project_id) !== Number(pid)) return

        const status = data.status as "RUNNING" | "COMPLETED" | "FAILED" | undefined
        const transitionedFromRunning = prevExecutionStatusRef.current === "RUNNING"

        if (status === "COMPLETED" && transitionedFromRunning) {
          void playSuccess()
        } else if (status === "FAILED" && transitionedFromRunning) {
          void playFailure()
        }

        if (status === "COMPLETED") {
          sessionStorage.setItem("archon_pipeline_status", "complete")
        } else if (status === "FAILED") {
          sessionStorage.setItem("archon_pipeline_status", "failed")
        }

        if (status === "RUNNING" || status === "COMPLETED" || status === "FAILED") {
          prevExecutionStatusRef.current = status
        }
      } catch {
        // Non-fatal. Next interval will retry.
      }
    }

    void pollExecutionStatus()
    const interval = window.setInterval(() => {
      void pollExecutionStatus()
    }, POLL_INTERVAL_MS)

    return () => {
      mounted = false
      window.clearInterval(interval)
    }
  }, [playFailure, playSuccess])

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />
      <main className="flex-1 flex flex-col">{children}</main>
    </div>
  )
}
