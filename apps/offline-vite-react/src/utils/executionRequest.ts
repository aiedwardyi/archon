export type ExecutionRequest = {
  requested_at_iso: string;
  milestone_index: number;
  task_index: number;

  // IDs/titles are best-effort (schema drift safe)
  milestone_title?: string;
  task_id?: string;
  task_title?: string;

  // raw snapshot for determinism/debug
  task_snapshot: unknown;
};

export function buildExecutionRequest(args: {
  milestoneIndex: number;
  taskIndex: number;
  milestoneTitle: string;
  taskId?: string;
  taskTitle?: string;
  taskSnapshot: unknown;
}): ExecutionRequest {
  return {
    requested_at_iso: new Date().toISOString(),
    milestone_index: args.milestoneIndex,
    task_index: args.taskIndex,
    milestone_title: args.milestoneTitle,
    task_id: args.taskId,
    task_title: args.taskTitle,
    task_snapshot: args.taskSnapshot,
  };
}
