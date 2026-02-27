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
  type ChatMessage,
} from "@/services/api";
import { Search, Plus, Trash2, Zap, Mic, Send, Volume2, Filter, Loader2, AlertCircle } from "lucide-react";

const Index = () => {
  const [activeTab, setActiveTab] = useState("projects");
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [showNewProject, setShowNewProject] = useState(false);
  const { t } = useLanguage();
  const { projects, loading, error, stats: projectStats } = useProjects();

  // Pipeline state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [sending, setSending] = useState(false);
  const [pipelineError, setPipelineError] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const pipeline = usePipelineStatus(selectedProjectId, activeTab === "pipeline" && sending);

  // Load chat history when project changes
  useEffect(() => {
    if (!selectedProjectId) { setChatMessages([]); return; }
    let cancelled = false;
    fetchChatHistory(selectedProjectId).then((msgs) => {
      if (!cancelled) setChatMessages(msgs);
    });
    return () => { cancelled = true; };
  }, [selectedProjectId]);

  // Auto-scroll chat
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

  const handleSend = useCallback(async () => {
    if (!chatInput.trim() || !selectedProjectId || sending) return;
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

      // Build intent — start pipeline
      const assistantMsg: ChatMessage = { role: "assistant", content: "Got it! Starting the build now… ⚡", timestamp: Date.now() };
      setChatMessages((prev) => [...prev, assistantMsg]);

      const allMessages = [...chatMessages, userMsg];
      const promptHistory = allMessages.map((m) => ({ role: m.role, content: m.content }));

      setSending(true);
      await iterateProject(selectedProjectId, prompt, promptHistory as ChatMessage[]);
      // Polling starts automatically via usePipelineStatus (sending=true triggers enabled)
    } catch (err: any) {
      setPipelineError(err.message || "Failed to start build");
      setSending(false);
    }
  }, [chatInput, selectedProjectId, sending, chatMessages]);

  const stats = [
    { label: t("totalProjects"), value: projectStats.total },
    { label: t("running"), value: projectStats.running, color: "text-blue-500" },
    { label: t("completed"), value: projectStats.completed, color: "text-success" },
    { label: t("failed"), value: projectStats.failed, color: "text-destructive" },
  ];

  // Derive agent card statuses from pipeline stage
  const deriveAgentStatus = (agentStage: string): "done" | "running" | "pending" => {
    const stageOrder = ["pm", "planner", "engineer"];
    const currentIdx = stageOrder.indexOf(pipeline.stage);
    const agentIdx = stageOrder.indexOf(agentStage);
    if (!pipeline.running && pipeline.status === "IDLE") return "pending";
    if (pipeline.status === "COMPLETED") return "done";
    if (pipeline.status === "FAILED") return agentIdx <= currentIdx ? (agentIdx < currentIdx ? "done" : "running") : "pending";
    if (agentIdx < currentIdx) return "done";
    if (agentIdx === currentIdx) return "running";
    return "pending";
  };

  const agents = [
    { name: t("requirementsAgent"), description: t("understandsYourRequest"), status: deriveAgentStatus("pm") },
    { name: t("architectureAgent"), description: t("plansTheBuild"), status: deriveAgentStatus("planner") },
    { name: t("designAgent"), description: t("generatesVisuals"), status: deriveAgentStatus("planner") }, // design runs parallel with planner
    { name: t("buildAgent"), description: t("writesYourCode"), status: deriveAgentStatus("engineer") },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navbar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        selectedProjectName={projects.find(p => p.id === selectedProjectId)?.name}
        selectedProjectVersion={selectedVersion != null ? `v${selectedVersion}` : projects.find(p => p.id === selectedProjectId)?.versions}
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
                        <span className="text-xs font-medium text-blue-500 flex items-center gap-1.5">
                          <span className="inline-block h-1.5 w-1.5 rounded-full bg-blue-500 animate-pulse" />
                          {t("building")}
                        </span>
                      ) : pipeline.status === "COMPLETED" ? (
                        <span className="text-xs font-medium text-success flex items-center gap-1.5">
                          <span className="inline-block h-1.5 w-1.5 rounded-full bg-green-500" />
                          {t("completed")}
                        </span>
                      ) : pipeline.status === "FAILED" ? (
                        <span className="text-xs font-medium text-destructive flex items-center gap-1.5">
                          <span className="inline-block h-1.5 w-1.5 rounded-full bg-red-500" />
                          {t("failed")}
                        </span>
                      ) : (
                        <span className="text-xs font-medium text-muted-foreground">
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
                                  You{msg.timestamp ? ` · ${new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : ""}
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

                    {/* Chat Input */}
                    <div className="border border-border rounded-md bg-card p-3 flex items-center gap-2">
                      <input
                        type="text"
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                        placeholder={t("whatWouldYouLikeToBuild")}
                        disabled={sending}
                        className="flex-1 h-9 px-3 text-sm border border-border rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
                      />
                      <button className="h-9 w-9 flex items-center justify-center text-muted-foreground hover:text-foreground border border-border rounded-md transition-colors" title="Voice input">
                        <Mic className="h-4 w-4" />
                      </button>
                      <button
                        onClick={handleSend}
                        disabled={sending || !chatInput.trim()}
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
                        <span className="text-[10px] text-muted-foreground">{pipeline.logs.length} {t("entries")}</span>
                      </div>
                      <div ref={logContainerRef} className="p-3 font-mono text-[11px] text-muted-foreground space-y-1.5 max-h-48 overflow-y-auto">
                        {pipeline.logs.length === 0 ? (
                          <div className="text-center py-3 text-muted-foreground">—</div>
                        ) : (
                          pipeline.logs.map((log) => (
                            <div key={log.id} className="flex gap-2">
                              <span className="text-foreground flex-shrink-0">
                                {new Date(log.timestamp).toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                              </span>
                              <span>{log.message}</span>
                            </div>
                          ))
                        )}
                      </div>
                    </div>

                    {/* Build Info */}
                    <BuildDetailsCard projectId={selectedProjectId} version={selectedVersion ?? (projects.find(p => p.id === selectedProjectId) ? parseInt(projects.find(p => p.id === selectedProjectId)!.versions.replace("v", "")) : null)} />
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
                <ProjectTable projects={projects} onProjectSelect={(id) => { setSelectedProjectId(id); setActiveTab("pipeline"); }} />
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

        {activeTab === "versions" && <VersionsView projectId={selectedProjectId} selectedVersion={selectedVersion} onVersionSelect={setSelectedVersion} />}

        {activeTab === "artifacts" && <ArtifactsView projectId={selectedProjectId} selectedVersion={selectedVersion} onVersionSelect={setSelectedVersion} />}
      </main>
    </div>
  );
};

export default Index;
