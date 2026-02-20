"use client"

import { useState, useEffect } from "react"
import {
  FileText,
  Code2,
  ListChecks,
  ScrollText,
  MapPin,
  Braces,
  ChevronRight,
  ChevronDown,
  File,
  Folder,
  Shield,
  CheckCircle2,
  Play,
  Monitor,
  Smartphone,
  ExternalLink,
  Eye,
} from "lucide-react"

const tabs = [
  { id: "brief", label: "Brief", icon: FileText },
  { id: "plan", label: "Plan", icon: MapPin },
  { id: "code", label: "Code", icon: Code2 },
  { id: "tasks", label: "Tasks", icon: ListChecks },
  { id: "logs", label: "Logs", icon: ScrollText },
  { id: "preview", label: "Preview", icon: Eye },
]

type FileNode = {
  name: string
  type: "file" | "folder"
  children?: FileNode[]
  language?: string
}

const fileTree: FileNode[] = [
  {
    name: "src",
    type: "folder",
    children: [
      {
        name: "handlers",
        type: "folder",
        children: [
          { name: "webhook.ts", type: "file", language: "typescript" },
          { name: "payment.ts", type: "file", language: "typescript" },
          { name: "retry.ts", type: "file", language: "typescript" },
        ],
      },
      {
        name: "models",
        type: "folder",
        children: [
          { name: "transaction.ts", type: "file", language: "typescript" },
          { name: "webhook-event.ts", type: "file", language: "typescript" },
        ],
      },
      {
        name: "utils",
        type: "folder",
        children: [
          { name: "crypto.ts", type: "file", language: "typescript" },
          { name: "logger.ts", type: "file", language: "typescript" },
        ],
      },
      { name: "index.ts", type: "file", language: "typescript" },
      { name: "config.ts", type: "file", language: "typescript" },
    ],
  },
  {
    name: "tests",
    type: "folder",
    children: [
      { name: "webhook.test.ts", type: "file", language: "typescript" },
      { name: "retry.test.ts", type: "file", language: "typescript" },
    ],
  },
  { name: "package.json", type: "file", language: "json" },
  { name: "tsconfig.json", type: "file", language: "json" },
]

const codeContent = [
  "import { WebhookEvent } from '../models/webhook-event';",
  "import { logger } from '../utils/logger';",
  "import { verifySignature } from '../utils/crypto';",
  "",
  "interface RetryConfig {",
  "  maxAttempts: number;",
  "  baseDelay: number;",
  "  maxDelay: number;",
  "  backoffMultiplier: number;",
  "}",
  "",
  "const DEFAULT_RETRY_CONFIG: RetryConfig = {",
  "  maxAttempts: 5,",
  "  baseDelay: 1000,",
  "  maxDelay: 30000,",
  "  backoffMultiplier: 2,",
  "};",
  "",
  "export class WebhookRetryHandler {",
  "  private config: RetryConfig;",
  "  private deadLetterQueue: WebhookEvent[] = [];",
  "",
  "  constructor(config: Partial<RetryConfig> = {}) {",
  "    this.config = { ...DEFAULT_RETRY_CONFIG, ...config };",
  "  }",
  "",
  "  async processWithRetry(event: WebhookEvent): Promise<boolean> {",
  "    let attempt = 0;",
  "    let delay = this.config.baseDelay;",
  "",
  "    while (attempt < this.config.maxAttempts) {",
  "      try {",
  "        await this.deliver(event);",
  "        logger.info(`Webhook delivered successfully`, {",
  "          eventId: event.id,",
  "          attempt: attempt + 1,",
  "        });",
  "        return true;",
  "      } catch (error) {",
  "        attempt++;",
  "        if (attempt >= this.config.maxAttempts) {",
  "          logger.error(`Max retry attempts reached`, {",
  "            eventId: event.id,",
  "            attempts: attempt,",
  "          });",
  "          this.deadLetterQueue.push(event);",
  "          return false;",
  "        }",
  "        logger.warn(`Retry attempt ${attempt}`, {",
  "          eventId: event.id,",
  "          nextDelay: delay,",
  "        });",
  "        await this.sleep(delay);",
  "        delay = Math.min(",
  "          delay * this.config.backoffMultiplier,",
  "          this.config.maxDelay",
  "        );",
  "      }",
  "    }",
  "    return false;",
  "  }",
  "",
  "  private async deliver(event: WebhookEvent): Promise<void> {",
  "    const isValid = verifySignature(",
  "      event.payload,",
  "      event.signature,",
  "      event.secret",
  "    );",
  "    if (!isValid) {",
  "      throw new Error('Invalid webhook signature');",
  "    }",
  "",
  "    const response = await fetch(event.endpoint, {",
  "      method: 'POST',",
  "      headers: {",
  "        'Content-Type': 'application/json',",
  "        'X-Webhook-Signature': event.signature,",
  "        'X-Webhook-Id': event.id,",
  "      },",
  "      body: JSON.stringify(event.payload),",
  "    });",
  "",
  "    if (!response.ok) {",
  "      throw new Error(`Delivery failed: ${response.status}`);",
  "    }",
  "  }",
  "",
  "  private sleep(ms: number): Promise<void> {",
  "    return new Promise((resolve) => setTimeout(resolve, ms));",
  "  }",
  "",
  "  getDeadLetterQueue(): WebhookEvent[] {",
  "    return [...this.deadLetterQueue];",
  "  }",
  "}",
].join("\n")

const prdContent = {
  title: "Payment Service - Webhook Retry Logic",
  version: "v14",
  epics: [
    {
      name: "Webhook Retry Mechanism",
      requirements: [
        "Implement exponential backoff retry strategy for failed webhook deliveries",
        "Support configurable max attempts (default: 5)",
        "Support configurable base delay and max delay thresholds",
        "Log each retry attempt with structured metadata",
      ],
    },
    {
      name: "Dead Letter Queue",
      requirements: [
        "Move permanently failed webhooks to a dead letter queue",
        "Provide API endpoint to inspect DLQ contents",
        "Support manual retry of DLQ items",
      ],
    },
    {
      name: "Monitoring & Observability",
      requirements: [
        "Emit metrics for retry attempts and success/failure rates",
        "Add structured logging for all webhook lifecycle events",
        "Integrate with existing alerting for DLQ threshold breaches",
      ],
    },
  ],
}

const tasks = [
  { id: 1, title: "Create RetryConfig interface and defaults", status: "completed", agent: "Build" },
  { id: 2, title: "Implement WebhookRetryHandler class", status: "completed", agent: "Build" },
  { id: 3, title: "Add exponential backoff with jitter", status: "completed", agent: "Build" },
  { id: 4, title: "Implement dead letter queue storage", status: "completed", agent: "Build" },
  { id: 5, title: "Add webhook signature verification", status: "in-progress", agent: "Build" },
  { id: 6, title: "Create DLQ inspection API endpoint", status: "pending", agent: "Build" },
  { id: 7, title: "Add structured logging throughout", status: "pending", agent: "Build" },
  { id: 8, title: "Write unit tests for retry logic", status: "pending", agent: "Build" },
]

function FileTreeNode({
  node,
  depth = 0,
  selectedFile,
  onSelect,
}: {
  node: FileNode
  depth?: number
  selectedFile: string
  onSelect: (name: string) => void
}) {
  const [expanded, setExpanded] = useState(depth < 2)
  const isFolder = node.type === "folder"
  const isSelected = node.name === selectedFile

  return (
    <div>
      <button
        onClick={() => {
          if (isFolder) setExpanded(!expanded)
          else onSelect(node.name)
        }}
        className={`w-full flex items-center gap-1.5 py-1 px-2 text-xs hover:bg-muted/60 transition-colors rounded ${
          isSelected ? "bg-accent text-accent-foreground" : "text-foreground/80"
        }`}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
      >
        {isFolder ? (
          expanded ? (
            <ChevronDown className="h-3 w-3 text-muted-foreground shrink-0" />
          ) : (
            <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0" />
          )
        ) : (
          <span className="w-3 shrink-0" />
        )}
        {isFolder ? (
          <Folder className="h-3.5 w-3.5 text-primary/60 shrink-0" />
        ) : (
          <File className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
        )}
        <span className="font-mono truncate">{node.name}</span>
      </button>
      {isFolder && expanded && node.children && (
        <div>
          {node.children.map((child) => (
            <FileTreeNode
              key={child.name}
              node={child}
              depth={depth + 1}
              selectedFile={selectedFile}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function highlightLine(line: string): string {
  const keywords = /\b(import|from|export|class|interface|const|let|new|return|async|await|try|catch|throw|if|while|private|extends|typeof|void|number|string|boolean|true|false|null|undefined)\b/g
  const strings = /(["'` + "`" + `])(?:(?=(\\?))\2.)*?\1/g
  const comments = /(\/\/.*$)/g

  let highlighted = line
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")

  highlighted = highlighted.replace(
    comments,
    '<span class="text-muted-foreground/60 italic">$1</span>'
  )
  highlighted = highlighted.replace(
    strings,
    '<span class="text-success">$&</span>'
  )
  highlighted = highlighted.replace(
    keywords,
    '<span class="text-primary font-medium">$1</span>'
  )

  return highlighted
}

function SyntaxHighlightedCode({ code }: { code: string }) {
  const lines = code.split("\n")
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <div className="text-xs font-mono leading-5">
      {lines.map((line, i) => (
        <div key={i} className="flex hover:bg-muted/30 transition-colors">
          <span className="w-12 text-right pr-4 text-muted-foreground/40 select-none shrink-0">
            {i + 1}
          </span>
          <pre className="flex-1 overflow-x-auto">
            <code>
              {mounted ? (
                <span dangerouslySetInnerHTML={{ __html: highlightLine(line) }} />
              ) : (
                <span>{line}</span>
              )}
            </code>
          </pre>
        </div>
      ))}
    </div>
  )
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

export function ArtifactViewer() {
  const [activeTab, setActiveTab] = useState("brief")
  const [selectedFile, setSelectedFile] = useState("retry.ts")
  const [showRawJson, setShowRawJson] = useState(false)
  const [previewViewport, setPreviewViewport] = useState<"desktop" | "mobile">("desktop")

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="border-b border-border bg-card px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs">
            <span className="flex items-center gap-1 font-mono">
              <span className="text-muted-foreground font-medium">Requirements</span>
              <ChevronRight className="h-3 w-3 text-muted-foreground/50" />
              <span className="text-info font-medium">Architecture</span>
              <ChevronRight className="h-3 w-3 text-muted-foreground/50" />
              <span className="text-primary font-medium">Code</span>
            </span>
            <span className="mx-2 text-border">|</span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-success/30 bg-success/10 text-success">
              <Play className="h-3 w-3" />
              Reproducible
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-info/30 bg-info/10 text-info">
              <Shield className="h-3 w-3" />
              Verified
            </span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-primary/30 bg-primary/10 text-primary font-mono">
              V14
            </span>
          </div>
          <button
            onClick={() => setShowRawJson(!showRawJson)}
            className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded border transition-colors ${
              showRawJson
                ? "bg-primary text-primary-foreground border-primary"
                : "border-border text-muted-foreground hover:text-foreground hover:bg-muted"
            }`}
          >
            <Braces className="h-3 w-3" />
            Raw Data
          </button>
        </div>
      </div>

      <div className="border-b border-border bg-card px-6">
        <div className="flex items-center gap-0">
          {tabs.map((tab) => {
            const isActive = tab.id === activeTab
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-4 py-2.5 text-sm border-b-2 transition-colors ${
                  isActive
                    ? "border-primary text-foreground font-medium"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <tab.icon className="h-3.5 w-3.5" />
                {tab.label}
              </button>
            )
          })}
        </div>
      </div>

      <div className="flex-1 overflow-hidden flex">
        {activeTab === "code" && (
          <>
            <aside className="w-56 border-r border-border bg-card overflow-auto py-2 shrink-0">
              {fileTree.map((node) => (
                <FileTreeNode
                  key={node.name}
                  node={node}
                  selectedFile={selectedFile}
                  onSelect={setSelectedFile}
                />
              ))}
            </aside>
            <div className="flex-1 overflow-auto bg-card p-4">
              <div className="flex items-center gap-2 mb-3 pb-3 border-b border-border">
                <File className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs font-mono text-foreground">
                  src/handlers/{selectedFile}
                </span>
                <span className="text-xs text-muted-foreground ml-auto">
                  TypeScript
                </span>
              </div>
              {showRawJson ? (
                <pre className="text-xs font-mono text-foreground/80 whitespace-pre-wrap leading-5">
                  {JSON.stringify({ file: selectedFile, content: codeContent, language: "typescript" }, null, 2)}
                </pre>
              ) : (
                <SyntaxHighlightedCode code={codeContent} />
              )}
            </div>
          </>
        )}

        {activeTab === "brief" && (
          <div className="flex-1 overflow-auto p-6">
            {showRawJson ? (
              <pre className="text-xs font-mono text-foreground/80 whitespace-pre-wrap bg-card border border-border rounded-lg p-4 leading-5">
                {JSON.stringify(prdContent, null, 2)}
              </pre>
            ) : (
              <div className="max-w-3xl">
                <div className="flex items-center gap-3 mb-6">
                  <h2 className="text-lg font-semibold text-foreground">
                    {prdContent.title}
                  </h2>
                  <span className="text-xs font-mono bg-primary text-primary-foreground px-2 py-0.5 rounded">
                    {prdContent.version}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mb-4">
                  v1.0 &middot; Generated by Archon
                </p>
                <div className="space-y-6">
                  {prdContent.epics.map((epic, i) => (
                    <div
                      key={i}
                      className="bg-card border border-border rounded-lg p-5"
                    >
                      <h3 className="text-sm font-semibold text-foreground mb-1">
                        {i === 0 ? "What We're Building" : epic.name}
                      </h3>
                      <h4 className="text-xs text-muted-foreground mb-3">
                        Success Criteria
                      </h4>
                      <ul className="space-y-2">
                        {epic.requirements.map((req, j) => (
                          <li
                            key={j}
                            className="flex items-start gap-2 text-sm text-foreground/80"
                          >
                            <span className="h-1.5 w-1.5 rounded-full bg-primary mt-2 shrink-0" />
                            {req}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "plan" && (
          <div className="flex-1 overflow-auto p-6">
            <div className="max-w-3xl">
              <h2 className="text-lg font-semibold text-foreground mb-1">
                Build Plan
              </h2>
              <p className="text-xs text-muted-foreground mb-4">
                4 modules &middot; Est. 28s
              </p>
              <div className="bg-card border border-border rounded-lg p-5">
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-semibold text-foreground mb-2">
                      Architecture Overview
                    </h3>
                    <p className="text-sm text-foreground/70 leading-relaxed">
                      The retry mechanism will be implemented as a standalone handler class within the existing webhook processing pipeline. It uses exponential backoff with configurable parameters and routes permanently failed events to a dead letter queue for manual inspection and retry.
                    </p>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-foreground mb-2">
                      Files to Create / Modify
                    </h3>
                    <div className="space-y-1.5">
                      {[
                        { file: "src/handlers/retry.ts", action: "CREATE", uses: "logger, crypto" },
                        { file: "src/models/webhook-event.ts", action: "MODIFY", uses: "types" },
                        { file: "src/handlers/webhook.ts", action: "MODIFY", uses: "retry, logger" },
                        { file: "tests/retry.test.ts", action: "CREATE", uses: "vitest" },
                      ].map((item) => (
                        <div
                          key={item.file}
                          className="flex items-center gap-3 text-sm py-1.5 px-3 rounded bg-muted/30"
                        >
                          <span
                            className={`text-xs font-mono font-medium px-1.5 py-0.5 rounded ${
                              item.action === "CREATE"
                                ? "bg-success/10 text-success"
                                : "bg-warning/10 text-warning"
                            }`}
                          >
                            {item.action}
                          </span>
                          <span className="font-mono text-foreground/80 text-xs">
                            {item.file}
                          </span>
                          <span className="text-muted-foreground text-xs ml-auto">
                            Uses: {item.uses}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "tasks" && (
          <div className="flex-1 overflow-auto p-6">
            <div className="max-w-3xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-foreground">
                  Build Tasks
                </h2>
                <span className="text-xs text-muted-foreground">
                  {tasks.filter((t) => t.status === "completed").length}/{tasks.length} completed
                </span>
              </div>
              <div className="h-1.5 bg-muted rounded-full mb-6 overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all"
                  style={{
                    width: `${(tasks.filter((t) => t.status === "completed").length / tasks.length) * 100}%`,
                  }}
                />
              </div>
              <div className="space-y-2">
                {tasks.map((task) => (
                  <div
                    key={task.id}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg border transition-colors ${
                      task.status === "completed"
                        ? "border-border bg-card"
                        : task.status === "in-progress"
                        ? "border-info bg-info/5"
                        : "border-border bg-muted/20"
                    }`}
                  >
                    {task.status === "completed" ? (
                      <CheckCircle2 className="h-4 w-4 text-success shrink-0" />
                    ) : task.status === "in-progress" ? (
                      <div className="h-4 w-4 rounded-full border-2 border-info animate-pulse-dot shrink-0" />
                    ) : (
                      <div className="h-4 w-4 rounded-full border-2 border-muted-foreground/30 shrink-0" />
                    )}
                    <span
                      className={`text-sm flex-1 ${
                        task.status === "completed"
                          ? "text-muted-foreground line-through"
                          : "text-foreground"
                      }`}
                    >
                      {task.title}
                    </span>
                    <span className="text-xs text-muted-foreground font-mono">
                      {task.agent}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === "logs" && (
          <div className="flex-1 overflow-auto p-6">
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-border flex items-center justify-between">
                <h3 className="text-sm font-semibold text-foreground">
                  Pipeline Execution Logs
                </h3>
                <span className="text-xs text-muted-foreground">v14</span>
              </div>
              <div className="p-4 font-mono text-xs space-y-0.5">
                {[
                  { ts: "14:23:01.234", agent: "System", msg: "Pipeline started for payment-service v14" },
                  { ts: "14:23:01.235", agent: "System", msg: "Agent chain: Requirements > Architecture > Code" },
                  { ts: "14:23:01.500", agent: "Req", msg: "Analyzing your request..." },
                  { ts: "14:23:04.102", agent: "Req", msg: "Requirements document created" },
                  { ts: "14:23:07.445", agent: "Req", msg: "Requirements verified and ready" },
                  { ts: "14:23:08.201", agent: "Req", msg: "Handing off to Architecture Agent" },
                  { ts: "14:23:09.012", agent: "Arch", msg: "Planning the build..." },
                  { ts: "14:23:11.334", agent: "Arch", msg: "Created 4 build tasks" },
                  { ts: "14:23:13.891", agent: "Arch", msg: "Resolving build dependencies..." },
                  { ts: "14:23:15.102", agent: "Arch", msg: "Restructuring retry-handler dependencies" },
                  { ts: "14:23:17.445", agent: "Arch", msg: "Build plan ready — 4 files" },
                ].map((log, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 py-1 px-2 rounded hover:bg-muted/30"
                  >
                    <span className="text-muted-foreground/50 w-24 shrink-0">
                      {log.ts}
                    </span>
                    <span
                      className={`w-16 shrink-0 font-medium ${
                        log.agent === "Arch"
                          ? "text-info"
                          : "text-muted-foreground"
                      }`}
                    >
                      [{log.agent}]
                    </span>
                    <span className="text-foreground/70">{log.msg}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === "preview" && (
          <div className="flex-1 overflow-auto flex flex-col">
            <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-card">
              <div className="flex-1" />
              <ViewportToggle
                viewport={previewViewport}
                onChange={setPreviewViewport}
              />
              <div className="flex-1 flex justify-end">
                <button
                  className="p-1.5 rounded border border-border text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                  aria-label="Open in new tab"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <div className="flex-1 flex items-center justify-center bg-muted/30 p-6">
              {previewViewport === "mobile" ? (
                <div className="relative w-[290px]">
                  <div className="rounded-[2.5rem] border-[3px] border-foreground/20 bg-card p-2 shadow-lg">
                    <div className="flex justify-center mb-2">
                      <div className="w-20 h-5 bg-foreground/20 rounded-full" />
                    </div>
                    <div className="rounded-[2rem] overflow-hidden bg-muted/50 min-h-[520px] flex items-center justify-center border border-border">
                      <p className="text-xs text-muted-foreground text-center px-4">
                        Live preview will appear here when your build is complete
                      </p>
                    </div>
                    <div className="flex justify-center mt-2">
                      <div className="w-28 h-1 bg-foreground/15 rounded-full" />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="w-full h-full min-h-[400px]">
                  <div className="border-2 border-dashed border-border rounded-lg flex items-center justify-center h-full min-h-[400px]">
                    <p className="text-sm text-muted-foreground">
                      Live preview will appear here when your build is complete
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
