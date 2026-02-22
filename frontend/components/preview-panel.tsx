"use client"

import { useState, useEffect } from "react"
import { Monitor, Smartphone, ExternalLink, RefreshCw } from "lucide-react"

const API_BASE = "http://localhost:5000"

interface PreviewPanelProps {
  projectId?: number | null
  version?: number | null
}

function ViewportToggle({
  viewport,
  onChange,
}: {
  viewport: "desktop" | "mobile"
  onChange: (v: "desktop" | "mobile") => void
}) {
  return (
    <div className="flex items-center bg-muted rounded-md p-0.5">
      <button
        onClick={() => onChange("desktop")}
        className={`p-1.5 rounded transition-colors ${
          viewport === "desktop"
            ? "bg-card text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        }`}
        aria-label="Desktop view"
      >
        <Monitor className="h-3.5 w-3.5" />
      </button>
      <button
        onClick={() => onChange("mobile")}
        className={`p-1.5 rounded transition-colors ${
          viewport === "mobile"
            ? "bg-card text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        }`}
        aria-label="Mobile view"
      >
        <Smartphone className="h-3.5 w-3.5" />
      </button>
    </div>
  )
}

export function PreviewPanel({ projectId, version }: PreviewPanelProps) {
  const [viewport, setViewport] = useState<"desktop" | "mobile">("desktop")
  const [key, setKey] = useState(0) // increment to force iframe reload

  const previewUrl =
    projectId && version
      ? `${API_BASE}/api/preview/${projectId}/${version}`
      : null

  // Force reload when project/version changes
  useEffect(() => {
    setKey((k) => k + 1)
  }, [projectId, version])

  const handleOpenNewTab = () => {
    if (previewUrl) window.open(previewUrl, "_blank")
  }

  const handleRefresh = () => {
    setKey((k) => k + 1)
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-card">
        <div className="flex-1" />
        <ViewportToggle viewport={viewport} onChange={setViewport} />
        <div className="flex-1 flex justify-end items-center gap-1.5">
          {previewUrl && (
            <button
              onClick={handleRefresh}
              className="p-1.5 rounded border border-border text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              aria-label="Refresh preview"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
          )}
          <button
            onClick={handleOpenNewTab}
            disabled={!previewUrl}
            className="p-1.5 rounded border border-border text-muted-foreground hover:text-foreground hover:bg-muted transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            aria-label="Open in new tab"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Preview area */}
      <div className="flex-1 flex items-center justify-center bg-muted/30 p-6">
        {viewport === "mobile" ? (
          <div className="relative w-[290px]">
            {/* iPhone frame */}
            <div className="rounded-[2.5rem] border-[3px] border-foreground/20 bg-card p-2 shadow-lg">
              <div className="flex justify-center mb-2">
                <div className="w-20 h-5 bg-foreground/20 rounded-full" />
              </div>
              <div className="rounded-[2rem] overflow-hidden bg-muted/50 min-h-[520px] border border-border">
                {previewUrl ? (
                  <iframe
                    key={key}
                    src={previewUrl}
                    className="w-full h-full min-h-[520px] border-0"
                    title="Live preview (mobile)"
                    sandbox="allow-scripts allow-same-origin"
                  />
                ) : (
                  <div className="flex items-center justify-center min-h-[520px]">
                    <p className="text-xs text-muted-foreground text-center px-4">
                      Live preview will appear here
                      <br />
                      when your build is complete
                    </p>
                  </div>
                )}
              </div>
              <div className="flex justify-center mt-2">
                <div className="w-28 h-1 bg-foreground/15 rounded-full" />
              </div>
            </div>
          </div>
        ) : (
          <div className="w-full" style={{ height: "700px" }}>
            {previewUrl ? (
              <iframe
                key={key}
                src={previewUrl}
                className="w-full border border-border rounded-lg bg-white"
                style={{ height: "700px" }}
                title="Live preview (desktop)"
                sandbox="allow-scripts allow-same-origin"
              />
            ) : (
              <div className="border-2 border-dashed border-border rounded-lg flex items-center justify-center" style={{ height: "700px" }}>
                <p className="text-sm text-muted-foreground">
                  Live preview will appear here when your build is complete
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}


