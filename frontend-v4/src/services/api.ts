import { useState, useEffect, useRef, useCallback } from "react";

const API_BASE = "http://localhost:5000/api";

export interface Project {
  id: number;
  name: string;
  description: string;
  status: "Running" | "Completed" | "Failed" | "Idle";
  lastRun: string;
  versions: string;
  created: string;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function mapStatus(raw: string): Project["status"] {
  const upper = raw?.toUpperCase();
  if (upper === "RUNNING" || upper === "IN_PROGRESS") return "Running";
  if (upper === "COMPLETED" || upper === "SUCCESS") return "Completed";
  if (upper === "FAILED") return "Failed";
  return "Idle";
}

export async function createProject(name: string, description: string): Promise<Project> {
  const res = await fetch(`${API_BASE}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  const data = await res.json();
  return {
    id: data.id,
    name: data.name || "Untitled",
    description: data.description || "No description",
    status: mapStatus(data.status),
    lastRun: data.updated_at ? formatDate(data.updated_at) : data.created_at ? formatDate(data.created_at) : "—",
    versions: `v${data.version_count ?? 1}`,
    created: data.created_at ? formatDate(data.created_at) : "—",
  };
}

export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE}/projects`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  const list: any[] = Array.isArray(data) ? data : data.projects || [];
  if (list.length > 0) {
    console.log("[fetchProjects] raw project sample:", list[0]);
  }
  return list.map((p) => ({
    id: p.id,
    name: p.name || "Untitled",
    description: p.description || "No description",
    status: mapStatus(p.status),
    lastRun: p.updated_at ? formatDate(p.updated_at) : p.created_at ? formatDate(p.created_at) : "—",
    versions: `v${p.version_count ?? 1}`,
    created: p.created_at ? formatDate(p.created_at) : "—",
  }));
}

export interface ProjectStats {
  total: number;
  running: number;
  completed: number;
  failed: number;
}

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const data = await fetchProjects();
        if (cancelled) return;
        setProjects(data);
        setError(null);
      } catch (e: any) {
        if (!cancelled) setError(e.message || "Failed to fetch projects");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    intervalRef.current = setInterval(load, 3000);

    const onBuildReset = () => { load(); };
    window.addEventListener("archon:build-reset", onBuildReset);

    return () => {
      cancelled = true;
      if (intervalRef.current) clearInterval(intervalRef.current);
      window.removeEventListener("archon:build-reset", onBuildReset);
    };
  }, []);

  const stats: ProjectStats = {
    total: projects.length,
    running: projects.filter((p) => p.status === "Running").length,
    completed: projects.filter((p) => p.status === "Completed").length,
    failed: projects.filter((p) => p.status === "Failed").length,
  };

  return { projects, loading, error, stats };
}

// ── Platform Stats ──

export interface PlatformStats {
  versions_shipped: number;
  avg_build_time_seconds: number;
  lines_generated: number;
  pipelines_today: number;
}

export async function fetchPlatformStats(): Promise<PlatformStats | null> {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

export function usePlatformStats(pollMs = 30000) {
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const data = await fetchPlatformStats();
      if (!cancelled) setStats(data);
    };
    load();
    intervalRef.current = setInterval(load, pollMs);
    return () => { cancelled = true; if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [pollMs]);

  return stats;
}

// ── Dashboard Governance Stats ──

export interface DashboardStats {
  avg_prompt_score: number | null;
  avg_build_score: number | null;
  scored_builds: number;
}

export async function fetchDashboardStats(): Promise<DashboardStats | null> {
  try {
    const res = await fetch(`${API_BASE}/dashboard/stats`);
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

export function useDashboardStats(pollMs = 30000) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const data = await fetchDashboardStats();
      if (!cancelled) setStats(data);
    };
    load();
    intervalRef.current = setInterval(load, pollMs);
    return () => { cancelled = true; if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [pollMs]);

  return stats;
}

// ── Activity Feed ──

export interface ActivityItem {
  project_name: string;
  project_id: number;
  status: string;
  version: number;
  created_at: string;
}

export async function fetchActivity(): Promise<ActivityItem[]> {
  try {
    const res = await fetch(`${API_BASE}/activity`);
    if (!res.ok) return [];
    return await res.json();
  } catch { return []; }
}

export function useActivity(pollMs = 10000) {
  const [items, setItems] = useState<ActivityItem[]>([]);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const data = await fetchActivity();
      if (!cancelled) setItems(data);
    };
    load();
    intervalRef.current = setInterval(load, pollMs);
    return () => { cancelled = true; if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [pollMs]);

  return items;
}

// ── Version / Artifact APIs ──

const API = "http://localhost:5000";

export interface Version {
  id: string;
  version: number;
  status: string;
  created_at: string;
  prompt_history?: Array<{ role: string; content: string }>;
  artifacts?: { brief?: any; plan?: any };
  tokens_used?: number | null;
  estimated_cost?: number | null;
  duration_seconds?: number | null;
  model_used?: string | null;
  files_generated?: number;
  images_generated?: number;
  quality_tier?: string | null;
  readiness_score?: number | null;
}

export interface BuildDetails {
  model: string;
  creditsUsed: string;
  duration: string;
}

export async function fetchBuildDetails(projectId: number, version: number): Promise<BuildDetails | null> {
  try {
    const versions = await fetchVersions(projectId);
    const v = versions.find((ver: any) => ver.version === version);
    if (!v) return null;
    const dur = v.duration_seconds;
    let durStr = "—";
    if (dur != null) {
      const mins = Math.floor(dur / 60);
      const secs = Math.round(dur % 60);
      durStr = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
    }
    return {
      model: v.model_used || "—",
      creditsUsed: v.credits_used != null ? `${v.credits_used} credits` : "—",
      duration: durStr,
    };
  } catch { return null; }
}

export async function fetchVersions(projectId: number): Promise<Version[]> {
  const res = await fetch(`${API}/api/projects/${projectId}/versions`);
  if (!res.ok) return [];
  const data = await res.json();
  return Array.isArray(data) ? data : (data.versions || []);
}

export async function fetchProjectHead(projectId: number): Promise<number | null> {
  try {
    const res = await fetch(`${API}/api/projects/${projectId}/head`);
    if (!res.ok) return null;
    const data = await res.json();
    return data?.version ?? data?.version_number ?? null;
  } catch { return null; }
}

export async function fetchLogs(projectId: number, version: number): Promise<string[]> {
  try {
    const res = await fetch(`${API}/api/projects/${projectId}/versions/${version}/logs`);
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data.map((l: any) => `${l.timestamp ? new Date(l.timestamp).toLocaleTimeString([], {hour12:false,hour:'2-digit',minute:'2-digit',second:'2-digit'}) : ''} ${l.message || l}`) : [];
  } catch { return []; }
}

export async function fetchPrd(projectId: number, version: number): Promise<any> {
  try {
    const res = await fetch(`${API}/api/prd?project_id=${projectId}&version=${version}`);
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

export async function fetchPlan(projectId: number, version: number): Promise<any> {
  try {
    const res = await fetch(`${API}/api/plan?project_id=${projectId}&version=${version}`);
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

export async function fetchCodeFiles(projectId: number, version: number): Promise<Array<{filename: string; content: string; language: string}>> {
  try {
    const base = `${API}/api/projects/${projectId}/versions/${version}/files`;
    const res = await fetch(base);
    if (!res.ok) return [];
    const data = await res.json();
    const tree = data.tree || [];
    const flatten = (nodes: any[]): string[] => nodes.flatMap(n => n.type === 'file' ? [n.path] : flatten(n.children || []));
    const paths = flatten(tree);
    const files = await Promise.all(paths.map(async path => {
      try {
        const r = await fetch(`${base}?path=${encodeURIComponent(path)}`);
        if (!r.ok) return null;
        const f = await r.json();
        return { filename: path, content: f.content || '', language: f.language || 'text' };
      } catch { return null; }
    }));
    return files.filter(Boolean) as any[];
  } catch { return []; }
}

// ── Pipeline Execution ──

export interface ExecutionStatus {
  status: "RUNNING" | "COMPLETED" | "FAILED";
  currentStage: string; // "pm" | "planner" | "engineer" | "complete"
  logs: Array<{ id: string; timestamp: number; message: string }>;
  engineerTasks: any[];
  project_id: number | null;
  execution_id: number | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: number;
}

/** POST /api/projects/:id/chat — classify intent, returns {response_type, message?} */
export async function projectChat(projectId: number, message: string): Promise<{ response_type: "chat" | "build"; message?: string }> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/** POST /api/projects/:id/iterate — start a pipeline build */
export async function iterateProject(
  projectId: number,
  prompt: string,
  promptHistory: ChatMessage[],
): Promise<{ status: string; project_id: number; execution_id: number; version: number }> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/iterate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, prompt_history: promptHistory }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

/** POST /api/execute-task — start first build (no prior version) */
export async function executeTask(projectId: number): Promise<{ status: string; project_id: number; execution_id: number; version: number }> {
  const res = await fetch(`${API_BASE}/execute-task`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

/** GET /api/execution-status — poll pipeline progress */
export async function fetchExecutionStatus(): Promise<ExecutionStatus> {
  const res = await fetch(`${API_BASE}/execution-status`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/** GET /api/projects/:id/chat-history — load persisted chat messages */
export async function fetchChatHistory(projectId: number): Promise<ChatMessage[]> {
  try {
    const res = await fetch(`${API}/api/projects/${projectId}/chat-history`);
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch { return []; }
}

/** POST /api/projects/:id/chat-messages — persist chat messages to DB */
export async function saveChatMessages(projectId: number, messages: ChatMessage[]): Promise<void> {
  try {
    await fetch(`${API}/api/projects/${projectId}/chat-messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages }),
    });
  } catch { /* non-fatal */ }
}

// ── Pipeline Status Hook ──

type PipelineStage = "idle" | "pm" | "planner" | "engineer" | "complete";

export interface PipelineState {
  running: boolean;
  stage: PipelineStage;
  status: "RUNNING" | "COMPLETED" | "FAILED" | "IDLE";
  logs: ExecutionStatus["logs"];
  projectId: number | null;
  executionId: number | null;
}

export function usePipelineStatus(projectId: number | null, enabled: boolean) {
  const [state, setState] = useState<PipelineState>({
    running: false,
    stage: "idle",
    status: "IDLE",
    logs: [],
    projectId: null,
    executionId: null,
  });
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startPolling = useCallback(() => {
    // Clear any existing interval
    if (intervalRef.current) clearInterval(intervalRef.current);

    const poll = async () => {
      try {
        const data = await fetchExecutionStatus();
        // Only update if this status belongs to our project
        if (data.project_id !== projectId) return;
        const isRunning = data.status === "RUNNING";
        setState({
          running: isRunning,
          stage: data.currentStage as PipelineStage,
          status: data.status,
          logs: data.logs || [],
          projectId: data.project_id,
          executionId: data.execution_id,
        });
        if (!isRunning && intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      } catch {
        // ignore poll errors
      }
    };

    poll(); // immediate first poll
    intervalRef.current = setInterval(poll, 2000);
  }, [projectId]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Reset pipeline state when project changes
  useEffect(() => {
    stopPolling();
    setState({
      running: false,
      stage: "idle",
      status: "IDLE",
      logs: [],
      projectId: null,
      executionId: null,
    });
  }, [projectId]);

  // Auto-poll when enabled
  useEffect(() => {
    if (enabled && projectId) {
      startPolling();
    }
    return stopPolling;
  }, [enabled, projectId, startPolling, stopPolling]);

  return { ...state, startPolling, stopPolling };
}
