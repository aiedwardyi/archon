"use client"

import { useState, useEffect } from "react"
import {
  Clock,
  RotateCcw,
  ChevronRight,
  PanelLeftClose,
  PanelLeft,
  CheckCircle2,
  XCircle,
  Loader2,
  FileText,
  Map,
  Code2,
  Download,
} from "lucide-react"
import { PreviewPanel } from "@/components/preview-panel"
import { useLanguage } from "@/contexts/LanguageContext"

const API_BASE = "http://localhost:5000"

type Version = {
  id: number
  version: number
  prompt: string
  timestamp: string
  date: string
  status: "completed" | "failed" | "running" | "pending"
  filesChanged: number
  qualityTier?: string | null
  readinessScore?: number | null
}

function parseVersions(raw: any[]): Version[] {
  return raw.map((e) => {
    const date = new Date(e.created_at || e.updated_at || Date.now())
    const now = new Date()
    const isToday = date.toDateString() === now.toDateString()
    const yesterday = new Date(now)
    yesterday.setDate(now.getDate() - 1)
    const isYesterday = date.toDateString() === yesterday.toDateString()
    const dateLabel = isToday ? "Today" : isYesterday ? "Yesterday" : date.toLocaleDateString()
    const promptRaw = (() => {
      try {
        const hist = Array.isArray(e.prompt_history) ? e.prompt_history : JSON.parse(e.prompt_history || "[]")
        const last = hist.filter((h: any) => h.role === "user").pop()
        return last?.content || "No prompt"
      } catch { return "Build project" }
    })()
    const statusMap: Record<string, Version["status"]> = {
      success: "completed", completed: "completed",
      error: "failed", failed: "failed",
      running: "running", in_progress: "running", pending: "pending",
    }
    return {
      id: e.id, version: e.version, prompt: promptRaw,
      timestamp: date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: true }),
      date: dateLabel, status: statusMap[e.status] ?? "pending", filesChanged: e.files_generated ?? 0,
      qualityTier: e.quality_tier ?? null,
      readinessScore: e.readiness_score ?? null,
    }
  })
}

function VersionStatusIcon({ status }: { status: Version["status"] }) {
  if (status === "completed") return <CheckCircle2 className="h-4 w-4 text-success" />
  if (status === "failed") return <XCircle className="h-4 w-4 text-destructive" />
  if (status === "running") return <Loader2 className="h-4 w-4 text-info animate-spin" />
  return <Loader2 className="h-4 w-4 text-muted-foreground" />
}

export function VersionTimeline() {
  const { t } = useLanguage()
  const [panelOpen, setPanelOpen] = useState(true)
  const [versions, setVersions] = useState<Version[]>([])
  const [selectedVersionId, setSelectedVersionId] = useState<number | null>(null)
  const [projectId, setProjectId] = useState<number | null>(null)
  const [projectName, setProjectName] = useState<string>("Project")
  const [loading, setLoading] = useState(true)
  const [restoring, setRestoring] = useState(false)
  const [isProjectBuilding, setIsProjectBuilding] = useState(false)

  useEffect(() => {
    const pid = sessionStorage.getItem("archon_current_project_id")
    const pname = sessionStorage.getItem("archon_project_name")
    if (pid) setProjectId(Number(pid))
    if (pname) setProjectName(pname)
  }, [])

  useEffect(() => {
    if (!projectId) { setLoading(false); return }
    fetchVersions()
  }, [projectId])

  const fetchVersions = async () => {
    if (!projectId) return
    setLoading(true)
    try {
      const statusRes = await fetch(`${API_BASE}/api/execution-status?project_id=${projectId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('archon_token')}` }
      })
      const statusData = await statusRes.json()
      setIsProjectBuilding(statusData.status === 'RUNNING')
    } catch {
      setIsProjectBuilding(false)
    }
    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}/versions`)
      const data = await res.json()
      const parsed = parseVersions(data.versions || [])
      setVersions(parsed)
      if (parsed.length > 0 && selectedVersionId === null) {
        setSelectedVersionId(parsed[0].id)
        // Also fire the event for the default selection so navbar + artifacts sync
        sessionStorage.setItem("archon_selected_version", String(parsed[0].version))
        window.dispatchEvent(new CustomEvent("archon:version-change", { detail: { version: parsed[0].version } }))
      }
    } catch (e) { console.error("Failed to load versions:", e) }
    finally { setLoading(false) }
  }

  const handleVersionClick = (v: Version) => {
    setSelectedVersionId(v.id)
    sessionStorage.setItem("archon_selected_version", String(v.version))
    window.dispatchEvent(new CustomEvent("archon:version-change", { detail: { version: v.version } }))
  }

  const handleRestore = async (executionId: number) => {
    setRestoring(true)
    try {
      await fetch(`${API_BASE}/api/executions/${executionId}/restore`, { method: "POST" })
      await fetchVersions()
    } catch (e) { console.error("Restore failed:", e) }
    finally { setRestoring(false) }
  }

  const selected = versions.find((v) => v.id === selectedVersionId)
  const headVersion = versions[0]
  const versionsByDate = versions.reduce((acc, v) => {
    if (!acc[v.date]) acc[v.date] = []
    acc[v.date].push(v)
    return acc
  }, {} as Record<string, Version[]>)

  return (
    <div className="flex-1 flex overflow-hidden">
      {panelOpen && (
        <aside className="w-80 border-r border-border bg-card flex flex-col shrink-0">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border h-[49px]">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <h3 className="text-sm font-semibold text-foreground">{t("versionHistory")}</h3>
            </div>
            <button onClick={() => setPanelOpen(false)} className="p-1 rounded hover:bg-muted transition-colors">
              <PanelLeftClose className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
          <div className="flex-1 overflow-auto">
            {loading && (
              <div className="px-4 py-6 text-center">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground mx-auto mb-2" />
                <p className="text-xs text-muted-foreground">Loading versions...</p>
              </div>
            )}
            {!loading && !projectId && (
              <div className="px-4 py-6 text-center">
                <p className="text-xs text-muted-foreground">No project selected. Go to Projects first.</p>
              </div>
            )}
            {!loading && projectId && versions.length === 0 && (
              <div className="px-4 py-6 text-center">
                <p className="text-xs text-muted-foreground">No versions yet. Run the pipeline to create one.</p>
              </div>
            )}
            {Object.entries(versionsByDate).map(([date, dateVersions]) => (
              <div key={date}>
                <div className="px-4 py-2 bg-muted/50">
                  <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{date}</span>
                </div>
                {dateVersions.map((v) => {
                  const isActive = v.id === selectedVersionId
                  return (
                    <button
                      key={v.id}
                      onClick={() => handleVersionClick(v)}
                      className={`w-full text-left px-4 py-3 border-b border-border transition-colors ${
                        isActive ? "bg-accent border-l-2 border-l-primary" : "hover:bg-muted/50 opacity-70 hover:opacity-100"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2 shrink-0">
                          <span className={`text-xs font-mono font-semibold px-1.5 py-0.5 rounded ${
                            isActive ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                          }`}>
                            v{v.version}
                          </span>
                          {isProjectBuilding ? <Loader2 className="h-4 w-4 text-blue-500 animate-spin" /> : <VersionStatusIcon status={v.status} />}
                        </div>
                        <span className="text-xs text-muted-foreground">{v.timestamp}</span>
                      </div>
                      <p className="text-sm text-foreground truncate mt-1">{v.prompt}</p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                        <span>{v.filesChanged} {t("filesChanged")}</span>
                      </div>
                      {v.qualityTier === "high" && (
                        <span className="inline-block mt-1.5 bg-blue-500/10 text-blue-500 border border-blue-400/40 shadow-[0_0_6px_rgba(59,130,246,0.4)] text-[10px] px-1.5 py-0.5 rounded">High Quality</span>
                      )}
                      {v.qualityTier === "good" && (
                        <span className="inline-block mt-1.5 bg-emerald-500/10 text-emerald-600 border border-emerald-400/40 text-[10px] px-1.5 py-0.5 rounded">Good Quality</span>
                      )}
                      {v.qualityTier === "low" && (
                        <span className="inline-block mt-1.5 bg-red-500/10 text-red-500 border border-red-400/40 text-[10px] px-1.5 py-0.5 rounded">Low Quality</span>
                      )}
                    </button>
                  )
                })}
              </div>
            ))}
          </div>
        </aside>
      )}

      <div className="flex-1 flex flex-col overflow-auto">
        {selected && (
          <div className="flex-1 flex flex-col gap-6">
            <div className="border-b border-border bg-card px-6 py-3 flex items-center justify-between">
              <div className="flex items-center gap-3 text-xs">
              {!panelOpen && (
                <button onClick={() => setPanelOpen(true)} className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded border border-border hover:bg-muted">
                  <PanelLeft className="h-3.5 w-3.5" />
                  {t("showVersions")}
                </button>
              )}
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-primary/30 bg-primary/10 text-primary font-mono font-semibold">
                  V{selected.version}
                </span>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-border text-muted-foreground">
                  {isProjectBuilding ? <Loader2 className="h-4 w-4 text-blue-500 animate-spin" /> : <VersionStatusIcon status={selected.status} />}
                  {isProjectBuilding ? <span className="text-xs font-medium text-blue-500 ml-1">Building</span> : <span className="capitalize ml-1">{selected.status}</span>}
                </span>
                <span className="text-muted-foreground">{selected.date} at {selected.timestamp}</span>
              </div>
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded border border-border text-muted-foreground hover:text-foreground hover:bg-muted transition-colors">
                  <Download className="h-3 w-3" />
                  {t("downloadReport")}
                </button>
                {selected.status !== "running" && headVersion && selected.id !== headVersion.id && (
                  <button
                    onClick={() => handleRestore(selected.id)}
                    disabled={restoring}
                    className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded border border-border text-muted-foreground hover:text-foreground hover:bg-muted transition-colors disabled:opacity-50"
                  >
                    {restoring ? <Loader2 className="h-3 w-3 animate-spin" /> : <RotateCcw className="h-3 w-3" />}
                    {t("restoreToThisVersion")}
                  </button>
                )}
              </div>
            </div>
            <div className="px-6 flex flex-col gap-4">

            {/* Prompt card */}
            <div className="rounded-lg border-l-4 border-l-primary border border-border bg-card p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-primary">{t("prompt")}</span>
                <span className="text-xs text-muted-foreground">{selected.timestamp}</span>
              </div>
              <p className="text-sm text-foreground leading-relaxed">{selected.prompt}</p>
            </div>

            {/* What was built card */}
            <div className="rounded-lg border-l-4 border-l-info border border-border bg-card p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-info">{t("whatWasBuilt")}</span>
                <span className="text-xs text-muted-foreground">{selected.timestamp}</span>
              </div>
              <p className="text-sm text-foreground/80 leading-relaxed">
                {isProjectBuilding ? "Build in progress..." : (selected.filesChanged > 0
                  ? `${selected.filesChanged} code file${selected.filesChanged !== 1 ? "s" : ""} generated`
                  : "Pipeline completed successfully.")}
              </p>
            </div>

            {/* Artifacts grid */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: t("brief"), sub: t("requirementsDoc"), icon: FileText, color: "text-primary", bg: "bg-primary/10", border: "border-l-primary", tab: "brief" },
                { label: t("buildPlan"), sub: t("architecturePlan"), icon: Map, color: "text-info", bg: "bg-info/10", border: "border-l-info", tab: "plan" },
                { label: t("code"), sub: `${selected.filesChanged} ${t("files")}`, icon: Code2, color: "text-success", bg: "bg-success/10", border: "border-l-success", tab: "code" },
              ].map((art) => (
                <button
                  key={art.label}
                  onClick={() => {
                    sessionStorage.setItem("archon_selected_version", String(selected.version))
                    window.location.href = `/artifacts?tab=${art.tab}`
                  }}
                  className={`flex items-center gap-3 p-4 rounded-lg border-l-4 border border-border bg-card hover:bg-accent transition-colors cursor-pointer text-left w-full ${art.border}`}
                >
                  <div className={`h-9 w-9 rounded-md ${art.bg} flex items-center justify-center shrink-0`}>
                    <art.icon className={`h-4 w-4 ${art.color}`} />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">{art.label}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{art.sub}</p>
                  </div>
                </button>
              ))}
            </div>

            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-border">
                <h3 className="text-sm font-semibold text-foreground">{t("livePreview")}</h3>
              </div>
              <div className="flex flex-col">
                <PreviewPanel projectId={projectId} version={selected.version} />
              </div>
            </div>
          </div>
          </div>
        )}

        {!selected && !loading && (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-sm text-muted-foreground">
              {projectId ? "Select a version from the left panel." : "No project selected. Go to Projects first."}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}


