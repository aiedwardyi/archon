import React, { useEffect, useState, useRef } from "react";
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

type Project = {
  id: number;
  name: string;
  description: string;
  status: string;
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
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Project selection state
  const [showProjectModal, setShowProjectModal] = useState<boolean>(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [showCreateProject, setShowCreateProject] = useState<boolean>(false);
  const [newProjectName, setNewProjectName] = useState<string>("");
  const [newProjectDescription, setNewProjectDescription] = useState<string>("");

  useEffect(() => {
    const v = localStorage.getItem("last_execution_request");
    if (v) setLastRequestJson(v);
    
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, []);

  const loadProjects = async () => {
    try {
      const res = await fetch("http://localhost:5000/api/projects", { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
      }
    } catch (e) {
      console.error("Failed to load projects:", e);
    }
  };

  const handleExecuteClick = async () => {
    await loadProjects();
    setShowProjectModal(true);
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) {
      alert("Project name is required");
      return;
    }

    try {
      const res = await fetch("http://localhost:5000/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newProjectName,
          description: newProjectDescription,
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to create project");
      }

      const newProject = await res.json();
      setProjects([newProject, ...projects]);
      setSelectedProjectId(newProject.id);
      setNewProjectName("");
      setNewProjectDescription("");
      setShowCreateProject(false);
      showToast(`Project "${newProject.name}" created!`, "success");
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to create project");
    }
  };

  const handleExecute = async () => {
    if (!selectedProjectId) {
      alert("Please select a project");
      return;
    }

    setShowProjectModal(false);

    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    setIsExecuting(true);
    showToast("Task execution started...", "info");

    try {
      console.log("📡 Fetching plan artifact...");
      
      const planRes = await fetch("http://localhost:5000/api/plan", { cache: "no-store" });
      const planArtifact = await planRes.json();
      const agentSequence = planArtifact?._agent_sequence || [];
      
      console.log("📋 Agent sequence:", agentSequence);

      const milestoneTitle = getMilestoneTitle(milestone!);
      const taskTitle = getTaskTitle(task!, props.selectedTaskIndex);
      const anyT = task as any;
      const taskId = anyT.id as string | undefined;

      const req = buildExecutionRequest({
        milestoneIndex: props.selectedMilestoneIndex,
        taskIndex: props.selectedTaskIndex,
        milestoneTitle,
        taskId,
        taskTitle,
        taskSnapshot: task!,
        agentSequence,
      });

      // Add project_id to request
      (req as any).project_id = selectedProjectId;

      console.log("📤 Execution request:", req);

      localStorage.setItem("last_execution_request", JSON.stringify(req, null, 2));
      setLastRequestJson(JSON.stringify(req, null, 2));

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

      const executeData = await executeRes.json();
      console.log("✅ Flask response:", executeData);

      let attempts = 0;
      const maxAttempts = 30;
      
      const checkStatus = async () => {
        attempts++;
        console.log(`🔄 Poll attempt ${attempts}/${maxAttempts}`);

        try {
          const statusRes = await fetch("http://localhost:5000/api/execution-status", {
            method: "GET",
            cache: "no-store",
            headers: {
              "Cache-Control": "no-cache",
              "Pragma": "no-cache"
            }
          });

          console.log(`📡 Poll response status: ${statusRes.status}`);

          if (statusRes.ok) {
            const result = await statusRes.json();
            console.log("📥 Poll result:", result);
            console.log(`   ➜ status field: "${result.status}"`);
            
            if (result.status === "success") {
              if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
                pollIntervalRef.current = null;
              }
              setIsExecuting(false);
              console.log("✅ SUCCESS DETECTED! Showing green toast...");
              showToast("Task execution completed!", "success");
              return true;
            } else if (result.status === "error") {
              if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
                pollIntervalRef.current = null;
              }
              setIsExecuting(false);
              console.log("❌ ERROR DETECTED! Showing error toast...");
              showToast(`Execution failed: ${result.error?.message || "Unknown error"}`, "error");
              return true;
            } else {
              console.log(`⏳ Status: "${result.status}", continuing to poll...`);
            }
          } else {
            console.warn(`⚠️ Poll response not OK: ${statusRes.status}, continuing...`);
          }
        } catch (pollError) {
          console.error("❌ Poll fetch error (will retry):", pollError);
        }

        if (attempts >= maxAttempts) {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setIsExecuting(false);
          console.warn("⏱️ Polling timeout after", maxAttempts, "attempts");
          showToast("Execution timeout - check artifacts panel", "error");
          return true;
        }
        
        return false;
      };

      pollIntervalRef.current = setInterval(() => {
        checkStatus().catch(err => {
          console.error("❌ Unexpected error in checkStatus:", err);
        });
      }, 2000);

      setTimeout(() => {
        checkStatus().catch(err => {
          console.error("❌ Unexpected error in initial checkStatus:", err);
        });
      }, 1000);

    } catch (e) {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      setIsExecuting(false);
      const message = e instanceof Error ? e.message : "Unknown error";
      console.error("❌ Execution error:", e);
      showToast(`Failed to start execution: ${message}`, "error");
    }
  };

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
            onClick={handleExecuteClick}
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

      {/* Project Selection Modal */}
      {showProjectModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
          onClick={() => setShowProjectModal(false)}
        >
          <div
            className="card"
            style={{ width: "500px", maxWidth: "90vw" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="cardTitle">Select Project</div>
            
            {!showCreateProject ? (
              <>
                <div style={{ marginBottom: "1rem" }}>
                  <label style={{ display: "block", marginBottom: "0.5rem" }}>
                    Choose a project for this execution:
                  </label>
                  <select
                    value={selectedProjectId || ""}
                    onChange={(e) => setSelectedProjectId(Number(e.target.value))}
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      backgroundColor: "#1a1a1a",
                      border: "1px solid #333",
                      color: "#fff",
                      borderRadius: "4px",
                    }}
                  >
                    <option value="">Select a project...</option>
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.status})
                      </option>
                    ))}
                  </select>
                </div>

                <div style={{ marginBottom: "1rem" }}>
                  <button
                    type="button"
                    onClick={() => setShowCreateProject(true)}
                    style={{
                      padding: "0.5rem 1rem",
                      backgroundColor: "#333",
                      border: "1px solid #555",
                      color: "#fff",
                      borderRadius: "4px",
                      cursor: "pointer",
                      width: "100%",
                    }}
                  >
                    + Create New Project
                  </button>
                </div>

                <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
                  <button
                    type="button"
                    onClick={() => setShowProjectModal(false)}
                    style={{
                      padding: "0.5rem 1rem",
                      backgroundColor: "#333",
                      border: "none",
                      color: "#fff",
                      borderRadius: "4px",
                      cursor: "pointer",
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleExecute}
                    className="primaryBtn"
                    disabled={!selectedProjectId}
                  >
                    Execute
                  </button>
                </div>
              </>
            ) : (
              <>
                <div style={{ marginBottom: "1rem" }}>
                  <label style={{ display: "block", marginBottom: "0.5rem" }}>
                    Project Name *
                  </label>
                  <input
                    type="text"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    placeholder="e.g., Calculator App"
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      backgroundColor: "#1a1a1a",
                      border: "1px solid #333",
                      color: "#fff",
                      borderRadius: "4px",
                    }}
                    autoFocus
                  />
                </div>
                <div style={{ marginBottom: "1rem" }}>
                  <label style={{ display: "block", marginBottom: "0.5rem" }}>
                    Description (optional)
                  </label>
                  <textarea
                    value={newProjectDescription}
                    onChange={(e) => setNewProjectDescription(e.target.value)}
                    placeholder="Brief description..."
                    rows={3}
                    style={{
                      width: "100%",
                      padding: "0.5rem",
                      backgroundColor: "#1a1a1a",
                      border: "1px solid #333",
                      color: "#fff",
                      borderRadius: "4px",
                      resize: "vertical",
                    }}
                  />
                </div>
                <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateProject(false);
                      setNewProjectName("");
                      setNewProjectDescription("");
                    }}
                    style={{
                      padding: "0.5rem 1rem",
                      backgroundColor: "#333",
                      border: "none",
                      color: "#fff",
                      borderRadius: "4px",
                      cursor: "pointer",
                    }}
                  >
                    Back
                  </button>
                  <button
                    type="button"
                    onClick={handleCreateProject}
                    className="primaryBtn"
                  >
                    Create & Select
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
