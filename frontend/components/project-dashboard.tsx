"use client"

import { useState } from "react"
import {
  Plus,
  Search,
  MoreHorizontal,
  ArrowUpDown,
  Folder,
  Clock,
  ChevronDown,
  Download,
} from "lucide-react"
import { StatusBadge } from "@/components/status-badge"

type Project = {
  id: string
  name: string
  description: string
  status: "running" | "completed" | "failed" | "pending"
  lastRun: string
  versions: number
  created: string
  branch: string
}

const projects: Project[] = [
  {
    id: "proj_001",
    name: "payment-service",
    description: "Stripe integration microservice with webhook handling",
    status: "running",
    lastRun: "2 min ago",
    versions: 14,
    created: "Jan 12, 2026",
    branch: "main",
  },
  {
    id: "proj_002",
    name: "auth-gateway",
    description: "OAuth2 authentication gateway with RBAC",
    status: "completed",
    lastRun: "1 hr ago",
    versions: 23,
    created: "Dec 03, 2025",
    branch: "main",
  },
  {
    id: "proj_003",
    name: "notification-engine",
    description: "Multi-channel notification dispatch system",
    status: "failed",
    lastRun: "34 min ago",
    versions: 8,
    created: "Feb 01, 2026",
    branch: "develop",
  },
  {
    id: "proj_004",
    name: "data-pipeline-etl",
    description: "ETL pipeline for analytics data warehouse ingestion",
    status: "completed",
    lastRun: "3 hr ago",
    versions: 31,
    created: "Nov 18, 2025",
    branch: "main",
  },
  {
    id: "proj_005",
    name: "inventory-api",
    description: "REST API for warehouse inventory management",
    status: "pending",
    lastRun: "Never",
    versions: 1,
    created: "Feb 18, 2026",
    branch: "feature/init",
  },
  {
    id: "proj_006",
    name: "ml-scoring-service",
    description: "Real-time ML model scoring endpoint with A/B testing",
    status: "completed",
    lastRun: "6 hr ago",
    versions: 19,
    created: "Oct 22, 2025",
    branch: "main",
  },
  {
    id: "proj_007",
    name: "email-renderer",
    description: "Template-based email rendering with MJML support",
    status: "running",
    lastRun: "Just now",
    versions: 5,
    created: "Feb 14, 2026",
    branch: "develop",
  },
  {
    id: "proj_008",
    name: "config-service",
    description: "Centralized configuration management with versioning",
    status: "completed",
    lastRun: "12 hr ago",
    versions: 42,
    created: "Sep 05, 2025",
    branch: "main",
  },
]

export function ProjectDashboard() {
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")

  const filtered = projects.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === "all" || p.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const stats = {
    total: projects.length,
    running: projects.filter((p) => p.status === "running").length,
    completed: projects.filter((p) => p.status === "completed").length,
    failed: projects.filter((p) => p.status === "failed").length,
  }

  return (
    <div className="flex-1 p-6">
      {/* Stats bar */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: "Total Projects", value: stats.total, color: "text-foreground" },
          { label: "Running", value: stats.running, color: "text-info" },
          { label: "Completed", value: stats.completed, color: "text-success" },
          { label: "Failed", value: stats.failed, color: "text-destructive" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="bg-card border border-border rounded-lg p-4"
          >
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
        <button className="h-9 flex items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors">
          <Plus className="h-4 w-4" />
          New Project
        </button>
      </div>

      {/* Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              {["Project", "Status", "Last Run", "Versions", "Created", ""].map(
                (header) => (
                  <th
                    key={header}
                    className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider"
                  >
                    {header && (
                      <span className="flex items-center gap-1 cursor-pointer hover:text-foreground transition-colors">
                        {header}
                        {header !== "" && (
                          <ArrowUpDown className="h-3 w-3" />
                        )}
                      </span>
                    )}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            {filtered.map((project, i) => (
              <tr
                key={project.id}
                className={`border-b border-border last:border-b-0 hover:bg-muted/50 transition-colors cursor-pointer group ${
                  i % 2 === 0 ? "" : "bg-muted/20"
                }`}
              >
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-md bg-accent flex items-center justify-center">
                      <Folder className="h-4 w-4 text-accent-foreground" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-foreground font-mono">
                        {project.name}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5 max-w-xs truncate">
                        {project.description}
                      </p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={project.status} />
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                    <Clock className="h-3.5 w-3.5" />
                    {project.lastRun}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-foreground font-mono">
                    v{project.versions}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-muted-foreground">
                    {project.created}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      className="p-1 rounded hover:bg-muted transition-colors opacity-0 group-hover:opacity-100"
                      aria-label="Download report"
                    >
                      <Download className="h-4 w-4 text-muted-foreground" />
                    </button>
                    <button className="p-1 rounded hover:bg-muted transition-colors" aria-label="More options">
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
              No projects match your search criteria.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
