import { useState, useEffect } from "react";
import {
  FileText, Target, Code2, ListChecks, ScrollText, Eye,
  Monitor, Smartphone, ChevronRight, Download, Upload,
  Braces, FolderOpen, FileCode, CheckCircle2, Circle, Clock,
  AlertCircle, Loader2, Copy, Check, ExternalLink,
} from "lucide-react";
import { fetchProjectHead, fetchPrd, fetchPlan, fetchCodeFiles, fetchLogs } from "@/services/api";
import { useLanguage } from "@/contexts/LanguageContext";

type ArtifactTab = "brief" | "plan" | "code" | "tasks" | "logs" | "preview";

const tabDefs: { id: ArtifactTab; key: "brief" | "plan" | "code" | "tasks" | "logs" | "preview"; icon: typeof FileText }[] = [
  { id: "brief", key: "brief", icon: FileText },
  { id: "plan", key: "plan", icon: Target },
  { id: "code", key: "code", icon: Code2 },
  { id: "tasks", key: "tasks", icon: ListChecks },
  { id: "logs", key: "logs", icon: ScrollText },
  { id: "preview", key: "preview", icon: Eye },
];

// ── Data interfaces ──

interface BriefData {
  title: string;
  version: string;
  generatedBy: string;
  sections: Array<{ heading: string; subtitle?: string; content?: string; bullets?: string[] }>;
}

interface PlanData {
  title: string;
  milestoneCount: number;
  generatedBy: string;
  milestones: Array<{ title: string; tasks: Array<{ id: string; description: string }> }>;
}

interface CodeFile {
  path: string;
  language: string;
  content: string;
}

interface LogEntry {
  time: string;
  message: string;
}

// ── Component ──

interface ArtifactsViewProps {
  projectId: number | null;
  selectedVersion: number | null;
  onVersionSelect: (v: number) => void;
  initialTab?: "brief" | "plan" | "code";
}

export const ArtifactsView = ({ projectId, selectedVersion, onVersionSelect, initialTab }: ArtifactsViewProps) => {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<ArtifactTab>(initialTab || "brief");
  const [showRawData, setShowRawData] = useState(false);

  // Sync when navigating from VersionsView artifact cards
  useEffect(() => {
    if (initialTab) setActiveTab(initialTab);
  }, [initialTab]);
  const [previewDevice, setPreviewDevice] = useState<"desktop" | "mobile">("desktop");
  const [selectedFile, setSelectedFile] = useState(0);
  const [loading, setLoading] = useState(false);
  const [headVersion, setHeadVersion] = useState<number | null>(null);
  const [briefData, setBriefData] = useState<BriefData>({ title: "Brief", version: "", generatedBy: "Archon", sections: [] });
  const [planData, setPlanData] = useState<PlanData>({ title: "Build Plan", milestoneCount: 0, generatedBy: "Archon", milestones: [] });
  const [codeFiles, setCodeFiles] = useState<CodeFile[]>([]);
  const [logsData, setLogsData] = useState<LogEntry[]>([]);
  const [tasksData, setTasksData] = useState<Array<{ id: string; title: string; status: "done" | "running" | "pending" | "failed"; assignee: string }>>([]);
  const [publishState, setPublishState] = useState<"idle" | "loading" | "done">("idle");
  const [publishedUrl, setPublishedUrl] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    setLoading(true);

    (async () => {
      let ver: number | null;
      if (selectedVersion != null) {
        ver = selectedVersion;
      } else {
        ver = await fetchProjectHead(projectId);
        if (!cancelled && ver != null) {
          onVersionSelect(ver);
        }
      }
      if (cancelled) return;
      setHeadVersion(ver);
      if (!ver) { setLoading(false); return; }

      const [prdRaw, planRaw, filesRaw, logsRaw] = await Promise.all([
        fetchPrd(projectId, ver),
        fetchPlan(projectId, ver),
        fetchCodeFiles(projectId, ver),
        fetchLogs(projectId, ver),
      ]);
      if (cancelled) return;

      // Map PRD — API returns { prd: { document_title, overview, goals, ... } }
      if (prdRaw?.prd) {
        const prd = prdRaw.prd;
        const sections: BriefData["sections"] = [];
        if (prd.overview) sections.push({ heading: t("overview"), content: prd.overview });
        if (prd.goals) sections.push({ heading: t("goals"), subtitle: t("successCriteria"), bullets: prd.goals });
        if (prd.core_features_mvp) sections.push({ heading: t("coreFeatures"), subtitle: t("whatWereBuilding"), bullets: prd.core_features_mvp });
        if (prd.target_users) sections.push({ heading: t("targetUsers"), subtitle: t("whoWereBuildingFor"), bullets: prd.target_users });
        setBriefData({
          title: prd.document_title || "Brief",
          version: `v${ver}`,
          generatedBy: "Archon",
          sections,
        });
      }

      // Map Plan — API returns { milestones: [ { name, tasks: [{ id, description }] } ] }
      if (planRaw) {
        const milestonesList = planRaw?.milestones || planRaw?.plan?.milestones || planRaw?.phases || [];
        const milestones = milestonesList.map((m: any) => ({
          title: m.name,
          tasks: (m.tasks || []).map((t: any) => ({ id: t.id || t.task_id || "TASK", description: t.description || t.title })),
        }));
        setPlanData({ title: "Build Plan", milestoneCount: milestones.length, generatedBy: "Archon", milestones });

        // Derive tasks from plan phases
        const derived = milestones.flatMap((m: any) =>
          m.tasks.map((t: any) => ({ id: t.id, title: t.description, status: "done" as const, assignee: "Agent" }))
        );
        setTasksData(derived);
      }

      // Map code files
      setCodeFiles(filesRaw.map(f => ({ path: f.filename, language: f.language, content: f.content })));
      setSelectedFile(0);

      // Map logs — fetched from per-version /logs endpoint
      if (logsRaw.length > 0) {
        setLogsData(logsRaw.map((line: string) => {
          const spaceIdx = line.indexOf(" ");
          const timePart = spaceIdx > 0 ? line.slice(0, spaceIdx) : "—";
          const msgPart = spaceIdx > 0 ? line.slice(spaceIdx + 1) : line;
          return { time: timePart || "—", message: msgPart };
        }));
      } else {
        setLogsData([{ time: "—", message: "No logs available for this version." }]);
      }

      setLoading(false);
    })();

    return () => { cancelled = true; };
  }, [projectId, selectedVersion]);

  const rawDataAvailable = ["brief", "plan", "tasks"].includes(activeTab);

  if (!projectId) {
    return (
      <div className="border border-border rounded-md bg-card flex items-center justify-center py-20">
        <span className="text-sm text-muted-foreground">Select a project to view artifacts</span>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="border border-border rounded-md bg-card flex items-center justify-center py-20">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">Loading artifacts...</span>
      </div>
    );
  }

  return (
    <div className="border border-border rounded-md bg-card overflow-hidden">
      {/* Top Bar: Breadcrumbs + Badges + Actions */}
      <div className="px-5 py-2.5 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <nav className="flex items-center gap-1 text-xs">
            <span className="text-muted-foreground">{t("requirements")}</span>
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
            <span className="text-muted-foreground">{t("architecture")}</span>
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
            <span className="font-medium text-foreground">{t("code")}</span>
          </nav>
          <div className="h-4 w-px bg-border" />
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded border border-blue-300 text-blue-600 dark:text-blue-400 dark:border-blue-500/30 bg-blue-50 dark:bg-blue-500/10">
            ▷ {t("reproducible")}
          </span>
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded border border-emerald-300 text-emerald-600 dark:text-emerald-400 dark:border-emerald-500/30 bg-emerald-50 dark:bg-emerald-500/10">
            ○ {t("verified")}
          </span>
          <span className="text-[10px] font-bold bg-secondary text-muted-foreground px-1.5 py-0.5 rounded">{headVersion ? `V${headVersion}` : "V?"}</span>
        </div>
        <div className="flex items-center gap-2">
          {publishState === "done" ? (
            <div className="flex items-center gap-1.5">
              <input
                readOnly
                value={publishedUrl}
                className="h-8 text-xs px-2.5 rounded-md border border-emerald-300 dark:border-emerald-500/40 bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 font-mono w-60"
              />
              <button
                onClick={() => { navigator.clipboard.writeText(publishedUrl); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
                className="h-8 px-2.5 text-xs font-medium border border-emerald-300 dark:border-emerald-500/40 rounded-md bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-500/20 transition-colors flex items-center gap-1"
              >
                {copied ? <><Check className="h-3 w-3" /> Copied!</> : <><Copy className="h-3 w-3" /> Copy</>}
              </button>
              <a
                href={publishedUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="h-8 w-8 flex items-center justify-center border border-border rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
          ) : (
            <button
              onClick={async () => {
                if (!projectId || !headVersion) return;
                setPublishState("loading");
                try {
                  const res = await fetch(`http://localhost:5000/api/projects/${projectId}/versions/${headVersion}/publish`, { method: "POST" });
                  const data = await res.json();
                  if (data.url) {
                    setPublishedUrl(`http://localhost:5000${data.url}`);
                    setPublishState("done");
                  } else {
                    setPublishState("idle");
                  }
                } catch {
                  setPublishState("idle");
                }
              }}
              disabled={publishState === "loading"}
              className="h-8 px-3 text-xs font-semibold bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity flex items-center gap-1.5 disabled:opacity-50"
            >
              {publishState === "loading" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5" />}
              {publishState === "loading" ? "Publishing..." : t("publish")}
            </button>
          )}
          <a
            href={projectId && headVersion ? `http://localhost:5000/api/projects/${projectId}/versions/${headVersion}/download` : "#"}
            download
            className="h-8 px-3 text-xs font-medium border border-border rounded-md text-foreground hover:bg-secondary transition-colors flex items-center gap-1.5 no-underline"
          >
            <Download className="h-3.5 w-3.5" /> {t("downloadCode")}
          </a>
          <button
            onClick={() => rawDataAvailable && setShowRawData(!showRawData)}
            className={`h-8 px-3 text-xs font-medium border border-border rounded-md transition-colors flex items-center gap-1.5 ${
              rawDataAvailable
                ? showRawData
                  ? "bg-primary text-primary-foreground border-primary"
                  : "text-foreground hover:bg-secondary"
                : "text-muted-foreground cursor-not-allowed opacity-50"
            }`}
          >
            <Braces className="h-3.5 w-3.5" /> {t("rawData")}
          </button>
        </div>
      </div>

      {/* Tab Bar */}
      <div className="px-5 border-b border-border bg-secondary/20">
        <div className="flex items-center gap-0.5">
          {tabDefs.map(({ id, key, icon: Icon }) => (
            <button
              key={id}
              onClick={() => { setActiveTab(id); setShowRawData(false); }}
              className={`flex items-center gap-1.5 px-3 py-2.5 text-xs font-medium border-b-2 transition-colors ${
                activeTab === id
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {t(key)}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="p-5">
        {activeTab === "brief" && !showRawData && <BriefTab data={briefData} />}
        {activeTab === "brief" && showRawData && <RawJsonView data={briefData} />}
        {activeTab === "plan" && !showRawData && <PlanTab data={planData} />}
        {activeTab === "plan" && showRawData && <RawJsonView data={planData} />}
        {activeTab === "code" && <CodeTab files={codeFiles} selectedFile={selectedFile} onSelectFile={setSelectedFile} />}
        {activeTab === "tasks" && !showRawData && <TasksTab tasks={tasksData} />}
        {activeTab === "tasks" && showRawData && <RawJsonView data={tasksData} />}
        {activeTab === "logs" && <LogsTab logs={logsData} version={headVersion} />}
        {activeTab === "preview" && <PreviewTab device={previewDevice} onDeviceChange={setPreviewDevice} projectId={projectId} version={headVersion} />}
      </div>
    </div>
  );
};

// ── Sub-components ──

const BriefTab = ({ data }: { data: BriefData }) => {
  const { t } = useLanguage();
  return (
  <div className="max-w-2xl">
    <h1 className="text-lg font-bold text-foreground">
      {data.title}
      <span className="ml-2 text-[10px] font-bold bg-primary text-primary-foreground px-1.5 py-0.5 rounded align-middle">
        {data.version || "v1"}
      </span>
    </h1>
    <p className="text-xs text-muted-foreground mt-1">v1.0 · {t("generatedBy")} {data.generatedBy}</p>

    <div className="mt-6 space-y-5">
      {data.sections.map((s, i) => (
        <div key={i} className="border border-border rounded-md p-5">
          <h2 className="text-sm font-bold text-foreground">{s.heading}</h2>
          {s.subtitle && <p className="text-[11px] text-muted-foreground mt-0.5">{s.subtitle}</p>}
          {s.content && <p className="text-sm text-muted-foreground mt-2 leading-relaxed">{s.content}</p>}
          {s.bullets && (
            <ul className="mt-2 space-y-1.5">
              {s.bullets.map((b, j) => (
                <li key={j} className="text-sm text-muted-foreground flex items-start gap-2">
                  <span className="text-primary mt-1.5 flex-shrink-0">●</span>
                  {b}
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  </div>
); };

const PlanTab = ({ data }: { data: PlanData }) => {
  const { t } = useLanguage();
  return (
  <div className="max-w-2xl">
    <h1 className="text-lg font-bold text-foreground">{t("buildPlan")}</h1>
    <p className="text-xs text-muted-foreground mt-1">{data.milestoneCount} {t("milestones")} · {t("generatedBy")} {data.generatedBy}</p>

    <div className="mt-6 space-y-5">
      {data.milestones.map((m, i) => (
        <div key={i} className="border border-border rounded-md p-5">
          <h2 className="text-sm font-bold text-foreground">{m.title}</h2>
          <div className="mt-3 space-y-0 divide-y divide-border">
            {m.tasks.map((tk) => (
              <div key={tk.id} className="py-2.5 flex items-start gap-3">
                <span className="text-[10px] font-bold text-primary bg-primary/10 px-1.5 py-0.5 rounded flex-shrink-0 mt-0.5 font-mono">
                  {tk.id}
                </span>
                <p className="text-sm text-muted-foreground leading-relaxed">{tk.description}</p>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>
); };

const CodeTab = ({ files, selectedFile, onSelectFile }: { files: CodeFile[]; selectedFile: number; onSelectFile: (i: number) => void }) => {
  if (files.length === 0) return <div className="text-sm text-muted-foreground">No code files found.</div>;
  const safeIdx = Math.min(selectedFile, files.length - 1);
  return (
    <div className="grid grid-cols-[180px_1fr] gap-0 border border-border rounded-md bg-card" style={{ height: "calc(100vh - 260px)", overflow: "hidden" }}>
      {/* File Tree */}
      <div className="border-r border-border bg-secondary/30" style={{ height: "100%", overflowY: "auto" }}>
        <div className="px-3 py-2 flex items-center gap-1.5 text-xs text-muted-foreground sticky top-0 bg-secondary/30 z-10">
          <FolderOpen className="h-3.5 w-3.5" />
          <span className="font-medium">src</span>
        </div>
        {files.map((f, i) => (
          <button
            key={f.path}
            onClick={() => onSelectFile(i)}
            className={`w-full text-left pl-6 pr-3 py-1.5 text-xs flex items-center gap-1.5 transition-colors ${
              safeIdx === i
                ? "bg-primary/10 text-foreground font-medium"
                : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
            }`}
          >
            <FileCode className="h-3.5 w-3.5 flex-shrink-0" />
            {f.path.split("/").pop()}
          </button>
        ))}
      </div>

      {/* Code Viewer */}
      <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden", minWidth: 0 }}>
        <div className="px-4 py-2 border-b border-border flex items-center justify-between bg-secondary/20" style={{ flexShrink: 0 }}>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <FileCode className="h-3.5 w-3.5" />
            {files[safeIdx].path}
          </div>
          <span className="text-[10px] font-medium text-muted-foreground">{files[safeIdx].language}</span>
        </div>
        <pre className="p-4 text-xs font-mono text-foreground leading-relaxed" style={{ flex: 1, overflow: "auto", margin: 0 }}>
          {files[safeIdx].content.split("\n").map((line, i) => (
            <div key={i} className="flex">
              <span className="text-muted-foreground/50 w-8 text-right mr-4 select-none flex-shrink-0">{i + 1}</span>
              <span className="whitespace-pre">{line}</span>
            </div>
          ))}
        </pre>
      </div>
    </div>
  );
};

const taskStatusConfig = {
  done: { icon: CheckCircle2, color: "text-emerald-500" },
  running: { icon: Clock, color: "text-blue-500" },
  pending: { icon: Circle, color: "text-muted-foreground" },
  failed: { icon: AlertCircle, color: "text-destructive" },
};

const TasksTab = ({ tasks }: { tasks: Array<{ id: string; title: string; status: "done" | "running" | "pending" | "failed"; assignee: string }> }) => (
  <div className="border border-border rounded-md overflow-hidden bg-card">
    <div className="px-4 py-2.5 border-b border-border bg-secondary/30 flex items-center justify-between">
      <h3 className="text-xs font-semibold text-foreground uppercase tracking-wider">Pipeline Tasks</h3>
      <span className="text-[10px] text-muted-foreground">{tasks.length} tasks · All completed</span>
    </div>
    <div className="divide-y divide-border">
      {tasks.map((t) => {
        const cfg = taskStatusConfig[t.status];
        const Icon = cfg.icon;
        return (
          <div key={t.id} className="px-4 py-3 flex items-center gap-3">
            <Icon className={`h-4 w-4 flex-shrink-0 ${cfg.color}`} />
            <span className="text-[10px] font-bold text-primary bg-primary/10 px-1.5 py-0.5 rounded font-mono flex-shrink-0">
              {t.id}
            </span>
            <span className="text-sm text-foreground flex-1">{t.title}</span>
            <span className="text-[11px] text-muted-foreground">{t.assignee}</span>
          </div>
        );
      })}
    </div>
  </div>
);

const LogsTab = ({ logs, version }: { logs: LogEntry[]; version: number | null }) => (
  <div className="border border-border rounded-md overflow-hidden bg-card">
    <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
      <h3 className="text-sm font-semibold text-foreground">Pipeline Execution Logs</h3>
      <span className="text-[10px] font-medium text-muted-foreground bg-secondary px-1.5 py-0.5 rounded">{version ? `v${version}` : "v?"}</span>
    </div>
    <div className="p-4 font-mono text-sm text-muted-foreground space-y-1">
      {logs.map((l, i) => (
        <div key={i} className="flex gap-6">
          <span className="text-foreground/60 flex-shrink-0">{l.time}</span>
          <span>{l.message}</span>
        </div>
      ))}
    </div>
  </div>
);

const PreviewTab = ({ device, onDeviceChange, projectId, version }: { device: "desktop" | "mobile"; onDeviceChange: (d: "desktop" | "mobile") => void; projectId: number | null; version: number | null }) => (
  <div>
    <div className="flex items-center justify-center gap-2 mb-4">
      <button
        onClick={() => onDeviceChange("desktop")}
        className={`h-7 w-7 flex items-center justify-center rounded-md transition-colors ${
          device === "desktop" ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground"
        }`}
      >
        <Monitor className="h-4 w-4" />
      </button>
      <button
        onClick={() => onDeviceChange("mobile")}
        className={`h-7 w-7 flex items-center justify-center rounded-md transition-colors ${
          device === "mobile" ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground"
        }`}
      >
        <Smartphone className="h-4 w-4" />
      </button>
    </div>

    <div className="flex items-start justify-center min-h-[500px]">
      {device === "desktop" ? (
        <div className="w-full border border-border rounded-lg overflow-hidden bg-background shadow-sm flex flex-col" style={{ height: 500 }}>
          {/* Fake browser chrome */}
          <div className="h-8 bg-secondary/60 border-b border-border flex items-center gap-1.5 px-3 flex-shrink-0">
            <span className="h-2.5 w-2.5 rounded-full bg-destructive/60" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400/60" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/60" />
            <div className="ml-3 h-4 w-56 bg-secondary rounded-sm" />
          </div>
          <iframe
            src={projectId && version ? `http://localhost:5000/api/preview/${projectId}/${version}` : "about:blank"}
            className="w-full flex-1 border-0"
          />
        </div>
      ) : (
        <div className="w-[300px] bg-background border-2 border-foreground/20 rounded-[2.5rem] overflow-hidden shadow-xl flex flex-col" style={{ height: 500 }}>
          <div className="flex justify-center py-2 flex-shrink-0">
            <div className="h-5 w-24 bg-foreground/10 rounded-full" />
          </div>
          <div className="mx-2 mb-2 rounded-2xl overflow-hidden border border-border flex-1">
            <iframe
              src={projectId && version ? `http://localhost:5000/api/preview/${projectId}/${version}` : "about:blank"}
              className="w-full h-full border-0"
            />
          </div>
        </div>
      )}
    </div>
  </div>
);

const RawJsonView = ({ data }: { data: unknown }) => (
  <div className="border border-border rounded-md bg-card overflow-hidden">
    <div className="px-4 py-2.5 border-b border-border bg-secondary/30 flex items-center gap-2">
      <Braces className="h-3.5 w-3.5 text-muted-foreground" />
      <span className="text-xs font-semibold text-foreground uppercase tracking-wider">Raw JSON</span>
    </div>
    <pre className="p-4 text-xs font-mono text-foreground overflow-x-auto leading-relaxed">
      {JSON.stringify(data, null, 2)}
    </pre>
  </div>
);


