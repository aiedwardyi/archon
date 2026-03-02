"use client";
import { GoogleOAuthProvider } from "@react-oauth/google";

const GOOGLE_CLIENT_ID =
  "1094133324705-0dgm6o9cu0oud74l0im9l4ncsvlvknka.apps.googleusercontent.com";

export function GoogleOAuthWrapper({ children }: { children: React.ReactNode }) {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      {children}
    </GoogleOAuthProvider>
  );
}
