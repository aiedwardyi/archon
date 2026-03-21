import {
  AlertCircle,
  ArrowRight,
  ExternalLink,
  Eye,
  FileText,
  GitBranch,
  Layers3,
  Lock,
  PlayCircle,
  ShieldCheck,
  Sparkles,
  Wand2,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";

type DemoView = "preview" | "versions" | "pipeline" | "governance" | "brief";

type DemoProject = {
  id: string;
  code: string;
  title: string;
  archetype: string;
  prompt: string;
  summary: string;
  previewImage: string;
  previewAlt: string;
  score: string;
  qualityTier: string;
  latestVersion: string;
  lineage: string;
  artifactCount: number;
  surfaceNotes: Partial<Record<DemoView, string>>;
};

const examples: DemoProject[] = [
  {
    id: "dashboard",
    code: "demo-001",
    title: "Crypto Portfolio Dashboard",
    archetype: "Dashboard",
    previewImage: "/showcase/dashboard-crypto.jpg",
    previewAlt: "Crypto portfolio dashboard benchmark screenshot",
    prompt: "Build a crypto portfolio tracker with real-time prices, holdings table, and activity feed",
    summary:
      "Dense market data, portfolio visibility, and operational UI consistency across charts, tables, and activity surfaces.",
    score: "84 / 100",
    qualityTier: "High",
    latestVersion: "v12",
    lineage: "seeded benchmark execution",
    artifactCount: 18,
    surfaceNotes: {
      preview: "Representative generated output from the benchmark-backed dashboard set.",
      governance: "Governance factsheet for the dashboard flow, including model registry and quality scoring.",
      versions: "Version lineage and preview recovery surface from the same product area.",
      pipeline: "Execution pipeline view showing PM, planning, build, and governance stages.",
      brief: "Prompt and artifact record retained alongside the generated preview.",
    },
  },
  {
    id: "halo",
    code: "demo-002",
    title: "Halo Fan Page",
    archetype: "Game",
    previewImage: "/showcase/game-halo-full.jpg",
    previewAlt: "Halo fan page benchmark screenshot",
    prompt:
      "Build a premium Halo fan page centered on Master Chief, Cortana, and the Arbiter. Include a cinematic hero, polished character dossiers, a legendary weapon showcase, and an explorable ringworld atlas.",
    summary:
      "Cinematic composition, franchise-specific art direction, and richer visual pacing than generic card-grid output.",
    score: "91 / 100",
    qualityTier: "Showcase",
    latestVersion: "v4",
    lineage: "showcase benchmark execution",
    artifactCount: 14,
    surfaceNotes: {
      preview: "Hero demo for the game archetype with benchmark-tuned visual direction.",
      governance: "Representative governance surface reused in demo mode to show the same artifact pattern.",
      versions: "Representative version timeline surface. Public demo mode keeps this seeded and read-only.",
      pipeline: "Representative pipeline trace. Public demo mode does not execute new agent runs.",
      brief: "Prompt and artifact style preserved as part of the same versioned delivery model.",
    },
  },
  {
    id: "writeflow",
    code: "demo-003",
    title: "WriteFlow Landing",
    archetype: "SaaS Landing",
    previewImage: "/showcase/saas-writeflow-full.jpg",
    previewAlt: "WriteFlow landing page benchmark screenshot",
    prompt: "Build a landing page for an AI-powered writing assistant called WriteFlow",
    summary:
      "Sharper hierarchy, stronger marketing rhythm, and a cleaner premium landing-page surface built from the same pipeline.",
    score: "86 / 100",
    qualityTier: "High",
    latestVersion: "v7",
    lineage: "showcase benchmark execution",
    artifactCount: 13,
    surfaceNotes: {
      preview: "Landing-page benchmark surfaced from the same underlying artifact pipeline.",
      governance: "Representative governance factsheet carried over to show auditability at the product level.",
      versions: "Read-only timeline surface seeded from saved executions instead of live generation.",
      pipeline: "Pipeline surface is visible in the public demo, but build actions remain disabled.",
      brief: "Artifact browsing remains available even though generation endpoints are not public.",
    },
  },
];

const staticSurfaceImages: Record<Exclude<DemoView, "preview">, string> = {
  versions: "/showcase/dashboard-versions.png",
  pipeline: "/showcase/dashboard-pipeline.png",
  governance: "/showcase/dashboard-governance.png",
  brief: "/showcase/dashboard-brief.png",
};

const viewLabels: Record<DemoView, string> = {
  preview: "Preview",
  versions: "Versions",
  pipeline: "Pipeline",
  governance: "Governance",
  brief: "Brief",
};

const repoUrl = "https://github.com/aiedwardyi/ai-dev-team";
const videoUrl = "https://youtu.be/ci8xDNnxJKQ";

function DemoWorkspace() {
  const location = useLocation();
  const [selectedId, setSelectedId] = useState(examples[0].id);
  const [activeView, setActiveView] = useState<DemoView>("preview");

  const selected = examples.find((project) => project.id === selectedId) ?? examples[0];
  const currentImage = activeView === "preview" ? selected.previewImage : staticSurfaceImages[activeView];

  return (
    <main className="min-h-screen bg-[#07111f] text-slate-100">
      <div className="border-b border-cyan-500/15 bg-[linear-gradient(180deg,#08111d_0%,#091628_100%)]">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-6 sm:px-10 lg:px-12">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/25 bg-cyan-400/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.24em] text-cyan-200">
                <Lock className="h-3.5 w-3.5" />
                Read-Only Demo Workspace
              </div>
              <h1 className="mt-4 text-3xl font-semibold tracking-[-0.04em] text-white sm:text-4xl">
                Seeded enterprise demo
              </h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
                This workspace uses saved benchmark-backed executions. Preview, versions, pipeline, governance, and artifact browsing
                are visible here, but live generation and mutation actions are disabled in public mode.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                disabled
                className="inline-flex cursor-not-allowed items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-slate-500"
              >
                <Wand2 className="h-4 w-4" />
                New Build Disabled
              </button>
              <button
                type="button"
                disabled
                className="inline-flex cursor-not-allowed items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-slate-500"
              >
                <ArrowRight className="h-4 w-4" />
                Iterate Disabled
              </button>
              <Link
                to={location.pathname}
                className="inline-flex items-center gap-2 rounded-xl border border-cyan-400/25 bg-cyan-400/10 px-4 py-2.5 text-sm font-semibold text-cyan-100 transition hover:bg-cyan-400/15"
              >
                Back To Overview
              </Link>
            </div>
          </div>

          <div className="flex items-start gap-3 rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <p>
              Public demo mode is intentionally non-billable. No auth, pipeline execution, reset, publish, or delete actions are
              exposed here.
            </p>
          </div>
        </div>
      </div>

      <div className="mx-auto grid min-h-[calc(100vh-140px)] max-w-7xl gap-6 px-6 py-8 sm:px-10 lg:grid-cols-[320px_minmax(0,1fr)] lg:px-12">
        <aside className="rounded-3xl border border-white/10 bg-white/[0.03] p-5">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Seeded Projects</div>
              <h2 className="mt-2 text-xl font-semibold text-white">Public demo set</h2>
            </div>
            <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-400">3 projects</span>
          </div>

          <div className="mt-5 space-y-3">
            {examples.map((project) => {
              const selectedCard = project.id === selected.id;
              return (
                <button
                  key={project.id}
                  type="button"
                  onClick={() => {
                    setSelectedId(project.id);
                    setActiveView("preview");
                  }}
                  className={`w-full rounded-2xl border px-4 py-4 text-left transition ${
                    selectedCard
                      ? "border-cyan-300/40 bg-cyan-400/10 shadow-[0_20px_50px_-32px_rgba(34,211,238,0.8)]"
                      : "border-white/10 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.05]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">{project.archetype}</div>
                      <div className="mt-2 text-lg font-semibold text-white">{project.title}</div>
                    </div>
                    <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[11px] text-slate-400">
                      {project.code}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-400">{project.summary}</p>
                  <div className="mt-4 flex flex-wrap gap-2 text-xs">
                    <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-slate-300">
                      {project.latestVersion}
                    </span>
                    <span className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-2 py-1 text-cyan-100">
                      {project.qualityTier}
                    </span>
                    <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-slate-400">
                      {project.score}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </aside>

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
          <div className="rounded-3xl border border-white/10 bg-white/[0.03]">
            <div className="border-b border-white/10 px-6 py-5">
              <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">{selected.archetype}</div>
                  <h2 className="mt-2 text-3xl font-semibold tracking-[-0.03em] text-white">{selected.title}</h2>
                  <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">{selected.summary}</p>
                </div>
                <div className="grid min-w-[220px] grid-cols-2 gap-3 text-sm">
                  <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                    <div className="text-xs uppercase tracking-[0.16em] text-slate-500">Latest Version</div>
                    <div className="mt-2 text-lg font-semibold text-white">{selected.latestVersion}</div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                    <div className="text-xs uppercase tracking-[0.16em] text-slate-500">Quality Tier</div>
                    <div className="mt-2 text-lg font-semibold text-white">{selected.qualityTier}</div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                    <div className="text-xs uppercase tracking-[0.16em] text-slate-500">Score</div>
                    <div className="mt-2 text-lg font-semibold text-white">{selected.score}</div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                    <div className="text-xs uppercase tracking-[0.16em] text-slate-500">Artifacts</div>
                    <div className="mt-2 text-lg font-semibold text-white">{selected.artifactCount}</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="border-b border-white/10 px-6 py-4">
              <div className="flex flex-wrap gap-3">
                {(["preview", "versions", "pipeline", "governance", "brief"] as DemoView[]).map((view) => (
                  <button
                    key={view}
                    type="button"
                    onClick={() => setActiveView(view)}
                    className={`rounded-xl px-4 py-2 text-sm font-semibold transition ${
                      activeView === view
                        ? "bg-cyan-400 text-slate-950"
                        : "border border-white/10 bg-white/[0.03] text-slate-300 hover:border-white/20 hover:bg-white/[0.06]"
                    }`}
                  >
                    {viewLabels[view]}
                  </button>
                ))}
              </div>
            </div>

            <div className="p-6">
              <div className="overflow-hidden rounded-3xl border border-white/10 bg-[#08111d]">
                <img src={currentImage} alt={selected.previewAlt} className="w-full object-cover object-top" />
              </div>
              <div className="mt-4 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">{viewLabels[activeView]}</div>
                  <p className="mt-2 max-w-3xl text-sm leading-7 text-slate-400">
                    {selected.surfaceNotes[activeView] ?? "Representative seeded demo surface."}
                  </p>
                </div>
                <a
                  href={currentImage}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm font-semibold text-white transition hover:border-cyan-300/40 hover:bg-white/10"
                >
                  Open Full Capture
                  <ExternalLink className="h-4 w-4" />
                </a>
              </div>
            </div>
          </div>

          <aside className="space-y-6">
            <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-5">
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">Prompt</div>
              <blockquote className="mt-3 border-l border-cyan-300/30 pl-4 text-sm italic leading-7 text-slate-300">
                “{selected.prompt}”
              </blockquote>
              <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.03] p-3 text-xs leading-6 text-slate-400">
                Lineage: {selected.lineage}
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-5">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">
                <Layers3 className="h-4 w-4" />
                Version Timeline
              </div>
              <div className="mt-4 space-y-3">
                {[
                  { version: selected.latestVersion, label: "Current seeded demo", state: "Ready" },
                  { version: `v${Math.max(1, Number(selected.latestVersion.slice(1)) - 1)}`, label: "Prior accepted execution", state: "Archived" },
                  { version: `v${Math.max(1, Number(selected.latestVersion.slice(1)) - 2)}`, label: "Benchmark checkpoint", state: "Archived" },
                ].map((entry, index) => (
                  <div key={`${selected.id}-${entry.version}-${index}`} className="rounded-2xl border border-white/10 bg-white/[0.03] p-3">
                    <div className="flex items-center justify-between">
                      <div className="font-semibold text-white">{entry.version}</div>
                      <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[11px] text-slate-400">
                        {entry.state}
                      </span>
                    </div>
                    <div className="mt-2 text-sm text-slate-400">{entry.label}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-5">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">
                <PlayCircle className="h-4 w-4" />
                Disabled Actions
              </div>
              <div className="mt-4 grid gap-3">
                {[
                  "Execute new pipeline",
                  "Iterate prompt",
                  "Restore selected version",
                  "Publish public preview",
                ].map((label) => (
                  <button
                    key={label}
                    type="button"
                    disabled
                    className="inline-flex cursor-not-allowed items-center justify-between rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-left text-sm font-semibold text-slate-500"
                  >
                    <span>{label}</span>
                    <Lock className="h-4 w-4" />
                  </button>
                ))}
              </div>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}

export default function Demo() {
  const location = useLocation();
  const workspaceMode = new URLSearchParams(location.search).get("view") === "workspace";

  useEffect(() => {
    document.title = workspaceMode ? "Archon Demo Workspace" : "Archon Demo";
  }, [workspaceMode]);

  if (workspaceMode) {
    return <DemoWorkspace />;
  }

  return (
    <main className="min-h-screen bg-[#07111f] text-slate-100">
      <section className="relative overflow-hidden border-b border-cyan-500/20 bg-[radial-gradient(circle_at_top,rgba(34,211,238,0.14),transparent_42%),linear-gradient(180deg,#07111f_0%,#0b1730_48%,#08111d_100%)]">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(148,163,184,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.08)_1px,transparent_1px)] bg-[size:48px_48px] opacity-[0.12]" />
        <div className="relative mx-auto max-w-7xl px-6 py-20 sm:px-10 lg:px-12 lg:py-24">
          <div className="max-w-4xl">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-cyan-400/25 bg-cyan-400/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.24em] text-cyan-200">
              <Sparkles className="h-3.5 w-3.5" />
              Public Read-Only Showcase
            </div>
            <h1 className="max-w-4xl text-4xl font-semibold tracking-[-0.04em] text-white sm:text-5xl lg:text-6xl">
              Archon turns prompts into versioned application executions with preview, eval, and governance artifacts.
            </h1>
            <p className="mt-6 max-w-3xl text-base leading-8 text-slate-300 sm:text-lg">
              This public deployment is intentionally static. It showcases the strongest benchmark-backed outputs and core
              product surfaces without exposing live build endpoints, model execution paths, or billable generation APIs.
            </p>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-cyan-100/80 sm:text-base">
              This page is the public overview. The seeded enterprise demo lives one click deeper and stays fully read-only.
            </p>

            <div className="mt-8 grid gap-3 text-sm text-slate-300 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="font-medium text-white">Multi-agent delivery</div>
                <div className="mt-1 text-slate-400">PM, planner, design, engineer, eval, and governance stages.</div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="font-medium text-white">Versioned artifacts</div>
                <div className="mt-1 text-slate-400">Brief, plan, code, preview, logs, and factsheet outputs.</div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="font-medium text-white">Model-agnostic</div>
                <div className="mt-1 text-slate-400">OpenAI, Anthropic, Google, IBM Watson, and local-model hooks.</div>
              </div>
            </div>

            <div className="mt-10 flex flex-col gap-3 sm:flex-row">
              <a
                href={repoUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
              >
                View Repository
                <ExternalLink className="h-4 w-4" />
              </a>
              <a
                href={videoUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/15 bg-white/5 px-5 py-3 text-sm font-semibold text-white transition hover:border-cyan-300/40 hover:bg-white/10"
              >
                Watch Demo
                <ArrowRight className="h-4 w-4" />
              </a>
              <Link
                to={{ pathname: location.pathname, search: "?view=workspace" }}
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-cyan-400/25 bg-cyan-400/10 px-5 py-3 text-sm font-semibold text-cyan-100 transition hover:border-cyan-300/40 hover:bg-cyan-400/15"
              >
                Check Demo
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-16 sm:px-10 lg:px-12">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-cyan-300">Selected Generated Examples</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-[-0.03em] text-white">Three benchmark-backed demos</h2>
          </div>
          <p className="max-w-2xl text-sm leading-7 text-slate-400">
            These examples are the strongest benchmark-backed outputs currently included in the repo. They are shown here as a
            static public showcase, not as live generation endpoints.
          </p>
        </div>

        <div className="mt-10 grid gap-6 xl:grid-cols-3">
          {examples.map((example) => (
            <article key={example.title} className="overflow-hidden rounded-3xl border border-white/10 bg-white/[0.03] shadow-[0_30px_80px_-45px_rgba(34,211,238,0.45)]">
              <a href={example.previewImage} target="_blank" rel="noreferrer" className="block">
                <img src={example.previewImage} alt={example.previewAlt} className="h-72 w-full object-cover object-top" />
              </a>
              <div className="p-6">
                <div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">{example.archetype}</div>
                <h3 className="mt-3 text-2xl font-semibold text-white">{example.title}</h3>
                <p className="mt-4 text-sm leading-7 text-slate-300">{example.summary}</p>
                <blockquote className="mt-5 border-l border-cyan-300/30 pl-4 text-sm italic leading-7 text-slate-400">
                  “{example.prompt}”
                </blockquote>
                <div className="mt-6">
                  <a
                    href={example.previewImage}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-4 py-2 text-sm font-semibold text-white transition hover:border-cyan-300/40 hover:bg-white/10"
                  >
                    Open Full Capture
                    <ExternalLink className="h-4 w-4" />
                  </a>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="border-y border-white/10 bg-[#08111d]">
        <div className="mx-auto max-w-7xl px-6 py-16 sm:px-10 lg:px-12">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-cyan-300">Core Product Surfaces</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-[-0.03em] text-white">The product is more than prompt-to-page generation</h2>
            <p className="mt-4 text-base leading-8 text-slate-400">
              The differentiator in this repo is not a generic chat shell. It is the delivery workflow around the generated app:
              version history, preview recovery, governance artifacts, and a visible multi-agent pipeline.
            </p>
          </div>

          <div className="mt-10 grid gap-6 lg:grid-cols-3">
            {[
              {
                title: "Governance Factsheet",
                image: "/showcase/dashboard-governance.png",
                description:
                  "Model registry, quality scoring, and review posture captured as part of the artifact set rather than as a separate slide deck.",
                icon: ShieldCheck,
              },
              {
                title: "Versions And Preview",
                image: "/showcase/dashboard-versions.png",
                description:
                  "Version lineage, prompt traceability, and a built-in preview surface for comparing generated executions over time.",
                icon: GitBranch,
              },
              {
                title: "Pipeline View",
                image: "/showcase/dashboard-pipeline.png",
                description:
                  "A visible agent pipeline showing how requirements, planning, build, and governance stages move through the system.",
                icon: Eye,
              },
            ].map((surface) => {
              const Icon = surface.icon;
              return (
                <article key={surface.title} className="overflow-hidden rounded-3xl border border-white/10 bg-white/[0.03]">
                  <a href={surface.image} target="_blank" rel="noreferrer" className="block">
                    <img src={surface.image} alt={surface.title} className="h-64 w-full object-cover object-top" />
                  </a>
                  <div className="p-6">
                    <div className="flex items-center gap-2 text-cyan-300">
                      <Icon className="h-4 w-4" />
                      <span className="text-xs font-semibold uppercase tracking-[0.2em]">Surface</span>
                    </div>
                    <h3 className="mt-3 text-2xl font-semibold text-white">{surface.title}</h3>
                    <p className="mt-4 text-sm leading-7 text-slate-400">{surface.description}</p>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      </section>
    </main>
  );
}
