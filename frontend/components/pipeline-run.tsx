"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import {
  CheckCircle2,
  Circle,
  Loader2,
  ArrowRight,
  Send,
  Terminal,
  ChevronDown,
  Zap,
} from "lucide-react"

const API_BASE = "http://localhost:5000"
type AgentStatus = "pending" | "running" | "complete"

type LogEntry = {
  id: string
  timestamp: number
  message: string
  type: string
}

function AgentStatusIcon({ status }: { status: AgentStatus }) {
  if (status === "complete") return <CheckCircle2 className="h-5 w-5 text-success" />
  if (status === "running") return <Loader2 className="h-5 w-5 text-info animate-spin" />
  return <Circle className="h-5 w-5 text-muted-foreground/40" />
}

function AgentStatusLabel({ status }: { status: AgentStatus }) {
  if (status === "complete") return <span className="text-xs font-medium text-success">Done</span>
  if (status === "running") return <span className="text-xs font-medium text-info">Building...</span>
  return <span className="text-xs font-medium text-muted-foreground">Pending</span>
}

export function PipelineRun() {
  const [inputValue, setInputValue] = useState("")
  const [projectId, setProjectId] = useState<number | null>(null)
  const [projectName, setProjectName] = useState("my-project")
  const [version, setVersion] = useState<number | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [pipelineStatus, setPipelineStatus] = useState<"idle" | "running" | "complete" | "failed">("idle")
  const [currentStage, setCurrentStage] = useState<"pm" | "planner" | "engineer">("pm")
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [promptHistory, setPromptHistory] = useState<{ role: string; content: string }[]>([])
  const [showAllLogs, setShowAllLogs] = useState(false)
  const logsEndRef = useRef<HTMLDivElement>(null)
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  // Load project from sessionStorage on mount
  useEffect(() => {
    const pid = sessionStorage.getItem("archon_current_project_id")
    const pname = sessionStorage.getItem("archon_project_name")
    if (pid) setProjectId(Number(pid))
    if (pname) setProjectName(pname)
  }, [])

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [logs])

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  const pollStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/execution-status`)
      const data = await res.json()

      setLogs(data.logs || [])

      const stage = data.currentStage
      if (stage === "engineer") setCurrentStage("engineer")
      else if (stage === "planner") setCurrentStage("planner")
      else setCurrentStage("pm")

      if (data.status === "COMPLETED") {
        setPipelineStatus("complete")
        setIsRunning(false)
        stopPolling()
        if (data.execution_id) {
          sessionStorage.setItem("archon_current_execution_id", String(data.execution_id))
        }
        if (data.project_id) {
          sessionStorage.setItem("archon_current_project_id", String(data.project_id))
          setProjectId(data.project_id)
        }
        // Store version for preview
        const versionNum = version
        if (versionNum) {
          sessionStorage.setItem("archon_current_version", String(versionNum))
        }
      } else if (data.status === "FAILED") {
        setPipelineStatus("failed")
        setIsRunning(false)
        stopPolling()
      }
    } catch (e) {
      console.error("Poll error:", e)
    }
  }, [version])

  const handleSend = async () => {
    if (!inputValue.trim() || isRunning || !projectId) return

    const prompt = inputValue.trim()
    setInputValue("")
    setIsRunning(true)
    setPipelineStatus("running")
    setCurrentStage("pm")
    setLogs([])
    setShowAllLogs(false)

    const newHistory = [...promptHistory, { role: "user", content: prompt }]
    setPromptHistory(newHistory)

    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}/iterate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, prompt_history: newHistory }),
      })
      const data = await res.json()

      if (data.version) {
        setVersion(data.version)
        sessionStorage.setItem("archon_current_version", String(data.version))
      }

      // Start polling
      pollRef.current = setInterval(pollStatus, 1500)
    } catch (e) {
      setPipelineStatus("failed")
      setIsRunning(false)
    }
  }

  useEffect(() => {
    return () => stopPolling()
  }, [])

  // Re-attach pollStatus when version changes
  useEffect(() => {
    if (isRunning && !pollRef.current) {
      pollRef.current = setInterval(pollStatus, 1500)
    }
  }, [pollStatus, isRunning])

  const agentStages = [
    { key: "pm", name: "Requirements Agent", role: "Understands your request" },
    { key: "planner", name: "Architecture Agent", role: "Plans the build" },
    { key: "engineer", name: "Build Agent", role: "Writes your code" },
  ]

  const stageOrder = ["pm", "planner", "engineer"]

  const getAgentStatus = (key: string): AgentStatus => {
    const currentIdx = stageOrder.indexOf(currentStage)
    const agentIdx = stageOrder.indexOf(key)
    if (pipelineStatus === "complete") return "complete"
    if (pipelineStatus === "idle") return "pending"
    if (agentIdx < currentIdx) return "complete"
    if (agentIdx === currentIdx) return "running"
    return "pending"
  }

  const displayedLogs = showAllLogs ? logs : logs.slice(-6)

  const formatTime = (ts: number) => {
    const d = new Date(ts)
    return d.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" }) +
      "." + String(d.getMilliseconds()).padStart(3, "0")
  }

  const statusLabel = {
    idle: null,
    running: <span className="flex items-center gap-1.5 text-xs text-info bg-info/10 px-2.5 py-1 rounded-full font-medium"><Loader2 className="h-3 w-3 animate-spin" />Building...</span>,
    complete: <span className="flex items-center gap-1.5 text-xs text-success bg-success/10 px-2.5 py-1 rounded-full font-medium">Complete</span>,
    failed: <span className="flex items-center gap-1.5 text-xs text-destructive bg-destructive/10 px-2.5 py-1 rounded-full font-medium">Failed</span>,
  }[pipelineStatus]

  return (
    <div className="flex-1 flex flex-col">
      {/* Header */}
      <div className="border-b border-border bg-card px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-base font-semibold text-foreground">{projectName}</h2>
              {version && (
                <span className="text-xs font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">
                  Version {version}
                </span>
              )}
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              {projectId ? `Project ID: ${projectId}` : "Select a project from the Projects page"}
            </p>
          </div>
          <div>{statusLabel}</div>
        </div>
      </div>

      <div className="flex-1 flex flex-col p-6 gap-6 overflow-auto">
        {/* Agent pipeline */}
        <div className="bg-card border border-border rounded-lg p-5">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Agent Pipeline</h3>
          </div>
          <div className="flex items-stretch gap-0">
            {agentStages.map((agent, i) => {
              const status = getAgentStatus(agent.key)
              return (
                <div key={agent.key} className="flex items-stretch flex-1">
                  <div className={`flex-1 rounded-lg border p-4 transition-all ${
                    status === "running" ? "border-info bg-info/5 shadow-sm"
                    : status === "complete" ? "border-success/30 bg-success/5"
                    : "border-border bg-muted/30"
                  }`}>
                    <div className="flex items-center gap-2 mb-2">
                      <AgentStatusIcon status={status} />
                      <span className="text-sm font-semibold text-foreground">{agent.name}</span>
                    </div>
                    <p className="text-xs text-muted-foreground mb-2">{agent.role}</p>
                    <AgentStatusLabel status={status} />
                  </div>
                  {i < agentStages.length - 1 && (
                    <div className="flex items-center px-3">
                      <ArrowRight className={`h-4 w-4 ${
                        getAgentStatus(agentStages[i + 1].key) !== "pending" ? "text-foreground" : "text-muted-foreground/30"
                      }`} />
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Live log feed */}
        <div className="flex-1 bg-card border border-border rounded-lg flex flex-col min-h-0">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Terminal className="h-4 w-4 text-muted-foreground" />
              <h3 className="text-sm font-semibold text-foreground">LIVE OUTPUT</h3>
              <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                {logs.length} entries
              </span>
            </div>
            {!showAllLogs && logs.length > 6 && (
              <button onClick={() => setShowAllLogs(true)} className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors">
                Show all <ChevronDown className="h-3 w-3" />
              </button>
            )}
          </div>
          <div className="flex-1 overflow-auto p-4 font-mono text-xs">
            {logs.length === 0 && pipelineStatus === "idle" && (
              <p className="text-muted-foreground italic">
                {projectId ? "Type a prompt below to start building." : "Go to Projects and select or create a project first."}
              </p>
            )}
            {displayedLogs.map((log) => (
              <div key={`${log.id}-${log.timestamp}`} className="flex items-start gap-3 py-1 hover:bg-muted/30 px-2 -mx-2 rounded">
                <span className="text-muted-foreground/60 shrink-0 w-28">{formatTime(log.timestamp)}</span>
                <span className="text-foreground/70">{log.message}</span>
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        </div>
      </div>

      {/* Chat input */}
      <div className="border-t border-border bg-card px-6 py-3">
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground font-mono shrink-0">{projectName} {">"}</span>
          <div className="flex-1 relative">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleSend() }}
              placeholder={projectId ? "What would you like to build?" : "Select a project first..."}
              disabled={!projectId || isRunning}
              className="w-full h-9 rounded-md border border-input bg-background pl-3 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring font-mono disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || isRunning || !projectId}
              className="absolute right-1.5 top-1/2 -translate-y-1/2 p-1.5 rounded bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-40"
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

