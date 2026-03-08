"use client"

import { useState, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { ArtifactViewer } from "@/components/artifact-viewer"

const API_BASE = "http://localhost:5000"

function ArtifactsEmptyState({ message }: { message: string }) {
  return (
    <div className="flex min-h-[60vh] items-center justify-center px-6">
      <div className="max-w-md rounded-xl border border-border bg-card px-6 py-10 text-center">
        <h2 className="text-lg font-semibold text-foreground">Artifacts</h2>
        <p className="mt-2 text-sm text-muted-foreground">{message}</p>
      </div>
    </div>
  )
}

function ArtifactsInner() {
  const searchParams = useSearchParams()
  const initialTab = searchParams.get("tab") || undefined

  const [projectId, setProjectId] = useState<number | null>(null)
  const [version, setVersion] = useState<number | null>(null)
  const [ready, setReady] = useState(false)
  const [emptyMessage, setEmptyMessage] = useState<string | null>(null)

  useEffect(() => {
    const pid = sessionStorage.getItem("archon_current_project_id")
    const selectedVer = sessionStorage.getItem("archon_selected_version") || sessionStorage.getItem("archon_current_version")

    if (!pid) {
      setEmptyMessage("Select a project to view artifacts.")
      setReady(true)
      return
    }

    setProjectId(Number(pid))

    if (selectedVer) {
      setVersion(Number(selectedVer))
      setEmptyMessage(null)
      setReady(true)
      return
    }

    fetch(`${API_BASE}/api/projects/${pid}/head`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.version != null) {
          setVersion(data.version)
          setEmptyMessage(null)
        } else {
          setEmptyMessage("Run a build to generate artifacts.")
        }
      })
      .catch(() => {
        setEmptyMessage("Run a build to generate artifacts.")
      })
      .finally(() => setReady(true))
  }, [])

  if (!ready) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading artifacts...</p>
      </div>
    )
  }

  if (emptyMessage || projectId == null || version == null) {
    return <ArtifactsEmptyState message={emptyMessage || "Select a project to view artifacts."} />
  }

  return <ArtifactViewer projectId={projectId} version={version} initialTab={initialTab} />
}

export default function ArtifactsPage() {
  return (
    <Suspense>
      <ArtifactsInner />
    </Suspense>
  )
}
