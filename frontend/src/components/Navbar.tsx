import { useState, useRef, useEffect } from "react";
import { useTheme } from "./ThemeProvider";
import { useLanguage } from "@/contexts/LanguageContext";
import { authService } from "@/lib/auth";
import { ProfileModal } from "./ProfileModal";
import { SettingsModal } from "./SettingsModal";
import { PricingModal } from "./PricingModal";
import {
  Settings, LayoutGrid, Play, Clock, FileDown, Coins,
  User, Sun, Moon, Building2, Pencil, DollarSign, BookOpen, ExternalLink,
  LogOut, Zap, Hexagon, ChevronDown, Globe,
} from "lucide-react";

interface NavbarProps {
  activeTab?: string;
  onTabChange?: (tab: string) => void;
  selectedProjectName?: string;
  selectedProjectVersion?: string;
  selectedProjectId?: number | null;
}

export const Navbar = ({ activeTab = "projects", onTabChange, selectedProjectName, selectedProjectVersion, selectedProjectId }: NavbarProps) => {
  const [open, setOpen] = useState(false);
  const [activeModal, setActiveModal] = useState<"profile" | "settings" | "pricing" | null>(null);
  const [creditsRemaining, setCreditsRemaining] = useState<number | null>(null);
  const [userEmail, setUserEmail] = useState<string>("...");
  const menuRef = useRef<HTMLDivElement>(null);
  const { colorMode, setColorMode } = useTheme();
  const { language, toggleLanguage, t } = useLanguage();

  const initials = userEmail === "..." ? "..." : userEmail.slice(0, 2).toUpperCase();

  useEffect(() => {
    const token = localStorage.getItem("archon_token");
    if (!token) return;
    fetch("http://localhost:5000/api/auth/me", {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(d => { if (d.email) setUserEmail(d.email); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetch("http://localhost:5000/api/credits/balance")
      .then(r => r.json())
      .then(d => setCreditsRemaining(d.credits_remaining))
      .catch(() => {})
  }, []);

  const navItems = [
    { id: "projects", label: t("projects"), icon: LayoutGrid },
    { id: "pipeline", label: t("pipeline"), icon: Play },
    { id: "versions", label: t("versions"), icon: Clock },
    { id: "artifacts", label: t("artifacts"), icon: FileDown },
  ];

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <header className="h-12 border-b border-border bg-card flex items-center px-4 justify-between">
      {/* Left: Logo + Nav */}
      <div className="flex items-center gap-5">
        <div className="flex items-center gap-2 font-semibold text-foreground tracking-tight text-sm">
          <Hexagon className="h-5 w-5 text-blue-500 dark:text-primary" strokeWidth={2.5} />
          <span>Archon</span>
        </div>

        <div className="h-5 w-px bg-border" />

        <nav className="flex items-center gap-0.5">
          {navItems.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => onTabChange?.(id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeTab === id
                  ? "bg-secondary text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary/60"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Right: Breadcrumb + Language + Credits + Avatar */}
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-1.5 text-xs text-muted-foreground">
          <span>{selectedProjectName || t("buildAModern")}</span>
          <ChevronDown className="h-3 w-3" />
          <span className="font-medium text-foreground bg-secondary px-1.5 py-0.5 rounded text-[10px]">{selectedProjectVersion || "v1"}</span>
        </div>

        <div className="h-5 w-px bg-border" />

        {/* Language Toggle */}
        <button
          onClick={toggleLanguage}
          className="flex items-center gap-1 h-7 px-2 text-[11px] font-semibold rounded-md border border-border text-foreground hover:bg-secondary transition-colors"
        >
          <Globe className="h-3 w-3 text-muted-foreground" />
          {language === "en" ? "EN" : "KO"}
        </button>

        <div className="h-5 w-px bg-border" />

        <div className="flex items-center gap-1.5 text-xs font-medium text-foreground">
          <Coins className="h-3.5 w-3.5 text-amber-500" />
          {creditsRemaining !== null ? creditsRemaining.toLocaleString() : "—"}
        </div>

        <div className="h-5 w-px bg-border" />

        {/* Avatar + Dropdown */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setOpen(!open)}
            className="h-7 w-7 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-[11px] font-semibold cursor-pointer hover:opacity-90 transition-opacity ring-2 ring-background"
          >
            {initials}
          </button>

          {open && (
            <div className="absolute right-0 top-full mt-2 w-60 bg-card border border-border rounded-lg shadow-lg z-50 overflow-hidden">
              {/* Header */}
              <div className="px-4 py-3 border-b border-border bg-secondary/30">
                <div className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">{t("signedInAs")}</div>
                <div className="text-sm font-semibold text-foreground mt-0.5">{userEmail}</div>
              </div>

              {/* Menu items */}
              <div className="py-1">
                <MenuItem icon={User} label={t("profile")} onClick={() => { setActiveModal("profile"); setOpen(false); }} />
                <MenuItem icon={Settings} label={t("settings")} onClick={() => { setActiveModal("settings"); setOpen(false); }} />
                <MenuItem icon={DollarSign} label={t("pricing")} onClick={() => { setActiveModal("pricing"); setOpen(false); }} />
                <MenuItem icon={BookOpen} label={t("documentation")} external />
              </div>

              <div className="border-t border-border px-4 py-3">
                <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">{t("theme")}</div>
                <div className="grid grid-cols-2 gap-1">
                  {([
                    { value: "light" as const, label: t("light"), icon: Sun },
                    { value: "dark" as const, label: t("dark"), icon: Moon },
                  ]).map(({ value, label, icon: Icon }) => (
                    <button
                      key={value}
                      onClick={() => setColorMode(value)}
                      className={`flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs rounded-md transition-colors ${
                        colorMode === value
                          ? "bg-primary text-primary-foreground font-medium"
                          : "text-foreground hover:bg-secondary border border-border"
                      }`}
                    >
                      <Icon className="h-3.5 w-3.5" /> {label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="border-t border-border px-4 py-3">
                <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">{t("design")}</div>
                <div className="grid grid-cols-2 gap-1">
                  <button
                    onClick={() => { window.location.href = `http://localhost:8080${language === "ko" ? "?lang=ko" : ""}`; }}
                    className="flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs rounded-md transition-colors bg-primary text-primary-foreground font-medium"
                  >
                    <Building2 className="h-3.5 w-3.5" /> {t("enterprise")}
                  </button>
                  <button
                    onClick={() => {
                      const tab = activeTab || 'projects';
                      const params = new URLSearchParams();
                      const token = localStorage.getItem("archon_token");
                      if (token) params.set("token", token);
                      params.set("switch", "1");
                      if (selectedProjectId) params.set("pid", String(selectedProjectId));
                      if (language === "ko") params.set("lang", "ko");
                      const qs = params.toString() ? "?" + params.toString() : "";
                      const path = tab === "projects" ? "" : tab;
                      window.location.href = `http://localhost:3000/${path}${qs}`;
                    }}
                    className="flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs rounded-md transition-colors text-foreground hover:bg-secondary border border-border"
                  >
                    <Pencil className="h-3.5 w-3.5" /> {t("studio")}
                  </button>
                </div>
              </div>

              {/* Credits */}
              <div className="border-t border-border px-4 py-2.5 flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Coins className="h-3.5 w-3.5 text-amber-500" /> {t("credits")}
                </div>
                <span className="text-sm font-bold text-foreground">{creditsRemaining !== null ? creditsRemaining.toLocaleString() : "—"}</span>
              </div>

              {/* Upgrade */}
              <div className="border-t border-border px-4 py-3">
                <button className="w-full h-8 bg-primary text-primary-foreground text-xs font-semibold rounded-md flex items-center justify-center gap-1.5 hover:opacity-90 transition-opacity">
                  <Zap className="h-3.5 w-3.5" /> {t("upgradeToPro")}
                </button>
              </div>

              {/* Sign out */}
              <div className="border-t border-border py-1">
                <button
                  onClick={() => { authService.logout(); window.location.href = "/login"; }}
                  className="w-full flex items-center gap-2.5 px-4 py-2 text-xs text-destructive hover:bg-secondary transition-colors"
                >
                  <LogOut className="h-3.5 w-3.5" /> {t("signOut")}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
      <ProfileModal open={activeModal === "profile"} onClose={() => setActiveModal(null)} />
      <SettingsModal open={activeModal === "settings"} onClose={() => setActiveModal(null)} />
      <PricingModal open={activeModal === "pricing"} onClose={() => setActiveModal(null)} />
    </header>
  );
};

const MenuItem = ({ icon: Icon, label, external, onClick }: { icon: typeof User; label: string; external?: boolean; onClick?: () => void }) => (
  <button onClick={onClick} className="w-full flex items-center justify-between px-4 py-2 text-xs text-foreground hover:bg-secondary transition-colors">
    <span className="flex items-center gap-2.5">
      <Icon className="h-3.5 w-3.5 text-muted-foreground" /> {label}
    </span>
    {external && <ExternalLink className="h-3 w-3 text-muted-foreground" />}
  </button>
);
