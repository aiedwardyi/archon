import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

type Execution = {
  id: number;
  project_id: number;
  status: string;
  created_at: string;
  prd_path: string | null;
  plan_path: string | null;
  request_path: string | null;
  result_path: string | null;
  error_message: string | null;
};

type Project = {
  id: number;
  name: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
  execution_count: number;
  executions: Execution[];
};

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadProject = async () => {
    try {
      setLoading(true);
      const res = await fetch(`http://localhost:5000/api/projects/${projectId}`, {
        cache: "no-store",
      });

      if (!res.ok) {
        throw new Error(`Failed to load project: ${res.status}`);
      }

      const data = await res.json();
      setProject(data);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
      case "success":
        return "#10b981";
      case "in_progress":
      case "running":
        return "#3b82f6";
      case "failed":
      case "error":
        return "#ef4444";
      default:
        return "#6b7280";
    }
  };

  if (loading) {
    return (
      <section className="panel">
        <div className="panelHeader">
          <h2>Project Details</h2>
          <p className="muted">Loading project...</p>
        </div>
      </section>
    );
  }

  if (error || !project) {
    return (
      <section className="panel">
        <div className="panelHeader">
          <h2>Project Details</h2>
          <p className="muted" style={{ color: "#ef4444" }}>
            Error: {error || "Project not found"}
          </p>
          <button className="primaryBtn" onClick={() => navigate("/projects")}>
            Back to Projects
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panelHeader">
        <button
          onClick={() => navigate("/projects")}
          style={{
            background: "none",
            border: "none",
            color: "#3b82f6",
            cursor: "pointer",
            fontSize: "0.9rem",
            marginBottom: "0.5rem",
          }}
        >
          ← Back to Projects
        </button>
        <div className="headerRow">
          <h2>{project.name}</h2>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span
              style={{
                display: "inline-block",
                width: "10px",
                height: "10px",
                borderRadius: "50%",
                backgroundColor: getStatusColor(project.status),
              }}
            />
            <span className="mono" style={{ fontSize: "0.9rem" }}>
              {project.status}
            </span>
          </div>
        </div>
        {project.description && <p className="muted">{project.description}</p>}
        <p className="muted" style={{ fontSize: "0.85rem" }}>
          Created {new Date(project.created_at).toLocaleString()}
        </p>
      </div>

      <div className="panelBody">
        <h3 style={{ marginBottom: "1rem" }}>
          Execution History ({project.executions?.length || 0})
        </h3>

        {!project.executions || project.executions.length === 0 ? (
          <div className="card">
            <div className="cardBody" style={{ textAlign: "center", padding: "2rem" }}>
              <p className="muted">No executions yet for this project.</p>
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {project.executions.map((execution) => (
              <div key={execution.id} className="card">
                <div className="cardTitle">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span>Execution #{execution.id}</span>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <span
                        style={{
                          display: "inline-block",
                          width: "8px",
                          height: "8px",
                          borderRadius: "50%",
                          backgroundColor: getStatusColor(execution.status),
                        }}
                      />
                      <span className="mono" style={{ fontSize: "0.85rem" }}>
                        {execution.status}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="cardBody">
                  <div className="muted" style={{ fontSize: "0.85rem", marginBottom: "0.5rem" }}>
                    {new Date(execution.created_at).toLocaleString()}
                  </div>

                  {execution.error_message && (
                    <div
                      style={{
                        padding: "0.5rem",
                        backgroundColor: "#3d1f1f",
                        border: "1px solid #ef4444",
                        borderRadius: "4px",
                        marginTop: "0.5rem",
                      }}
                    >
                      <div style={{ fontSize: "0.85rem", color: "#ef4444" }}>
                        Error: {execution.error_message}
                      </div>
                    </div>
                  )}

                  <div style={{ marginTop: "0.75rem" }}>
                    <div className="muted" style={{ fontSize: "0.85rem", marginBottom: "0.25rem" }}>
                      Artifacts:
                    </div>
                    <div className="mono" style={{ fontSize: "0.75rem" }}>
                      {execution.request_path && (
                        <div>✓ Request: {execution.request_path}</div>
                      )}
                      {execution.result_path && (
                        <div>✓ Result: {execution.result_path}</div>
                      )}
                      {!execution.request_path && !execution.result_path && (
                        <div className="muted">No artifacts generated</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
