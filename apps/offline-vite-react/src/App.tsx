import React, { useEffect, useMemo, useState } from "react";
import "./App.css";
import { Plan, PlanMilestone, PlanTask, safeArray } from "./types/plan";
import { PlanSidebar } from "./components/PlanSidebar";
import { TaskPanel } from "./components/TaskPanel";
import { ArtifactsPanel } from "./components/ArtifactsPanel";

type Tab = "board" | "raw" | "artifacts";

async function fetchText(path: string): Promise<string> {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch ${path}: ${res.status}`);
  return await res.text();
}

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch ${path}: ${res.status}`);
  return (await res.json()) as T;
}

export default function App() {
  const [tab, setTab] = useState<Tab>("board");

  const [plan, setPlan] = useState<Plan | null>(null);
  const [planError, setPlanError] = useState<string>("");

  const [prdText, setPrdText] = useState<string>("");
  const [prdError, setPrdError] = useState<string>("");

  const [selectedMilestoneIndex, setSelectedMilestoneIndex] = useState<number>(0);
  const [selectedTaskIndex, setSelectedTaskIndex] = useState<number>(0);

  const [filterText, setFilterText] = useState<string>("");

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const p = await fetchJson<Plan>("/last_plan.json");
        if (cancelled) return;
        setPlan(p);
        setPlanError("");
      } catch (e) {
        if (cancelled) return;
        setPlan(null);
        setPlanError(e instanceof Error ? e.message : String(e));
      }
    })();

    (async () => {
      try {
        let txt = "";
        try {
          txt = await fetchText("/last_prd.txt");
        } catch {
          txt = await fetchText("/last_prd.md");
        }
        if (cancelled) return;
        setPrdText(txt);
        setPrdError("");
      } catch (e) {
        if (cancelled) return;
        setPrdText("");
        setPrdError(e instanceof Error ? e.message : String(e));
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const milestones = useMemo(() => safeArray<PlanMilestone>(plan?.milestones), [plan]);

  useEffect(() => {
    if (!plan) return;

    if (selectedMilestoneIndex < 0) setSelectedMilestoneIndex(0);
    if (selectedMilestoneIndex >= milestones.length) setSelectedMilestoneIndex(0);

    const m = milestones[selectedMilestoneIndex];
    const tasks = safeArray<PlanTask>(m?.tasks);

    if (selectedTaskIndex < 0) setSelectedTaskIndex(0);
    if (selectedTaskIndex >= tasks.length) setSelectedTaskIndex(0);
  }, [plan, milestones, selectedMilestoneIndex, selectedTaskIndex]);

  return (
    <div className="appShell">
      <PlanSidebar
        plan={plan}
        selectedMilestoneIndex={selectedMilestoneIndex}
        selectedTaskIndex={selectedTaskIndex}
        onSelectMilestone={setSelectedMilestoneIndex}
        onSelectTask={setSelectedTaskIndex}
        filterText={filterText}
        onChangeFilterText={setFilterText}
      />

      <main className="panel">
        <div className="topBar">
          <div className="tabs">
            <button
              className={`tabBtn ${tab === "board" ? "active" : ""}`}
              onClick={() => setTab("board")}
              type="button"
            >
              Board
            </button>

            <button
              className={`tabBtn ${tab === "raw" ? "active" : ""}`}
              onClick={() => setTab("raw")}
              type="button"
            >
              PRD / Raw JSON
            </button>

            <button
              className={`tabBtn ${tab === "artifacts" ? "active" : ""}`}
              onClick={() => setTab("artifacts")}
              type="button"
            >
              Artifacts
            </button>
          </div>

          <div className="small mono">
            {plan ? "plan loaded" : "plan missing"}
            {planError ? ` | error: ${planError}` : ""}
          </div>
        </div>

        {tab === "board" ? (
          <TaskPanel
            plan={plan}
            selectedMilestoneIndex={selectedMilestoneIndex}
            selectedTaskIndex={selectedTaskIndex}
          />
        ) : tab === "raw" ? (
          <RawView prdText={prdText} prdError={prdError} plan={plan} planError={planError} />
        ) : (
          <ArtifactsPanel />
        )}
      </main>
    </div>
  );
}

function RawView(props: { prdText: string; prdError: string; plan: Plan | null; planError: string }) {
  const planText = props.plan ? JSON.stringify(props.plan, null, 2) : "";

  return (
    <section className="panel">
      <div className="panelHeader">
        <h2>PRD / Raw JSON</h2>
        <p className="muted">Deterministic exports rendered for debugging + trust.</p>
      </div>

      <div className="panelBody twoCol">
        <div className="card">
          <div className="cardTitle">PRD</div>
          {props.prdError ? (
            <div className="muted small">Failed to load PRD: {props.prdError}</div>
          ) : (
            <pre className="codeBlock">{props.prdText || "(empty)"}</pre>
          )}
        </div>

        <div className="card">
          <div className="cardTitle">Plan JSON</div>
          {props.planError ? (
            <div className="muted small">Failed to load Plan: {props.planError}</div>
          ) : (
            <pre className="codeBlock">{planText || "(empty)"}</pre>
          )}
        </div>
      </div>
    </section>
  );
}