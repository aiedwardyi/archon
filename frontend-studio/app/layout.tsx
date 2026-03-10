import type { Metadata, Viewport } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import { IBM_Plex_Sans } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import { ThemeProvider } from '@/components/theme-provider'
import { LanguageProvider } from '@/contexts/LanguageContext'
import { AuthGuard } from '@/components/auth-guard'
import { GoogleOAuthWrapper } from '@/components/google-oauth-provider'
import { AppShell } from '@/components/app-shell'
import './globals.css'

const geistSans = Geist({ subsets: ["latin"] });
const geistMono = Geist_Mono({ subsets: ["latin"] });
const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-ibm-plex-sans",
});

export const metadata: Metadata = {
  title: 'Archon - Studio Build',
  description: 'Enterprise AI code generation with multi-agent pipelines, version control, and full audit trails.',
  icons: {
    icon: '/favicon.svg',
  },
}

export const viewport: Viewport = {
  themeColor: '#ffffff',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${ibmPlexSans.className} ${ibmPlexSans.variable} ${geistMono.variable} font-sans antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem={false}
          disableTransitionOnChange
        >
          <GoogleOAuthWrapper>
            <LanguageProvider>
              <AppShell>
                <AuthGuard>{children}</AuthGuard>
              </AppShell>
            </LanguageProvider>
          </GoogleOAuthWrapper>
        </ThemeProvider>
        <Analytics />
      </body>
    </html>
  )
}
