import { useTheme } from "./ThemeProvider";
import { Sun, Moon, Building2 } from "lucide-react";

const options = [
  { value: "light" as const, label: "Light", icon: Sun },
  { value: "dark" as const, label: "Dark", icon: Moon },
  { value: "enterprise" as const, label: "Enterprise", icon: Building2 },
];

export const ThemeSwitcher = () => {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex items-center border border-border rounded-md overflow-hidden">
      {options.map(({ value, label, icon: Icon }) => (
        <button
          key={value}
          onClick={() => setTheme(value)}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors ${
            theme === value
              ? "bg-primary text-primary-foreground"
              : "bg-card text-muted-foreground hover:bg-secondary"
          }`}
        >
          <Icon className="h-3.5 w-3.5" />
          {label}
        </button>
      ))}
    </div>
  );
};
