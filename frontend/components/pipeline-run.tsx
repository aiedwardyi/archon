"use client"

import { useState, useRef, useEffect } from "react"
import {
  CheckCircle2,
  Circle,
  Loader2,
  ArrowRight,
  Send,
  Terminal,
  ChevronDown,
  AlertCircle,
  Zap,
} from "lucide-react"

type AgentStatus = "pending" | "running" | "complete"

type Agent = {
  name: string
  role: string
  status: AgentStatus
  duration?: string
  output?: string
}

type LogEntry = {
  timestamp: string
  agent: string
  message: string
}

const agents: Agent[] = [
  {
    name: "Requirements Agent",
    role: "Understands your request",
    status: "complete",
    duration: "12s",
    output: "Requirements document created",
  },
  {
    name: "Architecture Agent",
    role: "Plans the build",
    status: "running",
    duration: "8s...",
    output: "Planning the build...",
  },
  {
    name: "Build Agent",
    role: "Writes your code",
    status: "pending",
  },
]

const logEntries: LogEntry[] = [
  {
    timestamp: "14:23:01.234",
    agent: "Req",
    message: "Analyzing your request...",
  },
  {
    timestamp: "14:23:02.891",
    agent: "Req",
    message: "Parsing: \"Add retry logic for failed webhook deliveries\"",
  },
  {
    timestamp: "14:23:04.102",
    agent: "Req",
    message: "Requirements document created",
  },
  {
    timestamp: "14:23:07.445",
    agent: "Req",
    message: "Requirements verified",
  },
  {
    timestamp: "14:23:08.201",
    agent: "Req",
    message: "Handing off to Architecture Agent",
  },
  {
    timestamp: "14:23:09.012",
    agent: "Arch",
    message: "Planning the build...",
  },
  {
    timestamp: "14:23:11.334",
    agent: "Arch",
    message: "Analyzing existing codebase: 12 files, 3 modules",
  },
  {
    timestamp: "14:23:13.891",
    agent: "Arch",
    message: "Created 4 build tasks",
  },
  {
    timestamp: "14:23:15.102",
    agent: "Arch",
    message: "Resolving build dependencies...",
  },
  {
    timestamp: "14:23:17.445",
    agent: "Arch",
    message: "Build plan ready -- 4 files",
  },
]

function AgentStatusIcon({ status }: { status: AgentStatus }) {
  if (status === "complete")
    return <CheckCircle2 className="h-5 w-5 text-success" />
  if (status === "running")
    return <Loader2 className="h-5 w-5 text-info animate-spin-slow" />
  return <Circle className="h-5 w-5 text-muted-foreground/40" />
}

function AgentStatusLabel({ status }: { status: AgentStatus }) {
  if (status === "complete") return <span className="text-xs font-medium text-success">Done</span>
  if (status === "running") return <span className="text-xs font-medium text-info">Building...</span>
  return <span className="text-xs font-medium text-muted-foreground">Pending</span>
}

export function PipelineRun() {
  const [inputValue, setInputValue] = useState("")
  const [showAllLogs, setShowAllLogs] = useState(false)
  const logsEndRef = useRef<HTMLDivElement>(null)

  const displayedLogs = showAllLogs ? logEntries : logEntries.slice(-6)

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [showAllLogs])

  return (
    <div className="flex-1 flex flex-col">
      {/* Pipeline header */}
      <div className="border-b border-border bg-card px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-base font-semibold text-foreground">
                payment-service
              </h2>
              <span className="text-xs font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">
                Version 14
              </span>
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              Add retry logic for failed webhook deliveries &middot; Started 32 seconds ago
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 text-xs text-info bg-info/10 px-2.5 py-1 rounded-full font-medium">
              <Loader2 className="h-3 w-3 animate-spin-slow" />
              Building...
            </span>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col p-6 gap-6 overflow-auto">
        {/* Agent pipeline */}
        <div className="bg-card border border-border rounded-lg p-5">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">
              Agent Pipeline
            </h3>
          </div>
          <div className="flex items-stretch gap-0">
            {agents.map((agent, i) => (
              <div key={agent.name} className="flex items-stretch flex-1">
                <div
                  className={`flex-1 rounded-lg border p-4 transition-all ${
                    agent.status === "running"
                      ? "border-info bg-info/5 shadow-sm"
                      : agent.status === "complete"
                      ? "border-success/30 bg-success/5"
                      : "border-border bg-muted/30"
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <AgentStatusIcon status={agent.status} />
                    <span className="text-sm font-semibold text-foreground">
                      {agent.name}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">
                    {agent.role}
                  </p>
                  <AgentStatusLabel status={agent.status} />
                  {agent.output && (
                    <p className="text-xs text-foreground/70 mt-2 leading-relaxed">
                      {agent.output}
                    </p>
                  )}
                </div>
                {i < agents.length - 1 && (
                  <div className="flex items-center px-3">
                    <ArrowRight
                      className={`h-4 w-4 ${
                        agents[i + 1].status !== "pending"
                          ? "text-foreground"
                          : "text-muted-foreground/30"
                      }`}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Live log feed */}
        <div className="flex-1 bg-card border border-border rounded-lg flex flex-col min-h-0">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Terminal className="h-4 w-4 text-muted-foreground" />
              <h3 className="text-sm font-semibold text-foreground">
                LIVE OUTPUT
              </h3>
              <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                {logEntries.length} entries
              </span>
            </div>
            {!showAllLogs && logEntries.length > 6 && (
              <button
                onClick={() => setShowAllLogs(true)}
                className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors"
              >
                Show all
                <ChevronDown className="h-3 w-3" />
              </button>
            )}
          </div>
          <div className="flex-1 overflow-auto p-4 font-mono text-xs">
            {displayedLogs.map((log, i) => (
              <div
                key={i}
                className="flex items-start gap-3 py-1 hover:bg-muted/30 px-2 -mx-2 rounded"
              >
                <span className="text-muted-foreground/60 shrink-0 w-24">
                  {log.timestamp}
                </span>
                <span
                  className={`shrink-0 w-16 font-medium ${
                    log.agent === "Req"
                      ? "text-muted-foreground"
                      : log.agent === "Arch"
                      ? "text-info"
                      : "text-primary"
                  }`}
                >
                  [{log.agent}]
                </span>
                <span className="text-foreground/70">{log.message}</span>
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        </div>
      </div>

      {/* Continuous chat input - bottom fixed */}
      <div className="border-t border-border bg-card px-6 py-3">
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground font-mono shrink-0">
            {"payment-service >"}
          </span>
          <div className="flex-1 relative">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="What would you like to change?"
              className="w-full h-9 rounded-md border border-input bg-background pl-3 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring font-mono"
            />
            <button
              className="absolute right-1.5 top-1/2 -translate-y-1/2 p-1.5 rounded bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-40"
              disabled={!inputValue.trim()}
              aria-label="Send message"
            >
              <Send className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
