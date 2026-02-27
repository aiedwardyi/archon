import { useState, useEffect, useRef } from "react";

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

    return () => {
      cancelled = true;
      if (intervalRef.current) clearInterval(intervalRef.current);
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
}

export interface BuildDetails {
  model: string;
  tokensUsed: string;
  estCost: string;
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
      tokensUsed: v.tokens_used != null ? v.tokens_used.toLocaleString() : "—",
      estCost: v.estimated_cost != null ? `$${v.estimated_cost.toFixed(4)}` : "—",
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
