
import type {Metadata} from 'next';
import { Toaster } from "@/components/ui/toaster"
import { Toaster as SonnerToaster } from "sonner"
import './globals.css';
import { Open_Sans, Roboto_Slab, Fira_Code } from 'next/font/google';
import { ThemeProvider } from '@/components/shared/theme-provider';

const openSans = Open_Sans({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-body',
  preload: true,
  fallback: ['system-ui', 'arial'],
});

const robotoSlab = Roboto_Slab({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-headline',
  preload: true,
  fallback: ['Georgia', 'serif'],
});

const firaCode = Fira_Code({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-code',
  preload: false, // Code font is less critical
  fallback: ['Menlo', 'Monaco', 'Consolas', 'monospace'],
});


export const metadata: Metadata = {
  title: 'BearSystemsHRT© - Agentic HR Intelligence Platform',
  description: 'Revolutionary agentic AI-powered HR intelligence platform. Transform recruitment, compliance, and workforce management with autonomous agents designed for Indian organizations.',
  keywords: 'agentic AI, HR intelligence, recruitment automation, compliance management, workforce analytics, Indian labor law',
  authors: [{ name: 'Bear Systems', url: 'https://bearsystems.co.in' }],
  creator: 'Bear Systems',
  publisher: 'Bear Systems',
  robots: 'index, follow',
  openGraph: {
    title: 'BearSystemsHRT© - Agentic HR Intelligence Platform',
    description: 'Revolutionary agentic AI-powered HR intelligence platform for modern organizations.',
    url: 'https://hrt.bearsystems.co.in',
    siteName: 'BearSystemsHRT',
    locale: 'en_IN',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'BearSystemsHRT© - Agentic HR Intelligence',
    description: 'Revolutionary agentic AI-powered HR intelligence platform.',
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Performance optimizations */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
        <link rel="dns-prefetch" href="https://fonts.gstatic.com" />
        
        {/* Viewport and theme optimizations */}
        <meta name="theme-color" content="#3b82f6" media="(prefers-color-scheme: light)" />
        <meta name="theme-color" content="#1e40af" media="(prefers-color-scheme: dark)" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        
        {/* Performance hints */}
        <link rel="prefetch" href="/images/logo/logo_light.png" />
        <link rel="prefetch" href="/images/logo/logo_dark.png" />
      </head>
      <body 
        className={`font-body antialiased ${openSans.variable} ${robotoSlab.variable} ${firaCode.variable}`} 
        suppressHydrationWarning
        style={{ 
          // Prevent layout shifts
          minHeight: '100vh',
          // Enable hardware acceleration
          transform: 'translateZ(0)',
          // Smooth scrolling
          scrollBehavior: 'smooth'
        }}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange={false}
          storageKey="bearsystems-hrt-theme"
        >
          <div style={{ 
            // Create stacking context for better performance
            isolation: 'isolate',
            // Enable hardware acceleration for main content
            willChange: 'contents'
          }}>
            {children}
          </div>
          <Toaster />
          <SonnerToaster richColors position="top-center" />
        </ThemeProvider>
      </body>
    </html>
  );
}
