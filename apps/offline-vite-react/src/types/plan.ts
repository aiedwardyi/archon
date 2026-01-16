export type TaskStatus = "todo" | "in_progress" | "blocked" | "done" | string;

export type PlanTask = {
  id?: string;
  title?: string;
  description?: string;

  status?: TaskStatus;
  owner?: string;
  eta?: string;
  acceptance_criteria?: string[] | string;
  dependencies?: string[];
  files?: string[];
  commands?: string[];

  [key: string]: unknown;
};

export type PlanMilestone = {
  id?: string;
  title?: string;
  description?: string;
  tasks?: PlanTask[];

  [key: string]: unknown;
};

export type Plan = {
  title?: string;
  description?: string;
  milestones?: PlanMilestone[];

  [key: string]: unknown;
};

export function safeArray<T>(v: unknown): T[] {
  return Array.isArray(v) ? (v as T[]) : [];
}

export function normalizeText(v: unknown): string {
  if (typeof v === "string") return v;
  if (v == null) return "";
  try {
    return JSON.stringify(v, null, 2);
  } catch {
    return String(v);
  }
}

export function normalizeAcceptanceCriteria(v: unknown): string[] {
  if (Array.isArray(v)) return v.map((x) => String(x));
  if (typeof v === "string") return v.split("\n").map((s) => s.trim()).filter(Boolean);
  return [];
}

export function getTaskStatus(task: PlanTask): TaskStatus {
  return (task.status ?? "todo") as TaskStatus;
}

export function isDone(task: PlanTask): boolean {
  const s = String(getTaskStatus(task)).toLowerCase();
  return s === "done" || s === "completed" || s === "complete";
}
