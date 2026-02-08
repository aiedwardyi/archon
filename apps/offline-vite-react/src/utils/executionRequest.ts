export type ExecutionRequest = {
  kind: string;
  task_id: string;
  milestone_id?: string | null;
  title?: string | null;
  created_at?: string | null;
  payload: {
    _agent_sequence?: string[];
    task_snapshot?: unknown;
    [key: string]: unknown;
  };
};

export function buildExecutionRequest(args: {
  milestoneIndex: number;
  taskIndex: number;
  milestoneTitle: string;
  taskId?: string;
  taskTitle?: string;
  taskSnapshot: unknown;
  agentSequence?: string[];
}): ExecutionRequest {
  return {
    kind: "execution_request",
    task_id: args.taskId || `TASK-${args.milestoneIndex}-${args.taskIndex}`,
    milestone_id: null,
    title: args.taskTitle || "Task execution",
    created_at: new Date().toISOString(),
    payload: {
      _agent_sequence: args.agentSequence || [],
      task_snapshot: args.taskSnapshot,
    },
  };
}
