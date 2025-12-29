import React from 'react';
import { 
  Upload, 
  BarChart3, 
  Settings, 
  FileText, 
  Mail, 
  Scale, 
  Terminal
} from 'lucide-react';
import clsx from 'clsx';

const navigationItems = [
  {
    id: 'upload',
    label: 'Upload Resumes',
    icon: Upload,
    description: 'Upload and process resume files'
  },
  {
    id: 'dashboard',
    label: 'Analytics Dashboard',
    icon: BarChart3,
    description: 'View analysis results and metrics'
  },
  {
    id: 'requirements',
    label: 'Role Requirements',
    icon: FileText,
    description: 'Define job requirements and criteria'
  },
  {
    id: 'ai-settings',
    label: 'AI Configuration',
    icon: Settings,
    description: 'Configure AI models and settings'
  },
  {
    id: 'email',
    label: 'Email Manager',
    icon: Mail,
    description: 'Manage candidate communications'
  },
  {
    id: 'hr-legal',
    label: 'HR Legal Assistant',
    icon: Scale,
    description: 'Legal compliance and guidance'
  },
  {
    id: 'debug',
    label: 'System Diagnostics',
    icon: Terminal,
    description: 'Debug console and system logs'
  }
];

const Sidebar = ({ activeTab, setActiveTab, isOpen, resumes, setSidebarOpen }) => {
  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div 
          className="sidebar-overlay visible"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      <nav className={clsx('sidebar', { 'open': isOpen })}>
        <div className="sidebar-content">
          <div className="mb-8">
            <div className="text-xs font-semibold text-tertiary uppercase tracking-wide mb-4">Main Features</div>
            <div className="space-y-1">
              {navigationItems.slice(0, 4).map((item) => {
                const Icon = item.icon;
                const count = item.id === 'dashboard' ? (resumes?.length || 0) : null;
                
                return (
                  <button
                    key={item.id}
                    className={clsx('nav-item', { 'active': activeTab === item.id })}
                    onClick={() => {
                      setActiveTab(item.id);
                      // Close sidebar on mobile after selection
                      if (window.innerWidth <= 768) {
                        setSidebarOpen(false);
                      }
                    }}
                  >
                    <Icon size={18} />
                    <span className="flex-1 text-left">
                      <div className="font-medium">
                        {item.label}
                        {count !== null && (
                          <span className="ml-2 px-2 py-1 bg-primary-light text-primary text-xs rounded-full font-medium">
                            {count}
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-tertiary mt-1">{item.description}</div>
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="mb-8">
            <div className="text-xs font-semibold text-tertiary uppercase tracking-wide mb-4">Advanced Tools</div>
            <div className="space-y-1">
              {navigationItems.slice(4).map((item) => {
                const Icon = item.icon;
                
                return (
                  <button
                    key={item.id}
                    className={clsx('nav-item', { 'active': activeTab === item.id })}
                    onClick={() => {
                      setActiveTab(item.id);
                      // Close sidebar on mobile after selection
                      if (window.innerWidth <= 768) {
                        setSidebarOpen(false);
                      }
                    }}
                  >
                    <Icon size={18} />
                    <span className="flex-1 text-left">
                      <div className="font-medium">{item.label}</div>
                      <div className="text-xs text-tertiary mt-1">{item.description}</div>
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </nav>
    </>
  );
};

export default Sidebar;
