'use client';
import * as React from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Briefcase,
  ChevronDown,
  Cog,
  FileText,
  Gavel,
  Gift,
  LayoutDashboard,
  LogOut,
  Shield,
} from 'lucide-react';
import {
  SidebarProvider,
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarTrigger,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuSub,
  SidebarMenuSubItem,
  SidebarMenuSubButton,
  useSidebar,
} from '@/components/ui/sidebar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Icons } from '@/components/icons';
import { cn } from '@/lib/utils';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { useToast } from '@/hooks/use-toast';

const UserNav = () => {
    const router = useRouter();
    const { toast } = useToast();

    const handleLogout = async () => {
        const token = localStorage.getItem('auth_token') || localStorage.getItem('admin_auth_token');
        
        try {
            const response = await fetch('https://hrtoolsbackend-production.up.railway.app/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Logout failed');
            }

        } catch (error: any) {
            console.error("Logout failed:", error.message);
            // Even if API fails, we log out the user from the frontend
        } finally {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('admin_auth_token');
            toast({
              title: "Logged Out",
              description: "You have been successfully logged out.",
            });
            router.push('/login');
        }
    };

    return (
        <DropdownMenu>
        <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-10 w-10 rounded-full">
            <Avatar className="h-10 w-10">
                <AvatarImage src="https://placehold.co/100x100" alt="@user" />
                <AvatarFallback>JD</AvatarFallback>
            </Avatar>
            </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-56" align="end" forceMount>
            <DropdownMenuLabel className="font-normal">
            <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">John Doe</p>
                <p className="text-xs leading-none text-muted-foreground">
                john.doe@example.com
                </p>
            </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
                <Cog className="mr-2 h-4 w-4" />
                <span>Settings</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
            </DropdownMenuItem>
        </DropdownMenuContent>
        </DropdownMenu>
    );
}

const AdminMenu = () => {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = React.useState(pathname.startsWith('/admin'));

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger asChild>
        <SidebarMenuButton className="justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4"/>
            <span>Admin</span>
          </div>
          <ChevronDown className={cn("h-4 w-4 transition-transform", isOpen && "rotate-180")} />
        </SidebarMenuButton>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <SidebarMenuSub>
            <SidebarMenuSubItem>
                <SidebarMenuSubButton asChild isActive={pathname === '/admin'}>
                  <Link href="/admin">Overview</Link>
                </SidebarMenuSubButton>
            </SidebarMenuSubItem>
            <SidebarMenuSubItem>
                <SidebarMenuSubButton asChild isActive={pathname === '/admin/users'}>
                  <Link href="/admin/users">Users</Link>
                </SidebarMenuSubButton>
            </SidebarMenuSubItem>
             <SidebarMenuSubItem>
                <SidebarMenuSubButton asChild isActive={pathname === '/admin/system-health'}>
                  <Link href="/admin/system-health">Health</Link>
                </SidebarMenuSubButton>
            </SidebarMenuSubItem>
             <SidebarMenuSubItem>
                <SidebarMenuSubButton asChild isActive={pathname === '/admin/sales-intelligence'}>
                  <Link href="/admin/sales-intelligence">Sales</Link>
                </SidebarMenuSubButton>
            </SidebarMenuSubItem>
            <SidebarMenuSubItem>
                <SidebarMenuSubButton asChild isActive={pathname === '/admin/resumes'}>
                  <Link href="/admin/resumes">Resumes</Link>
                </SidebarMenuSubButton>
            </SidebarMenuSubItem>
            <SidebarMenuSubItem>
                <SidebarMenuSubButton asChild isActive={pathname === '/admin/hr-legal-testing'}>
                  <Link href="/admin/hr-legal-testing">RAG Testing</Link>
                </SidebarMenuSubButton>
            </SidebarMenuSubItem>
        </SidebarMenuSub>
      </CollapsibleContent>
    </Collapsible>
  );
};

function DashboardLayoutContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { isMobile } = useSidebar();
  
  return (
    <>
      <Sidebar>
          <SidebarHeader>
              <div className="flex items-center gap-2">
                  <Icons.logo className="w-8 h-8 text-secondary" />
                  <span className="text-lg font-semibold text-primary-foreground">HR Intel Pro</span>
              </div>
          </SidebarHeader>
          <SidebarContent>
              <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={pathname === '/dashboard'}>
                        <Link href="/dashboard">
                            <LayoutDashboard />
                            <span>Dashboard</span>
                        </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={pathname === '/resume-analysis'}>
                        <Link href="/resume-analysis">
                            <FileText />
                            <span>Resume Analysis</span>
                        </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={pathname === '/resume-database'}>
                        <Link href="/resume-database">
                            <Briefcase />
                            <span>Resume Database</span>
                        </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={pathname === '/hr-legal'}>
                        <Link href="/hr-legal">
                            <Gavel />
                            <span>HR Legal</span>
                        </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={pathname === '/credits'}>
                        <Link href="/credits">
                            <Gift />
                            <span>Credits</span>
                        </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <AdminMenu />
                  </SidebarMenuItem>
              </SidebarMenu>
          </SidebarContent>
          <SidebarFooter>
              {/* Footer content if any */}
          </SidebarFooter>
      </Sidebar>

      <div className={cn("flex flex-col h-full w-full", (isMobile) ? "" : "md:pl-[16rem]")}>
          <header className="flex h-14 items-center gap-4 border-b bg-card px-4 lg:h-[60px] lg:px-6 sticky top-0 z-30">
              <SidebarTrigger className={cn("md:hidden", isMobile && "hidden")} />
              <div className="flex-1">
                  {/* Optional Header Title */}
              </div>
              <UserNav />
          </header>
          <main className="flex-1 p-4 sm:p-6 bg-background">
            {children}
          </main>
      </div>
    </>
  );
}


export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <DashboardLayoutContent>{children}</DashboardLayoutContent>
    </SidebarProvider>
  );
}
