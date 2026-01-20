export async function postExecutionRequest(
  req: unknown,
  endpoint = "http://127.0.0.1:8000/execution-request",
  timeoutMs = 1500
): Promise<{ ok: true } | { ok: false; error: string }> {
  // AbortController is built into the browser (no extra installs, no extra files)
  const controller = new AbortController();

  // Set up a timer that will abort the request after timeoutMs
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
      signal: controller.signal,
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      return { ok: false, error: `HTTP ${res.status} ${res.statusText} ${text}`.trim() };
    }

    return { ok: true };
  } catch (e: any) {
    // If we aborted due to timeout, show a clean message
    if (e?.name === "AbortError") {
      return { ok: false, error: "Request timed out" };
    }
    return { ok: false, error: e?.message ?? "Network error" };
  } finally {
    // Always clear the timer, whether success/fail/timeout
    window.clearTimeout(timer);
  }
}
