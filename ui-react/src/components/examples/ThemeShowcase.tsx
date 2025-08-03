import React from 'react';
import { 
  Sun, 
  Moon, 
  Star, 
  Heart, 
  Shield, 
  CheckCircle, 
  AlertTriangle, 
  XCircle,
  Info,
  Activity,
  TrendingUp,
  Users,
  FileText
} from 'lucide-react';
import { useTheme, useThemeClasses, useHealthcareTheme } from '@/contexts/ThemeContext';
import Card from '@components/ui/Card';
import Button from '@components/ui/Button';
import ThemeToggle from '@components/ui/ThemeToggle';

export default function ThemeShowcase() {
  const { theme, actualTheme, systemTheme, isSystemTheme } = useTheme();
  const themeClasses = useThemeClasses();
  const healthcareTheme = useHealthcareTheme();

  const statusItems = [
    { 
      label: 'Approved Claims', 
      value: '1,247', 
      icon: CheckCircle, 
      status: 'approved',
      change: '+12%'
    },
    { 
      label: 'Pending Reviews', 
      value: '89', 
      icon: AlertTriangle, 
      status: 'pending',
      change: '-5%'
    },
    { 
      label: 'Denied Claims', 
      value: '23', 
      icon: XCircle, 
      status: 'denied',
      change: '-8%'
    },
    { 
      label: 'Processing', 
      value: '156', 
      icon: Activity, 
      status: 'processing',
      change: '+3%'
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return healthcareTheme.approved;
      case 'pending': return healthcareTheme.pending;
      case 'denied': return healthcareTheme.denied;
      case 'processing': return healthcareTheme.processing;
      default: return healthcareTheme.primary;
    }
  };

  return (
    <div className={`min-h-screen p-8 ${themeClasses.bg} transition-colors duration-200`}>
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-4xl font-bold ${themeClasses.textPrimary}`}>
              Theme System Showcase
            </h1>
            <p className={`text-lg ${themeClasses.textSecondary} mt-2`}>
              Comprehensive dark/light theme system for healthcare applications
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <ThemeToggle variant="dropdown" />
          </div>
        </div>

        {/* Theme Status */}
        <Card title="Current Theme Configuration" className="mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="space-y-2">
              <div className={`text-sm font-medium ${themeClasses.textSecondary}`}>
                Theme Preference
              </div>
              <div className={`text-lg font-semibold ${themeClasses.textPrimary} capitalize`}>
                {theme}
              </div>
            </div>
            <div className="space-y-2">
              <div className={`text-sm font-medium ${themeClasses.textSecondary}`}>
                Active Theme
              </div>
              <div className={`text-lg font-semibold ${themeClasses.textPrimary} capitalize flex items-center gap-2`}>
                {actualTheme}
                {actualTheme === 'dark' ? (
                  <Moon className="w-4 h-4" />
                ) : (
                  <Sun className="w-4 h-4" />
                )}
              </div>
            </div>
            <div className="space-y-2">
              <div className={`text-sm font-medium ${themeClasses.textSecondary}`}>
                System Theme
              </div>
              <div className={`text-lg font-semibold ${themeClasses.textPrimary} capitalize`}>
                {systemTheme}
              </div>
            </div>
            <div className="space-y-2">
              <div className={`text-sm font-medium ${themeClasses.textSecondary}`}>
                Using System
              </div>
              <div className={`text-lg font-semibold ${themeClasses.textPrimary}`}>
                {isSystemTheme ? 'Yes' : 'No'}
              </div>
            </div>
          </div>
        </Card>

        {/* Healthcare Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {statusItems.map((item) => {
            const Icon = item.icon;
            const statusColor = getStatusColor(item.status);
            
            return (
              <div
                key={item.label}
                className={`${themeClasses.cardBg} rounded-xl p-6 ${themeClasses.border} shadow-soft hover:shadow-medium transition-all duration-200`}
              >
                <div className="flex items-center justify-between mb-4">
                  <div
                    className="p-3 rounded-lg"
                    style={{ backgroundColor: `${statusColor}20` }}
                  >
                    <Icon 
                      className="w-6 h-6" 
                      style={{ color: statusColor }}
                    />
                  </div>
                  <div 
                    className={`text-sm font-medium px-2 py-1 rounded-full`}
                    style={{ 
                      backgroundColor: `${statusColor}20`,
                      color: statusColor
                    }}
                  >
                    {item.change}
                  </div>
                </div>
                
                <div className={`text-2xl font-bold ${themeClasses.textPrimary} mb-1`}>
                  {item.value}
                </div>
                
                <div className={`text-sm ${themeClasses.textSecondary}`}>
                  {item.label}
                </div>
              </div>
            );
          })}
        </div>

        {/* Button Variants Showcase */}
        <Card title="Button Variants" subtitle="All button styles in current theme">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="space-y-4">
              <h4 className={`font-medium ${themeClasses.textPrimary}`}>Primary Buttons</h4>
              <div className="space-y-2">
                <Button variant="primary" size="sm" fullWidth>Small Primary</Button>
                <Button variant="primary" size="md" fullWidth>Medium Primary</Button>
                <Button variant="primary" size="lg" fullWidth>Large Primary</Button>
              </div>
            </div>
            
            <div className="space-y-4">
              <h4 className={`font-medium ${themeClasses.textPrimary}`}>Secondary Buttons</h4>
              <div className="space-y-2">
                <Button variant="secondary" size="sm" fullWidth>Small Secondary</Button>
                <Button variant="secondary" size="md" fullWidth>Medium Secondary</Button>
                <Button variant="secondary" size="lg" fullWidth>Large Secondary</Button>
              </div>
            </div>
            
            <div className="space-y-4">
              <h4 className={`font-medium ${themeClasses.textPrimary}`}>Tertiary Buttons</h4>
              <div className="space-y-2">
                <Button variant="tertiary" size="sm" fullWidth>Small Tertiary</Button>
                <Button variant="tertiary" size="md" fullWidth>Medium Tertiary</Button>
                <Button variant="tertiary" size="lg" fullWidth>Large Tertiary</Button>
              </div>
            </div>
            
            <div className="space-y-4">
              <h4 className={`font-medium ${themeClasses.textPrimary}`}>Danger Buttons</h4>
              <div className="space-y-2">
                <Button variant="danger" size="sm" fullWidth>Small Danger</Button>
                <Button variant="danger" size="md" fullWidth>Medium Danger</Button>
                <Button variant="danger" size="lg" fullWidth>Large Danger</Button>
              </div>
            </div>
          </div>
        </Card>

        {/* Form Elements Showcase */}
        <Card title="Form Elements" subtitle="Input fields and form controls in current theme">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium ${themeClasses.textSecondary} mb-2`}>
                  Patient Name
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="Enter patient name"
                  defaultValue="Ahmed Al Mansoori"
                />
              </div>
              
              <div>
                <label className={`block text-sm font-medium ${themeClasses.textSecondary} mb-2`}>
                  Medical Record Number
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="MRN-000000"
                  defaultValue="MRN-123456"
                />
              </div>
              
              <div>
                <label className={`block text-sm font-medium ${themeClasses.textSecondary} mb-2`}>
                  Insurance Provider
                </label>
                <select className="input">
                  <option>Dubai Health Insurance</option>
                  <option>Abu Dhabi Health Services</option>
                  <option>Sharjah Health Authority</option>
                </select>
              </div>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium ${themeClasses.textSecondary} mb-2`}>
                  Date of Birth
                </label>
                <input
                  type="date"
                  className="input"
                  defaultValue="1985-03-15"
                />
              </div>
              
              <div>
                <label className={`block text-sm font-medium ${themeClasses.textSecondary} mb-2`}>
                  Contact Number
                </label>
                <input
                  type="tel"
                  className="input"
                  placeholder="+971 50 000 0000"
                  defaultValue="+971 50 123 4567"
                />
              </div>
              
              <div className="space-y-3">
                <label className={`block text-sm font-medium ${themeClasses.textSecondary}`}>
                  Notification Preferences
                </label>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input type="checkbox" className="mr-3" defaultChecked />
                    <span className={themeClasses.textPrimary}>Email notifications</span>
                  </label>
                  <label className="flex items-center">
                    <input type="checkbox" className="mr-3" />
                    <span className={themeClasses.textPrimary}>SMS notifications</span>
                  </label>
                  <label className="flex items-center">
                    <input type="checkbox" className="mr-3" defaultChecked />
                    <span className={themeClasses.textPrimary}>Push notifications</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Status Badges and Pills */}
        <Card title="Status Indicators" subtitle="Healthcare status badges and indicators">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="space-y-4">
              <h4 className={`font-medium ${themeClasses.textPrimary}`}>Claim Status</h4>
              <div className="space-y-2">
                <div className="status-badge status-approved">Approved</div>
                <div className="status-badge status-pending">Pending Review</div>
                <div className="status-badge status-denied">Denied</div>
              </div>
            </div>
            
            <div className="space-y-4">
              <h4 className={`font-medium ${themeClasses.textPrimary}`}>Priority Levels</h4>
              <div className="space-y-2">
                <div 
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium"
                  style={{ 
                    backgroundColor: `${healthcareTheme.error}20`,
                    color: healthcareTheme.error
                  }}
                >
                  <span className="w-2 h-2 rounded-full mr-2" style={{ backgroundColor: healthcareTheme.error }} />
                  Critical
                </div>
                <div 
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium"
                  style={{ 
                    backgroundColor: `${healthcareTheme.warning}20`,
                    color: healthcareTheme.warning
                  }}
                >
                  <span className="w-2 h-2 rounded-full mr-2" style={{ backgroundColor: healthcareTheme.warning }} />
                  High
                </div>
                <div 
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium"
                  style={{ 
                    backgroundColor: `${healthcareTheme.success}20`,
                    color: healthcareTheme.success
                  }}
                >
                  <span className="w-2 h-2 rounded-full mr-2" style={{ backgroundColor: healthcareTheme.success }} />
                  Normal
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              <h4 className={`font-medium ${themeClasses.textPrimary}`}>Record Types</h4>
              <div className="space-y-2">
                <div className="badge badge-info">Patient Record</div>
                <div className="badge badge-success">Lab Result</div>
                <div className="badge badge-warning">Prescription</div>
                <div className="badge badge-error">Alert</div>
              </div>
            </div>
          </div>
        </Card>

        {/* Theme Toggle Options */}
        <Card title="Theme Toggle Variants" subtitle="Different ways to switch themes">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="space-y-4">
              <h4 className={`font-medium ${themeClasses.textPrimary}`}>Icon Toggle</h4>
              <div className="flex items-center justify-center">
                <ThemeToggle variant="icon" size="lg" />
              </div>
            </div>
            
            <div className="space-y-4">
              <h4 className={`font-medium ${themeClasses.textPrimary}`}>Button Toggle</h4>
              <div className="flex items-center justify-center">
                <ThemeToggle variant="button" showLabel />
              </div>
            </div>
            
            <div className="space-y-4">
              <h4 className={`font-medium ${themeClasses.textPrimary}`}>Switch Toggle</h4>
              <div className="flex items-center justify-center">
                <ThemeToggle variant="switch" size="lg" />
              </div>
            </div>
            
            <div className="space-y-4">
              <h4 className={`font-medium ${themeClasses.textPrimary}`}>Dropdown Toggle</h4>
              <div className="flex items-center justify-center">
                <ThemeToggle variant="dropdown" />
              </div>
            </div>
          </div>
        </Card>

        {/* Technical Details */}
        <Card title="Technical Implementation" subtitle="Theme system details and accessibility">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <h4 className={`font-medium ${themeClasses.textPrimary}`}>Features</h4>
              <ul className={`space-y-2 ${themeClasses.textSecondary}`}>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  Automatic system theme detection
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  localStorage persistence
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  Smooth transitions (200ms)
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  Healthcare-appropriate colors
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  WCAG AA contrast ratios
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  Reduced motion support
                </li>
              </ul>
            </div>
            
            <div className="space-y-4">
              <h4 className={`font-medium ${themeClasses.textPrimary}`}>Accessibility</h4>
              <ul className={`space-y-2 ${themeClasses.textSecondary}`}>
                <li className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-blue-500" />
                  High contrast mode support
                </li>
                <li className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-blue-500" />
                  Prefers-color-scheme detection
                </li>
                <li className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-blue-500" />
                  Prefers-reduced-motion support
                </li>
                <li className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-blue-500" />
                  Keyboard navigation friendly
                </li>
                <li className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-blue-500" />
                  Screen reader compatible
                </li>
                <li className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-blue-500" />
                  Focus indicators maintained
                </li>
              </ul>
            </div>
          </div>
        </Card>

      </div>
    </div>
  );
}