import React, { useEffect, useMemo, useState } from "react";

type HistoryDef = {
  id: "execution_requests" | "execution_results" | "evaluation_results";
  title: string;
  path: string;
  description: string;
};

type ParsedHistory =
  | {
      ok: true;
      items: unknown[];
      skippedLines: number;
      totalLines: number;
    }
  | {
      ok: false;
      message: string;
      status?: number;
    };

type LoadState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "missing"; message: string }
  | { status: "error"; message: string }
  | { status: "loaded"; items: unknown[]; totalLines: number; skippedLines: number };

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function asString(v: unknown): string {
  return typeof v === "string" ? v : "";
}

function safeShort(v: string, n: number): string {
  if (!v) return "";
  if (v.length <= n) return v;
  return v.slice(0, n) + "…";
}

function labelForItem(item: unknown): { title: string; subtitle: string } {
  if (!isRecord(item)) return { title: "(non-object)", subtitle: "" };

  const taskId = asString(item.task_id);
  const requestHash = asString((item as Record<string, unknown>).request_hash);
  const kind = asString(item.kind);

  const createdAt =
    asString((item as Record<string, unknown>).created_at) || asString((item as Record<string, unknown>).requested_at_iso);

  const titleParts: string[] = [];
  if (taskId) titleParts.push(taskId);
  if (requestHash) titleParts.push(safeShort(requestHash, 10));
  if (!taskId && !requestHash && kind) titleParts.push(kind);
  if (titleParts.length === 0) titleParts.push("(item)");

  const subtitleParts: string[] = [];
  if (createdAt) subtitleParts.push(createdAt);
  if (kind) subtitleParts.push(kind);

  return {
    title: titleParts.join(" • "),
    subtitle: subtitleParts.join(" • "),
  };
}

function tryPrettyJson(v: unknown): string {
  try {
    return JSON.stringify(v, null, 2);
  } catch {
    return String(v);
  }
}

function parseNdjson(text: string): { items: unknown[]; skippedLines: number; totalLines: number } {
  const lines = text.split(/\r?\n/);
  const items: unknown[] = [];
  let skippedLines = 0;
  let totalLines = 0;

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) continue;
    totalLines += 1;
    try {
      items.push(JSON.parse(line));
    } catch {
      skippedLines += 1;
    }
  }

  return { items, skippedLines, totalLines };
}

async function fetchTextStrict(path: string): Promise<{ ok: boolean; status: number; text: string }> {
  const res = await fetch(path, { cache: "no-store" });
  const text = await res.text();
  return { ok: res.ok, status: res.status, text };
}

async function loadHistory(path: string): Promise<ParsedHistory> {
  const res = await fetchTextStrict(path);
  if (!res.ok) {
    return { ok: false, message: `Failed to fetch ${path}: ${res.status}`, status: res.status };
  }
  const parsed = parseNdjson(res.text);
  return { ok: true, ...parsed };
}

function matchesFilter(item: unknown, filterTaskId: string, filterRequestHash: string): boolean {
  if (!filterTaskId && !filterRequestHash) return true;
  if (!isRecord(item)) return false;

  if (filterTaskId) {
    const taskId = asString(item.task_id);
    if (!taskId || !taskId.toLowerCase().includes(filterTaskId.toLowerCase())) return false;
  }

  if (filterRequestHash) {
    const requestHash = asString((item as Record<string, unknown>).request_hash);
    if (!requestHash || !requestHash.toLowerCase().includes(filterRequestHash.toLowerCase())) return false;
  }

  return true;
}

export function HistoryPanel() {
  const histories: HistoryDef[] = useMemo(
    () => [
      {
        id: "execution_requests",
        title: "execution_requests.ndjson",
        path: "/execution_requests.ndjson",
        description: "Append-only history of execution requests emitted by the UI/server.",
      },
      {
        id: "execution_results",
        title: "execution_results.ndjson",
        path: "/execution_results.ndjson",
        description: "Append-only history of execution results produced by the consumer.",
      },
      {
        id: "evaluation_results",
        title: "evaluation_results.ndjson",
        path: "/evaluation_results.ndjson",
        description: "Append-only history of evaluation results produced by the evaluator.",
      },
    ],
    []
  );

  const [selectedId, setSelectedId] = useState<string>(histories[0]?.id ?? "");
  const selected = useMemo(() => histories.find((h) => h.id === selectedId) ?? histories[0], [histories, selectedId]);

  const [filterTaskId, setFilterTaskId] = useState<string>("");
  const [filterRequestHash, setFilterRequestHash] = useState<string>("");

  const [state, setState] = useState<LoadState>({ status: "idle" });
  const [selectedIndex, setSelectedIndex] = useState<number>(0);

  useEffect(() => {
    let cancelled = false;
    if (!selected) return;

    (async () => {
      setState({ status: "loading" });
      const res = await loadHistory(selected.path);
      if (cancelled) return;

      if (!res.ok) {
        if (res.status === 404) {
          setState({ status: "missing", message: `Missing (404). File not found at ${selected.path}` });
          return;
        }

        setState({ status: "error", message: res.message });
        return;
      }

      setSelectedIndex(0);
      setState({ status: "loaded", items: res.items, totalLines: res.totalLines, skippedLines: res.skippedLines });
    })().catch((e) => {
      if (cancelled) return;
      setState({ status: "error", message: e instanceof Error ? e.message : String(e) });
    });

    return () => {
      cancelled = true;
    };
  }, [selected]);

  const filteredItems = useMemo(() => {
    if (state.status !== "loaded") return [] as unknown[];
    return state.items.filter((it) => matchesFilter(it, filterTaskId.trim(), filterRequestHash.trim()));
  }, [state, filterTaskId, filterRequestHash]);

  const selectedItem = filteredItems[selectedIndex];
  const selectedLabel = labelForItem(selectedItem);

  useEffect(() => {
    if (selectedIndex < 0) setSelectedIndex(0);
    if (selectedIndex >= filteredItems.length) setSelectedIndex(0);
  }, [filteredItems, selectedIndex]);

  return (
    <section className="panel">
      <div className="panelHeader">
        <h2>History</h2>
        <p className="muted">
          Read-only NDJSON histories loaded directly from <span className="mono">/public</span>. Malformed lines are
          ignored and surfaced as counts.
        </p>
      </div>

      <div className="panelBody historyLayout">
        <div className="card">
          <div className="cardTitle">Files</div>
          <div className="artifactsButtons">
            {histories.map((h) => (
              <button
                key={h.id}
                type="button"
                className={`artifactBtn ${h.id === selected?.id ? "active" : ""}`}
                onClick={() => setSelectedId(h.id)}
              >
                <div className="artifactBtnTitle mono">{h.title}</div>
                <div className="small">{h.description}</div>
              </button>
            ))}
          </div>

          <div style={{ marginTop: 12 }}>
            <div className="cardTitle">Filters</div>

            <label className="searchLabel small">
              task_id contains
              <input
                className="searchInput"
                value={filterTaskId}
                onChange={(e) => setFilterTaskId(e.target.value)}
                placeholder="e.g. TASK-001"
              />
            </label>

            <label className="searchLabel small">
              request_hash contains
              <input
                className="searchInput"
                value={filterRequestHash}
                onChange={(e) => setFilterRequestHash(e.target.value)}
                placeholder="e.g. 9f2c…"
              />
            </label>
          </div>
        </div>

        <div className="card">
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
            <>
              <div className="historyMeta">
                <div className="small">
                  lines parsed: <span className="mono">{state.totalLines}</span> • skipped:{" "}
                  <span className="mono">{state.skippedLines}</span>
                </div>
                <div className="small">
                  items shown: <span className="mono">{filteredItems.length}</span> /{" "}
                  <span className="mono">{state.items.length}</span>
                </div>
              </div>

              <div className="historySplit">
                <div className="historyList">
                  {filteredItems.length === 0 ? (
                    <div className="muted small">No items match the current filters.</div>
                  ) : (
                    filteredItems.map((it, idx) => {
                      const lbl = labelForItem(it);
                      return (
                        <button
                          key={idx}
                          type="button"
                          className={`historyRow ${idx === selectedIndex ? "active" : ""}`}
                          onClick={() => setSelectedIndex(idx)}
                        >
                          <div className="mono" style={{ fontSize: 12, marginBottom: 6 }}>
                            {lbl.title}
                          </div>
                          <div className="small">{lbl.subtitle || " "}</div>
                        </button>
                      );
                    })
                  )}
                </div>

                <div className="historyViewer">
                  <div className="cardTitle">Entry</div>
                  <div className="small" style={{ marginBottom: 8 }}>
                    {selectedLabel.title}
                  </div>
                  <pre className="codeBlock">{selectedItem ? tryPrettyJson(selectedItem) : "(no selection)"}</pre>
                </div>
              </div>
            </>
          ) : (
            <div className="muted small" style={{ marginTop: 10 }}>
              Select a history file.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}