import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Menu, 
  X, 
  Bell, 
  Settings, 
  User, 
  LogOut, 
  FileText, 
  BarChart3,
  Home,
  ChevronDown
} from 'lucide-react';
import { clsx } from 'clsx';
import ThemeToggle from '@components/ui/ThemeToggle';
import { useTheme } from '@contexts/ThemeContext';
import { useAppSelector } from '@/store/hooks';
import logoImage from '@assets/logo.png';

interface DashboardHeaderProps {
  title?: string;
  subtitle?: string;
  showNavigation?: boolean;
  className?: string;
}

export default function DashboardHeader({
  title = 'Dashboard',
  subtitle,
  showNavigation = true,
  className
}: DashboardHeaderProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const { isDarkMode } = useTheme();
  const notifications = useAppSelector(state => state.notifications);
  const unreadCount = notifications.unreadCount || 0;

  const navigationItems = [
    { href: '/dashboard', label: 'Overview', icon: Home },
    { href: '/dashboard/upload', label: 'Upload', icon: FileText },
    { href: '/dashboard/history', label: 'History', icon: BarChart3 },
  ];

  return (
    <header className={clsx(
      'bg-white dark:bg-dark-bg-secondary shadow-soft border-b border-gray-200 dark:border-dark-border-primary transition-colors duration-200',
      className
    )}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          {/* Logo and Title */}
          <div className="flex items-center space-x-4">
            <Link to="/" className="flex items-center space-x-2">
              <img src={logoImage} alt="Nazmito" className="h-8 w-8" />
              <span className="text-xl font-bold text-gray-900 dark:text-dark-text-primary">
                Nazmito
              </span>
            </Link>
            
            {title && (
              <div className="hidden sm:block">
                <div className="w-px h-6 bg-gray-300 dark:bg-dark-border-primary mx-4" />
                <div>
                  <h1 className="text-lg font-semibold text-gray-900 dark:text-dark-text-primary">
                    {title}
                  </h1>
                  {subtitle && (
                    <p className="text-sm text-gray-600 dark:text-dark-text-secondary">
                      {subtitle}
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Desktop Navigation */}
          {showNavigation && (
            <nav className="hidden lg:flex items-center space-x-8">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    className="flex items-center space-x-2 px-3 py-2 rounded-lg text-gray-600 dark:text-dark-text-secondary hover:text-gray-900 dark:hover:text-dark-text-primary hover:bg-gray-100 dark:hover:bg-dark-bg-tertiary transition-colors"
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          )}

          {/* Right Side Actions */}
          <div className="flex items-center space-x-4">
            {/* Theme Toggle */}
            <ThemeToggle variant="dropdown" />

            {/* Notifications */}
            <button
              className="relative p-2 text-gray-600 dark:text-dark-text-secondary hover:text-gray-900 dark:hover:text-dark-text-primary hover:bg-gray-100 dark:hover:bg-dark-bg-tertiary rounded-lg transition-colors"
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-primary-500 text-white text-xs font-medium flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                className="flex items-center space-x-2 p-2 text-gray-600 dark:text-dark-text-secondary hover:text-gray-900 dark:hover:text-dark-text-primary hover:bg-gray-100 dark:hover:bg-dark-bg-tertiary rounded-lg transition-colors"
                aria-label="User menu"
                aria-expanded={isUserMenuOpen}
              >
                <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
                <ChevronDown className="w-4 h-4" />
              </button>

              {isUserMenuOpen && (
                <>
                  {/* Overlay */}
                  <div 
                    className="fixed inset-0 z-10" 
                    onClick={() => setIsUserMenuOpen(false)}
                  />
                  
                  {/* Dropdown */}
                  <div className="absolute right-0 mt-2 w-48 rounded-lg shadow-large z-20 bg-white dark:bg-dark-bg-secondary border border-gray-200 dark:border-dark-border-primary py-2">
                    <div className="px-4 py-2 border-b border-gray-200 dark:border-dark-border-primary">
                      <p className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                        Healthcare Admin
                      </p>
                      <p className="text-sm text-gray-600 dark:text-dark-text-secondary">
                        admin@example.com
                      </p>
                    </div>
                    
                    <Link
                      to="/dashboard/settings"
                      className="flex items-center space-x-2 px-4 py-2 text-gray-700 dark:text-dark-text-secondary hover:bg-gray-100 dark:hover:bg-dark-bg-tertiary transition-colors"
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      <Settings className="w-4 h-4" />
                      <span>Settings</span>
                    </Link>
                    
                    <button
                      className="w-full flex items-center space-x-2 px-4 py-2 text-gray-700 dark:text-dark-text-secondary hover:bg-gray-100 dark:hover:bg-dark-bg-tertiary transition-colors"
                      onClick={() => setIsUserMenuOpen(false)}
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </>
              )}
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="lg:hidden p-2 text-gray-600 dark:text-dark-text-secondary hover:text-gray-900 dark:hover:text-dark-text-primary rounded-lg transition-colors"
              aria-label="Open mobile menu"
            >
              {isMobileMenuOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Title (shown when desktop title is hidden) */}
        {title && (
          <div className="sm:hidden pb-4">
            <h1 className="text-lg font-semibold text-gray-900 dark:text-dark-text-primary">
              {title}
            </h1>
            {subtitle && (
              <p className="text-sm text-gray-600 dark:text-dark-text-secondary">
                {subtitle}
              </p>
            )}
          </div>
        )}

        {/* Mobile Navigation */}
        {isMobileMenuOpen && showNavigation && (
          <div className="lg:hidden border-t border-gray-200 dark:border-dark-border-primary pt-4 pb-4">
            <nav className="space-y-2">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    className="flex items-center space-x-2 px-3 py-2 rounded-lg text-gray-600 dark:text-dark-text-secondary hover:text-gray-900 dark:hover:text-dark-text-primary hover:bg-gray-100 dark:hover:bg-dark-bg-tertiary transition-colors"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}