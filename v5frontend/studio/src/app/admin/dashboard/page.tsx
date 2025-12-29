'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AppLogo } from '@/components/shared/app-logo';
import { Button } from '@/components/ui/button';
import { 
  Users, 
  Database, 
  Activity, 
  Settings, 
  LogOut, 
  Shield, 
  FileText, 
  BarChart3, 
  Monitor, 
  UserCheck,
  ChevronDown,
  ChevronRight,
  Home,
  Search,
  Bell,
  User
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ThemeToggle } from '@/components/shared/theme-toggle';
import { toast } from 'sonner';

// Import admin components (we'll create these)
import UsersManagement from '@/components/admin/users-management';
import DatabaseView from '@/components/admin/database-view';
import SystemLogs from '@/components/admin/system-logs';
import HealthReports from '@/components/admin/health-reports';
import DashboardOverview from '@/components/admin/dashboard-overview';
import RecruiterAccounts from '@/components/admin/recruiter-accounts';
import CandidateOversight from '@/components/admin/candidate-oversight';
import BusinessAnalytics from '@/components/admin/business-analytics';
import SystemAdmin from '@/components/admin/system-admin';

interface SidebarItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  component?: React.ComponentType;
  children?: SidebarItem[];
  collapsed?: boolean;
}

const sidebarItems: SidebarItem[] = [
  {
    id: 'overview',
    label: 'Dashboard Overview',
    icon: <Home className="h-4 w-4" />,
    component: DashboardOverview
  },
  {
    id: 'users',
    label: 'User Management',
    icon: <Users className="h-4 w-4" />,
    component: UsersManagement
  },
  {
    id: 'recruiters',
    label: 'Recruiter Accounts',
    icon: <UserCheck className="h-4 w-4" />,
    component: RecruiterAccounts
  },
  {
    id: 'candidates',
    label: 'Candidate Oversight',
    icon: <Shield className="h-4 w-4" />,
    component: CandidateOversight
  },
  {
    id: 'database',
    label: 'Database Management',
    icon: <Database className="h-4 w-4" />,
    collapsed: true,
    children: [
      {
        id: 'db-overview',
        label: 'Database Overview',
        icon: <BarChart3 className="h-4 w-4" />,
        component: DatabaseView
      },
      {
        id: 'db-migrations',
        label: 'Migrations',
        icon: <FileText className="h-4 w-4" />,
        component: DatabaseView
      },
      {
        id: 'db-backups',
        label: 'Backups',
        icon: <Shield className="h-4 w-4" />,
        component: DatabaseView
      },
      {
        id: 'db-sql',
        label: 'Raw SQL Console',
        icon: <Monitor className="h-4 w-4" />,
        component: DatabaseView
      }
    ]
  },
  {
    id: 'analytics',
    label: 'Business Analytics',
    icon: <BarChart3 className="h-4 w-4" />,
    component: BusinessAnalytics
  },
  {
    id: 'system',
    label: 'System Administration',
    icon: <Settings className="h-4 w-4" />,
    collapsed: true,
    children: [
      {
        id: 'sys-logs',
        label: 'System Logs',
        icon: <FileText className="h-4 w-4" />,
        component: SystemLogs
      },
      {
        id: 'sys-health',
        label: 'Health Reports',
        icon: <Activity className="h-4 w-4" />,
        component: HealthReports
      },
      {
        id: 'sys-admin',
        label: 'System Settings',
        icon: <Monitor className="h-4 w-4" />,
        component: SystemAdmin
      }
    ]
  }
];

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [userInfo, setUserInfo] = useState<any>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [expandedItems, setExpandedItems] = useState<string[]>([]);
  const router = useRouter();

  useEffect(() => {
    // Add a small delay to allow for token to be set during login
    const checkAuth = () => {
      const token = localStorage.getItem('auth_token');

      if (!token) {
        toast.error('Please login to access the admin panel.');
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
      setUserInfo({ email: 'admin', role: 'admin' });
    };

    // Small delay to allow for navigation/token setting
    const timeoutId = setTimeout(checkAuth, 100);
    return () => clearTimeout(timeoutId);
  }, [router]);

  const handleLogout = () => {
    // Updated for v1.76 - only remove auth_token (no refresh_token, user_info, or token_expires)
    localStorage.removeItem('auth_token');
    toast.success('Logged out successfully');
    router.push('/admin/login');
  };

  const toggleSidebarItem = (itemId: string) => {
    setExpandedItems(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const handleItemClick = (item: SidebarItem) => {
    if (item.children) {
      toggleSidebarItem(item.id);
    } else {
      setActiveTab(item.id);
    }
  };

  const findActiveComponent = (items: SidebarItem[]): React.ComponentType | null => {
    for (const item of items) {
      if (item.id === activeTab && item.component) {
        return item.component;
      }
      if (item.children) {
        const found = findActiveComponent(item.children);
        if (found) return found;
      }
    }
    return null;
  };

  const ActiveComponent = findActiveComponent(sidebarItems);

  const renderSidebarItem = (item: SidebarItem, depth = 0) => {
    const isExpanded = expandedItems.includes(item.id);
    const isActive = activeTab === item.id;
    
    return (
      <div key={item.id}>
        <button
          onClick={() => handleItemClick(item)}
          className={cn(
            "w-full flex items-center justify-between px-3 py-2 text-left text-sm transition-colors rounded-md",
            depth > 0 && "ml-4 pl-6",
            isActive 
              ? "bg-primary text-primary-foreground" 
              : "text-muted-foreground hover:text-foreground hover:bg-accent"
          )}
        >
          <div className="flex items-center space-x-2">
            {item.icon}
            <span>{item.label}</span>
          </div>
          {item.children && (
            isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />
          )}
        </button>
        
        {item.children && isExpanded && (
          <div className="mt-1 space-y-1">
            {item.children.map(child => renderSidebarItem(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

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
        sidebarCollapsed ? "w-16" : "w-64"
      )}>
        {/* Sidebar Header */}
        <div className="p-4 border-b">
          <div className="flex items-center space-x-3">
            <AppLogo />
            {!sidebarCollapsed && (
              <div>
                <h2 className="font-bold font-headline text-sm">Admin Panel</h2>
                <p className="text-xs text-muted-foreground">Bear Systems HRT</p>
              </div>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {sidebarItems.map(item => renderSidebarItem(item))}
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
              <Settings className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-lg font-semibold">
                {sidebarItems.find(item => {
                  if (item.id === activeTab) return true;
                  return item.children?.some(child => child.id === activeTab);
                })?.label || 'Dashboard'}
              </h1>
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
          {ActiveComponent ? <ActiveComponent /> : <DashboardOverview />}
        </main>
      </div>
    </div>
  );
}
