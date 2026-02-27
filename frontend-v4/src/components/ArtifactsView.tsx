import { useState, useEffect } from "react";
import {
  FileText, Target, Code2, ListChecks, ScrollText, Eye,
  Monitor, Smartphone, ChevronRight, Download, Upload,
  Braces, FolderOpen, FileCode, CheckCircle2, Circle, Clock,
  AlertCircle, Loader2,
} from "lucide-react";
import { fetchProjectHead, fetchPrd, fetchPlan, fetchCodeFiles, fetchVersions } from "@/services/api";

type ArtifactTab = "brief" | "plan" | "code" | "tasks" | "logs" | "preview";

const tabs: { id: ArtifactTab; label: string; icon: typeof FileText }[] = [
  { id: "brief", label: "Brief", icon: FileText },
  { id: "plan", label: "Plan", icon: Target },
  { id: "code", label: "Code", icon: Code2 },
  { id: "tasks", label: "Tasks", icon: ListChecks },
  { id: "logs", label: "Logs", icon: ScrollText },
  { id: "preview", label: "Preview", icon: Eye },
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
}

export const ArtifactsView = ({ projectId, selectedVersion, onVersionSelect }: ArtifactsViewProps) => {
  const [activeTab, setActiveTab] = useState<ArtifactTab>("brief");
  const [showRawData, setShowRawData] = useState(false);
  const [previewDevice, setPreviewDevice] = useState<"desktop" | "mobile">("desktop");
  const [selectedFile, setSelectedFile] = useState(0);
  const [loading, setLoading] = useState(false);
  const [headVersion, setHeadVersion] = useState<number | null>(null);
  const [briefData, setBriefData] = useState<BriefData>({ title: "Brief", version: "", generatedBy: "Archon", sections: [] });
  const [planData, setPlanData] = useState<PlanData>({ title: "Build Plan", milestoneCount: 0, generatedBy: "Archon", milestones: [] });
  const [codeFiles, setCodeFiles] = useState<CodeFile[]>([]);
  const [logsData, setLogsData] = useState<LogEntry[]>([]);
  const [tasksData, setTasksData] = useState<Array<{ id: string; title: string; status: "done" | "running" | "pending" | "failed"; assignee: string }>>([]);

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

      const [prdRaw, planRaw, filesRaw, versionsRaw] = await Promise.all([
        fetchPrd(projectId, ver),
        fetchPlan(projectId, ver),
        fetchCodeFiles(projectId, ver),
        fetchVersions(projectId),
      ]);
      if (cancelled) return;

      // Map PRD — API returns { prd: { document_title, overview, goals, ... } }
      if (prdRaw?.prd) {
        const prd = prdRaw.prd;
        const sections: BriefData["sections"] = [];
        if (prd.overview) sections.push({ heading: "Overview", content: prd.overview });
        if (prd.goals) sections.push({ heading: "Goals", subtitle: "Success Criteria", bullets: prd.goals });
        if (prd.core_features_mvp) sections.push({ heading: "Core Features (MVP)", subtitle: "What We're Building", bullets: prd.core_features_mvp });
        if (prd.target_users) sections.push({ heading: "Target Users", subtitle: "Who We're Building For", bullets: prd.target_users });
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

      // Map logs — extract from versions data, fall back to placeholder
      const placeholderLogs: LogEntry[] = [
        { time: "—", message: "Starting pipeline..." },
        { time: "—", message: "Requirements Agent: Brief created." },
        { time: "—", message: "Architecture Agent: Build plan ready." },
        { time: "—", message: "Build Agent: Writing your code..." },
        { time: "—", message: "Build complete." },
      ];
      const matchingVersion = versionsRaw.find((v: any) => v.version === ver);
      if (matchingVersion?.execution_logs && Array.isArray(matchingVersion.execution_logs) && matchingVersion.execution_logs.length > 0) {
        setLogsData(matchingVersion.execution_logs.map((l: any) => ({
          time: l.timestamp ? new Date(l.timestamp).toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" }) : "—",
          message: l.message || String(l),
        })));
      } else {
        setLogsData(placeholderLogs);
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
            <span className="text-muted-foreground">Requirements</span>
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
            <span className="text-muted-foreground">Architecture</span>
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
            <span className="font-medium text-foreground">Code</span>
          </nav>
          <div className="h-4 w-px bg-border" />
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded border border-blue-300 text-blue-600 dark:text-blue-400 dark:border-blue-500/30 bg-blue-50 dark:bg-blue-500/10">
            ▷ Reproducible
          </span>
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded border border-emerald-300 text-emerald-600 dark:text-emerald-400 dark:border-emerald-500/30 bg-emerald-50 dark:bg-emerald-500/10">
            ○ Verified
          </span>
          <span className="text-[10px] font-bold bg-secondary text-muted-foreground px-1.5 py-0.5 rounded">{headVersion ? `V${headVersion}` : "V?"}</span>
        </div>
        <div className="flex items-center gap-2">
          <button className="h-8 px-3 text-xs font-semibold bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity flex items-center gap-1.5">
            <Upload className="h-3.5 w-3.5" /> Publish
          </button>
          <button className="h-8 px-3 text-xs font-medium border border-border rounded-md text-foreground hover:bg-secondary transition-colors flex items-center gap-1.5">
            <Download className="h-3.5 w-3.5" /> Download Code
          </button>
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
            <Braces className="h-3.5 w-3.5" /> Raw Data
          </button>
        </div>
      </div>

      {/* Tab Bar */}
      <div className="px-5 border-b border-border bg-secondary/20">
        <div className="flex items-center gap-0.5">
          {tabs.map(({ id, label, icon: Icon }) => (
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
              {label}
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

const BriefTab = ({ data }: { data: BriefData }) => (
  <div className="max-w-2xl">
    <h1 className="text-lg font-bold text-foreground">
      {data.title}
      <span className="ml-2 text-[10px] font-bold bg-primary text-primary-foreground px-1.5 py-0.5 rounded align-middle">
        {data.version || "v1"}
      </span>
    </h1>
    <p className="text-xs text-muted-foreground mt-1">v1.0 · Generated by {data.generatedBy}</p>

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
);

const PlanTab = ({ data }: { data: PlanData }) => (
  <div className="max-w-2xl">
    <h1 className="text-lg font-bold text-foreground">Build Plan</h1>
    <p className="text-xs text-muted-foreground mt-1">{data.milestoneCount} milestones · Generated by {data.generatedBy}</p>

    <div className="mt-6 space-y-5">
      {data.milestones.map((m, i) => (
        <div key={i} className="border border-border rounded-md p-5">
          <h2 className="text-sm font-bold text-foreground">{m.title}</h2>
          <div className="mt-3 space-y-0 divide-y divide-border">
            {m.tasks.map((t) => (
              <div key={t.id} className="py-2.5 flex items-start gap-3">
                <span className="text-[10px] font-bold text-primary bg-primary/10 px-1.5 py-0.5 rounded flex-shrink-0 mt-0.5 font-mono">
                  {t.id}
                </span>
                <p className="text-sm text-muted-foreground leading-relaxed">{t.description}</p>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>
);

const CodeTab = ({ files, selectedFile, onSelectFile }: { files: CodeFile[]; selectedFile: number; onSelectFile: (i: number) => void }) => {
  if (files.length === 0) return <div className="text-sm text-muted-foreground">No code files found.</div>;
  const safeIdx = Math.min(selectedFile, files.length - 1);
  return (
    <div className="grid grid-cols-[180px_1fr] gap-0 border border-border rounded-md overflow-hidden bg-card">
      {/* File Tree */}
      <div className="border-r border-border bg-secondary/30">
        <div className="px-3 py-2 flex items-center gap-1.5 text-xs text-muted-foreground">
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
      <div className="overflow-auto">
        <div className="px-4 py-2 border-b border-border flex items-center justify-between bg-secondary/20">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <FileCode className="h-3.5 w-3.5" />
            {files[safeIdx].path}
          </div>
          <span className="text-[10px] font-medium text-muted-foreground">{files[safeIdx].language}</span>
        </div>
        <pre className="p-4 text-xs font-mono text-foreground leading-relaxed overflow-x-auto">
          {files[safeIdx].content.split("\n").map((line, i) => (
            <div key={i} className="flex">
              <span className="text-muted-foreground/50 w-8 text-right mr-4 select-none flex-shrink-0">{i + 1}</span>
              <span>{line}</span>
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


