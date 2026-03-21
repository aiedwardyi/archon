import {
  ArrowRight,
  ExternalLink,
  Eye,
  GitBranch,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useEffect } from "react";
import { Link } from "react-router-dom";

type DemoProject = {
  title: string;
  archetype: string;
  prompt: string;
  summary: string;
  previewImage: string;
  previewAlt: string;
};

const examples: DemoProject[] = [
  {
    title: "Crypto Portfolio Dashboard",
    archetype: "Dashboard",
    previewImage: "/showcase/dashboard-crypto.jpg",
    previewAlt: "Crypto portfolio dashboard benchmark screenshot",
    prompt: "Build a crypto portfolio tracker with real-time prices, holdings table, and activity feed",
    summary:
      "Dense market data, portfolio visibility, and operational UI consistency across charts, tables, and activity surfaces.",
  },
  {
    title: "Halo Fan Page",
    archetype: "Game",
    previewImage: "/showcase/game-halo-full.jpg",
    previewAlt: "Halo fan page benchmark screenshot",
    prompt:
      "Build a premium Halo fan page centered on Master Chief, Cortana, and the Arbiter. Include a cinematic hero, polished character dossiers, a legendary weapon showcase, and an explorable ringworld atlas.",
    summary:
      "Cinematic composition, franchise-specific art direction, and richer visual pacing than generic card-grid output.",
  },
  {
    title: "WriteFlow Landing",
    archetype: "SaaS Landing",
    previewImage: "/showcase/saas-writeflow-full.jpg",
    previewAlt: "WriteFlow landing page benchmark screenshot",
    prompt: "Build a landing page for an AI-powered writing assistant called WriteFlow",
    summary:
      "Sharper hierarchy, stronger marketing rhythm, and a cleaner premium landing-page surface built from the same pipeline.",
  },
];

const repoUrl = "https://github.com/aiedwardyi/ai-dev-team";
const videoUrl = "https://youtu.be/ci8xDNnxJKQ";

export default function Demo() {
  useEffect(() => {
    document.title = "Archon Demo";
  }, []);

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
                to="/projects"
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
