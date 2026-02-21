"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import {
  Plus,
  Search,
  MoreHorizontal,
  ArrowUpDown,
  Folder,
  Clock,
  ChevronDown,
  Download,
  Loader2,
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

  useEffect(() => {
    fetchProjects()
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
      // Navigate to pipeline for the new project
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
    router.push(`/pipeline?pid=${project.id}`)
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

      {/* Stats bar */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: "Total Projects", value: stats.total, color: "text-foreground" },
          { label: "Running", value: stats.running, color: "text-info" },
          { label: "Completed", value: stats.completed, color: "text-success" },
          { label: "Failed", value: stats.failed, color: "text-destructive" },
        ].map((stat) => (
          <div key={stat.label} className="bg-card border border-border rounded-lg p-4">
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
              {stat.label}
            </p>
            <p className={`text-2xl font-semibold mt-1 ${stat.color}`}>
              {stat.value}
            </p>
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

      {/* Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              {["Project", "Status", "Last Run", "Versions", "Created", ""].map((header) => (
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
                  <StatusBadge status={project.status === "in_progress" ? "running" : project.status} />
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                    <Clock className="h-3.5 w-3.5" />
                    {formatDate(project.updated_at)}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-foreground font-mono">
                    v{project.execution_count || 1}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-muted-foreground">
                    {formatDate(project.created_at)}
                  </span>
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
                    <button
                      className="p-1 rounded hover:bg-muted transition-colors"
                      aria-label="More options"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
                    </button>
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
    </div>
  )
}


