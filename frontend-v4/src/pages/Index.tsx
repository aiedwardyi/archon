import { useState, useEffect } from "react";
import { Navbar } from "@/components/Navbar";
import { PipelineStatus } from "@/components/PipelineStatus";
import { StatsBar } from "@/components/StatsBar";
import { ProjectTable } from "@/components/ProjectTable";
import { WelcomeBanner } from "@/components/WelcomeBanner";
import { ActivityFeed } from "@/components/ActivityFeed";
import { VersionsView } from "@/components/VersionsView";
import { ArtifactsView } from "@/components/ArtifactsView";
import { useLanguage } from "@/contexts/LanguageContext";
import { useProjects } from "@/services/api";
import { Search, Plus, Trash2, Sparkles, Mic, Send, Volume2, Filter, Loader2 } from "lucide-react";

const Index = () => {
  const [activeTab, setActiveTab] = useState("projects");
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const { t } = useLanguage();
  const { projects, loading, error, stats: projectStats } = useProjects();

  useEffect(() => {
    if (projects.length > 0 && selectedProjectId === null) {
      setSelectedProjectId(projects[0].id);
    }
  }, [projects]);

  useEffect(() => {
    setSelectedVersion(null);
  }, [selectedProjectId]);

  const stats = [
    { label: t("totalProjects"), value: projectStats.total },
    { label: t("running"), value: projectStats.running, color: "text-blue-500" },
    { label: t("completed"), value: projectStats.completed, color: "text-success" },
    { label: t("failed"), value: projectStats.failed, color: "text-destructive" },
  ];

  const agents = [
    { name: t("requirementsAgent"), description: t("understandsYourRequest"), status: "done" as const },
    { name: t("architectureAgent"), description: t("plansTheBuild"), status: "done" as const },
    { name: t("buildAgent"), description: t("writesYourCode"), status: "running" as const },
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
            {/* Project Header Card */}
            <div className="border border-border rounded-md bg-card overflow-hidden">
              <div className="px-5 py-4 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2.5">
                    <div className="h-8 w-8 rounded-md bg-secondary flex items-center justify-center">
                      <Sparkles className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h1 className="text-base font-semibold text-foreground">
                          {(() => { const sp = projects.find(p => p.id === selectedProjectId); return sp ? sp.name : "Add AI-powered insights"; })()}
                        </h1>
                        <span className="text-[10px] font-semibold text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-500/15 px-1.5 py-0.5 rounded">
                          {(() => { const sp = projects.find(p => p.id === selectedProjectId); return sp ? sp.versions : "v2"; })()}
                        </span>
                      </div>
                      <p className="text-[11px] text-muted-foreground mt-0.5">
                        {(() => { const sp = projects.find(p => p.id === selectedProjectId); return sp ? `Project #${sp.id} · ${sp.created}` : "Project #58 · Started Feb 27, 2026"; })()}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs font-medium text-blue-500 flex items-center gap-1.5">
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-blue-500 animate-pulse" />
                    {(() => { const sp = projects.find(p => p.id === selectedProjectId); return sp ? sp.status : t("building"); })()}
                  </span>
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
                    <span className="text-[10px] text-muted-foreground">4 {t("messages")}</span>
                  </div>
                  <div className="p-4 space-y-4 flex-1">
                    {/* User message */}
                    <div className="flex justify-end">
                      <div className="max-w-sm">
                        <div className="text-[10px] font-medium text-muted-foreground text-right mb-1">You · 11:16</div>
                        <div className="bg-primary text-primary-foreground text-sm px-3 py-2 rounded-lg rounded-tr-sm">
                          Can you create me a Pokemon Game?
                        </div>
                      </div>
                    </div>
                    {/* Agent message */}
                    <div className="flex justify-start gap-2.5">
                      <span className="flex-shrink-0 h-7 w-7 rounded-lg bg-secondary flex items-center justify-center mt-5">
                        <Sparkles className="h-3.5 w-3.5 text-muted-foreground" />
                      </span>
                      <div className="max-w-md">
                        <div className="text-[10px] font-medium text-muted-foreground mb-1">Agent · 11:16</div>
                        <div className="bg-secondary text-secondary-foreground text-sm px-3 py-2 rounded-lg rounded-tl-sm">
                          Creating a Pokémon game is a big project! You might want to consider what type of game you want to build. Think about the features you want to include, like capturing Pokémon, battling, or trading.
                        </div>
                      </div>
                      <button className="flex-shrink-0 mt-5 h-7 w-7 flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors" title="Listen">
                        <Volume2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                    {/* User message */}
                    <div className="flex justify-end">
                      <div className="max-w-sm">
                        <div className="text-[10px] font-medium text-muted-foreground text-right mb-1">You · 11:16</div>
                        <div className="bg-primary text-primary-foreground text-sm px-3 py-2 rounded-lg rounded-tr-sm">
                          Web based game, I want all features you think is relevant. Start
                        </div>
                      </div>
                    </div>
                    {/* Agent message */}
                    <div className="flex justify-start gap-2.5">
                      <span className="flex-shrink-0 h-7 w-7 rounded-lg bg-secondary flex items-center justify-center mt-5">
                        <Sparkles className="h-3.5 w-3.5 text-muted-foreground" />
                      </span>
                      <div className="max-w-md">
                        <div className="text-[10px] font-medium text-muted-foreground mb-1">Agent · 11:16</div>
                        <div className="bg-secondary text-secondary-foreground text-sm px-3 py-2 rounded-lg rounded-tl-sm">
                          Got it! Starting the build now… ⚡
                        </div>
                      </div>
                      <button className="flex-shrink-0 mt-5 h-7 w-7 flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors" title="Listen">
                        <Volume2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Chat Input */}
                <div className="border border-border rounded-md bg-card p-3 flex items-center gap-2">
                  <input
                    type="text"
                    placeholder={t("whatWouldYouLikeToBuild")}
                    className="flex-1 h-9 px-3 text-sm border border-border rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                  />
                  <button className="h-9 w-9 flex items-center justify-center text-muted-foreground hover:text-foreground border border-border rounded-md transition-colors" title="Voice input">
                    <Mic className="h-4 w-4" />
                  </button>
                  <button className="h-9 w-9 flex items-center justify-center bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity" title="Send">
                    <Send className="h-4 w-4" />
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
                    <span className="text-[10px] text-muted-foreground">3 {t("entries")}</span>
                  </div>
                  <div className="p-3 font-mono text-[11px] text-muted-foreground space-y-1.5">
                    <div className="flex gap-2"><span className="text-foreground flex-shrink-0">11:16:48</span><span>Build Agent: Loading v1 for context...</span></div>
                    <div className="flex gap-2"><span className="text-foreground flex-shrink-0">11:16:48</span><span>Starting pipeline...</span></div>
                    <div className="flex gap-2"><span className="text-foreground flex-shrink-0">11:16:48</span><span>Requirements Agent: Analyzing your request...</span></div>
                  </div>
                </div>

                {/* Build Info */}
                <div className="border border-border rounded-md bg-card">
                  <div className="px-3 py-2 border-b border-border">
                    <h3 className="text-xs font-semibold text-foreground tracking-wide uppercase">{t("buildDetails")}</h3>
                  </div>
                  <div className="divide-y divide-border">
                    {[
                      { label: t("model"), value: "GPT-4o" },
                      { label: t("tokensUsed"), value: "12,480" },
                      { label: t("estCost"), value: "$0.04" },
                      { label: t("duration"), value: "1m 38s" },
                    ].map(({ label, value }) => (
                      <div key={label} className="px-3 py-2 flex items-center justify-between">
                        <span className="text-[11px] text-muted-foreground">{label}</span>
                        <span className="text-xs font-medium text-foreground">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
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
                <button className="h-8 px-3 text-xs font-medium bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity flex items-center gap-1.5">
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
          </>
        )}

        {activeTab === "versions" && <VersionsView projectId={selectedProjectId} selectedVersion={selectedVersion} onVersionSelect={setSelectedVersion} />}

        {activeTab === "artifacts" && <ArtifactsView projectId={selectedProjectId} selectedVersion={selectedVersion} onVersionSelect={setSelectedVersion} />}
      </main>
    </div>
  );
};

export default Index;
