import React, { useEffect, useMemo, useState } from "react";
import {
  Plan,
  PlanMilestone,
  PlanTask,
  safeArray,
  normalizeText,
  normalizeAcceptanceCriteria,
  getTaskStatus,
  isDone,
} from "../types/plan";
import { buildExecutionRequest } from "../utils/executionRequest";

type Props = {
  plan: Plan | null;
  selectedMilestoneIndex: number;
  selectedTaskIndex: number;
};

function getMilestoneTitle(m: PlanMilestone): string {
  const anyM = m as any;
  return m.title ?? anyM.name ?? "Milestone";
}

function getTaskTitle(t: PlanTask, idx: number): string {
  const anyT = t as any;
  return t.title ?? anyT.name ?? t.id ?? `Task ${idx + 1}`;
}

function pickMilestone(plan: Plan | null, idx: number): PlanMilestone | null {
  const milestones = safeArray<PlanMilestone>(plan?.milestones);
  return milestones[idx] ?? null;
}

function pickTask(m: PlanMilestone | null, idx: number): PlanTask | null {
  if (!m) return null;
  const anyM = m as any;
  const tasks = safeArray<PlanTask>(m.tasks ?? anyM.tasks);
  return tasks[idx] ?? null;
}

function persistExecutionRequest(req: unknown) {
  localStorage.setItem("last_execution_request", JSON.stringify(req, null, 2));

  const logKey = "execution_requests_log";
  const line = JSON.stringify(req);
  const prev = localStorage.getItem(logKey) ?? "";
  localStorage.setItem(logKey, prev ? `${prev}\n${line}` : line);
}

export function TaskPanel(props: Props) {
  const milestone = pickMilestone(props.plan, props.selectedMilestoneIndex);
  const task = pickTask(milestone, props.selectedTaskIndex);

  const [lastRequestJson, setLastRequestJson] = useState<string>("");

  useEffect(() => {
    const v = localStorage.getItem("last_execution_request");
    if (v) setLastRequestJson(v);
  }, []);

  if (!props.plan || !milestone || !task) {
    return (
      <section className="panel">
        <div className="panelHeader">
          <h2>Task details</h2>
          <p className="muted">No task selected.</p>
        </div>
      </section>
    );
  }

  const anyT = task as any;
  const status = String(getTaskStatus(task));
  const done = isDone(task);

  const milestoneTitle = getMilestoneTitle(milestone);
  const taskTitle = getTaskTitle(task, props.selectedTaskIndex);
  const taskId = anyT.id as string | undefined;

  const acceptance = normalizeAcceptanceCriteria(task.acceptance_criteria ?? anyT.outputs);
  const deps = safeArray<string>(task.dependencies ?? anyT.depends_on);
  const files = safeArray<string>(task.files ?? anyT.output_files);
  const cmds = safeArray<string>(task.commands ?? anyT.commands);

  const raw = normalizeText(task);

  return (
    <section className="panel">
      <div className="panelHeader">
        <div className="headerRow">
          <h2>{taskTitle}</h2>
          <span className={`statusPill ${done ? "done" : ""}`}>{status}</span>
        </div>

        <div className="actionRow">
          <button
            className="primaryBtn"
            type="button"
            onClick={() => {
              const req = buildExecutionRequest({
                milestoneIndex: props.selectedMilestoneIndex,
                taskIndex: props.selectedTaskIndex,
                milestoneTitle,
                taskId,
                taskTitle,
                taskSnapshot: task,
              });
              persistExecutionRequest(req);
              setLastRequestJson(JSON.stringify(req, null, 2));
              console.log("Execution request emitted:", req);
            }}
            title="Emit deterministic execution request (no execution yet)"
          >
            Execute task
          </button>
        </div>

        <p className="muted">{milestoneTitle}</p>
      </div>

      <div className="panelBody">
        {task.description && (
          <div className="card">
            <div className="cardTitle">Description</div>
            <div className="cardBody">{task.description}</div>
          </div>
        )}

        {acceptance.length > 0 && (
          <div className="card">
            <div className="cardTitle">Acceptance criteria</div>
            <ul className="list">
              {acceptance.map((x, i) => (
                <li key={i}>{x}</li>
              ))}
            </ul>
          </div>
        )}

        {(deps.length > 0 || files.length > 0 || cmds.length > 0) && (
          <div className="grid2">
            {deps.length > 0 && (
              <div className="card">
                <div className="cardTitle">Dependencies</div>
                <ul className="list">
                  {deps.map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </div>
            )}

            {files.length > 0 && (
              <div className="card">
                <div className="cardTitle">Files</div>
                <ul className="list mono">
                  {files.map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </div>
            )}

            {cmds.length > 0 && (
              <div className="card">
                <div className="cardTitle">Commands</div>
                <ul className="list mono">
                  {cmds.map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        <div className="card">
          <div className="cardTitle">Raw task (debug)</div>
          <pre className="codeBlock">{raw}</pre>
        </div>

        <div className="card">
          <div className="cardTitle">Execution request (latest)</div>
          {lastRequestJson ? (
            <pre className="codeBlock">{lastRequestJson}</pre>
          ) : (
            <div className="muted small">No execution request emitted yet.</div>
          )}
        </div>
      </div>
    </section>
  );
}
