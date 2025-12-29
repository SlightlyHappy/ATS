import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import RootProvider from "@/components/layout/root-provider";
import { GlobalErrorBoundary } from "@/components/error-boundary/global-error-boundary";

export const metadata: Metadata = {
  title: "Bear Systems - HRT",
  description: "AI-Powered Hiring and Resume Tracking",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-body antialiased" suppressHydrationWarning>
        <GlobalErrorBoundary>
          <RootProvider>{children}</RootProvider>
          <Toaster />
        </GlobalErrorBoundary>
      </body>
    </html>
  );
}
