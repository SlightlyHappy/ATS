import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "HR ATS by BearSystems - AI-Powered Resume Screening for Indian Businesses",
  description: "Transform your HR operations with our 4-agent AI system. Save 90% on screening costs, find better candidates 10x faster. Built specifically for Indian hiring laws and market.",
  keywords: "HR ATS, AI resume screening, Indian hiring, bias-free hiring, HR automation, talent acquisition, BearSystems",
  authors: [{ name: "BearSystems" }],
  openGraph: {
    title: "HR ATS by BearSystems - AI-Powered Hiring Revolution",
    description: "Turn ₹5,00,000 HR costs into ₹50,000 AI magic. 95% faster screening, 60% better hire quality.",
    url: "https://hrtool-sable.vercel.app",
    siteName: "HR ATS by BearSystems",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "HR ATS by BearSystems - AI-Powered Hiring Revolution",
    description: "Transform your HR operations with 4-agent AI system. Built for Indian market.",
  },
  robots: {
    index: true,
    follow: true,
  },
  verification: {
    google: "your-google-verification-code",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#2563eb" />
      </head>
      <body className={inter.className}>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
