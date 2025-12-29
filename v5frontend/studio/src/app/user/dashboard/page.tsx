'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AppLogo } from '@/components/shared/app-logo';
import { Button } from '@/components/ui/button';
import { 
  Upload, 
  MessageSquare, 
  BarChart3, 
  LogOut, 
  Home,
  Search,
  Bell,
  User,
  FileText,
  Users,
  TrendingUp
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ThemeToggle } from '@/components/shared/theme-toggle';
import { toast } from 'sonner';

// Import user components (we'll create these)
import ResumeUpload from '@/components/user/resume-upload';
import CandidateFinderChat from '@/components/user/candidate-finder-chat';
import UploadedResumeDashboard from '@/components/user/uploaded-resume-dashboard';

interface SidebarItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  component: React.ComponentType;
  description: string;
}

const sidebarItems: SidebarItem[] = [
  {
    id: 'upload',
    label: 'Resume Upload',
    icon: <Upload className="h-4 w-4" />,
    component: ResumeUpload,
    description: 'Upload single resumes or ZIP files for batch processing'
  },
  {
    id: 'finder',
    label: 'Candidate Finder Chat',
    icon: <MessageSquare className="h-4 w-4" />,
    component: CandidateFinderChat,
    description: 'AI-powered candidate search and comparison'
  },
  {
    id: 'dashboard',
    label: 'Uploaded Resumes',
    icon: <BarChart3 className="h-4 w-4" />,
    component: UploadedResumeDashboard,
    description: 'View and analyze your uploaded candidate resumes'
  }
];

export default function UserDashboard() {
  const [activeTab, setActiveTab] = useState('upload');
  const [userInfo, setUserInfo] = useState<any>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const router = useRouter();

  useEffect(() => {
    // Check authentication - Updated for v1.76 (basic token presence check)
    const token = localStorage.getItem('auth_token');

    if (!token) {
      toast.error('Please login to access your dashboard.');
      router.push('/admin/login');
      return;
    }

    // Basic token format validation (JWT should have 3 parts)
    if (token.split('.').length !== 3) {
      toast.error('Invalid token format. Please login again.');
      localStorage.removeItem('auth_token');
      router.push('/admin/login');
      return;
    }

    // Set basic user info for UI (actual validation will happen on API calls)
    setUserInfo({ email: 'user', role: 'user' });
  }, [router]);

  const handleLogout = () => {
    // Updated for v1.76 - only remove auth_token (no refresh_token, user_info, or token_expires)
    localStorage.removeItem('auth_token');
    toast.success('Logged out successfully');
    router.push('/admin/login');
  };

  const ActiveComponent = sidebarItems.find(item => item.id === activeTab)?.component || ResumeUpload;

  if (!userInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent mx-auto mb-4" />
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-background">
      {/* Sidebar */}
      <div className={cn(
        "flex flex-col border-r bg-card transition-all duration-300",
        sidebarCollapsed ? "w-16" : "w-80"
      )}>
        {/* Sidebar Header */}
        <div className="p-4 border-b">
          <div className="flex items-center space-x-3">
            <AppLogo />
            {!sidebarCollapsed && (
              <div>
                <h2 className="font-bold font-headline text-sm">User Dashboard</h2>
                <p className="text-xs text-muted-foreground">HR Resume Analysis</p>
              </div>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {sidebarItems.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={cn(
                "w-full flex items-start space-x-3 px-3 py-3 text-left text-sm transition-colors rounded-lg border",
                activeTab === item.id 
                  ? "bg-primary text-primary-foreground border-primary" 
                  : "text-muted-foreground hover:text-foreground hover:bg-accent border-transparent"
              )}
            >
              <div className="flex-shrink-0 mt-0.5">
                {item.icon}
              </div>
              {!sidebarCollapsed && (
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{item.label}</div>
                  <div className="text-xs opacity-70 mt-1 leading-relaxed">
                    {item.description}
                  </div>
                </div>
              )}
            </button>
          ))}
        </nav>

        {/* Sidebar Footer */}
        <div className="p-4 border-t">
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
              <User className="h-4 w-4 text-primary-foreground" />
            </div>
            {!sidebarCollapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{userInfo.username}</p>
                <p className="text-xs text-muted-foreground capitalize">{userInfo.role}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="h-16 border-b bg-card px-6 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            >
              <FileText className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-lg font-semibold">
                {sidebarItems.find(item => item.id === activeTab)?.label || 'Dashboard'}
              </h1>
              <p className="text-sm text-muted-foreground">
                {sidebarItems.find(item => item.id === activeTab)?.description}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="sm">
              <Search className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm">
              <Bell className="h-4 w-4" />
            </Button>
            <ThemeToggle />
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
              <span className="ml-2 hidden sm:inline">Logout</span>
            </Button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6 overflow-y-auto">
          <ActiveComponent />
        </main>
      </div>
    </div>
  );
}
