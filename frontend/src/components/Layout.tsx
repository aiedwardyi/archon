import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Box, LayoutDashboard, GitBranch, FileCode, ChevronRight, Sun, Moon } from 'lucide-react';

const navItems = [
  { path: '/', label: 'Projects', icon: LayoutDashboard },
  { path: '/pipeline', label: 'Pipeline', icon: Box },
  { path: '/versions', label: 'Versions', icon: GitBranch },
  { path: '/artifacts', label: 'Artifacts', icon: FileCode },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'));

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [dark]);

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 border-b border-border bg-card">
        <div className="flex h-12 items-center px-5">
          <Link to="/" className="flex items-center gap-2 mr-8">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-primary">
              <Box className="h-3.5 w-3.5 text-primary-foreground" />
            </div>
            <span className="text-xs font-semibold tracking-tight text-foreground">Archon</span>
          </Link>

          <nav className="flex items-center gap-0.5">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-secondary text-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
                  }`}
                >
                  <item.icon className="h-3 w-3" />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <span className="text-[11px] text-muted-foreground">checkout-service</span>
            <ChevronRight className="h-2.5 w-2.5 text-muted-foreground" />
            <span className="text-[11px] font-medium text-foreground">v14</span>
            <button
              onClick={() => setDark(!dark)}
              className="ml-1.5 rounded p-1 text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
              title="Toggle dark mode"
            >
              {dark ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
            </button>
            <div className="h-6 w-6 rounded-full bg-secondary flex items-center justify-center text-[10px] font-medium text-foreground">
              JD
            </div>
          </div>
        </div>
      </header>

      <main>{children}</main>
    </div>
  );
}
