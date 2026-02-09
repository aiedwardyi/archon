import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

type Project = {
  id: number;
  name: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
  execution_count: number;
};

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectDescription, setNewProjectDescription] = useState("");
  const navigate = useNavigate();

  const loadProjects = async () => {
    try {
      setLoading(true);
      const res = await fetch("http://localhost:5000/api/projects", {
        cache: "no-store",
      });

      if (!res.ok) {
        throw new Error(`Failed to load projects: ${res.status}`);
      }

      const data = await res.json();
      setProjects(data);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();

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

      setNewProjectName("");
      setNewProjectDescription("");
      setShowCreateModal(false);
      loadProjects();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to create project");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "#10b981";
      case "in_progress":
        return "#3b82f6";
      case "failed":
        return "#ef4444";
      default:
        return "#6b7280";
    }
  };

  if (loading) {
    return (
      <section className="panel">
        <div className="panelHeader">
          <h2>Projects</h2>
          <p className="muted">Loading projects...</p>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="panel">
        <div className="panelHeader">
          <h2>Projects</h2>
          <p className="muted" style={{ color: "#ef4444" }}>
            Error: {error}
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panelHeader">
        <button
          onClick={() => navigate("/")}
          style={{
            background: "none",
            border: "none",
            color: "#3b82f6",
            cursor: "pointer",
            fontSize: "0.9rem",
            marginBottom: "0.5rem",
          }}
        >
          ← Back to Board
        </button>
        <div className="headerRow">
          <h2>Projects</h2>
          <button
            className="primaryBtn"
            type="button"
            onClick={() => setShowCreateModal(true)}
          >
            + New Project
          </button>
        </div>
        <p className="muted">
          {projects.length} project{projects.length !== 1 ? "s" : ""}
        </p>
      </div>

      <div className="panelBody">
        {projects.length === 0 ? (
          <div className="card">
            <div className="cardBody" style={{ textAlign: "center", padding: "3rem" }}>
              <p className="muted">No projects yet.</p>
              <button
                className="primaryBtn"
                type="button"
                onClick={() => setShowCreateModal(true)}
                style={{ marginTop: "1rem" }}
              >
                Create your first project
              </button>
            </div>
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1rem" }}>
            {projects.map((project) => (
              <div
                key={project.id}
                className="card"
                style={{ cursor: "pointer", transition: "transform 0.2s", border: "1px solid #333" }}
                onClick={() => navigate(`/projects/${project.id}`)}
                onMouseEnter={(e) => (e.currentTarget.style.transform = "translateY(-2px)")}
                onMouseLeave={(e) => (e.currentTarget.style.transform = "translateY(0)")}
              >
                <div className="cardTitle">{project.name}</div>
                <div className="cardBody">
                  {project.description && (
                    <p className="muted" style={{ fontSize: "0.9rem", marginBottom: "0.5rem" }}>
                      {project.description}
                    </p>
                  )}
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.75rem" }}>
                    <span
                      style={{
                        display: "inline-block",
                        width: "8px",
                        height: "8px",
                        borderRadius: "50%",
                        backgroundColor: getStatusColor(project.status),
                      }}
                    />
                    <span className="mono" style={{ fontSize: "0.85rem" }}>
                      {project.status}
                    </span>
                  </div>
                  <div className="muted" style={{ fontSize: "0.85rem", marginTop: "0.5rem" }}>
                    {project.execution_count} execution{project.execution_count !== 1 ? "s" : ""}
                  </div>
                  <div className="muted" style={{ fontSize: "0.75rem", marginTop: "0.5rem" }}>
                    Updated {new Date(project.updated_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showCreateModal && (
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
          onClick={() => setShowCreateModal(false)}
        >
          <div
            className="card"
            style={{ width: "500px", maxWidth: "90vw" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="cardTitle">Create New Project</div>
            <form onSubmit={handleCreateProject}>
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
                  required
                />
              </div>
              <div style={{ marginBottom: "1rem" }}>
                <label style={{ display: "block", marginBottom: "0.5rem" }}>
                  Description (optional)
                </label>
                <textarea
                  value={newProjectDescription}
                  onChange={(e) => setNewProjectDescription(e.target.value)}
                  placeholder="Brief description of what you're building..."
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
                  onClick={() => setShowCreateModal(false)}
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
                  type="submit"
                  className="primaryBtn"
                >
                  Create Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}
