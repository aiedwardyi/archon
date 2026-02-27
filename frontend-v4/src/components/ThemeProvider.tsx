import { createContext, useContext, useEffect, useState, ReactNode } from "react";

type ColorMode = "light" | "dark";

interface ThemeContextType {
  colorMode: ColorMode;
  setColorMode: (mode: ColorMode) => void;
  // Legacy compat
  theme: string;
  setTheme: (t: string) => void;
}

const ThemeContext = createContext<ThemeContextType>({
  colorMode: "light",
  setColorMode: () => {},
  theme: "light",
  setTheme: () => {},
});

export const useTheme = () => useContext(ThemeContext);

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const [colorMode, setColorMode] = useState<ColorMode>(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem("app-color-mode") as ColorMode) || "light";
    }
    return "light";
  });

  useEffect(() => {
    const root = document.documentElement;
    localStorage.setItem("app-color-mode", colorMode);

    root.classList.remove("dark");
    root.removeAttribute("data-theme");

    if (colorMode === "dark") {
      root.classList.add("dark");
    }
  }, [colorMode]);

  return (
    <ThemeContext.Provider value={{
      colorMode,
      setColorMode,
      theme: colorMode,
      setTheme: (t) => setColorMode(t as ColorMode),
    }}>
      {children}
    </ThemeContext.Provider>
  );
};
