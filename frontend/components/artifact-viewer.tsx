"use client"

import { useState, useEffect } from "react"
import {
  FileText,
  Code2,
  ListChecks,
  ScrollText,
  MapPin,
  Braces,
  ChevronRight,
  ChevronDown,
  File,
  Folder,
  Shield,
  Play,
  Eye,
  Loader2,
  CheckCircle2,
  Circle,
} from "lucide-react"
import { PreviewPanel } from "@/components/preview-panel"
import { useLanguage } from "@/contexts/LanguageContext"

const API_BASE = "http://localhost:5000"

const tabDefs = [
  { id: "brief", key: "brief" as const, icon: FileText },
  { id: "plan", key: "plan" as const, icon: MapPin },
  { id: "code", key: "code" as const, icon: Code2 },
  { id: "tasks", key: "tasks" as const, icon: ListChecks },
  { id: "logs", key: "logs" as const, icon: ScrollText },
  { id: "preview", key: "preview" as const, icon: Eye },
  { id: "governance", key: "governance" as const, icon: Shield },
]

type FileNode = {
  name: string
  type: "file" | "folder"
  path?: string
  children?: FileNode[]
}

type PrdData = {
  title: string
  version: string
  overview: string
  goals: string[]
  core_features: string[]
  target_users: string[]
} | null

type PlanTask = { id: string; description: string }
type PlanMilestone = { name: string; tasks: PlanTask[] }
type PlanData = { milestones: PlanMilestone[] } | null

function FileTreeNode({
  node,
  depth = 0,
  selectedPath,
  onSelect,
}: {
  node: FileNode
  depth?: number
  selectedPath: string
  onSelect: (path: string, name: string) => void
}) {
  const [expanded, setExpanded] = useState(depth < 2)
  const isFolder = node.type === "folder"
  const nodePath = node.path || node.name
  const isSelected = nodePath === selectedPath

  return (
    <div>
      <button
        onClick={() => { if (isFolder) setExpanded(!expanded); else onSelect(nodePath, node.name) }}
        className={`w-full flex items-center gap-1.5 py-1 px-2 text-xs hover:bg-muted/60 transition-colors rounded ${
          isSelected ? "bg-accent text-accent-foreground" : "text-foreground/80"
        }`}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
      >
        {isFolder ? (
          expanded
            ? <ChevronDown className="h-3 w-3 text-muted-foreground shrink-0" />
            : <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0" />
        ) : (
          <span className="w-3 shrink-0" />
        )}
        {isFolder
          ? <Folder className="h-3.5 w-3.5 text-primary/60 shrink-0" />
          : <File className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
        }
        <span className="font-mono truncate">{node.name}</span>
      </button>
      {isFolder && expanded && node.children && (
        <div>
          {node.children.map((child) => (
            <FileTreeNode
              key={child.path || child.name}
              node={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function highlightLine(line: string): string {
  let h = line.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  h = h.replace(/(\/\/.*$|#.*$)/g, '<span class="text-muted-foreground/60 italic">$1</span>')
  h = h.replace(/(["'`])(?:(?=(\\?))\2.)*?\1/g, '<span class="text-success">$&</span>')
  h = h.replace(
    /\b(import|from|export|class|interface|const|let|new|return|async|await|try|catch|throw|if|while|private|extends|typeof|void|number|string|boolean|true|false|null|undefined|def|self|print|for|in|with|as|pass)\b/g,
    '<span class="text-primary font-medium">$1</span>'
  )
  return h
}

function SyntaxHighlightedCode({ code }: { code: string }) {
  const lines = code.split("\n")
  const [mounted, setMounted] = useState(false)
  useEffect(() => { setMounted(true) }, [])

  return (
    <div className="text-xs font-mono leading-5 overflow-x-auto">
      {lines.map((line, i) => (
        <div key={i} className="flex hover:bg-muted/30 transition-colors min-w-0">
          <span className="w-12 text-right pr-4 text-muted-foreground/40 select-none shrink-0">{i + 1}</span>
          <pre className="flex-1 whitespace-pre">
            <code>
              {mounted
                ? <span dangerouslySetInnerHTML={{ __html: highlightLine(line) }} />
                : <span>{line}</span>
              }
            </code>
          </pre>
        </div>
      ))}
    </div>
  )
}

function PublishButton({ projectId, version }: { projectId: number; version: number }) {
  const { t } = useLanguage()
  const [state, setState] = useState<"idle" | "loading" | "done">("idle")
  const [publishedUrl, setPublishedUrl] = useState("")
  const [copied, setCopied] = useState(false)

  const handlePublish = async () => {
    setState("loading")
    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}/versions/${version}/publish`, { method: "POST" })
      const data = await res.json()
      if (data.url) {
        setPublishedUrl(`http://localhost:5000${data.url}`)
        setState("done")
      } else {
        setState("idle")
        alert("Publish failed: " + (data.error || "Unknown error"))
      }
    } catch {
      setState("idle")
      alert("Publish failed - check Flask server")
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(publishedUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (state === "done") {
    return (
      <div className="flex items-center gap-1.5">
        <input
          readOnly
          value={publishedUrl}
          className="text-xs px-2 py-1 rounded border border-success/40 bg-success/10 text-success font-mono w-64"
        />
        <button
          onClick={handleCopy}
          className="text-xs px-2.5 py-1 rounded border border-success/40 bg-success/10 text-success hover:bg-success/20 transition-colors"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
    )
  }

  return (
    <button
      onClick={handlePublish}
      disabled={state === "loading"}
      className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded border border-primary/40 bg-primary/10 text-primary hover:bg-primary/20 transition-colors disabled:opacity-50"
    >
      {state === "loading" ? (
        <Loader2 className="h-3 w-3 animate-spin" />
      ) : (
        <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" /></svg>
      )}
      {state === "loading" ? "Publishing..." : t("publish")}
    </button>
  )
}

interface ArtifactViewerProps {
  projectId?: number | null
  version?: number | null
}

export function ArtifactViewer({ projectId: propProjectId, version: propVersion, initialTab }: ArtifactViewerProps & { initialTab?: string } = {}) {
  const { t } = useLanguage()
  const [activeTab, setActiveTab] = useState(initialTab ?? "brief")
  const [selectedFilePath, setSelectedFilePath] = useState("")
  const [selectedFileName, setSelectedFileName] = useState("")
  const [showRawJson, setShowRawJson] = useState(false)

  const [projectId, setProjectId] = useState<number | null>(propProjectId ?? null)
  const [version, setVersion] = useState<number | null>(propVersion ?? null)

  const [prdData, setPrdData] = useState<PrdData>(null)
  const [prdLoading, setPrdLoading] = useState(false)

  const [planData, setPlanData] = useState<PlanData>(null)
  const [planLoading, setPlanLoading] = useState(false)

  const [fileTree, setFileTree] = useState<FileNode[]>([])
  const [fileContent, setFileContent] = useState("")
  const [fileLanguage, setFileLanguage] = useState("text")
  const [treeLoading, setTreeLoading] = useState(false)
  const [fileLoading, setFileLoading] = useState(false)
  const [treeError, setTreeError] = useState<string | null>(null)

  useEffect(() => {
    if (propProjectId != null) setProjectId(propProjectId)
    else {
      const c = sessionStorage.getItem("archon_current_project_id")
      if (c) setProjectId(Number(c))
    }
  }, [propProjectId])

  useEffect(() => {
    if (propVersion != null) {
      setVersion(propVersion)
    } else {
      const sel = sessionStorage.getItem("archon_selected_version")
      const cur = sessionStorage.getItem("archon_current_version")
      if (sel || cur) setVersion(Number(sel || cur))
    }
  }, [propVersion])

  // Listen for version-timeline clicks (same-tab custom event)
  useEffect(() => {
    const onVersionChange = (e: Event) => {
      const v = (e as CustomEvent).detail?.version
      if (v != null) {
        setVersion(Number(v))
        setPrdData(null)
        setPlanData(null)
        setFileTree([])
        setFileContent("")
      }
    }
    window.addEventListener("archon:version-change", onVersionChange)
    return () => window.removeEventListener("archon:version-change", onVersionChange)
  }, [])

  useEffect(() => {
    if (activeTab === "brief" && projectId) fetchPrd()
  }, [activeTab, projectId, version])

  useEffect(() => {
    if (activeTab === "plan" && projectId) fetchPlan()
  }, [activeTab, projectId, version])

  useEffect(() => {
    if (activeTab === "code" && projectId && version) fetchFileTree()
  }, [activeTab, projectId, version])

  useEffect(() => {
    if (activeTab === "tasks" && projectId && !planData) fetchPlan()
  }, [activeTab, projectId, version])

  const fetchPrd = async () => {
    if (!projectId) return
    setPrdLoading(true)
    try {
      // Pass project_id and version so the backend can read from disk after a restart
      const res = await fetch(`${API_BASE}/api/prd?project_id=${projectId}&version=${version}`)
      if (!res.ok) throw new Error("Not found")
      const data = await res.json()
      // Real schema: { kind, agent_role, prd: { document_title, overview, goals[], core_features_mvp[], target_users[] } }
      const prd = data.prd ?? data
      setPrdData({
        title: prd.document_title ?? prd.title ?? "Brief",
        version: `v${version}`,
        overview: prd.overview ?? "",
        goals: prd.goals ?? [],
        core_features: prd.core_features_mvp ?? prd.core_features ?? [],
        target_users: prd.target_users ?? [],
      })
    } catch {
      setPrdData(null)
    } finally {
      setPrdLoading(false)
    }
  }

  const fetchPlan = async () => {
    if (!projectId) return
    setPlanLoading(true)
    try {
      // Pass project_id and version so the backend can read from disk after a restart
      const res = await fetch(`${API_BASE}/api/plan?project_id=${projectId}&version=${version}`)
      if (!res.ok) throw new Error("Not found")
      const data = await res.json()
      // Real schema: { milestones: [{ name, tasks: [{ id, description }] }] }
      setPlanData({ milestones: data.milestones ?? [] })
    } catch {
      setPlanData(null)
    } finally {
      setPlanLoading(false)
    }
  }

  const fetchFileTree = async () => {
    if (!projectId || !version) return
    setTreeLoading(true)
    setTreeError(null)
    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}/versions/${version}/files`)
      const data = await res.json()
      if (data.tree) {
        setFileTree(data.tree)
        const first = findFirstFile(data.tree)
        if (first) {
          setSelectedFilePath(first.path || first.name)
          setSelectedFileName(first.name)
          fetchFileContent(first.path || first.name)
        }
      } else {
        setTreeError(data.message || "No files found")
      }
    } catch {
      setTreeError("Failed to load file tree")
    } finally {
      setTreeLoading(false)
    }
  }

  const findFirstFile = (nodes: FileNode[]): FileNode | null => {
    for (const n of nodes) {
      if (n.type === "file") return n
      if (n.children) { const f = findFirstFile(n.children); if (f) return f }
    }
    return null
  }

  const fetchFileContent = async (filePath: string) => {
    if (!projectId || !version || !filePath) return
    setFileLoading(true)
    try {
      const res = await fetch(
        `${API_BASE}/api/projects/${projectId}/versions/${version}/files?path=${encodeURIComponent(filePath)}`
      )
      const data = await res.json()
      setFileContent(data.content || "")
      setFileLanguage(data.language || "text")
    } catch {
      setFileContent("// Error loading file content")
    } finally {
      setFileLoading(false)
    }
  }

  const handleFileSelect = (path: string, name: string) => {
    setSelectedFilePath(path)
    setSelectedFileName(name)
    fetchFileContent(path)
  }

  const getCachedLogs = () => {
    // Try to find logs for the specific version being viewed
    if (projectId && version) {
      // Scan sessionStorage for an execution matching this project+version
      const currentEid = sessionStorage.getItem("archon_current_execution_id")
      const currentVer = sessionStorage.getItem("archon_current_version")
      if (currentEid && currentVer && Number(currentVer) === version) {
        try {
          const logs = JSON.parse(sessionStorage.getItem(`archon_logs_${currentEid}`) || "[]")
          if (logs.length) return logs
        } catch {}
      }
      // Fallback: scan all archon_logs_* keys for any that match
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i)
        if (key && key.startsWith("archon_logs_")) {
          try {
            const logs = JSON.parse(sessionStorage.getItem(key) || "[]")
            if (logs.length) return logs
          } catch {}
        }
      }
    }
    const eid = sessionStorage.getItem("archon_current_execution_id")
    if (!eid) return []
    try { return JSON.parse(sessionStorage.getItem(`archon_logs_${eid}`) || "[]") } catch { return [] }
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Breadcrumb + badge bar */}
      <div className="border-b border-border bg-card px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs">
            <span className="flex items-center gap-1 font-mono">
              <span className="text-muted-foreground font-medium">{t("requirements")}</span>
              <ChevronRight className="h-3 w-3 text-muted-foreground/50" />
              <span className="text-info font-medium">{t("architecture")}</span>
              <ChevronRight className="h-3 w-3 text-muted-foreground/50" />
              <span className="text-primary font-medium">{t("code")}</span>
            </span>
            <span className="mx-2 text-border">|</span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-success/30 bg-success/10 text-success">
              <Play className="h-3 w-3" />{t("reproducible")}
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-info/30 bg-info/10 text-info">
              <Shield className="h-3 w-3" />{t("verified")}
            </span>
            {version && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-primary/30 bg-primary/10 text-primary font-mono">
                V{version}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {projectId && version && (
              <>
                <PublishButton projectId={projectId} version={version} />
                <a
                  href={`${API_BASE}/api/projects/${projectId}/versions/${version}/download`}
                  download
                  className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded border border-border text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                >
                  <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                  {t("downloadCode")}
                </a>
              </>
            )}
            <button
              onClick={() => setShowRawJson(!showRawJson)}
              className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded border transition-colors ${
                showRawJson
                  ? "bg-primary text-primary-foreground border-primary"
                  : "border-border text-muted-foreground hover:text-foreground hover:bg-muted"
              }`}
            >
              <Braces className="h-3 w-3" />{t("rawData")}
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border bg-card px-6">
        <div className="flex items-center gap-0">
          {tabDefs.map((tab) => {
            const isActive = tab.id === activeTab
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-4 py-2.5 text-sm border-b-2 transition-colors ${
                  isActive ? "border-primary text-foreground font-medium" : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <tab.icon className="h-3.5 w-3.5" />
                {t(tab.key)}
              </button>
            )
          })}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden flex">

        {/* â”€â”€ BRIEF â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
        {activeTab === "brief" && (
          <div className="flex-1 overflow-auto p-6">
            {prdLoading && (
              <div className="flex items-center gap-2 py-4">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Loading brief...</span>
              </div>
            )}
            {!prdLoading && !prdData && (
              <p className="text-sm text-muted-foreground italic">
                {projectId && version ? "No brief available yet. Run the pipeline to generate one." : "Select a project to view the brief."}
              </p>
            )}
            {!prdLoading && prdData && (
              showRawJson ? (
                <pre className="text-xs font-mono text-foreground/80 whitespace-pre-wrap bg-card border border-border rounded-lg p-4 leading-5">
                  {JSON.stringify(prdData, null, 2)}
                </pre>
              ) : (
                <div className="max-w-3xl">
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="text-lg font-semibold text-foreground">{prdData.title}</h2>
                    <span className="text-xs font-mono bg-primary text-primary-foreground px-2 py-0.5 rounded">
                      {prdData.version}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mb-6">v1.0 &middot; {t("generatedBy")} Archon</p>

                  {prdData.overview && (
                    <div className="bg-card border border-border rounded-lg p-5 mb-4">
                      <h3 className="text-sm font-semibold text-foreground mb-2">{t("overview")}</h3>
                      <p className="text-sm text-foreground/70 leading-relaxed">{prdData.overview}</p>
                    </div>
                  )}

                  {prdData.goals.length > 0 && (
                    <div className="bg-card border border-border rounded-lg p-5 mb-4">
                      <h3 className="text-sm font-semibold text-foreground mb-1">{t("goals")}</h3>
                      <p className="text-xs text-muted-foreground mb-3">{t("successCriteria")}</p>
                      <ul className="space-y-2">
                        {prdData.goals.map((g, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-foreground/80">
                            <span className="h-1.5 w-1.5 rounded-full bg-primary mt-2 shrink-0" />
                            {g}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {prdData.core_features.length > 0 && (
                    <div className="bg-card border border-border rounded-lg p-5 mb-4">
                      <h3 className="text-sm font-semibold text-foreground mb-1">{t("coreFeatures")}</h3>
                      <p className="text-xs text-muted-foreground mb-3">{t("whatWereBuilding")}</p>
                      <ul className="space-y-2">
                        {prdData.core_features.map((f, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-foreground/80">
                            <span className="h-1.5 w-1.5 rounded-full bg-info mt-2 shrink-0" />
                            {f}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {prdData.target_users.length > 0 && (
                    <div className="bg-card border border-border rounded-lg p-5">
                      <h3 className="text-sm font-semibold text-foreground mb-1">{t("targetUsers")}</h3>
                      <p className="text-xs text-muted-foreground mb-3">{t("whoWereBuildingFor")}</p>
                      <ul className="space-y-2">
                        {prdData.target_users.map((u, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-foreground/80">
                            <span className="h-1.5 w-1.5 rounded-full bg-success mt-2 shrink-0" />
                            {u}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )
            )}
          </div>
        )}

        {/* â”€â”€ PLAN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
        {activeTab === "plan" && (
          <div className="flex-1 overflow-auto p-6">
            {planLoading && (
              <div className="flex items-center gap-2 py-4">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Loading plan...</span>
              </div>
            )}
            {!planLoading && !planData && (
              <p className="text-sm text-muted-foreground italic">
                {projectId && version ? "No plan available yet. Run the pipeline to generate one." : "Select a project to view the plan."}
              </p>
            )}
            {!planLoading && planData && (
              showRawJson ? (
                <pre className="text-xs font-mono text-foreground/80 whitespace-pre-wrap bg-card border border-border rounded-lg p-4 leading-5">
                  {JSON.stringify(planData, null, 2)}
                </pre>
              ) : (
                <div className="max-w-3xl">
                  <h2 className="text-lg font-semibold text-foreground mb-1">{t("buildPlan")}</h2>
                  <p className="text-xs text-muted-foreground mb-6">
                    {planData.milestones.length} {t("milestones")} &middot; {t("generatedBy")} Archon
                  </p>
                  <div className="space-y-3">
                    {planData.milestones.map((m, i) => (
                      <div key={i} className="bg-card border border-border rounded-lg p-5">
                        <h3 className="text-sm font-semibold text-foreground mb-3">{m.name}</h3>
                        <div className="space-y-1.5">
                          {m.tasks.map((t, j) => (
                            <div key={t.id ?? j} className="flex items-start gap-3 text-xs py-1.5 px-3 rounded bg-muted/30">
                              <span className="font-mono text-muted-foreground shrink-0 pt-0.5">{t.id}</span>
                              <span className="text-foreground/80">{t.description}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            )}
          </div>
        )}

        {/* â”€â”€ CODE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
        {activeTab === "code" && (
          <>
            <aside className="w-56 border-r border-border bg-card overflow-auto py-2 shrink-0">
              {treeLoading && (
                <div className="flex items-center gap-2 px-4 py-3">
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">Loading...</span>
                </div>
              )}
              {treeError && <div className="px-4 py-3"><p className="text-xs text-muted-foreground italic">{treeError}</p></div>}
              {!treeLoading && !treeError && fileTree.length === 0 && (
                <div className="px-4 py-3">
                  <p className="text-xs text-muted-foreground italic">
                    {projectId && version ? "No files generated yet." : "Run a pipeline to see files."}
                  </p>
                </div>
              )}
              {fileTree.map((node) => (
                <FileTreeNode
                  key={node.path || node.name}
                  node={node}
                  selectedPath={selectedFilePath}
                  onSelect={handleFileSelect}
                />
              ))}
            </aside>

            <div className="flex-1 overflow-auto bg-card p-4">
              {selectedFileName && (
                <div className="flex items-center gap-2 mb-3 pb-3 border-b border-border">
                  <File className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-xs font-mono text-foreground">{selectedFilePath}</span>
                  <span className="text-xs text-muted-foreground ml-auto capitalize">{fileLanguage}</span>
                </div>
              )}
              {fileLoading && (
                <div className="flex items-center gap-2 py-4">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">Loading file...</span>
                </div>
              )}
              {!fileLoading && fileContent && (
                showRawJson
                  ? <pre className="text-xs font-mono text-foreground/80 whitespace-pre-wrap leading-5">{fileContent}</pre>
                  : <SyntaxHighlightedCode code={fileContent} />
              )}
              {!fileLoading && !fileContent && !treeLoading && (
                <p className="text-xs text-muted-foreground italic">Select a file to view its content.</p>
              )}
            </div>
          </>
        )}

        {/* â”€â”€ TASKS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
        {activeTab === "tasks" && (
          <div className="flex-1 overflow-auto p-6">
            <div className="max-w-3xl">
              <h2 className="text-lg font-semibold text-foreground mb-1">Build Tasks</h2>
              <p className="text-xs text-muted-foreground mb-6">
                {planData
                  ? `${planData.milestones.flatMap((m) => m.tasks).length} tasks · All completed by Agent`
                  : "Derived from build plan"}
              </p>
              {planLoading && (
                <div className="flex items-center gap-2 py-4">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Loading tasks...</span>
                </div>
              )}
              {!planLoading && !planData && (
                <p className="text-sm text-muted-foreground italic">
                  No tasks available yet. Run the pipeline to generate one.
                </p>
              )}
              {!planLoading && planData && (
                <div className="bg-card border border-border rounded-lg overflow-hidden">
                  <div className="divide-y divide-border">
                    {planData.milestones.flatMap((m) => m.tasks).map((task) => (
                      <div key={task.id} className="flex items-center gap-3 px-4 py-2.5 text-sm">
                        <CheckCircle2 className="h-4 w-4 text-success shrink-0" />
                        <span className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded text-muted-foreground shrink-0">
                          {task.id}
                        </span>
                        <span className="text-foreground/80 flex-1">{task.description}</span>
                        <span className="text-xs text-muted-foreground shrink-0">Agent</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* â”€â”€ LOGS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
        {activeTab === "logs" && (
          <div className="flex-1 overflow-auto p-6">
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                <h3 className="text-sm font-semibold text-foreground">Pipeline Execution Logs</h3>
                <span className="text-xs text-muted-foreground">{version ? `v${version}` : "â€”"}</span>
              </div>
              <div className="p-4 font-mono text-xs space-y-0.5">
                {(() => {
                  const logs = getCachedLogs()
                  if (!logs.length) return <p className="text-muted-foreground italic">No logs cached. Run a pipeline to see logs here.</p>
                  return logs.map((log: any) => (
                    <div key={log.id} className="flex items-start gap-3 py-0.5">
                      <span className="text-muted-foreground/60 shrink-0 w-28">
                        {new Date(log.timestamp).toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                      </span>
                      <span className="text-foreground/70">{log.message}</span>
                    </div>
                  ))
                })()}
              </div>
            </div>
          </div>
        )}

        {/* â”€â”€ PREVIEW â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
        {activeTab === "preview" && (
          <PreviewPanel projectId={projectId} version={version} />
        )}

        {activeTab === "governance" && (
          <div className="flex-1 overflow-auto p-6">
            <GovernanceTab projectId={projectId} version={version} />
          </div>
        )}

      </div>
    </div>
  )
}

interface StudioPromptQuality {
  score: number | null;
  label: string;
  sentiment: string;
  sentiment_score: number;
  keywords: string[];
  domain: string;
  powered_by: string;
}

interface StudioBuildBreakdown {
  factor: string;
  points: number;
  note: string;
}

interface StudioBuildConfidence {
  score: number;
  label: string;
  breakdown: StudioBuildBreakdown[];
}

interface StudioFactsheet {
  factsheet_version: string;
  generated_at: string;
  project: { id: number; name: string; version: number; execution_id: number };
  prompt_summary: string;
  pipeline: { status: string; agent_sequence: string[]; duration_seconds: number | null; ui_archetype: string | null };
  model_registry: Array<{ agent_role: string; model: string; provider: string }>;
  usage: { tokens_used: number | null; estimated_cost_usd: number | null; credits_used: number | null };
  outputs: { files_generated: number; images_generated: number };
  scoring?: { prompt_quality: StudioPromptQuality; build_confidence: StudioBuildConfidence };
  quality_indicators: Array<{ indicator: string; status: string; value: string }>;
  compliance: { audit_trail: boolean; version_history: boolean; artifact_retention: boolean; human_review_required: boolean };
}

function GovernanceTab({ projectId, version }: { projectId: number | null; version: number | null }) {
  const [factsheet, setFactsheet] = useState<StudioFactsheet | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!projectId || !version) return
    let cancelled = false
    setLoading(true)
    setError(null)
    ;(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/projects/${projectId}/versions/${version}/factsheet`)
        if (!res.ok) throw new Error("not found")
        const data = await res.json()
        if (!cancelled) setFactsheet(data)
      } catch {
        if (!cancelled) setError("Factsheet not available for this version. Run a new build to generate one.")
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, [projectId, version])

  if (loading) return <div className="flex items-center gap-2 py-8 justify-center"><Loader2 className="h-4 w-4 animate-spin text-muted-foreground" /><span className="text-sm text-muted-foreground">Loading factsheet...</span></div>
  if (error) return <div className="text-sm text-muted-foreground italic py-8 text-center">{error}</div>
  if (!factsheet) return <div className="text-sm text-muted-foreground italic py-8 text-center">No factsheet data.</div>

  const capitalize = (s: string) => s ? s.charAt(0).toUpperCase() + s.slice(1) : s
  const titleCase = (s: string) => s.replace(/\b\w/g, c => c.toUpperCase())
  const formatAgentPill = (val: string) => val === 'pm' ? 'PM' : capitalize(val)

  const formatQualityIndicator = (indicator: string, value: string) => {
    const label = indicator.replace(/\b\w/g, c => c.toUpperCase())
    const match = value.match(/^([\d,]+)\s+(.+)$/)
    if (!match) return `${label}: ${value}`
    const num = match[1]
    const rawUnit = match[2].replace(/\(s\)/, '')
    const count = parseInt(num.replace(/,/g, ''), 10)
    const unit = count === 1 ? rawUnit.replace(/s$/, '') : rawUnit.endsWith('s') ? rawUnit : rawUnit + 's'
    return `${label}: ${num} ${unit.charAt(0).toUpperCase() + unit.slice(1)}`
  }

  const ts = factsheet.generated_at ? new Date(factsheet.generated_at).toLocaleString() : "Unknown"

  return (
    <div className="max-w-3xl space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          AI Factsheet — v{factsheet.project.version}
        </h2>
        <p className="text-xs text-muted-foreground mt-1">Generated {ts} · Factsheet v{factsheet.factsheet_version}</p>
      </div>

      {/* PDF Download Buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => alert("PDF export coming soon — Phase 17.4")}
          className="h-8 px-3 text-xs font-medium border border-border rounded-md text-foreground hover:bg-muted transition-colors flex items-center gap-1.5"
        >
          <FileText className="h-3.5 w-3.5" /> Download Client PDF
        </button>
        <button
          onClick={() => alert("PDF export coming soon — Phase 17.4")}
          className="h-8 px-3 text-xs font-medium border border-border rounded-md text-foreground hover:bg-muted transition-colors flex items-center gap-1.5"
        >
          <FileText className="h-3.5 w-3.5" /> Download Internal PDF
        </button>
      </div>

      <div className="bg-card border border-border rounded-lg p-5">
        <h3 className="text-sm font-semibold text-foreground mb-3">Pipeline</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-muted-foreground text-xs">Status</span>
            <div className="mt-0.5"><span className="text-xs px-2 py-0.5 rounded border border-success/40 bg-success/10 text-success">{capitalize(factsheet.pipeline.status)}</span></div>
          </div>
          <div>
            <span className="text-muted-foreground text-xs">UI Archetype</span>
            <p className="mt-0.5 text-foreground">{factsheet.pipeline.ui_archetype ? capitalize(factsheet.pipeline.ui_archetype) : "Auto-detected"}</p>
          </div>
          <div className="col-span-2">
            <span className="text-muted-foreground text-xs">Agent Sequence</span>
            <div className="mt-0.5 flex flex-wrap gap-1">
              {factsheet.pipeline.agent_sequence.map((a) => (
                <span key={a} className="text-xs font-mono bg-muted px-1.5 py-0.5 rounded text-muted-foreground">{formatAgentPill(a)}</span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Scoring */}
      {factsheet.scoring && (
        <div className="grid grid-cols-2 gap-4">
          {/* Prompt Quality */}
          <div className="bg-card border border-border rounded-lg p-5 relative">
            <h3 className="text-sm font-semibold text-foreground">Prompt Quality</h3>
            <p className="text-[11px] text-muted-foreground mt-0.5 mb-3">How clearly your idea was communicated to the AI pipeline</p>
            {factsheet.scoring.prompt_quality.powered_by === "unavailable" ? (
              <p className="text-xs text-muted-foreground italic">
                Watson NLU credentials not configured — add WATSON_NLU_API_KEY and WATSON_NLU_URL to backend/.env to enable prompt scoring.
              </p>
            ) : (
              <>
                <div className="flex items-end gap-2 mb-3">
                  <span className="text-3xl font-bold text-foreground">{factsheet.scoring.prompt_quality.score}</span>
                  <span className="text-sm text-muted-foreground mb-1">/100</span>
                  <span className={`ml-2 text-[10px] font-semibold px-2 py-0.5 rounded border mb-1 ${
                    factsheet.scoring.prompt_quality.label === "high"
                      ? "border-success/40 bg-success/10 text-success"
                      : factsheet.scoring.prompt_quality.label === "medium"
                      ? "border-warning/40 bg-warning/10 text-warning"
                      : "border-destructive/40 bg-destructive/10 text-destructive"
                  }`}>
                    {capitalize(factsheet.scoring.prompt_quality.label)}
                  </span>
                </div>
                <div className="flex flex-col gap-1 mb-3">
                  <span className="text-xs text-muted-foreground">Domain</span>
                  <span className="text-sm font-normal text-foreground">{capitalize(factsheet.scoring.prompt_quality.domain)}</span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-xs text-muted-foreground">Keywords</span>
                  <span className="text-sm font-normal text-foreground leading-relaxed">{factsheet.scoring.prompt_quality.keywords.length > 0 ? factsheet.scoring.prompt_quality.keywords.map(k => capitalize(k)).join(", ") : "—"}</span>
                </div>
                <div className="absolute top-3 right-3">
                  <span className="text-[9px] font-medium px-1.5 py-0.5 rounded bg-info/10 text-info border border-info/30">
                    Powered by IBM Watson NLU
                  </span>
                </div>
              </>
            )}
          </div>

          {/* Build Quality Score */}
          <div className="bg-card border border-border rounded-lg p-5">
            <h3 className="text-sm font-semibold text-foreground">Build Quality Score</h3>
            <p className="text-[11px] text-muted-foreground mt-0.5 mb-3">Based on code output, archetype detection, and pipeline success</p>
            {(() => {
              const displayScore = factsheet.scoring!.build_confidence.score
              const displayLabel = displayScore >= 90 ? "excellent" : displayScore >= 75 ? "good" : displayScore >= 50 ? "fair" : "low"
              const labelColor = displayScore >= 75
                ? "border-success/40 bg-success/10 text-success"
                : displayScore >= 50
                ? "border-warning/40 bg-warning/10 text-warning"
                : "border-destructive/40 bg-destructive/10 text-destructive"
              const filteredBreakdown = factsheet.scoring!.build_confidence.breakdown.filter(b => b.factor.toLowerCase() !== "build speed" && b.factor.toLowerCase() !== "design assets")
              return (
                <>
                  <div className="flex items-end gap-2 mb-3">
                    <span className="text-3xl font-bold text-foreground">{displayScore}</span>
                    <span className="text-sm text-muted-foreground mb-1">/100</span>
                    <span className={`ml-2 text-[10px] font-semibold px-2 py-0.5 rounded border mb-1 ${labelColor}`}>
                      {capitalize(displayLabel)}
                    </span>
                  </div>
                  {filteredBreakdown.length > 0 && (
                    <div className="border border-border rounded-lg overflow-hidden">
                      <div className="grid gap-0 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground bg-muted/40 px-3 py-1.5" style={{ gridTemplateColumns: '1fr 60px 1fr' }}>
                        <span>Factor</span><span>Points</span><span>Note</span>
                      </div>
                      {filteredBreakdown.map((b) => (
                        <div key={b.factor} className="grid gap-0 text-xs px-3 py-1.5 border-t border-border" style={{ gridTemplateColumns: '1fr 60px 1fr' }}>
                          <span className="text-foreground">{titleCase(b.factor)}</span>
                          <span className="text-muted-foreground font-mono">{b.points}</span>
                          <span className="text-muted-foreground">{capitalize(b.note)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )
            })()}
          </div>
        </div>
      )}

      <div className="bg-card border border-border rounded-lg p-5">
        <h3 className="text-sm font-semibold text-foreground mb-3">Model Registry</h3>
        <div className="border border-border rounded-lg overflow-hidden">
          <div className="grid grid-cols-3 gap-0 text-xs font-semibold uppercase tracking-wider text-muted-foreground bg-muted/40 px-3 py-2">
            <span>Agent Role</span><span>Model</span><span>Provider</span>
          </div>
          {factsheet.model_registry.map((m) => (
            <div key={m.agent_role} className="grid grid-cols-3 gap-0 text-sm px-3 py-2 border-t border-border">
              <span className="text-foreground">{m.agent_role}</span>
              <span className="text-muted-foreground font-mono text-xs">{m.model}</span>
              <span className="text-muted-foreground">{m.provider}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-card border border-border rounded-lg p-5">
        <h3 className="text-sm font-semibold text-foreground mb-3">AI Processing</h3>
        <p className="text-sm text-muted-foreground">
          {(() => {
            const providers = [...new Set(factsheet.model_registry.map(m => m.provider))]
            const count = factsheet.model_registry.length
            if (providers.length === 0) return `${count} AI model${count !== 1 ? "s" : ""} processed this build.`
            const last = providers[providers.length - 1]
            const rest = providers.slice(0, -1)
            const providerStr = providers.length === 1 ? providers[0] : `${rest.join(", ")}, and ${last}`
            return `${count} AI model${count !== 1 ? "s" : ""} processed this build across ${providerStr}.`
          })()}
        </p>
      </div>

      <div className="bg-card border border-border rounded-lg p-5">
        <h3 className="text-sm font-semibold text-foreground mb-3">Outputs</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground text-xs">Files Generated</span>
            <p className="mt-0.5 text-foreground font-mono">{factsheet.outputs.files_generated}</p>
          </div>
          <div>
            <span className="text-muted-foreground text-xs">Images Generated</span>
            <p className="mt-0.5 text-foreground font-mono">{factsheet.outputs.images_generated}</p>
          </div>
        </div>
      </div>

      {factsheet.quality_indicators.length > 0 && (
        <div className="bg-card border border-border rounded-lg p-5">
          <h3 className="text-sm font-semibold text-foreground mb-3">Quality Indicators</h3>
          <div className="flex flex-wrap gap-2">
            {factsheet.quality_indicators.filter((qi) => qi.indicator.toLowerCase() !== "build speed").map((qi) => (
              <span
                key={qi.indicator}
                className={`text-xs px-2.5 py-1 rounded border ${
                  qi.status === "pass"
                    ? "border-success/40 bg-success/10 text-success"
                    : "border-warning/40 bg-warning/10 text-warning"
                }`}
              >
                {formatQualityIndicator(qi.indicator, qi.value)}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="bg-card border border-border rounded-lg p-5">
        <h3 className="text-sm font-semibold text-foreground mb-3">Compliance</h3>
        <p className="text-xs text-muted-foreground italic mb-3">This build was generated by a governed, auditable AI pipeline.</p>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(factsheet.compliance).map(([key, val]) => (
            <div key={key} className="flex items-center gap-2 text-sm">
              {val ? (
                <CheckCircle2 className="h-4 w-4 text-success" />
              ) : (
                <Circle className="h-4 w-4 text-muted-foreground" />
              )}
              <span className="text-foreground">{key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}









