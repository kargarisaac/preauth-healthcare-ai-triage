import React, { useState } from 'react';
import {
  Layout,
  BarChart3,
  Settings,
  Users,
  FileText,
  Bell,
  Menu,
  X,
  ChevronRight,
  Brain
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { AnalyticsDashboard } from './AnalyticsDashboard';
import { LLMDashboard } from './LLMDashboard';

interface DashboardPageProps {
  className?: string;
}

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  activeSection: string;
  onSectionChange: (section: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onToggle,
  activeSection,
  onSectionChange
}) => {
  const navigationItems = [
    { id: 'analytics', label: 'Analytics', icon: <BarChart3 className="h-5 w-5" /> },
    { id: 'llm-analysis', label: 'LLM Analysis', icon: <Brain className="h-5 w-5" /> },
    { id: 'processing', label: 'Processing', icon: <FileText className="h-5 w-5" /> },
    { id: 'providers', label: 'Providers', icon: <Users className="h-5 w-5" /> },
    { id: 'settings', label: 'Settings', icon: <Settings className="h-5 w-5" /> }
  ];

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed left-0 top-0 h-full w-64 bg-white border-r border-gray-200 z-50 transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:static lg:z-auto
      `}>
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Layout className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900">Nazmito</span>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={onToggle}
            className="lg:hidden"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <nav className="p-4">
          <div className="space-y-2">
            {navigationItems.map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  onSectionChange(item.id);
                  if (window.innerWidth < 1024) {
                    onToggle();
                  }
                }}
                className={`
                  w-full flex items-center justify-between p-3 rounded-lg text-left transition-colors duration-200
                  ${activeSection === item.id
                    ? 'bg-blue-50 text-blue-600 border border-blue-200'
                    : 'text-gray-700 hover:bg-gray-50'
                  }
                `}
              >
                <div className="flex items-center space-x-3">
                  {item.icon}
                  <span className="font-medium">{item.label}</span>
                </div>
                {activeSection === item.id && (
                  <ChevronRight className="h-4 w-4" />
                )}
              </button>
            ))}
          </div>
        </nav>

        {/* Quick Stats */}
        <div className="p-4 border-t border-gray-200 mt-auto">
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">System Status</span>
              <span className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-green-600 font-medium">Healthy</span>
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Active Users</span>
              <span className="font-medium text-gray-900">1,247</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Processing Queue</span>
              <span className="font-medium text-gray-900">23</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

const TopBar: React.FC<{
  onMenuToggle: () => void;
  activeSection: string;
}> = ({ onMenuToggle, activeSection }) => {
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const getSectionTitle = () => {
    switch (activeSection) {
      case 'analytics': return 'Analytics Dashboard';
      case 'llm-analysis': return 'LLM Analysis Dashboard';
      case 'processing': return 'Processing Center';
      case 'providers': return 'Provider Management';
      case 'settings': return 'System Settings';
      default: return 'Dashboard';
    }
  };

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="secondary"
            size="sm"
            onClick={onMenuToggle}
            className="lg:hidden"
          >
            <Menu className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">{getSectionTitle()}</h1>
            <p className="text-sm text-gray-600">UAE Healthcare Pre-Authorization Platform</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="relative">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setNotificationsOpen(!notificationsOpen)}
              className="relative"
            >
              <Bell className="h-4 w-4" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full text-xs flex items-center justify-center text-white">
                3
              </span>
            </Button>

            {notificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                <div className="p-4 border-b border-gray-200">
                  <h3 className="font-medium text-gray-900">Notifications</h3>
                </div>
                <div className="max-h-64 overflow-y-auto">
                  <div className="p-3 border-b border-gray-100 hover:bg-gray-50">
                    <p className="text-sm font-medium text-gray-900">High processing volume detected</p>
                    <p className="text-xs text-gray-600">System is handling 150% of normal volume</p>
                    <p className="text-xs text-gray-500 mt-1">2 minutes ago</p>
                  </div>
                  <div className="p-3 border-b border-gray-100 hover:bg-gray-50">
                    <p className="text-sm font-medium text-gray-900">Quality score improved</p>
                    <p className="text-xs text-gray-600">Data quality increased to 94.2%</p>
                    <p className="text-xs text-gray-500 mt-1">1 hour ago</p>
                  </div>
                  <div className="p-3 hover:bg-gray-50">
                    <p className="text-sm font-medium text-gray-900">Monthly report ready</p>
                    <p className="text-xs text-gray-600">October analytics report is available</p>
                    <p className="text-xs text-gray-500 mt-1">3 hours ago</p>
                  </div>
                </div>
                <div className="p-3 border-t border-gray-100">
                  <Button variant="secondary" size="sm" className="w-full">
                    View All Notifications
                  </Button>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-sm font-medium text-white">AM</span>
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-medium text-gray-900">Admin User</p>
              <p className="text-xs text-gray-600">administrator</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const EmptyState: React.FC<{ section: string }> = ({ section }) => {
  const getEmptyStateContent = () => {
    switch (section) {
      case 'processing':
        return {
          title: 'Processing Center',
          description: 'Real-time monitoring of healthcare data processing workflows',
          action: 'View Processing Queue'
        };
      case 'providers':
        return {
          title: 'Provider Management',
          description: 'Manage healthcare providers, performance metrics, and relationships',
          action: 'Add New Provider'
        };
      case 'settings':
        return {
          title: 'System Settings',
          description: 'Configure system parameters, user permissions, and integrations',
          action: 'Open Settings'
        };
      default:
        return {
          title: 'Coming Soon',
          description: 'This section is under development',
          action: 'Back to Analytics'
        };
    }
  };

  const content = getEmptyStateContent();

  return (
    <div className="flex items-center justify-center min-h-96">
      <Card className="p-8 text-center max-w-md">
        <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
          <BarChart3 className="h-8 w-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">{content.title}</h3>
        <p className="text-gray-600 mb-4">{content.description}</p>
        <Button variant="primary">
          {content.action}
        </Button>
      </Card>
    </div>
  );
};

export const DashboardPage: React.FC<DashboardPageProps> = ({
  className = ''
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('analytics');

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className={`min-h-screen bg-gray-50 ${className}`}>
      <div className="flex">
        {/* Sidebar */}
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={toggleSidebar}
          activeSection={activeSection}
          onSectionChange={setActiveSection}
        />

        {/* Main Content */}
        <div className="flex-1 lg:ml-0">
          {/* Top Bar */}
          <TopBar
            onMenuToggle={toggleSidebar}
            activeSection={activeSection}
          />

          {/* Page Content */}
          <div className="p-6">
            {activeSection === 'analytics' ? (
              <AnalyticsDashboard />
            ) : activeSection === 'llm-analysis' ? (
              <LLMDashboard />
            ) : (
              <EmptyState section={activeSection} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
