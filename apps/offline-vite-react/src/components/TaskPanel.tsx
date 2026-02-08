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
import { showToast } from "./ToastContainer";

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

export function TaskPanel(props: Props) {
  const milestone = pickMilestone(props.plan, props.selectedMilestoneIndex);
  const task = pickTask(milestone, props.selectedTaskIndex);

  const [lastRequestJson, setLastRequestJson] = useState<string>("");
  const [isExecuting, setIsExecuting] = useState<boolean>(false);

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

  const handleExecute = async () => {
    console.log("🚀 BUTTON CLICKED!");
    alert("Button clicked! Check console for logs.");
    
    setIsExecuting(true);
    showToast("Task execution started...", "info");

    try {
      console.log("📡 Fetching plan artifact...");
      
      // Fetch plan artifact to get agent sequence
      const planRes = await fetch("http://localhost:5000/api/plan", { cache: "no-store" });
      const planArtifact = await planRes.json();
      const agentSequence = planArtifact?._agent_sequence || [];
      
      console.log("📋 Agent sequence:", agentSequence);

      // Build execution request
      const req = buildExecutionRequest({
        milestoneIndex: props.selectedMilestoneIndex,
        taskIndex: props.selectedTaskIndex,
        milestoneTitle,
        taskId,
        taskTitle,
        taskSnapshot: task,
        agentSequence,
      });

      console.log("📤 Execution request:", req);

      // Save to localStorage for debugging
      localStorage.setItem("last_execution_request", JSON.stringify(req, null, 2));
      setLastRequestJson(JSON.stringify(req, null, 2));

      // POST to Flask API
      console.log("🌐 Sending to Flask...");
      const executeRes = await fetch("http://localhost:5000/api/execute-task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
      });

      if (!executeRes.ok) {
        const error = await executeRes.json();
        throw new Error(error.error || "Failed to execute task");
      }

      console.log("✅ Task execution request sent to Flask");

      // Poll for result
      let attempts = 0;
      const maxAttempts = 15;
      
      const pollInterval = setInterval(async () => {
        attempts++;
        console.log(`🔄 Polling attempt ${attempts}/${maxAttempts}`);

        try {
          const statusRes = await fetch("http://localhost:5000/api/execution-status", {
            cache: "no-store",
          });

          if (statusRes.ok) {
            const result = await statusRes.json();
            console.log("📥 Poll result:", {
              status: result.status,
              taskId: result.request?.task_id,
              hasError: !!result.error
            });
            
            if (result.status === "success") {
              clearInterval(pollInterval);
              setIsExecuting(false);
              console.log("✅ Execution succeeded!");
              showToast("Task execution completed!", "success");
            } else if (result.status === "error") {
              clearInterval(pollInterval);
              setIsExecuting(false);
              console.log("❌ Execution failed:", result.error);
              showToast(`Execution failed: ${result.error?.message || "Unknown error"}`, "error");
            }
          } else {
            console.warn("⚠️ Poll response not OK:", statusRes.status);
          }

          if (attempts >= maxAttempts) {
            clearInterval(pollInterval);
            setIsExecuting(false);
            console.warn("⏱️ Polling timeout");
            showToast("Execution timeout - check artifacts panel", "error");
          }
        } catch (e) {
          console.error("❌ Poll error:", e);
        }
      }, 2000);

    } catch (e) {
      setIsExecuting(false);
      const message = e instanceof Error ? e.message : "Unknown error";
      console.error("❌ Execution error:", e);
      showToast(`Failed to start execution: ${message}`, "error");
    }
  };

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
            onClick={handleExecute}
            disabled={isExecuting}
            title="Execute task via Flask API"
          >
            {isExecuting ? "Executing..." : "Execute task"}
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
