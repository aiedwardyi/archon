"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import {
  Plus,
  Search,
  MoreHorizontal,
  ArrowUpDown,
  Folder,
  Clock,
  ChevronDown,
  ChevronUp,
  Download,
  Loader2,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  GitBranch,
} from "lucide-react"
import { StatusBadge } from "@/components/status-badge"

const API_BASE = "http://localhost:5000"

type Project = {
  id: number
  name: string
  description: string
  status: "running" | "completed" | "failed" | "pending" | "in_progress"
  created_at: string
  updated_at: string
  execution_count: number
}

type ConfirmModal = {
  type: "single" | "all"
  projectId?: number
  projectName?: string
}

export function ProjectDashboard() {
  const router = useRouter()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [creating, setCreating] = useState(false)
  const [newProjectName, setNewProjectName] = useState("")
  const [showNewProjectInput, setShowNewProjectInput] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [openMenuId, setOpenMenuId] = useState<number | null>(null)
  const [confirmModal, setConfirmModal] = useState<ConfirmModal | null>(null)
  const [deleteConfirmText, setDeleteConfirmText] = useState("")
  const [deleting, setDeleting] = useState(false)
  const [activityExpanded, setActivityExpanded] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const fetchProjects = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/projects`)
      const data = await res.json()
      setProjects(data)
    } catch (e) {
      setError("Could not connect to backend")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchProjects() }, [])

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpenMenuId(null)
      }
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return
    setCreating(true)
    try {
      const res = await fetch(`${API_BASE}/api/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newProjectName.trim() }),
      })
      const project = await res.json()
      setProjects((prev) => [project, ...prev])
      setNewProjectName("")
      setShowNewProjectInput(false)
      sessionStorage.setItem("archon_current_project_id", String(project.id))
      sessionStorage.setItem("archon_project_name", project.name)
      sessionStorage.removeItem("archon_current_version")
      sessionStorage.removeItem("archon_current_execution_id")
      sessionStorage.removeItem("archon_pipeline_status")
      sessionStorage.removeItem("archon_current_stage")
      router.push(`/pipeline?pid=${project.id}`)
    } catch (e) {
      setError("Failed to create project")
    } finally {
      setCreating(false)
    }
  }

  const handleProjectClick = (project: Project) => {
    sessionStorage.setItem("archon_current_project_id", String(project.id))
    sessionStorage.setItem("archon_project_name", project.name)
    sessionStorage.removeItem("archon_current_version")
    sessionStorage.removeItem("archon_current_execution_id")
    sessionStorage.removeItem("archon_pipeline_status")
    sessionStorage.removeItem("archon_current_stage")
    sessionStorage.removeItem("archon_selected_version")
    router.push(`/pipeline?pid=${project.id}`)
  }

  const closeModal = () => {
    setConfirmModal(null)
    setDeleteConfirmText("")
  }

  const handleDeleteProject = async (projectId: number) => {
    setDeleting(true)
    try {
      await fetch(`${API_BASE}/api/projects/${projectId}`, { method: "DELETE" })
      setProjects((prev) => prev.filter((p) => p.id !== projectId))
      if (sessionStorage.getItem("archon_current_project_id") === String(projectId)) {
        sessionStorage.removeItem("archon_current_project_id")
        sessionStorage.removeItem("archon_project_name")
        sessionStorage.removeItem("archon_current_version")
      }
    } catch (e) {
      setError("Failed to delete project")
    } finally {
      setDeleting(false)
      closeModal()
    }
  }

  const handleDeleteAll = async () => {
    setDeleting(true)
    try {
      await Promise.all(
        projects.map((p) => fetch(`${API_BASE}/api/projects/${p.id}`, { method: "DELETE" }))
      )
      setProjects([])
      sessionStorage.removeItem("archon_current_project_id")
      sessionStorage.removeItem("archon_project_name")
      sessionStorage.removeItem("archon_current_version")
    } catch (e) {
      setError("Failed to delete all projects")
    } finally {
      setDeleting(false)
      closeModal()
    }
  }

  const filtered = projects.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.description || "").toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === "all" || p.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const stats = {
    total: projects.length,
    running: projects.filter((p) => p.status === "running" || p.status === "in_progress").length,
    completed: projects.filter((p) => p.status === "completed").length,
    failed: projects.filter((p) => p.status === "failed").length,
  }

  const formatDate = (iso: string) => {
    if (!iso) return "—"
    return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="flex-1 p-6">
      {error && (
        <div className="mb-4 px-4 py-3 rounded-lg border border-destructive/30 bg-destructive/10 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Pipeline stats bar */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: "Pipelines Today", value: projects.filter((p) => { const d = new Date(p.updated_at); const now = new Date(); return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate() }).length },
          { label: "Lines Generated", value: `${(projects.reduce((sum, p) => sum + (p.execution_count || 0), 0) * 500 / 1000).toFixed(1)}k` },
          { label: "Versions Shipped", value: projects.reduce((sum, p) => sum + (p.execution_count || 0), 0) },
          { label: "Avg Build Time", value: "5m 25s" },
        ].map((stat) => (
          <div key={stat.label} className="bg-card border border-border rounded-lg p-4">
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">{stat.label}</p>
            <p className="text-2xl font-semibold mt-1 text-foreground">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Project stats bar */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: "Total Projects", value: stats.total, color: "text-foreground" },
          { label: "Running", value: stats.running, color: "text-info" },
          { label: "Completed", value: stats.completed, color: "text-success" },
          { label: "Failed", value: stats.failed, color: "text-destructive" },
        ].map((stat) => (
          <div key={stat.label} className="bg-card border border-border rounded-lg p-4">
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">{stat.label}</p>
            <p className={`text-2xl font-semibold mt-1 ${stat.color}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Header row */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-9 w-64 rounded-md border border-input bg-card pl-9 pr-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div className="relative">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-9 appearance-none rounded-md border border-input bg-card pl-3 pr-8 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="all">All statuses</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="pending">Pending</option>
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          </div>
        </div>
        <div className="flex items-center gap-2">
          {projects.length > 0 && (
            <button
              onClick={() => setConfirmModal({ type: "all" })}
              className="h-9 flex items-center gap-2 rounded-md border border-border px-3 text-sm font-medium text-muted-foreground hover:text-destructive hover:border-destructive/50 transition-colors"
            >
              <Trash2 className="h-4 w-4" />
              Delete All
            </button>
          )}
          {showNewProjectInput && (
            <input
              autoFocus
              type="text"
              placeholder="Project name..."
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleCreateProject()
                if (e.key === "Escape") setShowNewProjectInput(false)
              }}
              className="h-9 w-52 rounded-md border border-input bg-card px-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          )}
          <button
            onClick={() => showNewProjectInput ? handleCreateProject() : setShowNewProjectInput(true)}
            disabled={creating}
            className="h-9 flex items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-60"
          >
            {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            {showNewProjectInput ? "Create" : "New Project"}
          </button>
        </div>
      </div>

      {/* Recent Activity */}
      {projects.length > 0 && (
        <div className="bg-card border border-border rounded-lg overflow-hidden mb-4">
          <div className="px-4 py-3 border-b border-border flex items-center justify-between">
            <h3 className="text-xs font-semibold text-foreground uppercase tracking-wider flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-muted-foreground" />
              Recent Activity
            </h3>
            <span className="text-[10px] font-medium text-emerald-600 bg-emerald-500/10 px-1.5 py-0.5 rounded">Live</span>
          </div>
          <div className="divide-y divide-border">
            {(() => {
              const sorted = [...projects].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
              const visible = activityExpanded ? sorted : sorted.slice(0, 4);
              return visible.map((p) => {
                const Icon = p.status === "completed" ? CheckCircle2 : p.status === "failed" ? XCircle : p.status === "running" || p.status === "in_progress" ? Loader2 : GitBranch;
                const iconClass = p.status === "completed" ? "text-emerald-500" : p.status === "failed" ? "text-destructive" : p.status === "running" || p.status === "in_progress" ? "text-blue-500 animate-spin" : "text-muted-foreground";
                const actionText = p.status === "completed" ? `${p.name} v${p.execution_count || 1} completed` : p.status === "failed" ? `${p.name} v${p.execution_count || 1} build failed` : p.status === "running" || p.status === "in_progress" ? `Pipeline started for ${p.name}` : `${p.name} v${p.execution_count || 1} pending`;
                const diff = Date.now() - new Date(p.updated_at).getTime();
                const mins = Math.floor(diff / 60000);
                const timeAgo = mins < 1 ? "just now" : mins < 60 ? `${mins}m ago` : Math.floor(mins / 60) < 24 ? `${Math.floor(mins / 60)}h ago` : `${Math.floor(Math.floor(mins / 60) / 24)}d ago`;
                return (
                  <div key={p.id} className="px-4 py-2.5 flex items-start gap-2.5 hover:bg-muted/40 transition-colors">
                    <Icon className={`h-3.5 w-3.5 mt-0.5 flex-shrink-0 ${iconClass}`} />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs text-foreground leading-snug">{actionText}</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">{timeAgo}</p>
                    </div>
                  </div>
                );
              });
            })()}
          </div>
          {projects.length > 4 && (
            <button
              onClick={() => setActivityExpanded(!activityExpanded)}
              className="w-full px-4 py-2 border-t border-border text-[11px] font-medium text-muted-foreground hover:text-foreground hover:bg-muted/40 transition-colors flex items-center justify-center gap-1"
            >
              {activityExpanded ? (
                <><ChevronUp className="h-3 w-3" /> Show less</>
              ) : (
                <><ChevronDown className="h-3 w-3" /> Show more ({projects.length - 4})</>
              )}
            </button>
          )}
        </div>
      )}

      {/* Projects Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden" ref={menuRef}>
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              {["Project", "ID", "Status", "Last Run", "Versions", "Created", ""].map((header) => (
                <th key={header} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {header && (
                    <span className="flex items-center gap-1 cursor-pointer hover:text-foreground transition-colors">
                      {header}
                      {header !== "" && <ArrowUpDown className="h-3 w-3" />}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((project, i) => (
              <tr
                key={project.id}
                onClick={() => handleProjectClick(project)}
                className={`border-b border-border last:border-b-0 hover:bg-muted/50 transition-colors cursor-pointer group ${i % 2 === 0 ? "" : "bg-muted/20"}`}
              >
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-md bg-accent flex items-center justify-center">
                      <Folder className="h-4 w-4 text-accent-foreground" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-foreground font-mono">{project.name}</p>
                      <p className="text-xs text-muted-foreground mt-0.5 max-w-xs truncate">
                        {project.description || "No description"}
                      </p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">
                    #{project.id}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={project.status === "in_progress" ? "running" : project.status} />
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                    <Clock className="h-3.5 w-3.5" />
                    {formatDate(project.updated_at)}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-foreground font-mono">v{project.execution_count || 1}</span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-muted-foreground">{formatDate(project.created_at)}</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      className="p-1 rounded hover:bg-muted transition-colors opacity-0 group-hover:opacity-100"
                      aria-label="Download report"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Download className="h-4 w-4 text-muted-foreground" />
                    </button>
                    <div className="relative">
                      <button
                        className="p-1 rounded hover:bg-muted transition-colors"
                        aria-label="More options"
                        onClick={(e) => {
                          e.stopPropagation()
                          setOpenMenuId(openMenuId === project.id ? null : project.id)
                        }}
                      >
                        <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
                      </button>
                      {openMenuId === project.id && (
                        <div className="absolute right-0 top-8 z-50 w-44 bg-popover border border-border rounded-lg shadow-lg py-1 overflow-hidden">
                          <button
                            className="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-destructive hover:bg-destructive/10 transition-colors"
                            onClick={(e) => {
                              e.stopPropagation()
                              setOpenMenuId(null)
                              setConfirmModal({ type: "single", projectId: project.id, projectName: project.name })
                            }}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                            Delete project
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="p-12 text-center">
            <p className="text-sm text-muted-foreground">
              {projects.length === 0 ? "No projects yet. Create your first project above." : "No projects match your search."}
            </p>
          </div>
        )}
      </div>


      {/* Confirmation Modal */}
      {confirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" onClick={closeModal} />
          <div className="relative bg-card border border-border rounded-xl shadow-2xl p-6 w-full max-w-sm mx-4">
            <div className="flex items-start gap-3 mb-5">
              <div className="h-10 w-10 rounded-full bg-destructive/10 flex items-center justify-center shrink-0 mt-0.5">
                <AlertTriangle className="h-5 w-5 text-destructive" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground">
                  {confirmModal.type === "all" ? "Delete all projects?" : "Delete project?"}
                </h3>
                <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                  {confirmModal.type === "all"
                    ? `Permanently deletes all ${projects.length} projects and their version history. This cannot be undone.`
                    : `Permanently deletes "${confirmModal.projectName}" and all its version history. This cannot be undone.`}
                </p>
              </div>
            </div>
            <div className="mb-5">
              <label className="block text-xs text-muted-foreground mb-1.5">
                Type <span className="font-mono font-semibold text-foreground">DELETE</span> to confirm
              </label>
              <input
                autoFocus
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && deleteConfirmText === "DELETE") {
                    if (confirmModal.type === "all") handleDeleteAll()
                    else if (confirmModal.projectId) handleDeleteProject(confirmModal.projectId)
                  }
                  if (e.key === "Escape") closeModal()
                }}
                placeholder="DELETE"
                className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground placeholder:text-muted-foreground/30 focus:outline-none focus:ring-2 focus:ring-destructive/40 font-mono"
              />
            </div>
            <div className="flex items-center gap-2 justify-end">
              <button
                onClick={closeModal}
                className="h-9 px-4 rounded-md border border-border text-sm font-medium text-foreground hover:bg-muted transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (confirmModal.type === "all") handleDeleteAll()
                  else if (confirmModal.projectId) handleDeleteProject(confirmModal.projectId)
                }}
                disabled={deleting || deleteConfirmText !== "DELETE"}
                className="h-9 px-4 rounded-md bg-destructive text-destructive-foreground text-sm font-medium hover:bg-destructive/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {deleting && <Loader2 className="h-4 w-4 animate-spin" />}
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
