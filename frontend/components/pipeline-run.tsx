"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { useSearchParams } from "next/navigation"
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
const POLL_INTERVAL_MS = 1500
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
  const [globallyBlocked, setGloballyBlocked] = useState(false)
  const [blockingProjectId, setBlockingProjectId] = useState<number | null>(null)
  const logsEndRef = useRef<HTMLDivElement>(null)
  const pollRef = useRef<NodeJS.Timeout | null>(null)
  const executionIdRef = useRef<number | null>(null)
  const versionRef = useRef<number | null>(null)
  const isRunningRef = useRef(false)
  const newRunRef = useRef(false)

  const searchParams = useSearchParams()

  useEffect(() => { versionRef.current = version }, [version])
  useEffect(() => { isRunningRef.current = isRunning }, [isRunning])

  // 7C.3: persist prompt history whenever it changes
  useEffect(() => {
    if (promptHistory.length > 0) {
      sessionStorage.setItem("archon_prompt_history", JSON.stringify(promptHistory))
    }
  }, [promptHistory])

  // Load project from URL or sessionStorage
  useEffect(() => {
    const urlPid = searchParams.get("pid")
    const storedPid = sessionStorage.getItem("archon_current_project_id")
    const pid = urlPid || storedPid
    const pname = sessionStorage.getItem("archon_project_name")

    if (!pid) return

    // Switching projects — clear all state
    if (urlPid && urlPid !== storedPid) {
      sessionStorage.setItem("archon_current_project_id", urlPid)
      setProjectId(Number(urlPid))
      setProjectName(pname || "my-project")
      setVersion(null)
      setLogs([])
      setPipelineStatus("idle")
      setCurrentStage("pm")
      executionIdRef.current = null
      sessionStorage.removeItem("archon_prompt_history")
      setPromptHistory([])
      return
    }

    const pidNum = Number(pid)
    if (pid) setProjectId(pidNum)
    if (pname) setProjectName(pname)

    const ver = sessionStorage.getItem("archon_current_version")
    const eid = sessionStorage.getItem("archon_current_execution_id")
    const cachedStatus = sessionStorage.getItem("archon_pipeline_status") as typeof pipelineStatus | null
    const cachedStage = sessionStorage.getItem("archon_current_stage") as typeof currentStage | null

    if (ver) setVersion(Number(ver))
    if (eid) {
      executionIdRef.current = Number(eid)
      const cachedLogs = sessionStorage.getItem(`archon_logs_${eid}`)
      if (cachedLogs) {
        try { setLogs(JSON.parse(cachedLogs)) } catch {}
      }
    }
    if (cachedStatus && cachedStatus !== "idle") setPipelineStatus(cachedStatus)
    if (cachedStage) setCurrentStage(cachedStage)

    // 7C.3: restore prompt history
    const cachedHistory = sessionStorage.getItem("archon_prompt_history")
    if (cachedHistory) {
      try { setPromptHistory(JSON.parse(cachedHistory)) } catch {}
    }

    // 7C.1: DB fallback — always sync version/execution from DB on mount
    if (!cachedStatus || cachedStatus === "idle" || cachedStatus === "complete") {
      fetch(`${API_BASE}/api/projects/${pidNum}`)
        .then(r => r.json())
        .then(data => {
          const execs: any[] = data.executions || []
          if (!execs.length) return
          execs.sort((a: any, b: any) => b.version - a.version)
          const latest = execs[0]
          const statusMap: Record<string, typeof pipelineStatus> = {
            success: "complete", completed: "complete",
            error: "failed", failed: "failed",
            running: "running", in_progress: "running",
          }
          const restored = statusMap[latest.status]
          if (restored) {
            setPipelineStatus(restored)
            sessionStorage.setItem("archon_pipeline_status", restored)
          }
          // Always sync to the latest execution so logs key matches
          const resolvedEid = latest.id
          const resolvedVer = latest.version
          if (resolvedVer) {
            setVersion(resolvedVer)
            versionRef.current = resolvedVer
            sessionStorage.setItem("archon_current_version", String(resolvedVer))
          }
          if (resolvedEid) {
            executionIdRef.current = resolvedEid
            sessionStorage.setItem("archon_current_execution_id", String(resolvedEid))
            // Load logs for this execution from cache
            const cachedLogs = sessionStorage.getItem(`archon_logs_${resolvedEid}`)
            if (cachedLogs) {
              try { setLogs(JSON.parse(cachedLogs)) } catch {}
            }
          }
          if (restored === "complete") {
            setCurrentStage("engineer")
            sessionStorage.setItem("archon_current_stage", "engineer")
          }
          // Restart polling if pipeline was mid-run when we navigated away
          if (restored === "running") {
            isRunningRef.current = true
            setIsRunning(true)
            stopPolling()
            pollRef.current = setInterval(pollStatus, POLL_INTERVAL_MS)
          }
        })
        .catch(() => {})
    }
  }, [searchParams])

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [logs])

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  const saveLogs = (newLogs: LogEntry[], eid: number | null) => {
    const id = eid ?? executionIdRef.current
    if (id) sessionStorage.setItem(`archon_logs_${id}`, JSON.stringify(newLogs))
    // Also save by version so Artifacts page can retrieve without knowing execution ID
    const v = versionRef.current
    if (v) sessionStorage.setItem(`archon_logs_v${v}`, JSON.stringify(newLogs))
  }

  const pollStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/execution-status`)
      const data = await res.json()

      const newLogs: LogEntry[] = data.logs || []
      setLogs(newLogs)
      saveLogs(newLogs, null)

      const stage = data.currentStage
      let derivedStage: "pm" | "planner" | "engineer" = "pm"
      if (stage === "engineer") derivedStage = "engineer"
      else if (stage === "planner") derivedStage = "planner"
      else {
        for (let i = newLogs.length - 1; i >= 0; i--) {
          const msg = newLogs[i].message
          if (msg.includes("Loading previous version")) continue
          if (msg.includes("Build Agent")) { derivedStage = "engineer"; break }
          if (msg.includes("Architecture Agent")) { derivedStage = "planner"; break }
        }
      }

      setCurrentStage(derivedStage)
      sessionStorage.setItem("archon_current_stage", derivedStage)

      // 7C.2: accept COMPLETED if we started this run OR backend says done
      if (data.status === "COMPLETED") {
        setCurrentStage("engineer")
        sessionStorage.setItem("archon_current_stage", "engineer")
        setPipelineStatus("complete")
        sessionStorage.setItem("archon_pipeline_status", "complete")
        setIsRunning(false)
        isRunningRef.current = false
        stopPolling()
        if (data.execution_id) {
          const eid = Number(data.execution_id)
          executionIdRef.current = eid
          sessionStorage.setItem("archon_current_execution_id", String(eid))
          saveLogs(newLogs, eid)
        }
        if (data.project_id) {
          sessionStorage.setItem("archon_current_project_id", String(data.project_id))
          setProjectId(data.project_id)
        }
        const v = versionRef.current
        if (v) sessionStorage.setItem("archon_current_version", String(v))
      } else if (data.status === "FAILED") {
        setPipelineStatus("failed")
        sessionStorage.setItem("archon_pipeline_status", "failed")
        setIsRunning(false)
        isRunningRef.current = false
        stopPolling()
      }
    } catch (e) {
      console.error("Poll error:", e)
    }
  }

  const handleSend = async () => {
    if (!inputValue.trim() || isRunning || !projectId) return

    const prompt = inputValue.trim()
    setInputValue("")

    sessionStorage.removeItem("archon_pipeline_status")
    sessionStorage.removeItem("archon_current_stage")
    // Don't clear execution_id here — keep it until the new one arrives so saveLogs works

    isRunningRef.current = true  // set ref synchronously before any async
    setIsRunning(true)
    setPipelineStatus("running")
    sessionStorage.setItem("archon_pipeline_status", "running")
    setCurrentStage("pm")
    sessionStorage.setItem("archon_current_stage", "pm")
    // Don't clear logs here — keep previous run visible until new logs stream in
    setShowAllLogs(false)
    newRunRef.current = true

    const newHistory = [...promptHistory, { role: "user", content: prompt }]
    setPromptHistory(newHistory)
    sessionStorage.setItem("archon_prompt_history", JSON.stringify(newHistory))

    try {
      const res = await fetch(`${API_BASE}/api/projects/${projectId}/iterate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, prompt_history: newHistory }),
      })
      const data = await res.json()

      if (data.version) {
        setVersion(data.version)
        versionRef.current = data.version
        sessionStorage.setItem("archon_current_version", String(data.version))
      }
      if (data.execution_id) {
        executionIdRef.current = Number(data.execution_id)
        sessionStorage.setItem("archon_current_execution_id", String(data.execution_id))
      }

      stopPolling()
      await new Promise(r => setTimeout(r, 800))
      pollRef.current = setInterval(pollStatus, POLL_INTERVAL_MS)
    } catch (e) {
      setPipelineStatus("failed")
      sessionStorage.setItem("archon_pipeline_status", "failed")
      setIsRunning(false)
      isRunningRef.current = false
    }
  }

  useEffect(() => { return () => stopPolling() }, [])

  // Re-sync pipeline state on every mount (handles Versions->Pipeline, Artifacts->Pipeline nav)
  useEffect(() => {
    const pid = sessionStorage.getItem("archon_current_project_id")
    if (!pid) return
    fetch(`${API_BASE}/api/execution-status`)
      .then(r => r.json())
      .then(data => {
        if (data.status === "COMPLETED") {
          setCurrentStage("engineer")
          setPipelineStatus("complete")
          sessionStorage.setItem("archon_pipeline_status", "complete")
          sessionStorage.setItem("archon_current_stage", "engineer")
          setIsRunning(false)
          isRunningRef.current = false
          stopPolling()
        } else if (data.status === "RUNNING") {
          setCurrentStage(data.currentStage || "pm")
          setPipelineStatus("running")
          sessionStorage.setItem("archon_pipeline_status", "running")
          if (!pollRef.current) {
            isRunningRef.current = true
            setIsRunning(true)
            pollRef.current = setInterval(pollStatus, POLL_INTERVAL_MS)
          }
        }
        if (data.logs?.length) setLogs(data.logs)
      })
      .catch(() => {})
  }, [])

  // Check if a different project is already building
  const checkGlobalBlock = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/execution-status`)
      const data = await res.json()
      if (data.status === "RUNNING" && data.project_id && data.project_id !== projectId) {
        setGloballyBlocked(true)
        setBlockingProjectId(data.project_id)
      } else {
        setGloballyBlocked(false)
        setBlockingProjectId(null)
      }
    } catch {}
  }

  useEffect(() => {
    if (projectId && !isRunning) checkGlobalBlock()
  }, [projectId, isRunning])

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
    return (
      d.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" }) +
      "." + String(d.getMilliseconds()).padStart(3, "0")
    )
  }

  const statusLabel = {
    idle: null,
    running: <span className="flex items-center gap-1.5 text-xs text-info bg-info/10 px-2.5 py-1 rounded-full font-medium"><Loader2 className="h-3 w-3 animate-spin" />Building...</span>,
    complete: <span className="flex items-center gap-1.5 text-xs text-success bg-success/10 px-2.5 py-1 rounded-full font-medium">Complete</span>,
    failed: <span className="flex items-center gap-1.5 text-xs text-destructive bg-destructive/10 px-2.5 py-1 rounded-full font-medium">Failed</span>,
  }[pipelineStatus]

  return (
    <div className="flex-1 flex flex-col">
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
                  <div className={`flex-1 rounded-lg border p-4 transition-all duration-300 ${
                    status === "running" ? "border-info bg-info/5 shadow-sm ring-1 ring-info/30"
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
              <div key={log.id} className="flex items-start gap-3 py-1 hover:bg-muted/30 px-2 -mx-2 rounded">
                <span className="text-muted-foreground/60 shrink-0 w-28">{formatTime(log.timestamp)}</span>
                <span className="text-foreground/70">{log.message}</span>
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        </div>
      </div>

      <div className="border-t border-border bg-card px-6 py-3">
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground font-mono shrink-0">{projectName} {">"}</span>
          <div className="flex-1 relative">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleSend() }}
              placeholder={
                !projectId ? "Select a project first..." :
                globallyBlocked ? `Another project (ID: ${blockingProjectId}) is building. Wait for it to finish.` :
                "What would you like to build?"
              }
              disabled={!projectId || isRunning || globallyBlocked}
              className="w-full h-9 rounded-md border border-input bg-background pl-3 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring font-mono disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || isRunning || !projectId || globallyBlocked}
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

