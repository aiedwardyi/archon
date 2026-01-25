import React, { useEffect, useMemo, useState } from "react";

type ArtifactKind = "json" | "text";

type ArtifactDef = {
  id: string;
  title: string;
  path: string;
  kind: ArtifactKind;
  description: string;
};

type LoadState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "missing"; message: string }
  | { status: "error"; message: string }
  | { status: "loaded"; rawText: string; prettyText?: string };

async function fetchTextStrict(path: string): Promise<{ ok: boolean; status: number; text: string }> {
  const res = await fetch(path, { cache: "no-store" });
  const text = await res.text();
  return { ok: res.ok, status: res.status, text };
}

function tryPrettyJson(raw: string): { ok: true; pretty: string } | { ok: false; error: string } {
  try {
    const parsed = JSON.parse(raw);
    return { ok: true, pretty: JSON.stringify(parsed, null, 2) };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : String(e) };
  }
}

export function ArtifactsPanel() {
  const artifacts: ArtifactDef[] = useMemo(
    () => [
      {
        id: "last_execution_request",
        title: "last_execution_request.json",
        path: "/last_execution_request.json",
        kind: "json",
        description: "Most recent request emitted by the orchestrator (runtime artifact).",
      },
      {
        id: "last_execution_result",
        title: "last_execution_result.json",
        path: "/last_execution_result.json",
        kind: "json",
        description: "Most recent execution result produced by the consumer (runtime artifact).",
      },
      {
        id: "last_evaluation_result",
        title: "last_evaluation_result.json",
        path: "/last_evaluation_result.json",
        kind: "json",
        description: "Most recent evaluation result produced by the evaluator (runtime artifact).",
      },
    ],
    []
  );

  const [selectedId, setSelectedId] = useState<string>(artifacts[0]?.id ?? "");
  const selected = useMemo(
    () => artifacts.find((a) => a.id === selectedId) ?? artifacts[0],
    [artifacts, selectedId]
  );

  const [state, setState] = useState<LoadState>({ status: "idle" });

  useEffect(() => {
    let cancelled = false;
    if (!selected) return;

    (async () => {
      setState({ status: "loading" });
      const res = await fetchTextStrict(selected.path);

      if (cancelled) return;

      if (!res.ok) {
        if (res.status === 404) {
          setState({ status: "missing", message: `Missing (${res.status}). File not found at ${selected.path}` });
          return;
        }

        setState({ status: "error", message: `Failed to fetch ${selected.path}: ${res.status}` });
        return;
      }

      const rawText = res.text;

      if (selected.kind === "json") {
        const pretty = tryPrettyJson(rawText);
        if (!pretty.ok) {
          setState({
            status: "error",
            message: `JSON parse error in ${selected.title}: ${pretty.error}`,
          });
          return;
        }

        setState({ status: "loaded", rawText, prettyText: pretty.pretty });
        return;
      }

      setState({ status: "loaded", rawText });
    })().catch((e) => {
      if (cancelled) return;
      setState({ status: "error", message: e instanceof Error ? e.message : String(e) });
    });

    return () => {
      cancelled = true;
    };
  }, [selected]);

  return (
    <section className="panel">
      <div className="panelHeader">
        <h2>Artifacts</h2>
        <p className="muted">
          Read-only runtime artifacts loaded directly from <span className="mono">/public</span>. Missing files and
          parse errors are treated as visible UI state.
        </p>
      </div>

      <div className="panelBody artifactsLayout">
        <div className="card artifactsList">
          <div className="cardTitle">Files</div>
          <div className="artifactsButtons">
            {artifacts.map((a) => (
              <button
                key={a.id}
                type="button"
                className={`artifactBtn ${a.id === selected?.id ? "active" : ""}`}
                onClick={() => setSelectedId(a.id)}
              >
                <div className="artifactBtnTitle mono">{a.title}</div>
                <div className="small">{a.description}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="card artifactsViewer">
          <div className="headerRow">
            <div>
              <div className="cardTitle">Selected</div>
              <div className="mono" style={{ fontSize: 13 }}>
                {selected?.path}
              </div>
            </div>

            <div className={`statusPill ${state.status === "loaded" ? "done" : ""}`} title={state.status}>
              {state.status}
            </div>
          </div>

          {state.status === "loading" ? (
            <div className="muted small" style={{ marginTop: 10 }}>
              Loading...
            </div>
          ) : state.status === "missing" ? (
            <div className="muted small" style={{ marginTop: 10 }}>
              {state.message}
            </div>
          ) : state.status === "error" ? (
            <div className="muted small" style={{ marginTop: 10 }}>
              {state.message}
            </div>
          ) : state.status === "loaded" ? (
            <pre className="codeBlock" style={{ marginTop: 10 }}>
              {state.prettyText ?? state.rawText ?? "(empty)"}
            </pre>
          ) : (
            <div className="muted small" style={{ marginTop: 10 }}>
              Select an artifact.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}