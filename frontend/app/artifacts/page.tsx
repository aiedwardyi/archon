"use client"

import { useState, useEffect } from "react"
import { ArtifactViewer } from "@/components/artifact-viewer"

const API_BASE = "http://localhost:5000"

export default function ArtifactsPage() {
  const [projectId, setProjectId] = useState<number | null>(null)
  const [version, setVersion] = useState<number | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const pid = sessionStorage.getItem("archon_current_project_id")
    const selectedVer = sessionStorage.getItem("archon_selected_version")

    if (pid) {
      setProjectId(Number(pid))
      if (selectedVer) {
        // User clicked a specific version on the Versions page — use it
        setVersion(Number(selectedVer))
        setReady(true)
      } else {
        // No selection — default to head
        fetch(`${API_BASE}/api/projects/${pid}/head`)
          .then(r => r.json())
          .then(data => {
            if (data.version) setVersion(data.version)
            setReady(true)
          })
          .catch(() => setReady(true))
      }
    } else {
      // No session at all — load most recent project + its head
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

  return <ArtifactViewer projectId={projectId} version={version} />
}


