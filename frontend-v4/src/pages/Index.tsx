import { useState, useEffect, useRef, useCallback } from "react";
import { Navbar } from "@/components/Navbar";
import { PipelineStatus } from "@/components/PipelineStatus";
import { BuildDetailsCard } from "@/components/BuildDetailsCard";
import { StatsBar } from "@/components/StatsBar";
import { ProjectTable } from "@/components/ProjectTable";
import { WelcomeBanner } from "@/components/WelcomeBanner";
import { ActivityFeed } from "@/components/ActivityFeed";
import { NewProjectModal } from "@/components/NewProjectModal";
import { VersionsView } from "@/components/VersionsView";
import { ArtifactsView } from "@/components/ArtifactsView";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  useProjects,
  usePipelineStatus,
  projectChat,
  iterateProject,
  fetchChatHistory,
  saveChatMessages,
  fetchVersions,
  fetchLogs,
  type ChatMessage,
} from "@/services/api";
import { Search, Plus, Trash2, Zap, Mic, MicOff, Send, Volume2, VolumeX, Filter, Loader2, AlertCircle, X } from "lucide-react";

const Index = () => {
  const [activeTab, setActiveTab] = useState(() => localStorage.getItem("archon_active_tab") || "projects");
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [artifactTab, setArtifactTab] = useState<"brief" | "plan" | "code">("brief");
  const [showNewProject, setShowNewProject] = useState(false);
  const [buildRefreshKey, setBuildRefreshKey] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const { t } = useLanguage();
  const { projects, loading, error, stats: projectStats } = useProjects();

  // Restore active tab from URL query param (set by Studio when switching)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tabFromUrl = params.get('tab');
    if (tabFromUrl) {
      setActiveTab(tabFromUrl);
    }
    const projectIdFromUrl = params.get('projectId');
    if (projectIdFromUrl) {
      setSelectedProjectId(parseInt(projectIdFromUrl));
    }
    if (tabFromUrl || projectIdFromUrl) {
      window.history.replaceState({}, '', '/');
    }
  }, []);

  // Persist active tab to localStorage
  useEffect(() => {
    localStorage.setItem("archon_active_tab", activeTab);
  }, [activeTab]);

  // Pipeline state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [sending, setSending] = useState(false);
  const [pipelineError, setPipelineError] = useState<string | null>(null);
  const [globalBuildBlocked, setGlobalBuildBlocked] = useState(false);
  const [blockingProjectId, setBlockingProjectId] = useState<number | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const activeProjectRef = useRef<number | null>(null);
  const [micState, setMicState] = useState<"idle" | "recording" | "processing">("idle");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const [ttsState, setTtsState] = useState<Record<string, "idle" | "loading" | "playing">>({});
  const ttsAudioRef = useRef<HTMLAudioElement | null>(null);
  const ttsPlayingIdRef = useRef<string | null>(null);
  const sendingRef = useRef(false);
  const buildStartTimeRef = useRef<number | null>(null);
  const [isStuck, setIsStuck] = useState(false);
  const pipeline = usePipelineStatus(selectedProjectId, activeTab === "pipeline" && sending);
  // Restore pipeline card state from DB when no live build is running
  const [historicalStatus, setHistoricalStatus] = useState<string | null>(null);
  const [historicalLogs, setHistoricalLogs] = useState<Array<{ id: string; timestamp: number; message: string }>>([]);

  // Track build start time and detect stuck builds (> 5 min)
  useEffect(() => {
    if (sending && !buildStartTimeRef.current) {
      buildStartTimeRef.current = Date.now();
    }
    if (!sending) {
      buildStartTimeRef.current = null;
      setIsStuck(false);
    }
  }, [sending]);

  useEffect(() => {
    if (!sending) return;
    const interval = setInterval(() => {
      if (buildStartTimeRef.current && Date.now() - buildStartTimeRef.current > 8 * 60 * 1000) {
        setIsStuck(true);
      }
    }, 10_000);
    return () => clearInterval(interval);
  }, [sending]);

  useEffect(() => {
    setHistoricalStatus(null); // reset synchronously BEFORE async fetch to prevent bleed
    setHistoricalLogs([]); // reset logs too
    setGlobalBuildBlocked(false);
    setBlockingProjectId(null);
    if (!selectedProjectId) return;
    let cancelled = false;
    // On project switch, verify build is actually running — clear stuck state and update block status
    fetch("http://localhost:5000/api/execution-status")
      .then(r => r.json())
      .then(data => {
        if (cancelled) return;
        const isActuallyRunning = data.status === "RUNNING" && data.project_id === selectedProjectId;
        if (!isActuallyRunning) {
          setSending(false);
          sendingRef.current = false;
        } else {
          // This project IS the one currently building — keep ref in sync
          setSending(true);
          sendingRef.current = true;
        }
        // Update global block state based on fresh status
        if (data.status === "RUNNING" && data.project_id !== selectedProjectId) {
          setGlobalBuildBlocked(true);
          setBlockingProjectId(data.project_id);
        } else {
          // Not blocked — another project isn't building (or this project is the one building)
          setGlobalBuildBlocked(false);
          setBlockingProjectId(null);
        }
      })
      .catch(() => {
        setSending(false);
        setGlobalBuildBlocked(false);
        setBlockingProjectId(null);
      });
    fetchVersions(selectedProjectId).then((versions) => {
      if (cancelled || versions.length === 0) return;
      // versions are returned newest-first from API
      const latest = versions[0];
      const latestStatus = latest.status?.toUpperCase() || null;
      setHistoricalStatus(latestStatus);
      // If DB shows running, re-enable sending so polling restarts
      if (latestStatus === "RUNNING" || latestStatus === "IN_PROGRESS") {
        setSending(true);
        sendingRef.current = true;
      }
      // Load historical logs for completed/failed projects (not currently building)
      if (!pipeline.running) {
        fetchLogs(selectedProjectId, latest.version).then((logStrings) => {
          if (cancelled) return;
          setHistoricalLogs(logStrings.map((msg, i) => ({
            id: `hist-${i}`,
            timestamp: 0,
            message: msg,
          })));
        });
      }
    });
    return () => { cancelled = true; };
  }, [selectedProjectId]);

  // Auto-dismiss build-lock banner when blocking project finishes
  useEffect(() => {
    if (!globalBuildBlocked) return;
    const interval = setInterval(() => {
      fetch("http://localhost:5000/api/execution-status")
        .then(r => r.json())
        .then(data => {
          if (data.status !== "RUNNING") {
            setGlobalBuildBlocked(false);
            setBlockingProjectId(null);
          }
        })
        .catch(() => {});
    }, 2000);
    return () => clearInterval(interval);
  }, [globalBuildBlocked]);

  // Save chat messages to sessionStorage whenever they change
  useEffect(() => {
    if (selectedProjectId && chatMessages.length > 0 && activeProjectRef.current === selectedProjectId && !sending) {
      sessionStorage.setItem(`archon_messages_${selectedProjectId}`, JSON.stringify(chatMessages));
      saveChatMessages(selectedProjectId, chatMessages);
    }
  }, [chatMessages, selectedProjectId, sending]);

  // Load chat history when project changes — sessionStorage first, then DB fallback
  useEffect(() => {
    if (!selectedProjectId) { setChatMessages([]); activeProjectRef.current = null; return; }
    activeProjectRef.current = selectedProjectId;
    setChatMessages([]); // clear immediately

    // Always load from DB — source of truth shared with Studio
    fetchChatHistory(selectedProjectId).then((msgs) => {
      if (activeProjectRef.current === selectedProjectId) {
        setChatMessages(msgs);
        if (msgs.length > 0) sessionStorage.setItem(`archon_messages_${selectedProjectId}`, JSON.stringify(msgs));
      }
    });
  }, [selectedProjectId]);

  // Auto-scroll chat to bottom on load AND when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  // Auto-scroll live output
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [pipeline.logs]);

  // Stop sending state when pipeline finishes
  useEffect(() => {
    if (pipeline.status === "COMPLETED" || pipeline.status === "FAILED") {
      setSending(false);
      sendingRef.current = false;
    }
    if (pipeline.status === "COMPLETED") {
      setBuildRefreshKey(k => k + 1);
      // Save messages on completion — this is the authoritative save after build finishes
      if (selectedProjectId) {
        setChatMessages(prev => {
          saveChatMessages(selectedProjectId, prev);
          sessionStorage.setItem(`archon_messages_${selectedProjectId}`, JSON.stringify(prev));
          return prev;
        });
      }
    }
  }, [pipeline.status]);

  useEffect(() => {
    if (projects.length > 0 && selectedProjectId === null) {
      setSelectedProjectId(projects[0].id);
    }
  }, [projects]);

  useEffect(() => {
    setSelectedVersion(null);
  }, [selectedProjectId]);

  // Scroll to top when switching to Pipeline tab
  const mainContainerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (activeTab === "pipeline") {
      setTimeout(() => {
        window.scrollTo(0, 0);
        document.documentElement.scrollTop = 0;
      }, 0);
    }
  }, [activeTab]);

  const handleSend = useCallback(async () => {
    if (!chatInput.trim() || !selectedProjectId) return;
    const prompt = chatInput.trim();
    setChatInput("");
    setPipelineError(null);

    // Add user message immediately
    const userMsg: ChatMessage = { role: "user", content: prompt, timestamp: Date.now() };
    setChatMessages((prev) => [...prev, userMsg]);

    try {
      // Classify intent via /chat
      const chatResult = await projectChat(selectedProjectId, prompt);

      if (chatResult.response_type === "chat") {
        // Pure chat reply — no build triggered
        const assistantMsg: ChatMessage = { role: "assistant", content: chatResult.message || "", timestamp: Date.now() };
        setChatMessages((prev) => [...prev, assistantMsg]);
        return;
      }

      // Check global build lock — show clean reply, no optimistic "building" message
      if (globalBuildBlocked) {
        const replyMsg: ChatMessage = { role: "assistant", content: "A build is already in progress. Send this again when it finishes.", timestamp: Date.now() };
        setChatMessages((prev) => [...prev, replyMsg]);
        return;
      }

      // Live check in case state is stale
      try {
        const statusRes = await fetch("http://localhost:5000/api/execution-status");
        const statusData = await statusRes.json();
        if (statusData.status === "RUNNING" && statusData.project_id !== selectedProjectId) {
          setGlobalBuildBlocked(true);
          setBlockingProjectId(statusData.project_id);
          const replyMsg: ChatMessage = { role: "assistant", content: "A build is already in progress. Send this again when it finishes.", timestamp: Date.now() };
          setChatMessages((prev) => [...prev, replyMsg]);
          return;
        }
      } catch {}

      // Don't start another build if one is already running for THIS project
      if (sendingRef.current) {
        const busyMsg: ChatMessage = {
          role: "assistant",
          content: "A build is already running for this project. Wait for it to finish, then try again.",
          timestamp: Date.now(),
        };
        setChatMessages((prev) => [...prev, busyMsg]);
        return;
      }

      // Build intent — start pipeline
      const assistantMsg: ChatMessage = { role: "assistant", content: "Got it! Starting the build now… ⚡", timestamp: Date.now() };
      setChatMessages((prev) => [...prev, assistantMsg]);

      const allMessages = [...chatMessages, userMsg];
      const promptHistory = allMessages.map((m) => ({ role: m.role, content: m.content }));

      setSending(true);
      sendingRef.current = true;
      await iterateProject(selectedProjectId, prompt, promptHistory as ChatMessage[]);
      // New execution is now active head — safe to save
      const msgsSnapshot = [...chatMessages, userMsg, assistantMsg];
      setTimeout(() => {
        saveChatMessages(selectedProjectId, msgsSnapshot);
      }, 300);
      // Polling starts automatically via usePipelineStatus (sending=true triggers enabled)
    } catch (err: any) {
      sendingRef.current = false;
      setSending(false);
      // Detect ANY 409 / pipeline lock error — show banner, never show red error
      const errMsg = (err.message || "").toLowerCase();
      const is409 = errMsg.includes("409") || errMsg.includes("build already running") || errMsg.includes("pipeline already running") || errMsg.includes("already running");
      if (is409) {
        // Show friendly banner only — no red error
        fetch("http://localhost:5000/api/execution-status")
          .then(r => r.json())
          .then(data => {
            if (data.status === "RUNNING") {
              setGlobalBuildBlocked(true);
              if (data.project_id !== selectedProjectId) {
                setBlockingProjectId(data.project_id);
              }
            }
          })
          .catch(() => {});
      } else {
        // Only show red error for genuine non-409 failures
        setPipelineError(err.message || "Failed to start build");
      }
    }
  }, [chatInput, selectedProjectId, sending, chatMessages]);

  const API_BASE = "http://localhost:5000";

  const handleTts = async (msgId: string, text: string) => {
    if (ttsAudioRef.current) {
      ttsAudioRef.current.pause();
      ttsAudioRef.current = null;
    }
    const prevId = ttsPlayingIdRef.current;
    ttsPlayingIdRef.current = null;
    if (prevId) setTtsState(s => ({ ...s, [prevId]: "idle" }));
    if (prevId === msgId) return;

    setTtsState(s => ({ ...s, [msgId]: "loading" }));
    try {
      const res = await fetch(`${API_BASE}/api/watson/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error("TTS request failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      ttsAudioRef.current = audio;
      ttsPlayingIdRef.current = msgId;
      setTtsState(s => ({ ...s, [msgId]: "playing" }));
      audio.onended = () => {
        ttsPlayingIdRef.current = null;
        ttsAudioRef.current = null;
        URL.revokeObjectURL(url);
        setTtsState(s => ({ ...s, [msgId]: "idle" }));
      };
      audio.play();
    } catch (e) {
      console.error("TTS error:", e);
      setTtsState(s => ({ ...s, [msgId]: "idle" }));
    }
  };

  const handleMic = async () => {
    if (micState === "idle") {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new MediaRecorder(stream);
        audioChunksRef.current = [];
        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunksRef.current.push(e.data);
        };
        recorder.onstop = async () => {
          stream.getTracks().forEach(t => t.stop());
          setMicState("processing");
          const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
          const formData = new FormData();
          formData.append("audio", blob, "recording.webm");
          try {
            const res = await fetch(`${API_BASE}/api/watson/stt`, {
              method: "POST",
              body: formData,
            });
            const data = await res.json();
            if (data.transcript) setChatInput(data.transcript);
          } catch (err) {
            console.error("STT error:", err);
          }
          setMicState("idle");
        };
        recorder.start();
        mediaRecorderRef.current = recorder;
        setMicState("recording");
      } catch (err) {
        console.error("Mic access denied:", err);
      }
    } else if (micState === "recording") {
      mediaRecorderRef.current?.stop();
    }
  };

  const stats = [
    { label: t("totalProjects"), value: projectStats.total },
    { label: t("running"), value: projectStats.running, color: "text-blue-500" },
    { label: t("completed"), value: projectStats.completed, color: "text-success" },
    { label: t("failed"), value: projectStats.failed, color: "text-destructive" },
  ];

  // Derive agent card statuses from pipeline stage (live) or DB status (historical)
  const deriveAgentStatus = (agentStage: string): "done" | "running" | "pending" | "failed" => {
    const stageOrder = ["pm", "planner", "engineer"];
    const agentIdx = stageOrder.indexOf(agentStage);

    // Live build in progress — use real-time polling data
    if (pipeline.running) {
      const currentIdx = stageOrder.indexOf(pipeline.stage);
      if (agentIdx < currentIdx) return "done";
      if (agentIdx === currentIdx) return "running";
      return "pending";
    }

    // Live build just finished this session
    if (pipeline.status === "COMPLETED") return "done";
    if (pipeline.status === "FAILED") {
      const currentIdx = stageOrder.indexOf(pipeline.stage);
      return agentIdx < currentIdx ? "done" : agentIdx === currentIdx ? "failed" : "pending";
    }

    // No live build — restore from DB (but not if we're actively sending/building)
    if (!sending && (historicalStatus === "SUCCESS" || historicalStatus === "COMPLETED")) return "done";
    if (historicalStatus === "FAILED" || historicalStatus === "ERROR") {
      // Requirements + Architecture + Design completed, Build failed
      return agentStage === "engineer" ? "failed" : "done";
    }
    if (historicalStatus === "RUNNING" || historicalStatus === "IN_PROGRESS") {
      // Stale running state (server died mid-build) — show as pending
      return "pending";
    }

    return "pending";
  };

  const agents = [
    { name: t("requirementsAgent"), description: t("understandsYourRequest"), status: deriveAgentStatus("pm") },
    { name: t("architectureAgent"), description: t("plansTheBuild"), status: deriveAgentStatus("planner") },
    { name: t("designAgent"), description: t("generatesVisuals"), status: deriveAgentStatus("planner") }, // design runs parallel with planner
    { name: t("buildAgent"), description: t("writesYourCode"), status: deriveAgentStatus("engineer") },
  ];

  return (
    <div ref={mainContainerRef} className="min-h-screen bg-background">
      <Navbar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        selectedProjectName={projects.find(p => p.id === selectedProjectId)?.name}
        selectedProjectVersion={selectedVersion != null ? `v${selectedVersion}` : projects.find(p => p.id === selectedProjectId)?.versions}
        selectedProjectId={selectedProjectId}
      />

      <main className="max-w-7xl mx-auto px-4 py-4 space-y-4">
        {activeTab === "pipeline" && (
          <>
            {!selectedProjectId ? (
              /* No project selected */
              <div className="border border-border rounded-md bg-card p-12 flex flex-col items-center justify-center text-center">
                <AlertCircle className="h-8 w-8 text-muted-foreground mb-3" />
                <h2 className="text-base font-semibold text-foreground mb-1">{t("selectProjectFirst")}</h2>
                <p className="text-sm text-muted-foreground">{t("selectProjectDesc")}</p>
              </div>
            ) : (
              <>
                {/* Project Header Card */}
                <div className="border border-border rounded-md bg-card overflow-hidden">
                  <div className="px-5 py-4 flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2.5">
                        <div className="h-8 w-8 rounded-md bg-secondary flex items-center justify-center">
                          <Zap className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h1 className="text-base font-semibold text-foreground">
                              {projects.find(p => p.id === selectedProjectId)?.name || "Untitled"}
                            </h1>
                            <span className="text-[10px] font-semibold text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-500/15 px-1.5 py-0.5 rounded">
                              {projects.find(p => p.id === selectedProjectId)?.versions || "v1"}
                            </span>
                          </div>
                          <p className="text-[11px] text-muted-foreground mt-0.5">
                            {(() => { const sp = projects.find(p => p.id === selectedProjectId); return sp ? `Project #${sp.id} · ${sp.created}` : ""; })()}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {pipeline.running ? (
                        <span className="inline-flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-0.5 rounded-full text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-500/10">
                          <span className="inline-block h-1.5 w-1.5 rounded-full bg-blue-500 animate-pulse" />
                          {t("building")}
                        </span>
                      ) : pipeline.status === "COMPLETED" ? (
                        <span className="inline-flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-0.5 rounded-full text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10">
                          <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500" />
                          {t("completed")}
                        </span>
                      ) : pipeline.status === "FAILED" && !sending ? (
                        <span className="inline-flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-0.5 rounded-full text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/10">
                          <span className="inline-block h-1.5 w-1.5 rounded-full bg-red-500" />
                          {t("failed")}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-0.5 rounded-full text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-500/10">
                          <span className="inline-block h-1.5 w-1.5 rounded-full bg-gray-400" />
                          {projects.find(p => p.id === selectedProjectId)?.status || "Idle"}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Two-column layout */}
                <div className="grid grid-cols-[1fr_320px] gap-4">
                  {/* Left: Conversation + Input */}
                  <div className="space-y-4">
                    {/* Conversation */}
                    <div className="border border-border rounded-md bg-card flex flex-col">
                      <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
                        <h3 className="text-xs font-semibold text-foreground tracking-wide uppercase flex items-center gap-1.5">
                          💬 {t("conversation")}
                        </h3>
                        <span className="text-[10px] text-muted-foreground">{chatMessages.length} {t("messages")}</span>
                      </div>
                      <div className="p-4 space-y-4 flex-1 max-h-[60vh] overflow-y-auto">
                        {chatMessages.length === 0 && (
                          <p className="text-sm text-muted-foreground text-center py-8">{t("noMessages")}</p>
                        )}
                        {chatMessages.map((msg, i) =>
                          msg.role === "user" ? (
                            <div key={i} className="flex justify-end">
                              <div className="max-w-sm">
                                <div className="text-[10px] font-medium text-muted-foreground text-right mb-1">
                                  {t("you")}{msg.timestamp ? ` · ${new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : ""}
                                </div>
                                <div className="bg-primary text-primary-foreground text-sm px-3 py-2 rounded-lg rounded-tr-sm">
                                  {msg.content}
                                </div>
                              </div>
                            </div>
                          ) : (
                            <div key={i} className="flex justify-start gap-2.5">
                              <span className="flex-shrink-0 h-7 w-7 rounded-lg bg-secondary flex items-center justify-center mt-5">
                                <Zap className="h-3.5 w-3.5 text-muted-foreground" />
                              </span>
                              <div className="max-w-md">
                                <div className="text-[10px] font-medium text-muted-foreground mb-1">
                                  Agent{msg.timestamp ? ` · ${new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : ""}
                                </div>
                                <div className="bg-secondary text-secondary-foreground text-sm px-3 py-2 rounded-lg rounded-tl-sm">
                                  {msg.content}
                                </div>
                              </div>
                              <button
                                onClick={() => handleTts(`msg-${i}`, msg.content)}
                                className={`flex-shrink-0 h-7 w-7 rounded-full flex items-center justify-center mt-5 transition-all duration-200 ${
                                  ttsState[`msg-${i}`] === "playing"
                                    ? "bg-primary text-primary-foreground shadow-md scale-110"
                                    : "bg-secondary text-muted-foreground hover:bg-primary hover:text-primary-foreground hover:scale-110"
                                }`}
                                aria-label="Play message audio"
                              >
                                {ttsState[`msg-${i}`] === "loading" ? (
                                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                ) : ttsState[`msg-${i}`] === "playing" ? (
                                  <VolumeX className="h-3.5 w-3.5" />
                                ) : (
                                  <Volume2 className="h-3.5 w-3.5" />
                                )}
                              </button>
                            </div>
                          )
                        )}
                        <div ref={chatEndRef} />
                      </div>
                    </div>

                    {/* Error banner */}
                    {pipelineError && (
                      <div className="border border-destructive/50 rounded-md bg-destructive/10 px-4 py-2 text-sm text-destructive flex items-center gap-2">
                        <AlertCircle className="h-4 w-4 flex-shrink-0" />
                        {pipelineError}
                      </div>
                    )}

                    {/* Build-lock banner — shown when another project is building */}
                    {globalBuildBlocked && (
                      <div className="border border-border rounded-md bg-muted/40 px-4 py-2 text-xs text-muted-foreground flex items-center gap-2">
                        <span className="inline-block h-1.5 w-1.5 rounded-full bg-blue-400 flex-shrink-0" />
                        <span>
                          {blockingProjectId ? `Project #${blockingProjectId}` : "Another project"} is building — chat is available while you wait.
                        </span>
                      </div>
                    )}

                    {/* Chat Input */}
                    <div className="border border-border rounded-md bg-card p-3 flex items-center gap-2">
                      <input
                        type="text"
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                        placeholder={t("whatWouldYouLikeToBuild")}
                        disabled={false}
                        className="flex-1 h-9 px-3 text-sm border border-border rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                      />
                      <button
                        onClick={handleMic}
                        disabled={sending || micState === "processing"}
                        className={`h-9 w-9 flex items-center justify-center border border-border rounded-md transition-colors disabled:opacity-50 ${
                          micState === "recording"
                            ? "bg-destructive text-destructive-foreground animate-pulse border-destructive"
                            : "text-muted-foreground hover:text-foreground"
                        }`}
                        title={micState === "recording" ? "Stop recording" : "Voice input"}
                      >
                        {micState === "processing" ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : micState === "recording" ? (
                          <MicOff className="h-4 w-4" />
                        ) : (
                          <Mic className="h-4 w-4" />
                        )}
                      </button>
                      {isStuck && selectedProjectId && (
                        <button
                          onClick={async () => {
                            try {
                              await fetch(`http://localhost:5000/api/projects/${selectedProjectId}/reset-build`, { method: "POST" });
                            } catch {}
                            setSending(false);
                            sendingRef.current = false;
                            buildStartTimeRef.current = null;
                            setIsStuck(false);
                            pipeline.stopPolling();
                            setPipelineError(null);
                            window.dispatchEvent(new Event("archon:build-reset"));
                          }}
                          className="bg-red-500 hover:bg-red-600 text-white font-medium rounded-md px-4 py-2 text-sm flex items-center gap-1.5 transition-colors"
                          title="Reset stuck build"
                        >
                          <X className="h-3.5 w-3.5" />
                          Reset
                        </button>
                      )}
                      <button
                        onClick={handleSend}
                        disabled={!chatInput.trim()}
                        className="h-9 px-3 flex items-center justify-center gap-1.5 bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity disabled:opacity-50 text-sm font-medium"
                        title={t("send")}
                      >
                        {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                        {sending ? t("sending") : t("send")}
                      </button>
                    </div>
                  </div>

                  {/* Right Sidebar: Pipeline + Live Output */}
                  <div className="space-y-4">
                    <PipelineStatus agents={agents} />

                    {/* Live Output */}
                    <div className="border border-border rounded-md bg-card">
                      <div className="px-3 py-2 border-b border-border flex items-center justify-between">
                        <h3 className="text-xs font-semibold text-foreground tracking-wide uppercase flex items-center gap-1.5">
                          {">_"} {t("liveOutput")}
                        </h3>
                        <span className="text-[10px] text-muted-foreground">{(pipeline.logs.length > 0 ? pipeline.logs.length : historicalLogs.length)} {t("entries")}</span>
                      </div>
                      <div ref={logContainerRef} className="p-3 font-mono text-[11px] text-muted-foreground space-y-1.5 max-h-48 overflow-y-auto">
                        {(() => {
                          const displayLogs = pipeline.logs.length > 0 ? pipeline.logs : historicalLogs;
                          return displayLogs.length === 0 ? (
                            <div className="text-center py-3 text-muted-foreground">—</div>
                          ) : (
                            displayLogs.map((log) => (
                              <div key={log.id} className="py-0.5">
                                <span>{log.message}</span>
                              </div>
                            ))
                          );
                        })()}
                      </div>
                    </div>

                    {/* Build Info */}
                    <BuildDetailsCard projectId={selectedProjectId} version={selectedVersion ?? (projects.find(p => p.id === selectedProjectId) ? parseInt(projects.find(p => p.id === selectedProjectId)!.versions.replace("v", "")) : null)} refreshKey={buildRefreshKey} />
                  </div>
                </div>
              </>
            )}
          </>
        )}

        {activeTab === "projects" && (
          <>
            <WelcomeBanner stats={projectStats} />
            <StatsBar stats={stats} />

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder={t("searchProjects")}
                    className="h-8 pl-8 pr-3 text-sm border border-border rounded-md bg-card text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring w-56"
                  />
                </div>
                <select className="h-8 px-2 text-xs border border-border rounded-md bg-card text-foreground focus:outline-none focus:ring-1 focus:ring-ring">
                  <option>{t("allStatuses")}</option>
                  <option>{t("running")}</option>
                  <option>{t("completed")}</option>
                  <option>{t("failed")}</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => setShowNewProject(true)} className="h-8 px-3 text-xs font-medium bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity flex items-center gap-1.5">
                  <Plus className="h-3.5 w-3.5" /> {t("newProject")}
                </button>
              </div>
            </div>

            <div className="grid grid-cols-[1fr_300px] gap-4">
              {loading ? (
                <div className="border border-border rounded-md bg-card flex items-center justify-center py-20">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-sm text-muted-foreground">Loading projects...</span>
                </div>
              ) : (
                <ProjectTable projects={searchQuery.trim() ? projects.filter(p => p.name.toLowerCase().includes(searchQuery.trim().toLowerCase())) : projects} onProjectSelect={(id) => { setSelectedProjectId(id); setActiveTab("pipeline"); }} />
              )}
              <ActivityFeed />
            </div>

            <NewProjectModal
              open={showNewProject}
              onClose={() => setShowNewProject(false)}
              onCreated={(id) => {
                setShowNewProject(false);
                setSelectedProjectId(id);
                setActiveTab("pipeline");
              }}
            />
          </>
        )}

        {activeTab === "versions" && (
          <VersionsView
            projectId={selectedProjectId}
            selectedVersion={selectedVersion}
            onVersionSelect={setSelectedVersion}
            onArtifactNavigate={(tab) => { setArtifactTab(tab); setActiveTab("artifacts"); }}
          />
        )}

        {activeTab === "artifacts" && <ArtifactsView projectId={selectedProjectId} selectedVersion={selectedVersion} onVersionSelect={setSelectedVersion} initialTab={artifactTab} />}
      </main>
    </div>
  );
};

export default Index;
