"use client"

import { useState, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { ArtifactViewer } from "@/components/artifact-viewer"

const API_BASE = "http://localhost:5000"

function ArtifactsInner() {
  const searchParams = useSearchParams()
  const initialTab = searchParams.get("tab") || undefined

  const [projectId, setProjectId] = useState<number | null>(null)
  const [version, setVersion] = useState<number | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const pid = sessionStorage.getItem("archon_current_project_id")
    const selectedVer = sessionStorage.getItem("archon_selected_version")

    if (pid) {
      setProjectId(Number(pid))
      if (selectedVer) {
        setVersion(Number(selectedVer))
        setReady(true)
      } else {
        fetch(`${API_BASE}/api/projects/${pid}/head`)
          .then(r => r.json())
          .then(data => {
            if (data.version) setVersion(data.version)
            setReady(true)
          })
          .catch(() => setReady(true))
      }
    } else {
      fetch(`${API_BASE}/api/projects`)
        .then(r => r.json())
        .then(projects => {
          if (projects.length > 0) {
            const p = projects[0]
            setProjectId(p.id)
            return fetch(`${API_BASE}/api/projects/${p.id}/head`)
              .then(r => r.json())
              .then(data => { if (data.version) setVersion(data.version) })
          }
        })
        .catch(() => {})
        .finally(() => setReady(true))
    }
  }, [])

  if (!ready) return null

  return <ArtifactViewer projectId={projectId} version={version} initialTab={initialTab} />
}

export default function ArtifactsPage() {
  return (
    <Suspense>
      <ArtifactsInner />
    </Suspense>
  )
}
