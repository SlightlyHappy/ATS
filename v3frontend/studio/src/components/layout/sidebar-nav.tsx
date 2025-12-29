
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarFooter,
  SidebarContent,
} from "@/components/ui/sidebar";
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
} from "lucide-react";
import type { NavItem } from "@/types";
import { useAuth } from "@/contexts/AuthContext";

const adminNavItems: NavItem[] = [
  { title: "Dashboard", href: "/admin/dashboard", icon: LayoutDashboard },
  { title: "Resumes", href: "/admin/resumes", icon: FileText },
  { title: "Users", href: "/admin/users", icon: Users },
  { title: "Legal Queries", href: "/admin/legal-queries", icon: Scale },
  { title: "Activity Log", href: "/admin/activity-log", icon: Activity },
  { title: "Usage Stats", href: "/admin/usage-stats", icon: BarChart3 },
];

const userNavItems: NavItem[] = [
  { title: "Dashboard", href: "/user", icon: LayoutDashboard },
  { title: "My Resumes", href: "/user/my-resumes", icon: FileText },
];

const adminBottomNavItems: NavItem[] = [
  { title: "Settings", href: "/admin/settings", icon: Settings },
];

const userBottomNavItems: NavItem[] = [
  { title: "Profile", href: "/user/profile", icon: UserCircle },
];

interface SidebarNavProps {
  isAdmin?: boolean
}

export function SidebarNav({ isAdmin = false }: SidebarNavProps) {
  const pathname = usePathname();
  const { logout } = useAuth();
  
  const navItems = isAdmin ? adminNavItems : userNavItems;
  const bottomNavItems = isAdmin ? adminBottomNavItems : userBottomNavItems;
  const submitResumeHref = isAdmin ? "/admin/resumes" : "/user/submit";

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  return (
    <>
      <SidebarHeader>
        <div className="flex items-center gap-2">
          <Briefcase className="h-6 w-6 text-primary" />
          <span className="text-lg font-semibold">Bear Systems</span>
        </div>
      </SidebarHeader>
      <SidebarContent className="p-2">
        <SidebarMenu>
          {!isAdmin && (
            <Link href={submitResumeHref}>
              <SidebarMenuButton className="w-full bg-primary text-primary-foreground hover:bg-primary/90">
                <Upload className="mr-2 h-4 w-4" />
                <span>Submit Resume</span>
              </SidebarMenuButton>
            </Link>
          )}
        </SidebarMenu>
        <SidebarMenu>
          {navItems.map((item) => (
            <SidebarMenuItem key={item.href}>
              <Link href={item.href}>
                <SidebarMenuButton
                  isActive={pathname === item.href}
                  tooltip={{ children: item.title }}
                >
                  <item.icon />
                  <span>{item.title}</span>
                </SidebarMenuButton>
              </Link>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          {bottomNavItems.map((item) => (
            <SidebarMenuItem key={item.href}>
              <Link href={item.href}>
                <SidebarMenuButton
                  isActive={pathname === item.href}
                  tooltip={{ children: item.title }}
                >
                  <item.icon />
                  <span>{item.title}</span>
                </SidebarMenuButton>
              </Link>
            </SidebarMenuItem>
          ))}
          <SidebarMenuItem>
            <SidebarMenuButton 
              onClick={handleLogout}
              tooltip={{ children: "Logout" }}
            >
              <LogOut />
              <span>Logout</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </>
  );
}
