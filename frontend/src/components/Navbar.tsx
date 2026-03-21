import { useState, useRef, useEffect } from "react";
import { useTheme } from "./ThemeProvider";
import { useLanguage } from "@/contexts/LanguageContext";
import { authService } from "@/lib/auth";
import { DEMO_MODE } from "@/demo/demoMode";
import { getDemoViewerProfile } from "@/demo/demoData";
import { ProfileModal } from "./ProfileModal";
import { SettingsModal } from "./SettingsModal";
import { PricingModal } from "./PricingModal";
import {
  Settings, LayoutGrid, Play, Clock, FileDown, Coins,
  User, Sun, Moon, Building2, Pencil, DollarSign, BookOpen, ExternalLink,
  LogOut, Hexagon, ChevronDown, Globe,
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
    if (DEMO_MODE) {
      const viewer = getDemoViewerProfile();
      setUserEmail(viewer.email);
      return;
    }
    const loadUser = () => {
      const params = new URLSearchParams(window.location.search);
      const urlToken = params.get("token");
      const token = localStorage.getItem("archon_token") || urlToken;
      if (!token) return;

      const cached = localStorage.getItem("archon_user");
      if (cached) {
        try {
          const u = JSON.parse(cached);
          if (u?.email) { setUserEmail(u.email); return; }
        } catch {}
      }

      fetch("http://localhost:5000/api/auth/me", {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((r) => r.json())
        .then((d) => { if (d.email) setUserEmail(d.email); })
        .catch(() => {});
    };

    loadUser();
    window.addEventListener("storage", loadUser);
    return () => window.removeEventListener("storage", loadUser);
  }, []);

  useEffect(() => {
    if (DEMO_MODE) {
      setCreditsRemaining(getDemoViewerProfile().creditsRemaining);
      return;
    }
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
          <Hexagon className="h-5 w-5 text-blue-600 dark:text-blue-500" strokeWidth={2.5} />
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
                <MenuItem icon={User} label={t("profile")} onClick={() => { if (!DEMO_MODE) { setActiveModal("profile"); } setOpen(false); }} disabled={DEMO_MODE} />
                <MenuItem icon={Settings} label={t("settings")} onClick={() => { if (!DEMO_MODE) { setActiveModal("settings"); } setOpen(false); }} disabled={DEMO_MODE} />
                <MenuItem icon={DollarSign} label={t("pricing")} onClick={() => { if (!DEMO_MODE) { setActiveModal("pricing"); } setOpen(false); }} disabled={DEMO_MODE} />
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
                    disabled
                    className="flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs rounded-md transition-colors bg-primary/70 text-primary-foreground font-medium opacity-70 cursor-not-allowed"
                  >
                    <Building2 className="h-3.5 w-3.5" /> {t("enterprise")}
                  </button>
                  <button
                    disabled
                    className="flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs rounded-md transition-colors text-muted-foreground border border-border opacity-60 cursor-not-allowed"
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
                <button disabled={DEMO_MODE} className={`w-full h-8 text-xs font-semibold rounded-md flex items-center justify-center gap-1.5 ${DEMO_MODE ? "bg-primary/50 text-primary-foreground opacity-70 cursor-not-allowed" : "bg-primary text-primary-foreground hover:opacity-90 transition-opacity"}`}>
                  <Hexagon className="h-3.5 w-3.5" /> {t("upgradeToPro")}
                </button>
              </div>

              {/* Sign out */}
              <div className="border-t border-border py-1">
                <button
                  onClick={() => {
                    if (DEMO_MODE) {
                      setOpen(false);
                      return;
                    }
                    authService.logout();
                    window.location.href = "/login";
                  }}
                  className={`w-full flex items-center gap-2.5 px-4 py-2 text-xs transition-colors ${DEMO_MODE ? "text-muted-foreground cursor-not-allowed" : "text-destructive hover:bg-secondary"}`}
                >
                  <LogOut className="h-3.5 w-3.5" /> {DEMO_MODE ? "Read-only demo" : t("signOut")}
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

const MenuItem = ({ icon: Icon, label, external, onClick, disabled }: { icon: typeof User; label: string; external?: boolean; onClick?: () => void; disabled?: boolean }) => (
  <button onClick={disabled ? undefined : onClick} disabled={disabled} className={`w-full flex items-center justify-between px-4 py-2 text-xs transition-colors ${disabled ? "text-muted-foreground cursor-not-allowed" : "text-foreground hover:bg-secondary"}`}>
    <span className="flex items-center gap-2.5">
      <Icon className="h-3.5 w-3.5 text-muted-foreground" /> {label}
    </span>
    {external && <ExternalLink className="h-3 w-3 text-muted-foreground" />}
  </button>
);
