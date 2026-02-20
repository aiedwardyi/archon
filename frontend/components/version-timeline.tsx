"use client"

import { useState } from "react"
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
  Monitor,
  Smartphone,
  ExternalLink,
} from "lucide-react"

type Version = {
  id: string
  version: string
  prompt: string
  timestamp: string
  date: string
  status: "completed" | "failed" | "running"
  changes: {
    files: number
    additions: number
    deletions: number
  }
  agent: string
}

const versions: Version[] = [
  {
    id: "v14",
    version: "v14",
    prompt: "Add retry logic for failed webhooks",
    timestamp: "2:23 PM",
    date: "Today",
    status: "running",
    changes: { files: 4, additions: 127, deletions: 12 },
    agent: "Build Agent",
  },
  {
    id: "v13",
    version: "v13",
    prompt: "Implement dead letter queue for...",
    timestamp: "1:45 PM",
    date: "Today",
    status: "completed",
    changes: { files: 3, additions: 89, deletions: 5 },
    agent: "Build Agent",
  },
  {
    id: "v12",
    version: "v12",
    prompt: "Add webhook signature validation",
    timestamp: "11:30 AM",
    date: "Today",
    status: "completed",
    changes: { files: 2, additions: 45, deletions: 3 },
    agent: "Build Agent",
  },
  {
    id: "v11",
    version: "v11",
    prompt: "Refactor payment processing to...",
    timestamp: "10:15 AM",
    date: "Today",
    status: "completed",
    changes: { files: 6, additions: 210, deletions: 87 },
    agent: "Build Agent",
  },
  {
    id: "v10",
    version: "v10",
    prompt: "Add Stripe Connect support for...",
    timestamp: "4:22 PM",
    date: "Yesterday",
    status: "completed",
    changes: { files: 5, additions: 334, deletions: 21 },
    agent: "Build Agent",
  },
  {
    id: "v9",
    version: "v9",
    prompt: "Fix currency conversion bug in...",
    timestamp: "3:01 PM",
    date: "Yesterday",
    status: "failed",
    changes: { files: 1, additions: 12, deletions: 8 },
    agent: "Build Agent",
  },
  {
    id: "v8",
    version: "v8",
    prompt: "Add multi-currency support with...",
    timestamp: "1:55 PM",
    date: "Yesterday",
    status: "completed",
    changes: { files: 7, additions: 445, deletions: 34 },
    agent: "Build Agent",
  },
  {
    id: "v7",
    version: "v7",
    prompt: "Implement idempotency keys for...",
    timestamp: "11:10 AM",
    date: "Yesterday",
    status: "completed",
    changes: { files: 3, additions: 78, deletions: 12 },
    agent: "Build Agent",
  },
]

function VersionStatusIcon({ status }: { status: Version["status"] }) {
  if (status === "completed")
    return <CheckCircle2 className="h-4 w-4 text-success" />
  if (status === "failed") return <XCircle className="h-4 w-4 text-destructive" />
  return <Loader2 className="h-4 w-4 text-info animate-spin-slow" />
}

function ViewportToggle({
  viewport,
  onChange,
}: {
  viewport: "desktop" | "mobile"
  onChange: (v: "desktop" | "mobile") => void
}) {
  return (
    <div className="flex items-center bg-muted rounded-md p-0.5">
      <button
        onClick={() => onChange("desktop")}
        className={`p-1.5 rounded transition-colors ${
          viewport === "desktop"
            ? "bg-card text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        }`}
        aria-label="Desktop view"
      >
        <Monitor className="h-3.5 w-3.5" />
      </button>
      <button
        onClick={() => onChange("mobile")}
        className={`p-1.5 rounded transition-colors ${
          viewport === "mobile"
            ? "bg-card text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        }`}
        aria-label="Mobile view"
      >
        <Smartphone className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}

export function VersionTimeline() {
  const [panelOpen, setPanelOpen] = useState(true)
  const [selectedVersion, setSelectedVersion] = useState<string>("v14")
  const [previewViewport, setPreviewViewport] = useState<"desktop" | "mobile">("desktop")

  const selected = versions.find((v) => v.id === selectedVersion)

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Version panel */}
      {panelOpen && (
        <aside className="w-80 border-r border-border bg-card flex flex-col shrink-0">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <h3 className="text-sm font-semibold text-foreground">
                Version History
              </h3>
            </div>
            <button
              onClick={() => setPanelOpen(false)}
              className="p-1 rounded hover:bg-muted transition-colors"
              aria-label="Close version panel"
            >
              <PanelLeftClose className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
          <div className="flex-1 overflow-auto">
            {versions.map((v, i) => {
              const isActive = v.id === selectedVersion
              const showDateHeader =
                i === 0 || versions[i - 1].date !== v.date

              return (
                <div key={v.id}>
                  {showDateHeader && (
                    <div className="px-4 py-2 bg-muted/50">
                      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        {v.date}
                      </span>
                    </div>
                  )}
                  <button
                    onClick={() => setSelectedVersion(v.id)}
                    className={`w-full text-left px-4 py-3 border-b border-border transition-colors ${
                      isActive
                        ? "bg-accent border-l-2 border-l-primary"
                        : "hover:bg-muted/50 opacity-70 hover:opacity-100"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-xs font-mono font-semibold px-1.5 py-0.5 rounded ${
                            isActive
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          {v.version}
                        </span>
                        <VersionStatusIcon status={v.status} />
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {v.timestamp}
                      </span>
                    </div>
                    <p className="text-sm text-foreground truncate mt-1">
                      {v.prompt}
                    </p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                      <span>{v.changes.files} files changed</span>
                    </div>
                  </button>
                </div>
              )
            })}
          </div>
        </aside>
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-auto">
        {!panelOpen && (
          <div className="px-6 pt-4">
            <button
              onClick={() => setPanelOpen(true)}
              className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded border border-border hover:bg-muted"
              aria-label="Open version panel"
            >
              <PanelLeft className="h-3.5 w-3.5" />
              Show versions
            </button>
          </div>
        )}

        {selected && (
          <div className="flex-1 p-6">
            {/* Version detail header */}
            <div className="flex items-start justify-between mb-6">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-sm font-mono font-bold bg-primary text-primary-foreground px-2 py-0.5 rounded">
                    {selected.version}
                  </span>
                  <VersionStatusIcon status={selected.status} />
                  <span className="text-sm text-muted-foreground">
                    {selected.date} at {selected.timestamp}
                  </span>
                </div>
                <h2 className="text-lg font-semibold text-foreground">
                  {selected.prompt}
                </h2>
              </div>
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-2 h-9 px-4 rounded-md border border-border text-sm font-medium text-foreground hover:bg-muted transition-colors">
                  <Download className="h-4 w-4" />
                  Download Report
                </button>
                {selected.status !== "running" && selected.version !== "v14" && (
                  <button className="flex items-center gap-2 h-9 px-4 rounded-md border border-border text-sm font-medium text-foreground hover:bg-muted transition-colors">
                    <RotateCcw className="h-4 w-4" />
                    Restore to this version
                  </button>
                )}
              </div>
            </div>

            {/* Prompt section */}
            <div className="bg-card border border-border rounded-lg mb-6">
              <div className="px-4 py-3 border-b border-border">
                <h3 className="text-sm font-semibold text-foreground">
                  Prompt
                </h3>
              </div>
              <div className="p-4">
                <div className="flex gap-3">
                  <div className="h-7 w-7 rounded-full bg-muted flex items-center justify-center shrink-0">
                    <span className="text-xs font-medium text-muted-foreground">
                      JD
                    </span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-foreground">
                        You
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {selected.timestamp}
                      </span>
                    </div>
                    <p className="text-sm text-foreground/80 leading-relaxed">
                      {selected.prompt}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Status inline */}
            <div className="flex items-center gap-4 mb-6">
              <div className="inline-flex items-center gap-2 bg-card border border-border rounded-lg px-4 py-2.5">
                <VersionStatusIcon status={selected.status} />
                <span className="text-sm text-foreground font-medium capitalize">
                  {selected.status}
                </span>
              </div>
              <span className="text-xs text-muted-foreground">
                {selected.changes.files} files changed
              </span>
            </div>

            {/* What Was Built */}
            <div className="bg-card border border-border rounded-lg mb-6">
              <div className="px-4 py-3 border-b border-border">
                <h3 className="text-sm font-semibold text-foreground">
                  What Was Built
                </h3>
              </div>
              <div className="p-4">
                <div className="flex gap-3">
                  <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    <ChevronRight className="h-3.5 w-3.5 text-primary" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-foreground">
                        Archon
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {selected.timestamp}
                      </span>
                    </div>
                    <p className="text-sm text-foreground/80 leading-relaxed">
                      Understood. I analyzed the requirements and generated an implementation plan. The pipeline has been initiated with the Requirements Agent leading the analysis phase.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Build Artifacts */}
            <div className="bg-card border border-border rounded-lg mb-6">
              <div className="px-4 py-3 border-b border-border">
                <h3 className="text-sm font-semibold text-foreground">
                  Build Artifacts
                </h3>
              </div>
              <div className="p-4">
                <div className="grid grid-cols-3 gap-3">
                  <button className="flex items-center gap-3 p-4 rounded-lg border border-border hover:bg-muted/50 hover:border-primary/30 transition-colors text-left group">
                    <div className="h-9 w-9 rounded-md bg-primary/10 flex items-center justify-center shrink-0 group-hover:bg-primary/20 transition-colors">
                      <FileText className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-foreground">Brief</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        3 requirements, 7 success criteria
                      </p>
                    </div>
                  </button>
                  <button className="flex items-center gap-3 p-4 rounded-lg border border-border hover:bg-muted/50 hover:border-primary/30 transition-colors text-left group">
                    <div className="h-9 w-9 rounded-md bg-info/10 flex items-center justify-center shrink-0 group-hover:bg-info/20 transition-colors">
                      <Map className="h-4 w-4 text-info" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-foreground">Build Plan</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        4 modules
                      </p>
                    </div>
                  </button>
                  <button className="flex items-center gap-3 p-4 rounded-lg border border-border hover:bg-muted/50 hover:border-primary/30 transition-colors text-left group">
                    <div className="h-9 w-9 rounded-md bg-success/10 flex items-center justify-center shrink-0 group-hover:bg-success/20 transition-colors">
                      <Code2 className="h-4 w-4 text-success" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-foreground">Code</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {selected.changes.files} files changed
                      </p>
                    </div>
                  </button>
                </div>
              </div>
            </div>

            {/* Live Preview */}
            <div className="bg-card border border-border rounded-lg">
              <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                <h3 className="text-sm font-semibold text-foreground">
                  Live Preview
                </h3>
                <div className="flex items-center gap-2">
                  <ViewportToggle
                    viewport={previewViewport}
                    onChange={setPreviewViewport}
                  />
                  <button
                    className="p-1.5 rounded border border-border text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                    aria-label="Open in new tab"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
              <div className="p-4 flex items-center justify-center bg-muted/30 min-h-[300px]">
                {previewViewport === "mobile" ? (
                  <div className="relative w-[290px]">
                    {/* iPhone frame */}
                    <div className="rounded-[2.5rem] border-[3px] border-foreground/20 bg-card p-2 shadow-lg">
                      {/* Notch / Dynamic Island */}
                      <div className="flex justify-center mb-2">
                        <div className="w-20 h-5 bg-foreground/20 rounded-full" />
                      </div>
                      {/* Screen */}
                      <div className="rounded-[2rem] overflow-hidden bg-muted/50 min-h-[480px] flex items-center justify-center border border-border">
                        <p className="text-xs text-muted-foreground text-center px-4">
                          Live preview will appear here when your build is complete
                        </p>
                      </div>
                      {/* Home indicator */}
                      <div className="flex justify-center mt-2">
                        <div className="w-28 h-1 bg-foreground/15 rounded-full" />
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="w-full">
                    <div className="border-2 border-dashed border-border rounded-lg flex items-center justify-center min-h-[260px]">
                      <p className="text-sm text-muted-foreground">
                        Live preview will appear here when your build is complete
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
