import { useState } from "react";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { CheckCircle2, XCircle, Download, RotateCcw, FileText, Blocks, Code2, Monitor, Smartphone } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface Version {
  id: number;
  label: string;
  status: "completed" | "failed";
  description: string;
  time: string;
  filesChanged: number;
  prompt?: string;
  buildSummary?: string;
  filesGenerated?: number;
}

const versions: Version[] = [
  { id: 10, label: "v10", status: "completed", description: "change the Join Community button …", time: "07:04 AM", filesChanged: 2, prompt: "change the Join Community button color to match the theme", buildSummary: "Pipeline completed successfully. 2 files were generated.", filesGenerated: 2 },
  { id: 9, label: "v9", status: "completed", description: "add a dark overlay to the hero b…", time: "06:52 AM", filesChanged: 2, prompt: "add a dark overlay to the hero background image", buildSummary: "Pipeline completed successfully. 2 files were generated.", filesGenerated: 2 },
  { id: 8, label: "v8", status: "completed", description: "add a mini game where the user ca…", time: "06:41 AM", filesChanged: 2, prompt: "add a mini game where the user can catch digimon", buildSummary: "Pipeline completed successfully. 2 files were generated.", filesGenerated: 2 },
  { id: 7, label: "v7", status: "completed", description: "add a mini game where the user ca…", time: "06:27 AM", filesChanged: 3, prompt: "add a mini game where the user can catch digimon", buildSummary: "Pipeline completed successfully. 3 files were generated.", filesGenerated: 3 },
  { id: 6, label: "v6", status: "failed", description: "add a mini game where the user ca…", time: "06:20 AM", filesChanged: 0, prompt: "add a mini game where the user can catch digimon", buildSummary: "Pipeline failed. 0 files were generated." },
  { id: 5, label: "v5", status: "failed", description: "add a mini game where the user ca…", time: "06:13 AM", filesChanged: 0, prompt: "add a mini game where the user can catch digimon", buildSummary: "Pipeline failed. 0 files were generated." },
  { id: 4, label: "v4", status: "failed", description: "add a mini game where the user ca…", time: "06:06 AM", filesChanged: 0, prompt: "add a mini game where the user can catch digimon", buildSummary: "Pipeline failed. 0 files were generated." },
  { id: 3, label: "v3", status: "failed", description: "i want to just add a mini game to…", time: "05:53 AM", filesChanged: 0, prompt: "i want to just add a mini game to the site", buildSummary: "Pipeline failed. 0 files were generated." },
  { id: 2, label: "v2", status: "completed", description: "lets do it", time: "05:21 AM", filesChanged: 2, prompt: "lets do it", buildSummary: "Pipeline completed successfully. 2 files were generated.", filesGenerated: 2 },
  { id: 1, label: "v1", status: "completed", description: "create me a digimon fan page webs…", time: "05:15 AM", filesChanged: 2, prompt: "create me a digimon fan page website", buildSummary: "Pipeline completed successfully. 2 files were generated.", filesGenerated: 2 },
];

const StatusIcon = ({ status }: { status: "completed" | "failed" }) =>
  status === "completed" ? (
    <CheckCircle2 className="h-4 w-4 text-emerald-500 flex-shrink-0" />
  ) : (
    <XCircle className="h-4 w-4 text-destructive flex-shrink-0" />
  );

export const VersionsView = () => {
  const [selected, setSelected] = useState(9);
  const [previewDevice, setPreviewDevice] = useState<"desktop" | "mobile">("desktop");
  const [collapsed, setCollapsed] = useState(false);
  const { t } = useLanguage();

  const version = versions.find((v) => v.id === selected)!;

  return (
    <div
      className="border border-border rounded-md overflow-hidden bg-card flex"
      style={{ height: "calc(100vh - 80px)" }}
    >
      {/* Left: Version History Sidebar */}
      {!collapsed && (
      <div className="w-[360px] flex-shrink-0 border-r border-border overflow-y-auto">
        <div className="px-5 py-3.5 border-b border-border flex items-center justify-between">
          <h2 className="text-xs font-semibold text-foreground uppercase tracking-wider flex items-center gap-1.5 whitespace-nowrap">
            ⏱ {t("versionHistory")}
          </h2>
          <button
            onClick={() => setCollapsed(true)}
            className="h-6 w-6 flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
            title="Collapse sidebar"
          >
            <PanelLeftClose className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="px-3 py-3">
          <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider px-2 py-1.5 mb-1">{t("yesterday")}</div>
          <div className="space-y-1">
            {versions.map((v) => {
              const isActive = v.id === selected;
              return (
                <button
                  key={v.id}
                  onClick={() => setSelected(v.id)}
                  className={`w-full text-left px-3 py-2.5 rounded-md transition-colors ${
                    isActive ? "bg-primary/10 border border-primary/20" : "hover:bg-secondary/60"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "bg-secondary text-muted-foreground"
                    }`}>
                      {v.label}
                    </span>
                    <StatusIcon status={v.status} />
                    <span className="text-[10px] text-muted-foreground ml-auto">{v.time}</span>
                  </div>
                  <p className="text-xs text-foreground mt-1.5 truncate leading-tight">{v.description}</p>
                  <p className="text-[11px] text-muted-foreground mt-1">{v.filesChanged} {t("filesChanged")}</p>
                </button>
              );
            })}
          </div>
        </div>
      </div>
      )}

      {/* Right: Version Detail */}
      <div className="flex-1 overflow-y-auto">
        {/* Header Bar */}
        <div className="px-5 py-3 border-b border-border bg-card flex items-center justify-between">
          <div className="flex items-center gap-3">
            {collapsed && (
              <button
                onClick={() => setCollapsed(false)}
                className="h-8 px-3 text-xs font-medium border border-border rounded-md text-foreground hover:bg-secondary transition-colors flex items-center gap-1.5"
              >
                <PanelLeftOpen className="h-3.5 w-3.5" /> {t("showVersions")}
              </button>
            )}
            <span className="text-xs font-bold bg-primary text-primary-foreground px-2 py-0.5 rounded">
              V{version.id}
            </span>
            <div className="flex items-center gap-1.5">
              <StatusIcon status={version.status} />
              <span className="text-xs font-medium text-foreground capitalize">{version.status}</span>
            </div>
            <span className="text-xs text-muted-foreground">{t("yesterday")} at {version.time}</span>
          </div>
          <div className="flex items-center gap-2">
            <button className="h-8 px-3 text-xs font-medium border border-border rounded-md text-foreground hover:bg-secondary transition-colors flex items-center gap-1.5">
              <Download className="h-3.5 w-3.5" /> {t("downloadReport")}
            </button>
            <button className="h-8 px-3 text-xs font-medium border border-border rounded-md text-foreground hover:bg-secondary transition-colors flex items-center gap-1.5">
              <RotateCcw className="h-3.5 w-3.5" /> {t("restoreToThisVersion")}
            </button>
          </div>
        </div>

        <div className="p-5 space-y-5">
          {/* Prompt Section */}
          <div className="border-l-2 border-primary pl-4">
            <div className="text-[10px] font-bold text-primary uppercase tracking-wider mb-1">
              {t("prompt")} {version.time}
            </div>
            <p className="text-sm text-foreground">{version.prompt}</p>
          </div>

          {/* What Was Built */}
          <div className="border-l-2 border-emerald-500 pl-4">
            <div className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider mb-1">
              {t("whatWasBuilt")} {version.time}
            </div>
            <p className="text-sm text-foreground">{version.buildSummary}</p>
          </div>

          {/* Artifacts Row */}
          <div className="grid grid-cols-3 gap-0 border border-border rounded-md overflow-hidden bg-card">
            {[
              { icon: FileText, title: t("brief"), subtitle: t("requirementsDoc") },
              { icon: Blocks, title: t("buildPlan"), subtitle: t("architecturePlan") },
              { icon: Code2, title: t("code"), subtitle: `${version.filesGenerated ?? 0} ${t("files")}` },
            ].map(({ icon: Icon, title, subtitle }, i) => (
              <button
                key={title}
                className={`flex items-center gap-3 px-4 py-3.5 text-left hover:bg-secondary/40 transition-colors ${
                  i < 2 ? "border-r border-border" : ""
                }`}
              >
                <div className="h-9 w-9 rounded-md bg-secondary flex items-center justify-center flex-shrink-0">
                  <Icon className="h-4.5 w-4.5 text-muted-foreground" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-foreground">{title}</div>
                  <div className="text-[11px] text-muted-foreground">{subtitle}</div>
                </div>
              </button>
            ))}
          </div>

          {/* Live Preview */}
          <div className="border border-border rounded-md bg-card overflow-hidden">
            <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground">{t("livePreview")}</h3>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPreviewDevice("desktop")}
                  className={`h-7 w-7 flex items-center justify-center rounded-md transition-colors ${
                    previewDevice === "desktop" ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Monitor className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => setPreviewDevice("mobile")}
                  className={`h-7 w-7 flex items-center justify-center rounded-md transition-colors ${
                    previewDevice === "mobile" ? "bg-secondary text-foreground" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Smartphone className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            <div className="flex items-center justify-center p-6 bg-secondary/20 min-h-[400px]">
              {previewDevice === "desktop" ? (
                <div className="w-full max-w-3xl bg-background border border-border rounded-lg overflow-hidden shadow-sm">
                  <div className="h-8 bg-secondary/60 border-b border-border flex items-center gap-1.5 px-3">
                    <span className="h-2.5 w-2.5 rounded-full bg-destructive/60" />
                    <span className="h-2.5 w-2.5 rounded-full bg-amber-400/60" />
                    <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/60" />
                    <div className="ml-3 h-4 w-48 bg-secondary rounded-sm" />
                  </div>
                  <div className="p-6 space-y-4">
                    <div className="h-6 w-48 bg-secondary rounded" />
                    <div className="h-32 bg-secondary/60 rounded-md" />
                    <div className="grid grid-cols-3 gap-3">
                      <div className="h-20 bg-secondary/40 rounded" />
                      <div className="h-20 bg-secondary/40 rounded" />
                      <div className="h-20 bg-secondary/40 rounded" />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="w-[280px] bg-background border-2 border-foreground/20 rounded-[2rem] overflow-hidden shadow-lg">
                  <div className="flex justify-center py-2">
                    <div className="h-4 w-20 bg-foreground/10 rounded-full" />
                  </div>
                  <div className="mx-2 mb-2 rounded-xl overflow-hidden border border-border">
                    <div className="p-4 space-y-3">
                      <div className="h-5 w-32 bg-secondary rounded" />
                      <div className="h-24 bg-secondary/60 rounded-md" />
                      <div className="h-4 w-full bg-secondary/40 rounded" />
                      <div className="h-4 w-3/4 bg-secondary/40 rounded" />
                      <div className="flex gap-2">
                        <div className="h-8 w-20 bg-primary/20 rounded" />
                        <div className="h-8 w-20 bg-secondary rounded" />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
