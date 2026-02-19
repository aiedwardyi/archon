/**
 * Archon API service — all backend calls go through here.
 * Backend runs on http://localhost:5000
 */

const BASE = 'http://localhost:5000/api';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface Project {
  id: number;
  name: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  execution_count: number;
}

export interface Execution {
  id: number;
  project_id: number;
  status: 'pending' | 'running' | 'success' | 'error';
  created_at: string;
  version: number;
  prompt_history: { role: string; content: string }[];
  is_active_head: boolean;
  parent_execution_id: number | null;
  prd_path: string | null;
  plan_path: string | null;
  result_path: string | null;
  error_message: string | null;
}

export interface VersionsResponse {
  project_id: number;
  project_name: string;
  versions: Execution[];
}

export interface ExecutionStatus {
  status: 'RUNNING' | 'COMPLETED' | 'FAILED';
  currentStage: string;
  logs: { id: string; timestamp: number; message: string; type: string }[];
  engineerTasks: string[];
  execution_id?: number;
  project_id?: number;
}

// ─── Projects ─────────────────────────────────────────────────────────────────

export async function listProjects(): Promise<Project[]> {
  const res = await fetch(`${BASE}/projects`);
  if (!res.ok) throw new Error('Failed to load projects');
  return res.json();
}

export async function createProject(name: string, description: string): Promise<Project> {
  const res = await fetch(`${BASE}/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) throw new Error('Failed to create project');
  return res.json();
}

export async function getProject(id: number): Promise<Project & { executions: Execution[] }> {
  const res = await fetch(`${BASE}/projects/${id}`);
  if (!res.ok) throw new Error('Project not found');
  return res.json();
}

export async function deleteProject(id: number): Promise<void> {
  const res = await fetch(`${BASE}/projects/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete project');
}

// ─── Versions ─────────────────────────────────────────────────────────────────

export async function getVersions(projectId: number): Promise<VersionsResponse> {
  const res = await fetch(`${BASE}/projects/${projectId}/versions`);
  if (!res.ok) throw new Error('Failed to load versions');
  return res.json();
}

export async function restoreVersion(executionId: number): Promise<void> {
  const res = await fetch(`${BASE}/executions/${executionId}/restore`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to restore version');
}

// ─── Pipeline ─────────────────────────────────────────────────────────────────

export async function startExecution(projectId: number): Promise<{ execution_id: number; version: number }> {
  const res = await fetch(`${BASE}/execute-task`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project_id: projectId }),
  });
  if (!res.ok) throw new Error('Failed to start execution');
  return res.json();
}

export async function iterateProject(
  projectId: number,
  prompt: string,
  promptHistory: { role: string; content: string }[]
): Promise<{ execution_id: number; version: number }> {
  const res = await fetch(`${BASE}/projects/${projectId}/iterate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, prompt_history: promptHistory }),
  });
  if (!res.ok) throw new Error('Failed to start iteration');
  return res.json();
}

export async function getExecutionStatus(): Promise<ExecutionStatus> {
  const res = await fetch(`${BASE}/execution-status`);
  if (!res.ok) throw new Error('Failed to get status');
  return res.json();
}

// ─── Artifacts ────────────────────────────────────────────────────────────────

export async function getPRD(): Promise<Record<string, unknown> | null> {
  const res = await fetch(`${BASE}/prd`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error('Failed to load brief');
  return res.json();
}

export async function getPlan(): Promise<Record<string, unknown> | null> {
  const res = await fetch(`${BASE}/plan`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error('Failed to load build plan');
  return res.json();
}

export async function getCode(): Promise<Record<string, unknown> | null> {
  const res = await fetch(`${BASE}/code`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error('Failed to load code');
  return res.json();
}
