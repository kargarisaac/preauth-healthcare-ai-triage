import React, { useState, useEffect, useRef } from 'react';
import {
  Bell,
  Clock,
  AlertTriangle,
  User,
  FileText,
  TrendingUp,
  X,
  Check,
  MoreHorizontal,
  Calendar,
  Filter,
} from 'lucide-react';
import Button from '@components/ui/Button';
import Card from '@components/ui/Card';
import LoadingSpinner from '@components/ui/LoadingSpinner';
import type { MobileNotification } from '@/types/insurer';

// Mock notifications data
const mockNotifications: MobileNotification[] = [
  {
    id: 'NOTIF-001',
    type: 'urgent_review',
    title: 'Urgent Review Required',
    message: 'High-value cardiac procedure (PA-001-2025) requires immediate attention. Deadline: 2 hours.',
    requestId: 'REQ-2025-001',
    priority: 'high',
    timestamp: '2025-08-17T14:30:00Z',
    read: false,
    actionRequired: true,
  },
  {
    id: 'NOTIF-002',
    type: 'deadline_approaching',
    title: 'Review Deadline Approaching',
    message: 'Knee replacement authorization (PA-002-2025) deadline in 4 hours.',
    requestId: 'REQ-2025-002',
    priority: 'medium',
    timestamp: '2025-08-17T12:15:00Z',
    read: false,
    actionRequired: true,
  },
  {
    id: 'NOTIF-003',
    type: 'new_assignment',
    title: 'New Case Assigned',
    message: 'Diabetes management program authorization assigned to you.',
    requestId: 'REQ-2025-003',
    priority: 'medium',
    timestamp: '2025-08-17T11:45:00Z',
    read: true,
    actionRequired: false,
  },
  {
    id: 'NOTIF-004',
    type: 'escalation',
    title: 'Case Escalated',
    message: 'Complex oncology treatment requires senior medical director review.',
    requestId: 'REQ-2025-004',
    priority: 'high',
    timestamp: '2025-08-17T10:20:00Z',
    read: true,
    actionRequired: true,
  },
  {
    id: 'NOTIF-005',
    type: 'deadline_approaching',
    title: 'Multiple Deadlines Today',
    message: '3 authorizations require decisions by end of day.',
    priority: 'medium',
    timestamp: '2025-08-17T09:00:00Z',
    read: true,
    actionRequired: true,
  },
];

interface InsurerNotificationsProps {
  onClose: () => void;
  onRequestSelect?: (requestId: string) => void;
}

export const InsurerNotifications: React.FC<InsurerNotificationsProps> = ({
  onClose,
  onRequestSelect,
}) => {
  const [notifications, setNotifications] = useState<MobileNotification[]>(mockNotifications);
  const [isLoading, setIsLoading] = useState(false);
  const [filter, setFilter] = useState<'all' | 'unread' | 'urgent'>('all');
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose]);

  const markAsRead = (notificationId: string) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === notificationId 
          ? { ...notif, read: true }
          : notif
      )
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(notif => ({ ...notif, read: true }))
    );
  };

  const handleNotificationClick = (notification: MobileNotification) => {
    markAsRead(notification.id);
    if (notification.requestId && onRequestSelect) {
      onRequestSelect(notification.requestId);
      onClose();
    }
  };

  const filteredNotifications = Array.isArray(notifications) ? notifications.filter(notif => {
    switch (filter) {
      case 'unread':
        return !notif.read;
      case 'urgent':
        return notif.priority === 'high';
      default:
        return true;
    }
  }) : [];

  const unreadCount = Array.isArray(notifications) ? notifications.filter(n => !n.read).length : 0;
  const urgentCount = Array.isArray(notifications) ? notifications.filter(n => n.priority === 'high' && !n.read).length : 0;

  const getNotificationIcon = (type: MobileNotification['type']) => {
    switch (type) {
      case 'urgent_review':
        return AlertTriangle;
      case 'deadline_approaching':
        return Clock;
      case 'new_assignment':
        return User;
      case 'escalation':
        return TrendingUp;
      default:
        return Bell;
    }
  };

  const getNotificationColor = (priority: MobileNotification['priority'], read: boolean) => {
    if (read) return 'text-gray-500';
    
    switch (priority) {
      case 'high':
        return 'text-red-600';
      case 'medium':
        return 'text-orange-600';
      default:
        return 'text-blue-600';
    }
  };

  const formatTimeAgo = (timestamp: string): string => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays}d ago`;
  };

  return (
    <div ref={dropdownRef} className="absolute right-0 top-full mt-2 w-96 z-50">
      <Card className="shadow-lg border border-gray-200 dark:border-dark-border-primary">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-dark-border-primary">
          <div className="flex items-center space-x-3">
            <Bell className="h-5 w-5 text-gray-600 dark:text-dark-text-secondary" />
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary">
                Notifications
              </h3>
              <p className="text-sm text-gray-600 dark:text-dark-text-secondary">
                {unreadCount} unread{urgentCount > 0 && `, ${urgentCount} urgent`}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {unreadCount > 0 && (
              <Button
                variant="tertiary"
                size="sm"
                onClick={markAllAsRead}
                className="text-xs"
              >
                Mark all read
              </Button>
            )}
            <Button
              variant="tertiary"
              onClick={onClose}
              className="p-1"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex border-b border-gray-200 dark:border-dark-border-primary">
          {[
            { id: 'all', label: 'All', count: Array.isArray(notifications) ? notifications.length : 0 },
            { id: 'unread', label: 'Unread', count: unreadCount },
            { id: 'urgent', label: 'Urgent', count: urgentCount },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id as any)}
              className={`flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                filter === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className={`ml-2 px-1.5 py-0.5 rounded-full text-xs ${
                  filter === tab.id
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Notifications List */}
        <div className="max-h-96 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center p-8">
              <LoadingSpinner size="md" />
            </div>
          ) : filteredNotifications.length === 0 ? (
            <div className="text-center p-8">
              <Bell className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-dark-text-primary mb-2">
                No Notifications
              </h3>
              <p className="text-gray-600 dark:text-dark-text-secondary">
                {filter === 'unread' ? 'All caught up! No unread notifications.' :
                 filter === 'urgent' ? 'No urgent notifications at this time.' :
                 'No notifications to display.'}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-dark-border-primary">
              {filteredNotifications.map((notification) => {
                const Icon = getNotificationIcon(notification.type);
                const iconColor = getNotificationColor(notification.priority, notification.read);
                
                return (
                  <div
                    key={notification.id}
                    className={`p-4 hover:bg-gray-50 dark:hover:bg-dark-bg-tertiary cursor-pointer transition-colors ${
                      !notification.read ? 'bg-blue-50 dark:bg-blue-900/10' : ''
                    }`}
                    onClick={() => handleNotificationClick(notification)}
                  >
                    <div className="flex items-start space-x-3">
                      {/* Notification Icon */}
                      <div className={`p-2 rounded-full ${
                        notification.priority === 'high' ? 'bg-red-100 dark:bg-red-900/30' :
                        notification.priority === 'medium' ? 'bg-orange-100 dark:bg-orange-900/30' :
                        'bg-blue-100 dark:bg-blue-900/30'
                      }`}>
                        <Icon className={`h-4 w-4 ${iconColor}`} />
                      </div>
                      
                      {/* Notification Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className={`text-sm font-medium ${
                              notification.read 
                                ? 'text-gray-700 dark:text-dark-text-secondary' 
                                : 'text-gray-900 dark:text-dark-text-primary'
                            }`}>
                              {notification.title}
                            </h4>
                            <p className={`text-sm mt-1 ${
                              notification.read 
                                ? 'text-gray-500 dark:text-dark-text-tertiary' 
                                : 'text-gray-600 dark:text-dark-text-secondary'
                            }`}>
                              {notification.message}
                            </p>
                            
                            {/* Action Required Badge */}
                            {notification.actionRequired && (
                              <div className="mt-2">
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
                                  Action Required
                                </span>
                              </div>
                            )}
                          </div>
                          
                          {/* Timestamp and Actions */}
                          <div className="ml-4 flex-shrink-0 text-right">
                            <p className="text-xs text-gray-500 dark:text-dark-text-tertiary">
                              {formatTimeAgo(notification.timestamp)}
                            </p>
                            
                            {/* Unread Indicator */}
                            {!notification.read && (
                              <div className="mt-1 flex justify-end">
                                <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                              </div>
                            )}
                          </div>
                        </div>
                        
                        {/* Request ID Link */}
                        {notification.requestId && (
                          <div className="mt-2">
                            <span className="text-xs text-blue-600 dark:text-blue-400 hover:underline">
                              View Request {notification.requestId}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        {filteredNotifications.length > 0 && (
          <div className="p-4 border-t border-gray-200 dark:border-dark-border-primary text-center">
            <Button
              variant="tertiary"
              size="sm"
              onClick={() => {
                // Navigate to full notifications page
                console.log('Navigate to notifications page');
                onClose();
              }}
              className="text-blue-600 hover:text-blue-700"
            >
              View All Notifications
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};
