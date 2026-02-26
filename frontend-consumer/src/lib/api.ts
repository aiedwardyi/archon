export const API_BASE = "http://localhost:5000";

export async function fetchProjects() {
  const res = await fetch(`${API_BASE}/api/projects`);
  return res.json();
}

export async function fetchProject(id: number) {
  const res = await fetch(`${API_BASE}/api/projects/${id}`);
  return res.json();
}

export async function fetchVersions(projectId: number) {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/versions`);
  return res.json();
}

export async function sendChat(projectId: number, message: string) {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  return res.json();
}

export async function iterateProject(projectId: number, prompt: string, promptHistory: any[]) {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/iterate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, prompt_history: promptHistory }),
  });
  return res.json();
}

export async function fetchExecutionStatus() {
  const res = await fetch(`${API_BASE}/api/execution-status`);
  return res.json();
}

export async function restoreVersion(executionId: number) {
  const res = await fetch(`${API_BASE}/api/executions/${executionId}/restore`, {
    method: "POST",
  });
  return res.json();
}

export async function createProject(name: string, description = "") {
  const res = await fetch(`${API_BASE}/api/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description }),
  });
  return res.json();
}
