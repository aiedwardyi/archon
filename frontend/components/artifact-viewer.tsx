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
} from "lucide-react"
import { PreviewPanel } from "@/components/preview-panel"

const API_BASE = "http://localhost:5000"

const tabs = [
  { id: "brief", label: "Brief", icon: FileText },
  { id: "plan", label: "Plan", icon: MapPin },
  { id: "code", label: "Code", icon: Code2 },
  { id: "tasks", label: "Tasks", icon: ListChecks },
  { id: "logs", label: "Logs", icon: ScrollText },
  { id: "preview", label: "Preview", icon: Eye },
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

interface ArtifactViewerProps {
  projectId?: number | null
  version?: number | null
}

export function ArtifactViewer({ projectId: propProjectId, version: propVersion }: ArtifactViewerProps = {}) {
  const [activeTab, setActiveTab] = useState("brief")
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
    if (propVersion != null) setVersion(propVersion)
    else {
      const c = sessionStorage.getItem("archon_current_version")
      if (c) setVersion(Number(c))
    }
  }, [propVersion])

  useEffect(() => {
    if (activeTab === "brief" && projectId && version) fetchPrd()
  }, [activeTab, projectId, version])

  useEffect(() => {
    if (activeTab === "plan" && projectId && version) fetchPlan()
  }, [activeTab, projectId, version])

  useEffect(() => {
    if (activeTab === "code" && projectId && version) fetchFileTree()
  }, [activeTab, projectId, version])

  const fetchPrd = async () => {
    setPrdLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/prd`)
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
    setPlanLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/plan`)
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
              <span className="text-muted-foreground font-medium">Requirements</span>
              <ChevronRight className="h-3 w-3 text-muted-foreground/50" />
              <span className="text-info font-medium">Architecture</span>
              <ChevronRight className="h-3 w-3 text-muted-foreground/50" />
              <span className="text-primary font-medium">Code</span>
            </span>
            <span className="mx-2 text-border">|</span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-success/30 bg-success/10 text-success">
              <Play className="h-3 w-3" />Reproducible
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-info/30 bg-info/10 text-info">
              <Shield className="h-3 w-3" />Verified
            </span>
            {version && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-primary/30 bg-primary/10 text-primary font-mono">
                V{version}
              </span>
            )}
          </div>
          <button
            onClick={() => setShowRawJson(!showRawJson)}
            className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded border transition-colors ${
              showRawJson
                ? "bg-primary text-primary-foreground border-primary"
                : "border-border text-muted-foreground hover:text-foreground hover:bg-muted"
            }`}
          >
            <Braces className="h-3 w-3" />Raw Data
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border bg-card px-6">
        <div className="flex items-center gap-0">
          {tabs.map((tab) => {
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
                {tab.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden flex">

        {/* ── BRIEF ─────────────────────────────────────────────────────── */}
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
                  <p className="text-xs text-muted-foreground mb-6">v1.0 &middot; Generated by Archon</p>

                  {/* Overview */}
                  {prdData.overview && (
                    <div className="bg-card border border-border rounded-lg p-5 mb-4">
                      <h3 className="text-sm font-semibold text-foreground mb-2">Overview</h3>
                      <p className="text-sm text-foreground/70 leading-relaxed">{prdData.overview}</p>
                    </div>
                  )}

                  {/* Goals */}
                  {prdData.goals.length > 0 && (
                    <div className="bg-card border border-border rounded-lg p-5 mb-4">
                      <h3 className="text-sm font-semibold text-foreground mb-1">Goals</h3>
                      <p className="text-xs text-muted-foreground mb-3">Success Criteria</p>
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

                  {/* Core Features */}
                  {prdData.core_features.length > 0 && (
                    <div className="bg-card border border-border rounded-lg p-5 mb-4">
                      <h3 className="text-sm font-semibold text-foreground mb-1">Core Features (MVP)</h3>
                      <p className="text-xs text-muted-foreground mb-3">What We're Building</p>
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

                  {/* Target Users */}
                  {prdData.target_users.length > 0 && (
                    <div className="bg-card border border-border rounded-lg p-5">
                      <h3 className="text-sm font-semibold text-foreground mb-1">Target Users</h3>
                      <p className="text-xs text-muted-foreground mb-3">Who We're Building For</p>
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

        {/* ── PLAN ──────────────────────────────────────────────────────── */}
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
                  <h2 className="text-lg font-semibold text-foreground mb-1">Build Plan</h2>
                  <p className="text-xs text-muted-foreground mb-6">
                    {planData.milestones.length} milestones &middot; Generated by Archon
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

        {/* ── CODE ──────────────────────────────────────────────────────── */}
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

        {/* ── TASKS ─────────────────────────────────────────────────────── */}
        {activeTab === "tasks" && (
          <div className="flex-1 overflow-auto p-6">
            <div className="max-w-3xl">
              <h2 className="text-lg font-semibold text-foreground mb-4">Build Tasks</h2>
              <p className="text-sm text-muted-foreground italic">
                Task tracking coming in a future update. Check the Logs tab for real-time pipeline progress.
              </p>
            </div>
          </div>
        )}

        {/* ── LOGS ──────────────────────────────────────────────────────── */}
        {activeTab === "logs" && (
          <div className="flex-1 overflow-auto p-6">
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                <h3 className="text-sm font-semibold text-foreground">Pipeline Execution Logs</h3>
                <span className="text-xs text-muted-foreground">{version ? `v${version}` : "—"}</span>
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

        {/* ── PREVIEW ───────────────────────────────────────────────────── */}
        {activeTab === "preview" && (
          <PreviewPanel projectId={projectId} version={version} />
        )}

      </div>
    </div>
  )
}
