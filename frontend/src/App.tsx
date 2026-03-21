import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { ThemeProvider } from "@/components/ThemeProvider";
import { LanguageProvider } from "@/contexts/LanguageContext";
import { useEffect, useState } from "react";
import Index from "./pages/Index";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import NotFound from "./pages/NotFound";
import Demo from "./pages/Demo";
import TokenHandler from "./TokenHandler";
import { DEMO_MODE } from "@/demo/demoMode";

const queryClient = new QueryClient();
const PUBLIC_PATHS = ["/login", "/register", "/forgot-password", "/demo"];

function AuthGuard({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [verified, setVerified] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const isPublicPath = PUBLIC_PATHS.includes(window.location.pathname);
    if (isPublicPath) {
      setVerified(true);
      setChecking(false);
      return;
    }

    const token = localStorage.getItem("archon_token");
    if (!token) {
      setChecking(false);
      return;
    }

    fetch("http://localhost:5000/api/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Token validation failed");
        }
        setVerified(true);
      })
      .catch(() => {
        localStorage.removeItem("archon_token");
        localStorage.removeItem("archon_user");
      })
      .finally(() => {
        setChecking(false);
      });
  }, []);

  if (PUBLIC_PATHS.includes(location.pathname)) {
    return <>{children}</>;
  }

  if (checking) {
    return null;
  }

  if (!verified) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

const GOOGLE_CLIENT_ID =
  "975672204403-a1tbslh4raerh7tlrdgepr19qlnvvlmk.apps.googleusercontent.com";

const AppShell = (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <LanguageProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            {DEMO_MODE ? (
              <Routes>
                <Route path="/" element={<Demo />} />
                <Route path="/projects" element={<Index />} />
                <Route path="/pipeline" element={<Index />} />
                <Route path="/versions" element={<Index />} />
                <Route path="/artifacts" element={<Index />} />
                <Route path="/demo" element={<Demo />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            ) : (
              <>
                <TokenHandler />
                <AuthGuard>
                  <Routes>
                    <Route path="/" element={<Index />} />
                    <Route path="/projects" element={<Index />} />
                    <Route path="/pipeline" element={<Index />} />
                    <Route path="/versions" element={<Index />} />
                    <Route path="/artifacts" element={<Index />} />
                    <Route path="/demo" element={<Demo />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    <Route path="/forgot-password" element={<ForgotPassword />} />
                    <Route path="*" element={<NotFound />} />
                  </Routes>
                </AuthGuard>
              </>
            )}
          </BrowserRouter>
        </TooltipProvider>
      </LanguageProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

const App = () =>
  DEMO_MODE ? (
    AppShell
  ) : (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>{AppShell}</GoogleOAuthProvider>
  );

export default App;
