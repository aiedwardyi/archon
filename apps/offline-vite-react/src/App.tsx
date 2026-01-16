import { useEffect, useMemo, useState } from "react";

type Plan = unknown;

function CodeBlock({ title, text }: { title: string; text: string }) {
  return (
    <section className="card">
      <div className="cardHeader">
        <h2>{title}</h2>
      </div>
      <pre className="code">
        <code>{text}</code>
      </pre>
    </section>
  );
}

export default function App() {
  const [prd, setPrd] = useState<string>("");
  const [planRaw, setPlanRaw] = useState<string>("");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setError("");

        const [prdRes, planRes] = await Promise.all([
          fetch("/last_prd.txt", { cache: "no-store" }),
          fetch("/last_plan.json", { cache: "no-store" }),
        ]);

        if (!prdRes.ok) throw new Error(`Failed to load /last_prd.txt (${prdRes.status})`);
        if (!planRes.ok) throw new Error(`Failed to load /last_plan.json (${planRes.status})`);

        const prdText = await prdRes.text();
        const planText = await planRes.text();

        if (cancelled) return;

        setPrd(prdText);
        setPlanRaw(planText);
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : String(e));
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const planPretty = useMemo(() => {
    if (!planRaw.trim()) return "";
    try {
      const parsed: Plan = JSON.parse(planRaw);
      return JSON.stringify(parsed, null, 2);
    } catch {
      return planRaw;
    }
  }, [planRaw]);

  return (
    <main className="page">
      <header className="header">
        <div>
          <h1>AI Dev Team — Preview</h1>
          <p className="muted">
            Reads <code>public/last_prd.txt</code> and <code>public/last_plan.json</code> exported by{" "}
            the orchestrator.
          </p>
        </div>
        <div className="pill">OFFLINE friendly</div>
      </header>

      {error ? (
        <section className="card">
          <h2>Load error</h2>
          <p className="error">{error}</p>
          <p className="muted">
            Run <code>python run.py</code> (OFFLINE_MODE=1 is fine) to export the files, then refresh.
          </p>
        </section>
      ) : (
        <>
          <CodeBlock title="PRD" text={prd || "(loading...)"} />
          <CodeBlock title="Plan JSON" text={planPretty || "(loading...)"} />
        </>
      )}
    </main>
  );
}
