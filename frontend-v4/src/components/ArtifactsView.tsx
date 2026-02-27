import { useState } from "react";
import {
  FileText, Target, Code2, ListChecks, ScrollText, Eye,
  Monitor, Smartphone, ChevronRight, Download, Upload,
  Braces, FolderOpen, FileCode, CheckCircle2, Circle, Clock,
  AlertCircle,
} from "lucide-react";

type ArtifactTab = "brief" | "plan" | "code" | "tasks" | "logs" | "preview";

const tabs: { id: ArtifactTab; label: string; icon: typeof FileText }[] = [
  { id: "brief", label: "Brief", icon: FileText },
  { id: "plan", label: "Plan", icon: Target },
  { id: "code", label: "Code", icon: Code2 },
  { id: "tasks", label: "Tasks", icon: ListChecks },
  { id: "logs", label: "Logs", icon: ScrollText },
  { id: "preview", label: "Preview", icon: Eye },
];

// ── Mock Data ──

const briefData = {
  title: "Agumon - Digital Monster Fan Page - Mini Game and Overlay Update",
  version: "v9",
  generatedBy: "Archon",
  sections: [
    {
      heading: "Overview",
      content: "This document outlines the requirements for adding a mini game feature and a dark overlay to the hero background image on the Agumon - Digital Monster Fan Page. The mini game will allow users to interact with a Digimon character, enhancing user engagement.",
    },
    {
      heading: "Goals",
      subtitle: "Success Criteria",
      bullets: [
        "Implement a mini game where users can click on a Digimon to make it attack.",
        "Add a dark overlay to the existing hero background image to improve visual contrast.",
        "Ensure the mini game is responsive and works on both desktop and mobile devices.",
        "Maintain the current branding and theme of the Agumon fan page.",
        "Test the new features for functionality and user experience before deployment.",
      ],
    },
    {
      heading: "Core Features (MVP)",
      subtitle: "What We're Building",
      bullets: [
        "Clickable Digimon character that triggers an attack animation.",
        "Score tracking for the mini game.",
        "Dark overlay on the hero background image.",
      ],
    },
    {
      heading: "Target Users",
      subtitle: "Who We're Building For",
      bullets: [
        "Fans of Digimon looking for interactive content.",
        "Casual gamers interested in quick mini games.",
        "Visitors to the Agumon fan page seeking engaging experiences.",
      ],
    },
  ],
};

const planData = {
  title: "Build Plan",
  milestoneCount: 4,
  generatedBy: "Archon",
  milestones: [
    {
      title: "Milestone 1: Planning & Initial Design",
      tasks: [
        { id: "PLAN-1", description: "Review PRD and existing Agumon Fan Page structure to identify integration points for the mini-game and dark overlay." },
        { id: "PLAN-2", description: "Define specific attack animations for the Digimon character and determine preferred opacity for the dark overlay." },
        { id: "PLAN-3", description: "Outline the scoring mechanism and display requirements for the mini-game." },
      ],
    },
    {
      title: "Milestone 2: Core Feature Development",
      tasks: [
        { id: "FE-1", description: "Integrate mini-game and dark overlay into existing Agumon Fan Page (src/index.html and src/style.css) with inline scripts and styles." },
        { id: "FE-2", description: "Implement the dark overlay for the hero background image using CSS, ensuring it enhances text visibility." },
        { id: "GAME-1", description: "Develop the JavaScript logic for the clickable Digimon character, triggering attack animations and score updates." },
      ],
    },
    {
      title: "Milestone 3: Responsiveness & Refinement",
      tasks: [
        { id: "FE-3", description: "Ensure the mini-game and dark overlay are fully responsive across desktop and mobile devices." },
        { id: "GAME-2", description: "Implement visual feedback for each attack, such as a temporary score display or hit indicator." },
      ],
    },
    {
      title: "Milestone 4: Testing & Deployment Preparation",
      tasks: [
        { id: "QA-1", description: "Conduct comprehensive functional testing of the mini-game and dark overlay on various browsers and devices." },
        { id: "QA-2", description: "Verify that the new features do not introduce any regressions or critical bugs to the existing fan page." },
        { id: "PLAN-4", description: "Prepare deployment package and documentation for the updated Agumon Fan Page." },
      ],
    },
  ],
};

const codeFiles = [
  {
    path: "src/index.html",
    language: "Html",
    content: `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agumon - Digital Monster Fan Page</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="./style.css">
</head>
<body>
  <header class="header">
    <div class="container header-inner">
      <div class="logo">AGUMON</div>
      <nav class="nav">
        <a href="#hero" class="nav-link">Home</a>
        <a href="#features" class="nav-link">Features</a>
        <a href="#evolution" class="nav-link">Evolution</a>
        <a href="#community" class="nav-link">Community</a>
        <a href="#game" class="nav-link">Mini Game</a>
      </nav>
      <button class="cta-button" id="joinBtn">Join Community</button>
    </div>
  </header>
  <section class="hero" id="hero">
    <div class="hero-bg"></div>
    <div class="hero-overlay"></div>
    <div class="container hero-content">
      <div class="hero-text">
        <div class="badge">CHAMPION LEVEL DIGIMON</div>
        <h1 class="hero-title">MEET AGUMON</h1>
        <p class="hero-subtitle">The legendary Dinosaur Digimon...</p>
        <div class="hero-actions">
          <button class="btn-primary">Explore Powers</button>
          <button class="btn-secondary">Watch Evolution</button>
        </div>
      </div>
    </div>
  </section>
</body>
</html>`,
  },
  {
    path: "src/style.css",
    language: "Css",
    content: `* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Inter', sans-serif;
  background: #0a0a0a;
  color: #ffffff;
}

.header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: rgba(10, 10, 10, 0.9);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.hero {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 1;
}

.btn-primary {
  padding: 12px 32px;
  background: linear-gradient(135deg, #ff6b35, #ff8c42);
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 600;
  cursor: pointer;
}`,
  },
];

const tasksData = [
  { id: "PLAN-1", title: "Review PRD and existing page structure", status: "done" as const, assignee: "Requirements Agent" },
  { id: "PLAN-2", title: "Define attack animations and overlay opacity", status: "done" as const, assignee: "Requirements Agent" },
  { id: "PLAN-3", title: "Outline scoring mechanism and display", status: "done" as const, assignee: "Architecture Agent" },
  { id: "FE-1", title: "Integrate mini-game into Agumon Fan Page", status: "done" as const, assignee: "Build Agent" },
  { id: "FE-2", title: "Implement dark overlay with CSS", status: "done" as const, assignee: "Build Agent" },
  { id: "GAME-1", title: "Develop clickable Digimon game logic", status: "done" as const, assignee: "Build Agent" },
  { id: "FE-3", title: "Make mini-game responsive across devices", status: "done" as const, assignee: "Build Agent" },
  { id: "GAME-2", title: "Add visual feedback for attacks", status: "done" as const, assignee: "Build Agent" },
  { id: "QA-1", title: "Functional testing on browsers and devices", status: "done" as const, assignee: "QA Agent" },
  { id: "QA-2", title: "Verify no regressions on existing page", status: "done" as const, assignee: "QA Agent" },
  { id: "PLAN-4", title: "Prepare deployment package", status: "done" as const, assignee: "Architecture Agent" },
];

const logsData = [
  { time: "11:27:28", message: "Starting pipeline..." },
  { time: "11:27:28", message: "Requirements Agent: Analyzing your request..." },
  { time: "11:27:42", message: "Requirements Agent: Brief created." },
  { time: "11:27:42", message: "Architecture Agent: Planning the build..." },
  { time: "11:28:08", message: "Architecture Agent: Build plan ready." },
  { time: "11:28:08", message: "Design Agent: Generating visuals..." },
  { time: "11:28:09", message: "Design Agent: No images generated, continuing..." },
  { time: "11:28:09", message: "Build Agent: Writing your code..." },
  { time: "11:30:23", message: "Build Agent: Created src/index.html" },
  { time: "11:30:23", message: "Build Agent: Created src/style.css" },
  { time: "11:30:23", message: "Build complete." },
];

// ── Component ──

export const ArtifactsView = () => {
  const [activeTab, setActiveTab] = useState<ArtifactTab>("brief");
  const [showRawData, setShowRawData] = useState(false);
  const [previewDevice, setPreviewDevice] = useState<"desktop" | "mobile">("desktop");
  const [selectedFile, setSelectedFile] = useState(0);

  const rawDataAvailable = ["brief", "plan"].includes(activeTab);

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
          <span className="text-[10px] font-bold bg-secondary text-muted-foreground px-1.5 py-0.5 rounded">V9</span>
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
        {activeTab === "brief" && !showRawData && <BriefTab />}
        {activeTab === "brief" && showRawData && <RawJsonView data={briefData} />}
        {activeTab === "plan" && !showRawData && <PlanTab />}
        {activeTab === "plan" && showRawData && <RawJsonView data={planData} />}
        {activeTab === "code" && <CodeTab selectedFile={selectedFile} onSelectFile={setSelectedFile} />}
        {activeTab === "tasks" && <TasksTab />}
        {activeTab === "logs" && <LogsTab />}
        {activeTab === "preview" && <PreviewTab device={previewDevice} onDeviceChange={setPreviewDevice} />}
      </div>
    </div>
  );
};

// ── Sub-components ──

const BriefTab = () => (
  <div className="max-w-2xl">
    <h1 className="text-lg font-bold text-foreground">
      {briefData.title}
      <span className="ml-2 text-[10px] font-bold bg-primary text-primary-foreground px-1.5 py-0.5 rounded align-middle">
        v9
      </span>
    </h1>
    <p className="text-xs text-muted-foreground mt-1">v1.0 · Generated by Archon</p>

    <div className="mt-6 space-y-5">
      {briefData.sections.map((s, i) => (
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

const PlanTab = () => (
  <div className="max-w-2xl">
    <h1 className="text-lg font-bold text-foreground">Build Plan</h1>
    <p className="text-xs text-muted-foreground mt-1">{planData.milestoneCount} milestones · Generated by Archon</p>

    <div className="mt-6 space-y-5">
      {planData.milestones.map((m, i) => (
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

const CodeTab = ({ selectedFile, onSelectFile }: { selectedFile: number; onSelectFile: (i: number) => void }) => (
  <div className="grid grid-cols-[180px_1fr] gap-0 border border-border rounded-md overflow-hidden bg-card">
    {/* File Tree */}
    <div className="border-r border-border bg-secondary/30">
      <div className="px-3 py-2 flex items-center gap-1.5 text-xs text-muted-foreground">
        <FolderOpen className="h-3.5 w-3.5" />
        <span className="font-medium">src</span>
      </div>
      {codeFiles.map((f, i) => (
        <button
          key={f.path}
          onClick={() => onSelectFile(i)}
          className={`w-full text-left pl-6 pr-3 py-1.5 text-xs flex items-center gap-1.5 transition-colors ${
            selectedFile === i
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
          {codeFiles[selectedFile].path}
        </div>
        <span className="text-[10px] font-medium text-muted-foreground">{codeFiles[selectedFile].language}</span>
      </div>
      <pre className="p-4 text-xs font-mono text-foreground leading-relaxed overflow-x-auto">
        {codeFiles[selectedFile].content.split("\n").map((line, i) => (
          <div key={i} className="flex">
            <span className="text-muted-foreground/50 w-8 text-right mr-4 select-none flex-shrink-0">{i + 1}</span>
            <span>{line}</span>
          </div>
        ))}
      </pre>
    </div>
  </div>
);

const taskStatusConfig = {
  done: { icon: CheckCircle2, color: "text-emerald-500" },
  running: { icon: Clock, color: "text-blue-500" },
  pending: { icon: Circle, color: "text-muted-foreground" },
  failed: { icon: AlertCircle, color: "text-destructive" },
};

const TasksTab = () => (
  <div className="border border-border rounded-md overflow-hidden bg-card">
    <div className="px-4 py-2.5 border-b border-border bg-secondary/30 flex items-center justify-between">
      <h3 className="text-xs font-semibold text-foreground uppercase tracking-wider">Pipeline Tasks</h3>
      <span className="text-[10px] text-muted-foreground">{tasksData.length} tasks · All completed</span>
    </div>
    <div className="divide-y divide-border">
      {tasksData.map((t) => {
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

const LogsTab = () => (
  <div className="border border-border rounded-md overflow-hidden bg-card">
    <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
      <h3 className="text-sm font-semibold text-foreground">Pipeline Execution Logs</h3>
      <span className="text-[10px] font-medium text-muted-foreground bg-secondary px-1.5 py-0.5 rounded">v9</span>
    </div>
    <div className="p-4 font-mono text-sm text-muted-foreground space-y-1">
      {logsData.map((l, i) => (
        <div key={i} className="flex gap-6">
          <span className="text-foreground/60 flex-shrink-0">{l.time}</span>
          <span>{l.message}</span>
        </div>
      ))}
    </div>
  </div>
);

const PreviewTab = ({ device, onDeviceChange }: { device: "desktop" | "mobile"; onDeviceChange: (d: "desktop" | "mobile") => void }) => (
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
        <div className="w-full border border-border rounded-lg overflow-hidden bg-background shadow-sm">
          {/* Fake browser chrome */}
          <div className="h-8 bg-secondary/60 border-b border-border flex items-center gap-1.5 px-3">
            <span className="h-2.5 w-2.5 rounded-full bg-destructive/60" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400/60" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/60" />
            <div className="ml-3 h-4 w-56 bg-secondary rounded-sm" />
          </div>
          {/* Dark site mockup */}
          <div className="bg-[hsl(0,0%,4%)] text-white">
            {/* Nav */}
            <div className="flex items-center justify-between px-6 py-3 border-b border-white/10">
              <span className="text-sm font-bold text-orange-400">AGUMON</span>
              <div className="flex items-center gap-4 text-[11px] text-white/70">
                <span>Home</span><span>Features</span><span>Evolution</span><span>Community</span><span>Mini Game</span>
              </div>
              <span className="text-[10px] font-semibold bg-orange-500 text-white px-3 py-1 rounded-full">Join Community</span>
            </div>
            {/* Hero */}
            <div className="px-8 py-12">
              <span className="text-[10px] font-semibold text-orange-300 bg-orange-500/20 border border-orange-500/30 px-2 py-0.5 rounded">
                CHAMPION LEVEL DIGIMON
              </span>
              <h2 className="text-4xl font-black mt-3 leading-none">
                <span className="text-orange-200">MEET</span><br />
                <span className="text-orange-400">AGUMON</span>
              </h2>
              <p className="text-xs text-white/60 mt-3 max-w-sm leading-relaxed">
                The legendary Dinosaur Digimon who partners with brave DigiDestined across the Digital World. Known for incredible courage and devastating fire attacks.
              </p>
              <div className="flex gap-2 mt-4">
                <span className="text-[10px] font-semibold bg-orange-500 text-white px-4 py-2 rounded-lg">Explore Powers</span>
                <span className="text-[10px] font-semibold bg-white/10 text-white px-4 py-2 rounded-lg border border-white/20">Watch Evolution</span>
              </div>
              <div className="flex gap-8 mt-8">
                {[{ v: "25", l: "YEARS LEGACY" }, { v: "8", l: "EVOLUTION FORMS" }, { v: "150", l: "BATTLES WON" }].map(({ v, l }) => (
                  <div key={l} className="text-center">
                    <div className="text-xl font-black text-orange-400">{v}</div>
                    <div className="text-[9px] text-white/40 tracking-wider">{l}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="w-[300px] bg-background border-2 border-foreground/20 rounded-[2.5rem] overflow-hidden shadow-xl">
          <div className="flex justify-center py-2">
            <div className="h-5 w-24 bg-foreground/10 rounded-full" />
          </div>
          <div className="mx-2 mb-2 rounded-2xl overflow-hidden border border-border">
            <div className="bg-[hsl(0,0%,4%)] text-white">
              {/* Mobile Nav */}
              <div className="flex items-center justify-between px-4 py-2 border-b border-white/10">
                <span className="text-xs font-bold text-orange-400">AGUMON</span>
                <span className="text-[9px] font-semibold bg-orange-500 text-white px-2 py-0.5 rounded-full">Join Community</span>
              </div>
              <div className="flex justify-center gap-3 py-1.5 text-[9px] text-white/60 border-b border-white/10">
                <span>Home</span><span>Features</span><span>Evolution</span><span>Community</span><span>Mini Game</span>
              </div>
              {/* Mobile Hero */}
              <div className="px-4 py-8 text-center">
                <span className="text-[9px] font-semibold text-orange-300 bg-orange-500/20 border border-orange-500/30 px-2 py-0.5 rounded">
                  CHAMPION LEVEL DIGIMON
                </span>
                <h2 className="text-2xl font-black mt-3 leading-none">
                  <span className="text-orange-200">MEET</span><br />
                  <span className="text-orange-400">AGUMON</span>
                </h2>
                <p className="text-[10px] text-white/60 mt-2 leading-relaxed">
                  The legendary Dinosaur Digimon who partners with brave DigiDestined across the Digital World. Known for incredible courage and devastating fire attacks.
                </p>
                <div className="flex justify-center gap-2 mt-4">
                  <span className="text-[9px] font-semibold bg-orange-500 text-white px-3 py-1.5 rounded-lg">Explore Powers</span>
                  <span className="text-[9px] font-semibold bg-white/10 text-white px-3 py-1.5 rounded-lg border border-white/20">Watch Evolution</span>
                </div>
                <div className="flex justify-center gap-6 mt-6">
                  {[{ v: "17", l: "YEARS LEGACY" }].map(({ v, l }) => (
                    <div key={l} className="text-center">
                      <div className="text-lg font-black text-orange-400">{v}</div>
                      <div className="text-[8px] text-white/40 tracking-wider">{l}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
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
