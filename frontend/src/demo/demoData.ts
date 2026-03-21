type DemoVersionSeed = {
  executionId: number;
  version: number;
  status: string;
  createdAt: string;
  parentExecutionId?: number | null;
  promptHistory: Array<{ role: string; content: string }>;
  filesGenerated: number;
  imagesGenerated: number;
  durationSeconds: number;
  modelUsed: string;
  qualityTier: string;
  readinessScore: number;
};

type DemoFactsheet = {
  factsheet_version: string;
  generated_at: string;
  project: { id: number; name: string; version: number; execution_id: number };
  prompt_summary: string;
  pipeline: { status: string; agent_sequence: string[]; duration_seconds: number | null; ui_archetype: string | null };
  model_registry: Array<{ agent_role: string; model: string; provider: string }>;
  usage: { tokens_used: number | null; estimated_cost_usd: number | null; credits_used: number | null };
  outputs: { files_generated: number; images_generated: number };
  scoring: {
    prompt_quality: {
      score: number;
      label: string;
      sentiment: string;
      sentiment_score: number;
      keywords: string[];
      domain: string;
      powered_by: string;
    };
    build_confidence: {
      score: number;
      label: string;
      breakdown: Array<{ factor: string; points: number; note: string }>;
    };
  };
  quality_indicators: Array<{ indicator: string; status: string; value: string }>;
  readiness: { combined_score: number; quality_tier: string };
  compliance: { audit_trail: boolean; version_history: boolean; artifact_retention: boolean; human_review_required: boolean };
};

type DemoProjectSeed = {
  id: number;
  name: string;
  description: string;
  status: "Completed" | "Running" | "Failed" | "Idle";
  createdAt: string;
  updatedAt: string;
  latestVersion: number;
  previewPath: string;
  publishedPath: string;
  codeZipPath: string;
  clientPdfPath: string;
  internalPdfPath: string;
  brief: {
    title: string;
    overview: string;
    goals: string[];
    mvp: string[];
    users: string[];
  };
  plan: {
    milestones: Array<{
      name: string;
      tasks: Array<{ id: string; description: string }>;
    }>;
  };
  files: Array<{ filename: string; language: string; content: string }>;
  versions: DemoVersionSeed[];
  chat: Array<{ role: "user" | "assistant"; content: string; timestamp: number }>;
  factsheet: DemoFactsheet;
  insights: Array<{ category: string; suggestion: string; priority: string }>;
};

const baseRegistry = [
  { agent_role: "Requirements Agent", model: "Gemini 2.5 Flash", provider: "Google" },
  { agent_role: "Architecture Agent", model: "Gemini 2.5 Flash", provider: "Google" },
  { agent_role: "Design Agent", model: "Imagen 4.0 Ultra + Gemini 2.5 Flash", provider: "Google" },
  { agent_role: "Governance Agent", model: "Watson NLU", provider: "IBM" },
] as const;

const projects: DemoProjectSeed[] = [
  {
    id: 744,
    name: "CryptoTrack Enterprise",
    description: "Benchmark-backed crypto dashboard with positions, market movers, and portfolio visibility.",
    status: "Completed",
    createdAt: "2026-03-20T20:55:00Z",
    updatedAt: "2026-03-20T21:34:04Z",
    latestVersion: 12,
    previewPath: "/demo-sites/dashboard/",
    publishedPath: "/demo-sites/dashboard/",
    codeZipPath: "/demo-assets/zips/dashboard-code.zip",
    clientPdfPath: "/demo-assets/pdfs/dashboard-client.pdf",
    internalPdfPath: "/demo-assets/pdfs/dashboard-internal.pdf",
    brief: {
      title: "Crypto Portfolio Dashboard",
      overview: "A read-heavy portfolio workspace for monitoring holdings, intraday movement, and recent account activity in one high-density layout.",
      goals: [
        "Make holdings, price movement, and P/L legible within one viewport.",
        "Keep the interface dense without collapsing hierarchy.",
        "Support executive review via preview, factsheet, and exported artifacts.",
      ],
      mvp: [
        "Portfolio summary strip with high-signal market movers.",
        "Holdings table with balances, weights, and intraday changes.",
        "Activity feed and supporting market modules.",
      ],
      users: ["Portfolio managers", "Operations reviewers", "Product demo audiences"],
    },
    plan: {
      milestones: [
        {
          name: "Requirements and decomposition",
          tasks: [
            { id: "PM-1", description: "Translate the prompt into concrete UI modules and data surfaces." },
            { id: "PM-2", description: "Lock the fintech archetype and target quality bar." },
          ],
        },
        {
          name: "Build and verification",
          tasks: [
            { id: "ENG-1", description: "Generate the React/Vite workspace and resolve preview output." },
            { id: "ENG-2", description: "Capture readiness factsheet and score the final build." },
          ],
        },
      ],
    },
    files: [
      {
        filename: "src/App.tsx",
        language: "tsx",
        content: `export default function App() {\n  return <main className="min-h-screen bg-slate-950 text-white">CryptoTrack Enterprise</main>;\n}\n`,
      },
      {
        filename: "src/components/HoldingsTable.tsx",
        language: "tsx",
        content: `export function HoldingsTable() {\n  return <section className="rounded-2xl border border-white/10">Holdings table</section>;\n}\n`,
      },
      {
        filename: "src/lib/portfolioData.ts",
        language: "ts",
        content: `export const holdings = [{ symbol: "BTC", allocation: 42 }, { symbol: "ETH", allocation: 28 }];\n`,
      },
    ],
    versions: [
      {
        executionId: 12012,
        version: 12,
        status: "success",
        createdAt: "2026-03-20T21:34:04Z",
        parentExecutionId: 12011,
        promptHistory: [
          { role: "user", content: "Build a crypto portfolio tracker with real-time prices, holdings table, and activity feed" },
          { role: "user", content: "Tighten the hierarchy and make the market strip denser without losing readability" },
          { role: "user", content: "Improve the holdings table spacing and surface the top movers more clearly" },
        ],
        filesGenerated: 13,
        imagesGenerated: 0,
        durationSeconds: 390,
        modelUsed: "Gemini 2.5 Flash",
        qualityTier: "high",
        readinessScore: 95,
      },
      {
        executionId: 12011,
        version: 11,
        status: "success",
        createdAt: "2026-03-20T21:11:30Z",
        parentExecutionId: 12010,
        promptHistory: [
          { role: "user", content: "Build a crypto portfolio tracker with real-time prices, holdings table, and activity feed" },
          { role: "user", content: "Tighten the hierarchy and make the market strip denser without losing readability" },
        ],
        filesGenerated: 14,
        imagesGenerated: 0,
        durationSeconds: 421,
        modelUsed: "Gemini 2.5 Flash",
        qualityTier: "good",
        readinessScore: 91,
      },
      {
        executionId: 12010,
        version: 10,
        status: "success",
        createdAt: "2026-03-20T20:58:20Z",
        parentExecutionId: null,
        promptHistory: [{ role: "user", content: "Build a crypto portfolio tracker with real-time prices, holdings table, and activity feed" }],
        filesGenerated: 12,
        imagesGenerated: 0,
        durationSeconds: 448,
        modelUsed: "Gemini 2.5 Flash",
        qualityTier: "good",
        readinessScore: 88,
      },
    ],
    chat: [
      { role: "user", content: "Build a crypto portfolio tracker with real-time prices, holdings table, and activity feed.", timestamp: 1774010100000 },
      { role: "assistant", content: "Mapped to the fintech dashboard family. I’ll keep the layout dense and preserve a clean preview/factsheet trail.", timestamp: 1774010109000 },
      { role: "user", content: "Tighten the hierarchy and make the market strip denser without losing readability.", timestamp: 1774011200000 },
      { role: "assistant", content: "Applied a refinement pass focused on summary density, table spacing, and higher-signal movers. The accepted result is seeded here as the current demo version.", timestamp: 1774011214000 },
    ],
    factsheet: {
      factsheet_version: "1.1",
      generated_at: "2026-03-20T12:40:42.207453+00:00",
      project: { id: 744, name: "CryptoTrack Enterprise", version: 12, execution_id: 12012 },
      prompt_summary: "Build a crypto portfolio tracker with real-time prices, holdings table, and activity feed",
      pipeline: { status: "success", agent_sequence: ["pm", "planner", "design", "engineer"], duration_seconds: 390.08, ui_archetype: "fintech" },
      model_registry: [...baseRegistry, { agent_role: "Build Agent", model: "Gemini 2.5 Flash", provider: "Google" }],
      usage: { tokens_used: null, estimated_cost_usd: null, credits_used: null },
      outputs: { files_generated: 13, images_generated: 0 },
      scoring: {
        prompt_quality: { score: 90, label: "high", sentiment: "neutral", sentiment_score: 0, keywords: ["crypto portfolio tracker", "real-time prices", "holdings", "activity feed"], domain: "personal finance", powered_by: "IBM Watson NLU" },
        build_confidence: { score: 100, label: "excellent", breakdown: [{ factor: "Code files", points: 50, note: "13 files" }, { factor: "Archetype detected", points: 30, note: "fintech" }, { factor: "Pipeline success", points: 20, note: "Completed without error" }] },
      },
      quality_indicators: [{ indicator: "Code generated", status: "pass", value: "13 files" }, { indicator: "Prompt clarity", status: "pass", value: "90/100" }],
      readiness: { combined_score: 95, quality_tier: "high" },
      compliance: { audit_trail: true, version_history: true, artifact_retention: true, human_review_required: false },
    },
    insights: [
      { category: "Hierarchy", suggestion: "Keep the ticker strip compact and reserve contrast for net portfolio movement.", priority: "medium" },
      { category: "Reviewability", suggestion: "Ship the client-facing factsheet alongside the dashboard preview for stakeholder handoff.", priority: "high" },
    ],
  },
  {
    id: 9001,
    name: "Halo Ringworld Atlas",
    description: "Cinematic Halo benchmark demo with character dossiers, world map, and premium fan-page pacing.",
    status: "Completed",
    createdAt: "2026-03-19T22:18:00Z",
    updatedAt: "2026-03-20T03:44:00Z",
    latestVersion: 4,
    previewPath: "/demo-sites/halo/",
    publishedPath: "/demo-sites/halo/",
    codeZipPath: "/demo-assets/zips/halo-code.zip",
    clientPdfPath: "/demo-assets/pdfs/halo-client.pdf",
    internalPdfPath: "/demo-assets/pdfs/halo-internal.pdf",
    brief: {
      title: "Halo Ringworld Fan Experience",
      overview: "A cinematic franchise page focused on worldbuilding, character framing, and a more authored visual pace than a generic marketing grid.",
      goals: ["Anchor the page around a strong hero and lore-forward section rhythm.", "Preserve franchise-specific texture without sliding into generic sci-fi clichés.", "Show that the same delivery system can support high-style non-enterprise outputs."],
      mvp: ["Premium hero with atmosphere and faction framing.", "Character dossier section with visual depth.", "Ringworld atlas and artifact surfaces for lore browsing."],
      users: ["Hiring reviewers", "Design benchmark comparisons", "Franchise fan-page demos"],
    },
    plan: {
      milestones: [
        {
          name: "Franchise direction",
          tasks: [
            { id: "PM-1", description: "Translate the Halo prompt into a cinematic content model with clear section rhythm." },
            { id: "DES-1", description: "Define atmosphere, type hierarchy, and image treatment against the benchmark references." },
          ],
        },
      ],
    },
    files: [
      { filename: "src/App.tsx", language: "tsx", content: `export default function App() {\n  return <main className="min-h-screen bg-[#05080f] text-slate-100">Halo Ringworld Atlas</main>;\n}\n` },
      { filename: "src/components/DossierGrid.tsx", language: "tsx", content: `export function DossierGrid() {\n  return <section className="grid gap-6 lg:grid-cols-3">Character dossiers</section>;\n}\n` },
      { filename: "src/data/roster.ts", language: "ts", content: `export const roster = [{ name: "Master Chief" }, { name: "Cortana" }, { name: "The Arbiter" }];\n` },
    ],
    versions: [
      {
        executionId: 19004,
        version: 4,
        status: "success",
        createdAt: "2026-03-20T03:44:00Z",
        parentExecutionId: 19003,
        promptHistory: [
          { role: "user", content: "Build a premium Halo fan page centered on Master Chief, Cortana, and the Arbiter." },
          { role: "user", content: "Make the hero more cinematic and give the atlas section more presence." },
        ],
        filesGenerated: 17,
        imagesGenerated: 5,
        durationSeconds: 418,
        modelUsed: "Claude Opus 4.6",
        qualityTier: "high",
        readinessScore: 93,
      },
      {
        executionId: 19003,
        version: 3,
        status: "success",
        createdAt: "2026-03-20T03:12:00Z",
        parentExecutionId: 19002,
        promptHistory: [{ role: "user", content: "Build a premium Halo fan page centered on Master Chief, Cortana, and the Arbiter." }],
        filesGenerated: 15,
        imagesGenerated: 4,
        durationSeconds: 442,
        modelUsed: "Claude Opus 4.6",
        qualityTier: "good",
        readinessScore: 89,
      },
    ],
    chat: [
      { role: "user", content: "Build a premium Halo fan page centered on Master Chief, Cortana, and the Arbiter.", timestamp: 1773951000000 },
      { role: "assistant", content: "I’m framing this as a high-style game build: cinematic hero, tighter section rhythm, and more franchise-specific atmosphere than the default family floor.", timestamp: 1773951016000 },
      { role: "user", content: "Make the hero more cinematic and give the atlas section more presence.", timestamp: 1773952400000 },
      { role: "assistant", content: "Accepted. The seeded demo version keeps the cinematic hero, stronger visual pacing, and a more deliberate atlas reveal.", timestamp: 1773952413000 },
    ],
    factsheet: {
      factsheet_version: "1.1",
      generated_at: "2026-03-20T03:46:00.000000+00:00",
      project: { id: 9001, name: "Halo Ringworld Atlas", version: 4, execution_id: 19004 },
      prompt_summary: "Build a premium Halo fan page centered on Master Chief, Cortana, and the Arbiter",
      pipeline: { status: "success", agent_sequence: ["pm", "planner", "design", "engineer"], duration_seconds: 418, ui_archetype: "game" },
      model_registry: [...baseRegistry, { agent_role: "Build Agent", model: "Claude Opus 4.6", provider: "Anthropic" }],
      usage: { tokens_used: null, estimated_cost_usd: null, credits_used: null },
      outputs: { files_generated: 17, images_generated: 5 },
      scoring: {
        prompt_quality: { score: 94, label: "high", sentiment: "neutral", sentiment_score: 0, keywords: ["halo fan page", "master chief", "cortana", "ringworld atlas"], domain: "entertainment", powered_by: "IBM Watson NLU" },
        build_confidence: { score: 96, label: "excellent", breakdown: [{ factor: "Code files", points: 46, note: "17 files" }, { factor: "Archetype detected", points: 30, note: "game" }, { factor: "Pipeline success", points: 20, note: "Completed without error" }] },
      },
      quality_indicators: [{ indicator: "Code generated", status: "pass", value: "17 files" }, { indicator: "Design assets", status: "pass", value: "5 images" }],
      readiness: { combined_score: 93, quality_tier: "high" },
      compliance: { audit_trail: true, version_history: true, artifact_retention: true, human_review_required: false },
    },
    insights: [
      { category: "Visual direction", suggestion: "Keep this archetype outside the generic family floor so the franchise art direction stays specific.", priority: "high" },
      { category: "Showcase positioning", suggestion: "Use this build as the premium non-enterprise demo in public portfolio material.", priority: "medium" },
    ],
  },
  {
    id: 9002,
    name: "WriteFlow AI Workspace",
    description: "Premium SaaS landing page benchmark focused on hierarchy, rhythm, and product messaging clarity.",
    status: "Completed",
    createdAt: "2026-03-19T17:08:00Z",
    updatedAt: "2026-03-19T17:41:00Z",
    latestVersion: 7,
    previewPath: "/demo-sites/writeflow/",
    publishedPath: "/demo-sites/writeflow/",
    codeZipPath: "/demo-assets/zips/writeflow-code.zip",
    clientPdfPath: "/demo-assets/pdfs/writeflow-client.pdf",
    internalPdfPath: "/demo-assets/pdfs/writeflow-internal.pdf",
    brief: {
      title: "WriteFlow SaaS Landing Page",
      overview: "A premium marketing page for an AI writing assistant with sharper product hierarchy and stronger product messaging.",
      goals: ["Present the product clearly without dropping into generic startup template output.", "Keep the layout persuasive and premium on desktop and mobile.", "Demonstrate the same artifact/governance workflow on a marketing archetype."],
      mvp: ["Hero with product positioning and proof strip.", "Feature grid and conversion flow.", "Versioned artifacts and governance outputs retained alongside the preview."],
      users: ["Founders", "Marketing reviewers", "Portfolio reviewers"],
    },
    plan: {
      milestones: [
        {
          name: "Positioning and layout",
          tasks: [
            { id: "PM-1", description: "Turn the writing-assistant prompt into a premium landing-page outline." },
            { id: "ENG-1", description: "Ship the landing page with stronger hierarchy and cleaner component pacing." },
          ],
        },
      ],
    },
    files: [
      { filename: "src/App.tsx", language: "tsx", content: `export default function App() {\n  return <main className="min-h-screen bg-slate-950 text-white">WriteFlow</main>;\n}\n` },
      { filename: "src/components/FeatureGrid.tsx", language: "tsx", content: `export function FeatureGrid() {\n  return <section className="grid gap-6 md:grid-cols-3">Feature grid</section>;\n}\n` },
      { filename: "src/content/copy.ts", language: "ts", content: `export const heroCopy = { heading: "Write faster. Publish cleaner." };\n` },
    ],
    versions: [
      {
        executionId: 17007,
        version: 7,
        status: "success",
        createdAt: "2026-03-19T17:41:00Z",
        parentExecutionId: 17006,
        promptHistory: [
          { role: "user", content: "Build a landing page for an AI-powered writing assistant called WriteFlow" },
          { role: "user", content: "Make the hierarchy tighter and the sections feel more premium" },
        ],
        filesGenerated: 11,
        imagesGenerated: 1,
        durationSeconds: 276,
        modelUsed: "Gemini 2.5 Flash",
        qualityTier: "high",
        readinessScore: 90,
      },
      {
        executionId: 17006,
        version: 6,
        status: "success",
        createdAt: "2026-03-19T17:28:00Z",
        parentExecutionId: 17005,
        promptHistory: [{ role: "user", content: "Build a landing page for an AI-powered writing assistant called WriteFlow" }],
        filesGenerated: 10,
        imagesGenerated: 1,
        durationSeconds: 294,
        modelUsed: "Gemini 2.5 Flash",
        qualityTier: "good",
        readinessScore: 86,
      },
    ],
    chat: [
      { role: "user", content: "Build a landing page for an AI-powered writing assistant called WriteFlow.", timestamp: 1773920400000 },
      { role: "assistant", content: "Using the SaaS landing archetype. I’ll bias toward stronger hierarchy, premium section pacing, and clearer product messaging.", timestamp: 1773920411000 },
      { role: "user", content: "Make the hierarchy tighter and the sections feel more premium.", timestamp: 1773921100000 },
      { role: "assistant", content: "Refinement accepted. The seeded demo version keeps the premium rhythm while preserving the product story and conversion flow.", timestamp: 1773921114000 },
    ],
    factsheet: {
      factsheet_version: "1.1",
      generated_at: "2026-03-19T17:43:00.000000+00:00",
      project: { id: 9002, name: "WriteFlow AI Workspace", version: 7, execution_id: 17007 },
      prompt_summary: "Build a landing page for an AI-powered writing assistant called WriteFlow",
      pipeline: { status: "success", agent_sequence: ["pm", "planner", "design", "engineer"], duration_seconds: 276, ui_archetype: "saas_landing" },
      model_registry: [...baseRegistry, { agent_role: "Build Agent", model: "Gemini 2.5 Flash", provider: "Google" }],
      usage: { tokens_used: null, estimated_cost_usd: null, credits_used: null },
      outputs: { files_generated: 11, images_generated: 1 },
      scoring: {
        prompt_quality: { score: 88, label: "high", sentiment: "neutral", sentiment_score: 0, keywords: ["landing page", "AI writing assistant", "premium hierarchy"], domain: "technology", powered_by: "IBM Watson NLU" },
        build_confidence: { score: 92, label: "excellent", breakdown: [{ factor: "Code files", points: 42, note: "11 files" }, { factor: "Archetype detected", points: 30, note: "saas_landing" }, { factor: "Pipeline success", points: 20, note: "Completed without error" }] },
      },
      quality_indicators: [{ indicator: "Code generated", status: "pass", value: "11 files" }, { indicator: "Design assets", status: "pass", value: "1 image" }],
      readiness: { combined_score: 90, quality_tier: "high" },
      compliance: { audit_trail: true, version_history: true, artifact_retention: true, human_review_required: false },
    },
    insights: [
      { category: "Messaging", suggestion: "Preserve the premium section rhythm when iterating on copy-heavy archetypes.", priority: "medium" },
      { category: "Portfolio use", suggestion: "Pair this landing page with the dashboard and game demos to show range across enterprise and high-style surfaces.", priority: "low" },
    ],
  },
];

const projectById = new Map(projects.map((project) => [project.id, project]));

function ensureProject(projectId: number) {
  const project = projectById.get(projectId);
  if (!project) throw new Error(`Unknown demo project ${projectId}`);
  return project;
}

function latestVersion(projectId: number) {
  return getDemoVersions(projectId)[0];
}

function selectedVersion(projectId: number, version?: number | null) {
  return getDemoVersions(projectId).find((entry) => entry.version === version) ?? latestVersion(projectId);
}

function formatDuration(durationSeconds?: number | null) {
  if (durationSeconds == null) return "—";
  const mins = Math.floor(durationSeconds / 60);
  const secs = Math.round(durationSeconds % 60);
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
}

export function getDemoProjects() {
  return projects.map((project) => ({
    id: project.id,
    name: project.name,
    description: project.description,
    status: project.status,
    updated_at: project.updatedAt,
    created_at: project.createdAt,
    version_count: project.versions.length,
  }));
}

export function getDemoVersions(projectId: number) {
  return [...ensureProject(projectId).versions]
    .sort((a, b) => b.version - a.version)
    .map((version) => ({
      id: version.executionId,
      version: version.version,
      status: version.status,
      created_at: version.createdAt,
      parent_execution_id: version.parentExecutionId ?? null,
      prompt_history: version.promptHistory,
      files_generated: version.filesGenerated,
      images_generated: version.imagesGenerated,
      duration_seconds: version.durationSeconds,
      model_used: version.modelUsed,
      quality_tier: version.qualityTier,
      readiness_score: version.readinessScore,
    }));
}

export function getDemoProjectHead(projectId: number) {
  return latestVersion(projectId)?.version ?? null;
}

export function getDemoLogs(projectId: number, version?: number | null) {
  const versionEntry = selectedVersion(projectId, version);
  return [
    { timestamp: versionEntry?.created_at ?? new Date().toISOString(), message: "Prompt classified and requirements draft accepted." },
    { timestamp: versionEntry?.created_at ?? new Date().toISOString(), message: "Planner decomposed the build into preview, artifacts, and governance stages." },
    { timestamp: versionEntry?.created_at ?? new Date().toISOString(), message: "Design pass aligned the interface to the selected archetype benchmark." },
    { timestamp: versionEntry?.created_at ?? new Date().toISOString(), message: "Build output completed successfully and artifacts were retained." },
  ];
}

export function getDemoPrd(projectId: number) {
  const project = ensureProject(projectId);
  return {
    prd: {
      document_title: project.brief.title,
      overview: project.brief.overview,
      goals: project.brief.goals,
      core_features_mvp: project.brief.mvp,
      target_users: project.brief.users,
    },
  };
}

export function getDemoPlan(projectId: number) {
  return { milestones: ensureProject(projectId).plan.milestones };
}

export function getDemoCodeFiles(projectId: number) {
  return ensureProject(projectId).files;
}

export function getDemoActivity() {
  return projects.map((project) => ({
    project_name: project.name,
    project_id: project.id,
    status: "COMPLETED",
    version: project.latestVersion,
    created_at: project.updatedAt,
  }));
}

export function getDemoPlatformStats() {
  return { versions_shipped: 8, avg_build_time_seconds: 361, lines_generated: 18420, pipelines_today: 3 };
}

export function getDemoDashboardStats() {
  return { avg_prompt_score: 90, avg_build_score: 94, scored_builds: 3 };
}

export function getDemoExecutionStatus(projectId?: number | null) {
  if (!projectId) {
    return { status: "IDLE" as const, currentStage: "complete", logs: [], engineerTasks: [], project_id: null, execution_id: null };
  }
  const version = latestVersion(projectId);
  return {
    status: "COMPLETED" as const,
    currentStage: "complete",
    logs: getDemoLogs(projectId, version?.version).map((entry, index) => ({
      id: `demo-log-${projectId}-${index}`,
      timestamp: Date.parse(entry.timestamp),
      message: entry.message,
    })),
    engineerTasks: [],
    project_id: projectId,
    execution_id: version?.id ?? null,
  };
}

export function getDemoChatHistory(projectId: number) {
  return ensureProject(projectId).chat;
}

export function getDemoFactsheet(projectId: number) {
  return ensureProject(projectId).factsheet;
}

export function getDemoInsights(projectId: number) {
  return ensureProject(projectId).insights;
}

export function getDemoBuildDetails(projectId: number, version?: number | null) {
  const versionEntry = selectedVersion(projectId, version);
  if (!versionEntry) return null;
  return {
    model: versionEntry.model_used || "—",
    creditsUsed: "—",
    duration: formatDuration(versionEntry.duration_seconds),
  };
}

export function getDemoPreviewUrl(projectId: number, _version?: number | null) {
  return ensureProject(projectId).previewPath;
}

export function getDemoPublishedUrl(projectId: number) {
  return ensureProject(projectId).publishedPath;
}

export function getDemoCodeDownloadUrl(projectId: number) {
  return ensureProject(projectId).codeZipPath;
}

export function getDemoFactsheetPdfUrl(projectId: number, type: "client" | "internal") {
  const project = ensureProject(projectId);
  return type === "client" ? project.clientPdfPath : project.internalPdfPath;
}

export function getDemoViewerProfile() {
  return { name: "Demo Reviewer", email: "public-demo@archon.dev", creditsRemaining: 120000 };
}
