"use client"

import { useState, useRef, useEffect } from "react"
import { useSearchParams } from "next/navigation"
import {
  CheckCircle2,
  Circle,
  Loader2,
  XCircle,
  ArrowRight,
  Send,
  Terminal,
  ChevronDown,


  User,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Cpu,
  Hash,
  Clock,
  X,
} from "lucide-react"
import { useLanguage } from "@/contexts/LanguageContext"
import { useNotificationSound } from "@/hooks/useNotificationSound"

const API_BASE = "http://localhost:5000"
const POLL_INTERVAL_MS = 1500
type AgentStatus = "pending" | "running" | "complete" | "failed"

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
  if (status === "failed") return <XCircle className="h-5 w-5 text-destructive" />
  if (status === "running") return <Loader2 className="h-5 w-5 text-info animate-spin" />
  return <Circle className="h-5 w-5 text-muted-foreground/40" />
}

function AgentStatusLabel({ status }: { status: AgentStatus }) {
  const { t } = useLanguage()
  if (status === "complete") return <span className="text-xs font-medium text-success">{t("done")}</span>
  if (status === "failed") return <span className="text-xs font-medium text-destructive">{t("failed")}</span>
  if (status === "running") return <span className="text-xs font-medium text-info">{t("building")}</span>
  return <span className="text-xs font-medium text-muted-foreground">{t("pending")}</span>
}

export function PipelineRun() {
  const { t } = useLanguage()
  const { playSuccess, playFailure } = useNotificationSound()
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
    model: string; creditsUsed: string; duration: string
  } | null>(null)
  const logsEndRef = useRef<HTMLDivElement>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const pollRef = useRef<NodeJS.Timeout | null>(null)
  const executionIdRef = useRef<number | null>(null)
  const versionRef = useRef<number | null>(null)
  const isRunningRef = useRef(false)
  const newRunRef = useRef(false)
  const buildStartTimeRef = useRef<number | null>(null)
  const [isStuck, setIsStuck] = useState(false)

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
      if (pid) {
        sessionStorage.setItem(`archon_messages_${pid}`, JSON.stringify(messages))
        // Always persist to DB — including mid-build so Enterprise/Studio stay in sync
        fetch(`${API_BASE}/api/projects/${pid}/chat-messages`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ messages }),
        }).catch(() => {}) // non-fatal
      }
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
      // Fetch the real project name from API instead of trusting stale sessionStorage
      fetch(`http://localhost:5000/api/projects/${urlPid}`)
        .then(r => r.json())
        .then(data => {
          const name = data.name || data.project?.name || "my-project"
          setProjectName(name)
          sessionStorage.setItem("archon_project_name", name)
        })
        .catch(() => setProjectName(pname || "my-project"))
      setVersion(null)
      setLogs([])
      setPipelineStatus("idle")
      setCurrentStage("pm")
      executionIdRef.current = null
      sessionStorage.removeItem("archon_prompt_history")
      setPromptHistory([])
      // Load messages from DB — but first check sessionStorage for the NEW project
      // (messages for urlPid may already exist from a previous visit)
      const cachedForNewPid = sessionStorage.getItem(`archon_messages_${urlPid}`)
      if (cachedForNewPid) {
        try {
          const parsed = JSON.parse(cachedForNewPid)
          if (Array.isArray(parsed) && parsed.length > 0) {
            setMessages(parsed)
          } else {
            setMessages([])
          }
        } catch { setMessages([]) }
      } else {
        setMessages([])
      }
      fetch(`${API_BASE}/api/projects/${urlPid}/chat-history`)
        .then(r => r.json())
        .then((data: any) => {
          if (!Array.isArray(data) || data.length === 0) return
          const normalized = data.map((m: any, i: number) => ({
            id: m.id || `db-${i}`,
            role: m.role === "assistant" ? "archon" : m.role,
            content: m.content,
            timestamp: m.timestamp || Date.now(),
          }))
          setMessages(normalized)
          sessionStorage.setItem(`archon_messages_${urlPid}`, JSON.stringify(normalized))
        })
        .catch(() => {})
      // Also restore pipeline status for the new project
      fetch(`${API_BASE}/api/projects/${urlPid}`)
        .then(r => r.json())
        .then(data => {
          const execs: any[] = data.executions || []
          if (!execs.length) return
          execs.sort((a: any, b: any) => b.version - a.version)
          const latest = execs[0]
          const statusMap: Record<string, "idle" | "running" | "complete" | "failed"> = {
            success: "complete", completed: "complete",
            error: "failed", failed: "failed",
            running: "running", in_progress: "running",
          }
          const restored = statusMap[latest.status]
          if (restored) {
            setPipelineStatus(restored)
            sessionStorage.setItem("archon_pipeline_status", restored)
          }
          if (restored === "complete") {
            setCurrentStage("engineer")
            sessionStorage.setItem("archon_current_stage", "engineer")
          }
          if (latest.version) {
            setVersion(latest.version)
            versionRef.current = latest.version
            sessionStorage.setItem("archon_current_version", String(latest.version))
          }
        })
        .catch(() => {})
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
    // Apply cached status immediately (synchronous) so cards don't flash Pending
    // DB restore below will overwrite this with authoritative data
    if (cachedStatus === "complete") {
      setPipelineStatus("complete")
      setCurrentStage("engineer")
    } else if (cachedStatus === "failed") {
      setPipelineStatus("failed")
    }
    if (cachedStage && cachedStatus === "complete") setCurrentStage("engineer")

    const cachedHistory = sessionStorage.getItem("archon_prompt_history")
    if (cachedHistory) {
      try { setPromptHistory(JSON.parse(cachedHistory)) } catch {}
    }

    // Always load from DB — source of truth shared with Enterprise
    setMessages([])
    fetch(`${API_BASE}/api/projects/${pidNum}/chat-history`)
      .then(r => r.json())
      .then((data: any) => {
        if (!Array.isArray(data) || data.length === 0) return
        const normalized = data.map((m: any, i: number) => ({
          id: m.id || `db-${i}`,
          role: m.role === "assistant" ? "archon" : m.role,
          content: m.content,
          timestamp: m.timestamp || Date.now(),
        }))
        setMessages(normalized)
        sessionStorage.setItem(`archon_messages_${pidNum}`, JSON.stringify(normalized))
      })
      .catch(() => {})

    // Always restore from DB — DB is source of truth, don't trust stale sessionStorage status
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
            // Eagerly fetch build details when restoring completed state
            if (resolvedVer) {
              fetch(`${API_BASE}/api/projects/${pidNum}/versions`)
                .then(r => r.json())
                .then((vdata: any) => {
                  const list = Array.isArray(vdata) ? vdata : vdata.versions || []
                  const v = list.find((x: any) => x.version === resolvedVer)
                  if (!v) return
                  const dur = v.duration_seconds
                  let durStr = "—"
                  if (dur != null) {
                    const mins = Math.floor(dur / 60)
                    const secs = Math.round(dur % 60)
                    durStr = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
                  }
                  setBuildDetails({
                    model: v.model_used || "—",
                    creditsUsed: v.credits_used != null ? `${v.credits_used} credits` : "—",
                    duration: durStr,
                  })
                })
                .catch(() => {})
              // Restore logs from DB after restart
              fetch(`${API_BASE}/api/projects/${pidNum}/versions/${resolvedVer}/logs`)
                .then(r => r.json())
                .then((logData: any) => {
                  const entries = logData.logs || logData
                  if (Array.isArray(entries) && entries.length > 0) {
                    const restored = entries.map((l: any, i: number) => ({
                      id: l.id || `log-${i}`,
                      timestamp: l.timestamp || 0,
                      message: l.message || String(l),
                      type: l.type || "info",
                    }))
                    setLogs(restored)
                  }
                })
                .catch(() => {})
            }
          }
          if (restored === "running") {
            isRunningRef.current = true
            setIsRunning(true)
            stopPolling()
            pollRef.current = setInterval(pollStatus, POLL_INTERVAL_MS)
          }
        })
        .catch(() => {})
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
        playSuccess()
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
        // Save messages now — new execution is active head
        const savePid = data.project_id || sessionStorage.getItem("archon_current_project_id")
        if (savePid) {
          setMessages(prev => {
            fetch(`${API_BASE}/api/projects/${savePid}/chat-messages`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ messages: prev }),
            }).catch(() => {})
            return prev
          })
        }
      } else if (data.status === "FAILED") {
        playFailure()
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
    if (!inputValue.trim() || !projectId) return
    if (isRunning) return

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

      // Build intent — check global lock, show clean reply
      if (globallyBlocked) {
        const replyMsg: ChatMessage = {
          id: `msg-${Date.now()}-archon`,
          role: "archon",
          content: "A build is already in progress. Send this again when it finishes.",
          timestamp: Date.now(),
        }
        setMessages(prev => [...prev, replyMsg])
        return
      }

      // It is a build — add a system message then call /iterate
      const buildMsg: ChatMessage = {
        id: `msg-${Date.now()}-archon`,
        role: "archon",
        content: "Got it! Starting the build now.",
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

  // Track build start time and detect stuck builds (> 5 min)
  useEffect(() => {
    if (isRunning && !buildStartTimeRef.current) {
      buildStartTimeRef.current = Date.now()
    }
    if (!isRunning) {
      buildStartTimeRef.current = null
      setIsStuck(false)
    }
  }, [isRunning])

  useEffect(() => {
    if (!isRunning) return
    const interval = setInterval(() => {
      if (buildStartTimeRef.current && Date.now() - buildStartTimeRef.current > 8 * 60 * 1000) {
        setIsStuck(true)
      }
    }, 10_000)
    return () => clearInterval(interval)
  }, [isRunning])

  // Auto-scroll chat to bottom when messages load or change
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView()
    }
  }, [messages])

  useEffect(() => {
    const pid = sessionStorage.getItem("archon_current_project_id")
    if (!pid) return
    fetch(`${API_BASE}/api/execution-status`)
      .then(r => r.json())
      .then(data => {
        // ONLY act on execution-status if it belongs to THIS project
        // If project_id is null or different, ignore it entirely — DB restore handles the rest
        if (!data.project_id || Number(data.project_id) !== Number(pid)) {
          // Don't touch pipelineStatus — DB restore useEffect will set it correctly
          return
        }
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
        } else if (data.status === "FAILED") {
          // Only apply FAILED if it's definitively this project's failure
          setPipelineStatus("failed")
          setIsRunning(false)
          isRunningRef.current = false
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
          creditsUsed: v.credits_used != null ? `${v.credits_used} credits` : "—",
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
    if (pipelineStatus === "failed") {
      // All agents before current are done, current is failed, rest are pending
      if (agentIdx < currentIdx) return "complete"
      if (agentIdx === currentIdx) return "failed"
      return "pending"
    }
    if (pipelineStatus === "running") {
      if (agentIdx < currentIdx) return "complete"
      if (agentIdx === currentIdx) return "running"
      return "pending"
    }
    // idle — check if currentStage suggests we actually finished (engineer stage = all done)
    if (pipelineStatus === "idle" && currentStage === "engineer") return "complete"
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
            <svg className="h-4 w-4 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
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
              { icon: Hash, label: t("creditsUsed"), value: buildDetails.creditsUsed },
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

        <div className="bg-card border border-border rounded-lg flex flex-col">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
            <svg className="h-4 w-4 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
            <h3 className="text-sm font-semibold text-foreground">{t("conversation")}</h3>
          </div>
          <div className="p-4 flex flex-col gap-3 max-h-[55vh] overflow-y-auto">
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
                  {msg.role === "user" ? <User className="h-3.5 w-3.5" /> : <svg className="h-3.5 w-3.5 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>}
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
                  <span className="text-foreground/70">{log.message}</span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>
        )}
      </div>

      {/* Build-lock banner */}
      {globallyBlocked && (
        <div className="border-t border-border bg-muted/40 px-6 py-2 flex items-center gap-2 text-xs text-muted-foreground">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-blue-400 flex-shrink-0" />
          <span>
            {blockingProjectId ? `Project #${blockingProjectId}` : "Another project"} is building — chat is available while you wait.
          </span>
        </div>
      )}
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
                isRunning ? t("building") :
                t("whatToBUILD")
              }
              disabled={!projectId || isRunning}
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
              {isStuck && projectId && (
                <button
                  onClick={async () => {
                    try {
                      await fetch(`${API_BASE}/api/projects/${projectId}/reset-build`, { method: "POST" })
                    } catch {}
                    stopPolling()
                    setIsRunning(false)
                    isRunningRef.current = false
                    buildStartTimeRef.current = null
                    setIsStuck(false)
                    setPipelineStatus("failed")
                    sessionStorage.setItem("archon_pipeline_status", "failed")
                  }}
                  className="bg-red-500 hover:bg-red-600 text-white font-medium rounded-md px-4 py-2 text-sm flex items-center gap-1.5 transition-colors"
                  title="Reset stuck build"
                >
                  <X className="h-3 w-3" />
                  Reset
                </button>
              )}
              <button
                onClick={handleSend}
                disabled={!inputValue.trim() || isRunning || !projectId}
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








