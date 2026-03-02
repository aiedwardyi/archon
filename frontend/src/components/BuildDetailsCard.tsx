import { useState, useEffect } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import { fetchBuildDetails, type BuildDetails } from "@/services/api";

interface BuildDetailsCardProps {
  projectId: number | null;
  version: number | null;
  refreshKey?: number;
}

export const BuildDetailsCard = ({ projectId, version, refreshKey }: BuildDetailsCardProps) => {
  const { t } = useLanguage();
  const [details, setDetails] = useState<BuildDetails | null>(null);

  useEffect(() => {
    if (!projectId || !version) { setDetails(null); return; }
    let cancelled = false;
    fetchBuildDetails(projectId, version).then((d) => {
      if (!cancelled) setDetails(d);
    });
    return () => { cancelled = true; };
  }, [projectId, version, refreshKey]);

  const rows = [
    { label: t("model"), value: details?.model ?? "—" },
    { label: t("creditsUsed"), value: details?.creditsUsed ?? "—" },
    { label: t("duration"), value: details?.duration ?? "—" },
  ];

  return (
    <div className="border border-border rounded-md bg-card">
      <div className="px-3 py-2 border-b border-border">
        <h3 className="text-xs font-semibold text-foreground tracking-wide uppercase">{t("buildDetails")}</h3>
      </div>
      <div className="divide-y divide-border">
        {rows.map(({ label, value }) => (
          <div key={label} className="px-3 py-2 flex items-center justify-between">
            <span className="text-[11px] text-muted-foreground">{label}</span>
            <span className="text-xs font-medium text-foreground">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
