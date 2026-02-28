"use client"

import { useState, useRef, useEffect } from "react"
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
  Bot,
  User,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Cpu,
  Hash,
  DollarSign,
  Clock,
} from "lucide-react"
import { useLanguage } from "@/contexts/LanguageContext"

const API_BASE = "http://localhost:5000"
const POLL_INTERVAL_MS = 1500
type AgentStatus = "pending" | "running" | "complete"

type LogEntry = {
  id: string
  timestamp: number
  message: string
  type: string
}

type ChatMessage = {
  id: string
  role: "user" | "archon"
  content: string
  timestamp: number
}

function AgentStatusIcon({ status }: { status: AgentStatus }) {
  if (status === "complete") return <CheckCircle2 className="h-5 w-5 text-success" />
  if (status === "running") return <Loader2 className="h-5 w-5 text-info animate-spin" />
  return <Circle className="h-5 w-5 text-muted-foreground/40" />
}

function AgentStatusLabel({ status }: { status: AgentStatus }) {
  const { t } = useLanguage()
  if (status === "complete") return <span className="text-xs font-medium text-success">{t("done")}</span>
  if (status === "running") return <span className="text-xs font-medium text-info">{t("building")}</span>
  return <span className="text-xs font-medium text-muted-foreground">{t("pending")}</span>
}

export function PipelineRun() {
  const { t } = useLanguage()
  const [inputValue, setInputValue] = useState("")
  const [projectId, setProjectId] = useState<number | null>(null)
  const [projectName, setProjectName] = useState("my-project")
  const [version, setVersion] = useState<number | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [pipelineStatus, setPipelineStatus] = useState<"idle" | "running" | "complete" | "failed">("idle")
  const [currentStage, setCurrentStage] = useState<"pm" | "planner" | "engineer">("pm")
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [promptHistory, setPromptHistory] = useState<{ role: string; content: string }[]>([])
  const [showAllLogs, setShowAllLogs] = useState(false)
  const [micState, setMicState] = useState<"idle" | "recording" | "processing">("idle")
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const [ttsState, setTtsState] = useState<Record<string, "idle" | "loading" | "playing">>({})
  const ttsAudioRef = useRef<HTMLAudioElement | null>(null)
  const ttsPlayingIdRef = useRef<string | null>(null)
  const [globallyBlocked, setGloballyBlocked] = useState(false)
  const [blockingProjectId, setBlockingProjectId] = useState<number | null>(null)
  const [buildDetails, setBuildDetails] = useState<{
    model: string; tokensUsed: string; estCost: string; duration: string
  } | null>(null)
  const logsEndRef = useRef<HTMLDivElement>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const pollRef = useRef<NodeJS.Timeout | null>(null)
  const executionIdRef = useRef<number | null>(null)
  const versionRef = useRef<number | null>(null)
  const isRunningRef = useRef(false)
  const newRunRef = useRef(false)

  const searchParams = useSearchParams()

  useEffect(() => { versionRef.current = version }, [version])
  useEffect(() => { isRunningRef.current = isRunning }, [isRunning])

  useEffect(() => {
    if (promptHistory.length > 0) {
      sessionStorage.setItem("archon_prompt_history", JSON.stringify(promptHistory))
    }
  }, [promptHistory])

  useEffect(() => {
    if (messages.length > 0) {
      const pid = sessionStorage.getItem("archon_current_project_id")
      if (pid) sessionStorage.setItem(`archon_messages_${pid}`, JSON.stringify(messages))
    }
  }, [messages])

  useEffect(() => {
    const urlPid = searchParams.get("pid")
    const storedPid = sessionStorage.getItem("archon_current_project_id")
    const pid = urlPid || storedPid
    const pname = sessionStorage.getItem("archon_project_name")

    if (!pid) return

    if (urlPid && urlPid !== storedPid) {
      sessionStorage.setItem("archon_current_project_id", urlPid)
      setProjectId(Number(urlPid))
      setProjectName(pname || "my-project")
      setVersion(null)
      setLogs([])
      setMessages([])
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

    const cachedHistory = sessionStorage.getItem("archon_prompt_history")
    if (cachedHistory) {
      try { setPromptHistory(JSON.parse(cachedHistory)) } catch {}
    }

    // Always clear messages first, then load only this project's messages
    setMessages([])
    const cachedMsgs = sessionStorage.getItem(`archon_messages_${pidNum}`)
    if (cachedMsgs) {
      try { setMessages(JSON.parse(cachedMsgs)) } catch {}
    }

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
            const cachedLogs = sessionStorage.getItem(`archon_logs_${resolvedEid}`)
            if (cachedLogs) {
              try { setLogs(JSON.parse(cachedLogs)) } catch {}
            }
          }
          if (restored === "complete") {
            setCurrentStage("engineer")
            sessionStorage.setItem("archon_current_stage", "engineer")
          }
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



  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  const saveLogs = (newLogs: LogEntry[], eid: number | null) => {
    const id = eid ?? executionIdRef.current
    if (id) sessionStorage.setItem(`archon_logs_${id}`, JSON.stringify(newLogs))
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

  const handleTts = async (msgId: string, text: string) => {
    // Stop current playback if any
    if (ttsAudioRef.current) {
      ttsAudioRef.current.pause()
      ttsAudioRef.current = null
    }
    const prevId = ttsPlayingIdRef.current
    ttsPlayingIdRef.current = null
    if (prevId) setTtsState(s => ({ ...s, [prevId]: "idle" }))

    // If clicking the same message that was playing, just stop
    if (prevId === msgId) return

    setTtsState(s => ({ ...s, [msgId]: "loading" }))
    try {
      const res = await fetch(`${API_BASE}/api/watson/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      })
      if (!res.ok) throw new Error("TTS request failed")
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      ttsAudioRef.current = audio
      ttsPlayingIdRef.current = msgId
      setTtsState(s => ({ ...s, [msgId]: "playing" }))
      audio.onended = () => {
        ttsPlayingIdRef.current = null
        ttsAudioRef.current = null
        URL.revokeObjectURL(url)
        setTtsState(s => ({ ...s, [msgId]: "idle" }))
      }
      audio.play()
    } catch (e) {
      console.error("TTS error:", e)
      setTtsState(s => ({ ...s, [msgId]: "idle" }))
    }
  }


  const handleSend = async () => {
    if (!inputValue.trim() || isRunning || !projectId) return

    const prompt = inputValue.trim()
    setInputValue("")

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      role: "user",
      content: prompt,
      timestamp: Date.now(),
    }
    setMessages(prev => [...prev, userMsg])

    try {
      // Hit /chat first — fast classify, never touches DB or versions
      const chatRes = await fetch(`${API_BASE}/api/projects/${projectId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: prompt }),
      })
      const chatData = await chatRes.json()

      if (chatData.response_type === "chat") {
        const archonMsg: ChatMessage = {
          id: `msg-${Date.now()}-archon`,
          role: "archon",
          content: chatData.message,
          timestamp: Date.now(),
        }
        setMessages(prev => [...prev, archonMsg])
        return  // Stop here — no pipeline, no version created
      }

      // It is a build — add a system message then call /iterate
      const buildMsg: ChatMessage = {
        id: `msg-${Date.now()}-archon`,
        role: "archon",
        content: "Got it! Starting the build now... ⚡",
        timestamp: Date.now(),
      }
      setMessages(prev => [...prev, buildMsg])

      const newHistory = [...promptHistory, { role: "user", content: prompt }]
      setPromptHistory(newHistory)
      sessionStorage.setItem("archon_prompt_history", JSON.stringify(newHistory))

      sessionStorage.removeItem("archon_pipeline_status")
      sessionStorage.removeItem("archon_current_stage")

      isRunningRef.current = true
      setIsRunning(true)
      setPipelineStatus("running")
      sessionStorage.setItem("archon_pipeline_status", "running")
      setCurrentStage("pm")
      sessionStorage.setItem("archon_current_stage", "pm")
      setShowAllLogs(false)
      newRunRef.current = true

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

  const handleMic = async () => {
    if (micState === "idle") {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        const recorder = new MediaRecorder(stream)
        audioChunksRef.current = []
        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunksRef.current.push(e.data)
        }
        recorder.onstop = async () => {
          stream.getTracks().forEach(t => t.stop())
          setMicState("processing")
          const blob = new Blob(audioChunksRef.current, { type: "audio/webm" })
          const formData = new FormData()
          formData.append("audio", blob, "recording.webm")
          try {
            const res = await fetch(`${API_BASE}/api/watson/stt`, {
              method: "POST",
              body: formData,
            })
            const data = await res.json()
            if (data.transcript) setInputValue(data.transcript)
          } catch (err) {
            console.error("STT error:", err)
          }
          setMicState("idle")
        }
        recorder.start()
        mediaRecorderRef.current = recorder
        setMicState("recording")
      } catch (err) {
        console.error("Mic access denied:", err)
      }
    } else if (micState === "recording") {
      mediaRecorderRef.current?.stop()
    }
  }

  useEffect(() => { return () => stopPolling() }, [])

  useEffect(() => {
    const pid = sessionStorage.getItem("archon_current_project_id")
    if (!pid) return
    fetch(`${API_BASE}/api/execution-status`)
      .then(r => r.json())
      .then(data => {
        // Only restore state if this pipeline belongs to THIS project
        if (data.project_id && Number(data.project_id) !== Number(pid)) return
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

  useEffect(() => {
    if (!projectId || !version) { setBuildDetails(null); return }
    fetch(`http://localhost:5000/api/projects/${projectId}/versions`)
      .then(r => r.json())
      .then((data: any) => {
        const list = Array.isArray(data) ? data : data.versions || []
        const v = list.find((x: any) => x.version === version)
        if (!v) { setBuildDetails(null); return }
        const dur = v.duration_seconds
        let durStr = "—"
        if (dur != null) {
          const mins = Math.floor(dur / 60)
          const secs = Math.round(dur % 60)
          durStr = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
        }
        setBuildDetails({
          model: v.model_used || "—",
          tokensUsed: v.tokens_used != null ? v.tokens_used.toLocaleString() : "—",
          estCost: v.estimated_cost != null ? `${v.estimated_cost.toFixed(4)}` : "—",
          duration: durStr,
        })
      })
      .catch(() => setBuildDetails(null))
  }, [projectId, version])

  const agentStages = [
    { key: "pm", name: t("requirementsAgent"), role: t("understandsRequest") },
    { key: "planner", name: t("architectureAgent"), role: t("plansTheBuild") },
    { key: "engineer", name: t("buildAgent"), role: t("writesYourCode") },
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
    return d.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit" })
  }

  const statusLabel = {
    idle: null,
    running: <span className="flex items-center gap-1.5 text-xs text-info bg-info/10 px-2.5 py-1 rounded-full font-medium"><Loader2 className="h-3 w-3 animate-spin" />{t("building")}</span>,
    complete: <span className="flex items-center gap-1.5 text-xs text-success bg-success/10 px-2.5 py-1 rounded-full font-medium">{t("complete")}</span>,
    failed: <span className="flex items-center gap-1.5 text-xs text-destructive bg-destructive/10 px-2.5 py-1 rounded-full font-medium">{t("failed")}</span>,
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

      <div className="flex-1 flex flex-col p-6 gap-4 overflow-auto">
        <div className="bg-card border border-border rounded-lg p-5">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">{t("agentPipeline")}</h3>
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

        {pipelineStatus === "complete" && buildDetails && (
          <div className="flex items-center divide-x divide-border text-xs font-mono">
            {[
              { icon: Cpu, label: t("model"), value: buildDetails.model },
              { icon: Hash, label: t("tokensUsed"), value: buildDetails.tokensUsed },
              { icon: DollarSign, label: t("estCost"), value: buildDetails.estCost },
              { icon: Clock, label: t("duration"), value: buildDetails.duration },
            ].map(({ icon: Icon, label, value }) => (
              <div key={label} className="flex items-center gap-1.5 px-3 first:pl-0">
                <Icon className="h-3 w-3 text-muted-foreground" />
                <span className="text-muted-foreground">{label}</span>
                <span className="font-medium text-foreground">{value}</span>
              </div>
            ))}
          </div>
        )}

        <div className="flex-1 bg-card border border-border rounded-lg flex flex-col min-h-0">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
            <Bot className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold text-foreground">{t("conversation")}</h3>
          </div>
          <div className="flex-1 overflow-auto p-4 flex flex-col gap-3">
            {messages.length === 0 && (
              <p className="text-sm text-muted-foreground italic text-center mt-4">
                {projectId ? t("askOrBuild") : t("selectProjectFirst")}
              </p>
            )}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex items-start gap-2 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
              >
                <div className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${
                  msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                }`}>
                  {msg.role === "user" ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
                </div>
                <div className={`max-w-[75%] rounded-xl px-4 py-2.5 text-sm ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground rounded-tr-sm"
                    : "bg-muted text-foreground rounded-tl-sm"
                }`}>
                  {msg.content}
                  <div className="text-xs mt-1 opacity-60">
                    {formatTime(msg.timestamp)}
                  </div>
                </div>
                {msg.role === "archon" && (
                  <button
                    onClick={() => handleTts(msg.id, msg.content)}
                    className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-all duration-200 ${
                      ttsState[msg.id] === "playing"
                        ? "bg-primary text-primary-foreground shadow-md scale-110"
                        : "bg-muted/60 text-muted-foreground hover:bg-primary hover:text-primary-foreground hover:scale-110"
                    }`}
                    aria-label="Play message audio"
                  >
                    {ttsState[msg.id] === "loading" ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : ttsState[msg.id] === "playing" ? (
                      <VolumeX className="h-3.5 w-3.5" />
                    ) : (
                      <Volume2 className="h-3.5 w-3.5" />
                    )}
                  </button>
                )}
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
        </div>

        {logs.length > 0 && (
          <div className="bg-card border border-border rounded-lg flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <div className="flex items-center gap-2">
                <Terminal className="h-4 w-4 text-muted-foreground" />
                <h3 className="text-sm font-semibold text-foreground">{t("liveOutput")}</h3>
                <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                  {logs.length} {t("entries")}
                </span>
              </div>
              {!showAllLogs && logs.length > 6 && (
                <button onClick={() => setShowAllLogs(true)} className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors">
                  Show all <ChevronDown className="h-3 w-3" />
                </button>
              )}
            </div>
            <div className="p-4 font-mono text-xs max-h-48 overflow-auto">
              {displayedLogs.map((log) => (
                <div key={log.id} className="flex items-start gap-3 py-1 hover:bg-muted/30 px-2 -mx-2 rounded">
                  <span className="text-muted-foreground/60 shrink-0 w-14">
                    {new Date(log.timestamp).toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                  </span>
                  <span className="text-foreground/70">{log.message}</span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>
        )}
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
                !projectId ? t("selectProjectFirst") :
                globallyBlocked ? `Another project (ID: ${blockingProjectId}) is building. Wait for it to finish.` :
                isRunning ? t("building") :
                t("whatToBUILD")
              }
              disabled={!projectId || isRunning || globallyBlocked}
              className="w-full h-9 rounded-md border border-input bg-background pl-3 pr-20 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring font-mono disabled:opacity-50"
            />
            <div className="absolute right-1.5 top-1/2 -translate-y-1/2 flex items-center gap-1">
              <button
                onClick={handleMic}
                disabled={isRunning || !projectId || micState === "processing"}
                className={`p-1.5 rounded transition-colors disabled:opacity-40 ${
                  micState === "recording"
                    ? "bg-destructive text-destructive-foreground animate-pulse"
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                }`}
                aria-label={micState === "recording" ? "Stop recording" : "Start voice input"}
              >
                {micState === "processing" ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : micState === "recording" ? (
                  <MicOff className="h-3.5 w-3.5" />
                ) : (
                  <Mic className="h-3.5 w-3.5" />
                )}
              </button>
              <button
                onClick={handleSend}
                disabled={!inputValue.trim() || isRunning || !projectId || globallyBlocked}
                className="p-1.5 rounded bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-40"
                aria-label="Send message"
              >
                <Send className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}








