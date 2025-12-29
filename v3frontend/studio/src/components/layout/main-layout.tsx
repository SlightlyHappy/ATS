"use client";

import { useState } from "react";
import { NavigationSidebar } from "./navigation-sidebar";
import { Header } from "./header";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { useIsMobile } from "@/hooks/use-mobile";

interface MainLayoutProps {
  children: React.ReactNode
  isAdmin?: boolean
}

export default function MainLayout({ children, isAdmin = false }: MainLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isMobile = useIsMobile();

  return (
    <div className="h-screen flex overflow-hidden bg-background">
      {/* Mobile sidebar */}
      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetContent side="left" className="p-0 w-64 lg:hidden">
          <NavigationSidebar isAdmin={isAdmin} />
        </SheetContent>
      </Sheet>

      {/* Desktop sidebar */}
      <NavigationSidebar 
        isAdmin={isAdmin} 
        className="hidden lg:flex lg:flex-shrink-0" 
      />

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header isAdmin={isAdmin} onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-auto">
          <div className="p-4 md:p-6 lg:p-8 max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
