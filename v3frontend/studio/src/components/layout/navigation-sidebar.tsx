"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  FileText,
  Users,
  Settings,
  Upload,
  UserCircle,
  LogOut,
  Briefcase,
  Activity,
  BarChart3,
  Scale,
  CreditCard,
  Server,
} from "lucide-react";
import type { NavItem } from "@/types";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";

const adminNavItems: NavItem[] = [
  { title: "Dashboard", href: "/admin/dashboard", icon: LayoutDashboard },
  { title: "Resumes", href: "/admin/resumes", icon: FileText },
  { title: "Users", href: "/admin/users", icon: Users },
  { title: "Legal Queries", href: "/admin/legal-queries", icon: Scale },
  { title: "Activity Log", href: "/admin/activity-log", icon: Activity },
  { title: "Usage Stats", href: "/admin/usage-stats", icon: BarChart3 },
  { title: "System Monitoring", href: "/admin/monitoring", icon: Server },
];

const userNavItems: NavItem[] = [
  { title: "Dashboard", href: "/user", icon: LayoutDashboard },
  { title: "My Resumes", href: "/user/my-resumes", icon: FileText },
  // Temporarily hidden: { title: "Billing & Credits", href: "/user/billing", icon: CreditCard },
];

const adminBottomNavItems: NavItem[] = [
  { title: "Settings", href: "/admin/settings", icon: Settings },
];

const userBottomNavItems: NavItem[] = [
  { title: "Profile", href: "/user/profile", icon: UserCircle },
];

interface NavigationSidebarProps {
  isAdmin?: boolean;
  className?: string;
}

export function NavigationSidebar({ isAdmin = false, className }: NavigationSidebarProps) {
  const pathname = usePathname();
  const { logout } = useAuth();
  
  const navItems = isAdmin ? adminNavItems : userNavItems;
  const bottomNavItems = isAdmin ? adminBottomNavItems : userBottomNavItems;
  const submitResumeHref = isAdmin ? "/admin/resumes" : "/user/submit";

  const handleLogout = async () => {
    console.log('🚪 Navigation: User initiated logout...');
    console.log('🔄 Navigation: Current page:', pathname);
    console.log('🔄 Navigation: User type:', isAdmin ? 'admin' : 'user');
    
    try {
      console.log('📤 Navigation: Calling auth context logout...');
      await logout();
      console.log('✅ Navigation: Logout completed successfully');
    } catch (error) {
      console.log('❌ Navigation: Logout failed:', error);
    }
  };

  const handleNavigation = (href: string, title: string) => {
    console.log('🧭 Navigation: User navigating...', {
      from: pathname,
      to: href,
      title: title,
      userType: isAdmin ? 'admin' : 'user',
      timestamp: new Date().toISOString()
    });
  };

  return (
    <div className={cn("flex h-full w-64 flex-col border-r bg-background", className)}>
      {/* Header */}
      <div className="flex h-16 items-center gap-2 border-b px-6">
        <Briefcase className="h-6 w-6 text-primary" />
        <span className="text-lg font-semibold">Bear Systems</span>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        <div className="space-y-2">
          {/* Submit Resume Button (User only) */}
          {!isAdmin && (
            <Link 
              href={submitResumeHref} 
              className="block mb-4"
              onClick={() => handleNavigation(submitResumeHref, 'Submit Resume')}
            >
              <Button className="w-full bg-primary text-primary-foreground hover:bg-primary/90">
                <Upload className="mr-2 h-4 w-4" />
                Submit Resume
              </Button>
            </Link>
          )}

          {/* Main Navigation */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => handleNavigation(item.href, item.title)}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200 hover:bg-accent hover:text-accent-foreground",
                    isActive
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  {item.title}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t p-4">
        <div className="space-y-1">
          {/* Bottom Navigation Items */}
            {bottomNavItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => handleNavigation(item.href, item.title)}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200 hover:bg-accent hover:text-accent-foreground",
                    isActive
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  {item.title}
                </Link>
              );
            })}          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-all duration-200 hover:bg-accent hover:text-accent-foreground"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}
