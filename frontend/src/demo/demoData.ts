import avalanchePrdRaw from "./seed-json/avalanche/last_prd.json?raw";
import avalanchePlanRaw from "./seed-json/avalanche/last_plan.json?raw";
import avalancheExecutionRaw from "./seed-json/avalanche/last_execution_result.json?raw";
import avalancheFactsheetRaw from "./seed-json/avalanche/last_factsheet.json?raw";
import avalancheInsightsRaw from "./seed-json/avalanche/last_insights.json?raw";
import midgarPrdRaw from "./seed-json/midgar/last_prd.json?raw";
import midgarPlanRaw from "./seed-json/midgar/last_plan.json?raw";
import midgarExecutionRaw from "./seed-json/midgar/last_execution_result.json?raw";
import midgarFactsheetRaw from "./seed-json/midgar/last_factsheet.json?raw";
import midgarInsightsRaw from "./seed-json/midgar/last_insights.json?raw";
import avalancheIndexRaw from "./seed-code/avalanche/index.html?raw";
import avalancheStyleRaw from "./seed-code/avalanche/style.css?raw";
import midgarIndexRaw from "./seed-code/midgar/index.html?raw";
import midgarStyleRaw from "./seed-code/midgar/style.css?raw";

type PromptTurn = { role: string; content: string };

type DemoVersionSeed = {
  executionId: number;
  version: number;
  status: string;
  createdAt: string;
  parentExecutionId?: number | null;
  promptHistory: PromptTurn[];
  filesGenerated: number;
  imagesGenerated: number;
  durationSeconds: number;
  modelUsed: string;
  qualityTier: string;
  readinessScore: number;
  previewPath?: string;
  publishedPath?: string;
  codeZipPath?: string;
  clientPdfPath?: string;
  internalPdfPath?: string;
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
  prd: any;
  plan: any;
  executionResult: any;
  files: Array<{ filename: string; language: string; content: string }>;
  versions: DemoVersionSeed[];
  chat: Array<{ role: "user" | "assistant"; content: string; timestamp: number }>;
  factsheet: any;
  insights: Array<{ category: string; suggestion: string; priority: string }>;
};

const avalanchePrd = JSON.parse(avalanchePrdRaw);
const avalanchePlan = JSON.parse(avalanchePlanRaw);
const avalancheExecution = JSON.parse(avalancheExecutionRaw);
const avalancheFactsheet = JSON.parse(avalancheFactsheetRaw);
const avalancheInsights = JSON.parse(avalancheInsightsRaw);
const midgarPrd = JSON.parse(midgarPrdRaw);
const midgarPlan = JSON.parse(midgarPlanRaw);
const midgarExecution = JSON.parse(midgarExecutionRaw);
const midgarFactsheet = JSON.parse(midgarFactsheetRaw);
const midgarInsights = JSON.parse(midgarInsightsRaw);

function normalizeFactsheet(factsheet: any, projectId: number, executionId: number) {
  return {
    ...factsheet,
    project: {
      ...(factsheet.project || {}),
      id: projectId,
      execution_id: executionId,
      version: 1,
    },
  };
}

const projects: DemoProjectSeed[] = [
  {
    id: 71,
    name: "FF7 — Avalanche Archive",
    description: "A fan tribute site for Final Fantasy VII with character profiles, weapons gallery, and interactive world map.",
    status: "Completed",
    createdAt: "2026-03-09T11:29:00Z",
    updatedAt: "2026-03-09T11:30:00Z",
    latestVersion: 1,
    previewPath: "/demo-sites/avalanche/index.html",
    publishedPath: "/demo-sites/avalanche/index.html",
    codeZipPath: "/demo-assets/zips/ff7-avalanche-code.zip",
    clientPdfPath: "/demo-assets/pdfs/ff7-avalanche-client.pdf",
    internalPdfPath: "/demo-assets/pdfs/ff7-avalanche-internal.pdf",
    prd: avalanchePrd,
    plan: avalanchePlan,
    executionResult: avalancheExecution,
    files: [
      { filename: "src/index.html", language: "html", content: avalancheIndexRaw },
      { filename: "src/style.css", language: "css", content: avalancheStyleRaw },
    ],
    versions: [
      {
        executionId: 1,
        version: 1,
        status: "success",
        createdAt: "2026-03-09T11:30:00Z",
        parentExecutionId: null,
        promptHistory: [
          {
            role: "user",
            content:
              "Create a premium Final Fantasy VII fan archive with hero art, character spotlights, weapons, and an atmospheric Midgar world map.",
          },
        ],
        filesGenerated: 2,
        imagesGenerated: 5,
        durationSeconds: 45,
        modelUsed: "Gemini 2.5 Flash",
        qualityTier: "good",
        readinessScore: 86,
      },
    ],
    chat: [
      {
        role: "user",
        content:
          "Create a premium Final Fantasy VII fan archive with hero art, character spotlights, weapons, and an atmospheric Midgar world map.",
        timestamp: 1773054900000,
      },
      {
        role: "assistant",
        content:
          "Got it — building a premium FF7 fan archive with cinematic hero art, character spotlights for Cloud, Barret, and Tifa, a weapons gallery, and an atmospheric Midgar world map. Kicking off the pipeline now.",
        timestamp: 1773054960000,
      },
    ],
    factsheet: normalizeFactsheet(avalancheFactsheet, 71, 1),
    insights: avalancheInsights.insights || [],
  },
  {
    id: 38,
    name: "FF7 — Midgar Archives",
    description: "An interactive Final Fantasy VII database with search, filtering, grid/list views, and character detail modals.",
    status: "Completed",
    createdAt: "2026-03-09T11:29:00Z",
    updatedAt: "2026-03-09T11:30:00Z",
    latestVersion: 1,
    previewPath: "/demo-sites/midgar/index.html",
    publishedPath: "/demo-sites/midgar/index.html",
    codeZipPath: "/demo-assets/zips/ff7-midgar-code.zip",
    clientPdfPath: "/demo-assets/pdfs/ff7-midgar-client.pdf",
    internalPdfPath: "/demo-assets/pdfs/ff7-midgar-internal.pdf",
    prd: midgarPrd,
    plan: midgarPlan,
    executionResult: midgarExecution,
    files: [
      { filename: "src/index.html", language: "html", content: midgarIndexRaw },
      { filename: "src/style.css", language: "css", content: midgarStyleRaw },
    ],
    versions: [
      {
        executionId: 1,
        version: 1,
        status: "success",
        createdAt: "2026-03-09T11:30:00Z",
        parentExecutionId: null,
        promptHistory: [
          {
            role: "user",
            content:
              "Create an interactive Final Fantasy VII archive with filtering, modal details, animated character cards, and premium generated art.",
          },
        ],
        filesGenerated: 2,
        imagesGenerated: 6,
        durationSeconds: 45,
        modelUsed: "Gemini 2.5 Flash",
        qualityTier: "good",
        readinessScore: 86,
      },
    ],
    chat: [
      {
        role: "user",
        content:
          "Create an interactive Final Fantasy VII archive with filtering, modal details, animated character cards, and premium generated art.",
        timestamp: 1773054900000,
      },
      {
        role: "assistant",
        content:
          "On it — creating an interactive FF7 database with search and filtering, animated character cards with modal details, and premium AI-generated art. Starting the build pipeline.",
        timestamp: 1773054960000,
      },
    ],
    factsheet: normalizeFactsheet(midgarFactsheet, 38, 1),
    insights: midgarInsights.insights || [],
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
  const project = ensureProject(projectId);
  const selected = selectedVersion(projectId, version);
  const logs = project.executionResult.logs || [];
  return logs.map((entry: any) => ({
    timestamp: entry.timestamp ? new Date(entry.timestamp).toISOString() : selected?.created_at ?? new Date().toISOString(),
    message: entry.message || "Pipeline event recorded.",
  }));
}

export function getDemoPrd(projectId: number, _version?: number | null) {
  return ensureProject(projectId).prd;
}

export function getDemoPlan(projectId: number, _version?: number | null) {
  return ensureProject(projectId).plan;
}

export function getDemoCodeFiles(projectId: number, _version?: number | null) {
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
  return { versions_shipped: 2, avg_build_time_seconds: 45, lines_generated: 721, pipelines_today: 2 };
}

export function getDemoDashboardStats() {
  return { avg_prompt_score: 85, avg_build_score: 88, scored_builds: 2 };
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

export function getDemoFactsheet(projectId: number, _version?: number | null) {
  return ensureProject(projectId).factsheet;
}

export function getDemoInsights(projectId: number, _version?: number | null) {
  return ensureProject(projectId).insights;
}

export function getDemoBuildDetails(projectId: number, version?: number | null) {
  const versionEntry = selectedVersion(projectId, version);
  if (!versionEntry) return null;
  return {
    model: versionEntry.model_used || "—",
    creditsUsed: "7 credits",
    duration: formatDuration(versionEntry.duration_seconds),
  };
}

export function getDemoPreviewUrl(projectId: number, version?: number | null) {
  const project = ensureProject(projectId);
  const versionEntry = project.versions.find((entry) => entry.version === version) ?? project.versions[0];
  return versionEntry.previewPath || project.previewPath;
}

export function getDemoPublishedUrl(projectId: number, version?: number | null) {
  const project = ensureProject(projectId);
  const versionEntry = project.versions.find((entry) => entry.version === version) ?? project.versions[0];
  return versionEntry.publishedPath || project.publishedPath;
}

export function getDemoCodeDownloadUrl(projectId: number, version?: number | null) {
  const project = ensureProject(projectId);
  const versionEntry = project.versions.find((entry) => entry.version === version) ?? project.versions[0];
  return versionEntry.codeZipPath || project.codeZipPath;
}

export function getDemoFactsheetPdfUrl(projectId: number, version: number | null | undefined, type: "client" | "internal") {
  const project = ensureProject(projectId);
  const versionEntry = project.versions.find((entry) => entry.version === version) ?? project.versions[0];
  if (type === "client") return versionEntry.clientPdfPath || project.clientPdfPath;
  return versionEntry.internalPdfPath || project.internalPdfPath;
}

export function getDemoViewerProfile() {
  return { name: "Demo Reviewer", email: "public-demo@archon.dev", creditsRemaining: 120000 };
}
