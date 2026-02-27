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
  return list.map((p) => ({
    id: p.id,
    name: p.name || "Untitled",
    description: p.description || "No description",
    status: mapStatus(p.status),
    lastRun: p.updated_at ? formatDate(p.updated_at) : p.created_at ? formatDate(p.created_at) : "—",
    versions: `v${p.version_count || 1}`,
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
        if (!cancelled) {
          setProjects(data);
          setError(null);
        }
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
