import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { Language, t, TranslationKey } from "@/i18n";

interface LanguageContextValue {
  language: Language;
  toggleLanguage: () => void;
  t: (key: TranslationKey) => string;
}

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

const STORAGE_KEY = "archon-language";

export const LanguageProvider = ({ children }: { children: ReactNode }) => {
  const [language, setLanguage] = useState<Language>(() => {
    const urlLang = new URLSearchParams(window.location.search).get("lang");
    if (urlLang === "ko" || urlLang === "en") {
      localStorage.setItem(STORAGE_KEY, urlLang);
      return urlLang;
    }
    const stored = localStorage.getItem(STORAGE_KEY);
    return (stored === "ko" ? "ko" : "en") as Language;
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, language);
  }, [language]);

  const toggleLanguage = () => setLanguage((prev) => (prev === "en" ? "ko" : "en"));

  const translate = (key: TranslationKey) => t(key, language);

  return (
    <LanguageContext.Provider value={{ language, toggleLanguage, t: translate }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within a LanguageProvider");
  return ctx;
};
