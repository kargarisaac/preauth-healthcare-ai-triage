import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { ToastMessage } from '../../types/ui';

// Extended notification types
interface NotificationAction {
  label: string;
  action: () => void;
  style?: 'primary' | 'secondary';
}

interface ExtendedToastMessage extends Omit<ToastMessage, 'id'> {
  id?: string;
  category?: 'system' | 'validation' | 'processing' | 'user' | 'api';
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  persistent?: boolean;
  actions?: NotificationAction[];
  progress?: number;
  metadata?: Record<string, any>;
}

interface NotificationHistory {
  id: string;
  type: ToastMessage['type'];
  title: string;
  message: string;
  category: string;
  timestamp: Date;
  read: boolean;
}

interface NotificationState {
  // Active notifications
  toasts: ToastMessage[];
  
  // Notification history
  history: NotificationHistory[];
  unreadCount: number;
  
  // System notifications
  systemNotifications: Array<{
    id: string;
    type: 'maintenance' | 'update' | 'announcement';
    title: string;
    message: string;
    actionUrl?: string;
    actionLabel?: string;
    priority: 'low' | 'normal' | 'high';
    startDate: Date;
    endDate?: Date;
    dismissed: boolean;
  }>;
  
  // Processing notifications
  progressNotifications: Record<string, {
    id: string;
    title: string;
    progress: number;
    status: 'running' | 'completed' | 'failed';
    startTime: Date;
    estimatedEndTime?: Date;
  }>;
  
  // Settings
  settings: {
    enableNotifications: boolean;
    enableSound: boolean;
    enableDesktop: boolean;
    defaultDuration: number;
    maxToasts: number;
    groupSimilar: boolean;
  };
}

const initialState: NotificationState = {
  toasts: [],
  history: [],
  unreadCount: 0,
  systemNotifications: [],
  progressNotifications: {},
  settings: {
    enableNotifications: true,
    enableSound: false,
    enableDesktop: false,
    defaultDuration: 5000,
    maxToasts: 5,
    groupSimilar: true,
  },
};

// Helper functions
const generateId = () => Math.random().toString(36).substr(2, 9);

const playNotificationSound = (type: ToastMessage['type']) => {
  if ('Audio' in window) {
    try {
      // Simple audio feedback using Web Audio API
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      // Different frequencies for different notification types
      switch (type) {
        case 'success':
          oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
          break;
        case 'error':
          oscillator.frequency.setValueAtTime(400, audioContext.currentTime);
          break;
        case 'warning':
          oscillator.frequency.setValueAtTime(600, audioContext.currentTime);
          break;
        default:
          oscillator.frequency.setValueAtTime(500, audioContext.currentTime);
      }
      
      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.2);
    } catch (error) {
      console.warn('Could not play notification sound:', error);
    }
  }
};

const requestDesktopPermission = async () => {
  if ('Notification' in window && Notification.permission === 'default') {
    return await Notification.requestPermission();
  }
  return Notification.permission;
};

const showDesktopNotification = (notification: ToastMessage) => {
  if ('Notification' in window && Notification.permission === 'granted') {
    const desktopNotification = new Notification(notification.title, {
      body: notification.message,
      icon: '/favicon.ico',
      tag: notification.id,
    });
    
    // Auto-close after duration
    setTimeout(() => {
      desktopNotification.close();
    }, notification.duration || 5000);
  }
};

// Slice
const notificationSlice = createSlice({
  name: 'notifications',
  initialState,
  reducers: {
    // Toast management
    showToast: (state, action: PayloadAction<ExtendedToastMessage>) => {
      const notification = action.payload;
      const id = notification.id || generateId();
      const duration = notification.duration || state.settings.defaultDuration;
      
      const toast: ToastMessage = {
        id,
        type: notification.type,
        title: notification.title,
        message: notification.message,
        duration,
      };
      
      // Check for similar notifications if grouping is enabled
      if (state.settings.groupSimilar) {
        const existingIndex = state.toasts.findIndex(
          t => t.type === toast.type && t.title === toast.title
        );
        
        if (existingIndex > -1) {
          // Update existing notification
          state.toasts[existingIndex] = { ...state.toasts[existingIndex], ...toast };
          return;
        }
      }
      
      // Add new toast
      state.toasts.push(toast);
      
      // Limit number of toasts
      if (state.toasts.length > state.settings.maxToasts) {
        state.toasts = state.toasts.slice(-state.settings.maxToasts);
      }
      
      // Add to history
      const historyItem: NotificationHistory = {
        id,
        type: notification.type,
        title: notification.title,
        message: notification.message,
        category: notification.category || 'user',
        timestamp: new Date(),
        read: false,
      };
      
      state.history.unshift(historyItem);
      state.unreadCount++;
      
      // Keep history limited to 100 items
      if (state.history.length > 100) {
        state.history = state.history.slice(0, 100);
      }
      
      // Play sound if enabled
      if (state.settings.enableSound) {
        // This will be handled by middleware or component
      }
      
      // Show desktop notification if enabled
      if (state.settings.enableDesktop) {
        // This will be handled by middleware or component
      }
    },
    
    removeToast: (state, action: PayloadAction<string>) => {
      state.toasts = state.toasts.filter(toast => toast.id !== action.payload);
    },
    
    clearToasts: (state) => {
      state.toasts = [];
    },
    
    updateToast: (state, action: PayloadAction<{ id: string; updates: Partial<ToastMessage> }>) => {
      const { id, updates } = action.payload;
      const toastIndex = state.toasts.findIndex(toast => toast.id === id);
      
      if (toastIndex > -1) {
        state.toasts[toastIndex] = { ...state.toasts[toastIndex], ...updates };
      }
    },
    
    // Progress notifications
    showProgressNotification: (state, action: PayloadAction<{
      id: string;
      title: string;
      progress: number;
      estimatedEndTime?: Date;
    }>) => {
      const { id, title, progress, estimatedEndTime } = action.payload;
      
      state.progressNotifications[id] = {
        id,
        title,
        progress,
        status: 'running',
        startTime: state.progressNotifications[id]?.startTime || new Date(),
        estimatedEndTime,
      };
    },
    
    updateProgressNotification: (state, action: PayloadAction<{
      id: string;
      progress?: number;
      status?: 'running' | 'completed' | 'failed';
      estimatedEndTime?: Date;
    }>) => {
      const { id, progress, status, estimatedEndTime } = action.payload;
      
      if (state.progressNotifications[id]) {
        const notification = state.progressNotifications[id];
        
        if (progress !== undefined) notification.progress = progress;
        if (status !== undefined) notification.status = status;
        if (estimatedEndTime !== undefined) notification.estimatedEndTime = estimatedEndTime;
        
        // Auto-remove completed notifications after delay
        if (status === 'completed') {
          // This will be handled by a timeout
        }
      }
    },
    
    removeProgressNotification: (state, action: PayloadAction<string>) => {
      delete state.progressNotifications[action.payload];
    },
    
    // System notifications
    showSystemNotification: (state, action: PayloadAction<{
      type: 'maintenance' | 'update' | 'announcement';
      title: string;
      message: string;
      actionUrl?: string;
      actionLabel?: string;
      priority?: 'low' | 'normal' | 'high';
      startDate?: Date;
      endDate?: Date;
    }>) => {
      const notification = {
        id: generateId(),
        type: action.payload.type,
        title: action.payload.title,
        message: action.payload.message,
        actionUrl: action.payload.actionUrl,
        actionLabel: action.payload.actionLabel,
        priority: action.payload.priority || 'normal',
        startDate: action.payload.startDate || new Date(),
        endDate: action.payload.endDate,
        dismissed: false,
      };
      
      state.systemNotifications.push(notification);
    },
    
    dismissSystemNotification: (state, action: PayloadAction<string>) => {
      const notificationIndex = state.systemNotifications.findIndex(
        n => n.id === action.payload
      );
      
      if (notificationIndex > -1) {
        state.systemNotifications[notificationIndex].dismissed = true;
      }
    },
    
    removeSystemNotification: (state, action: PayloadAction<string>) => {
      state.systemNotifications = state.systemNotifications.filter(
        n => n.id !== action.payload
      );
    },
    
    // History management
    markAsRead: (state, action: PayloadAction<string>) => {
      const historyItem = state.history.find(h => h.id === action.payload);
      if (historyItem && !historyItem.read) {
        historyItem.read = true;
        state.unreadCount = Math.max(0, state.unreadCount - 1);
      }
    },
    
    markAllAsRead: (state) => {
      state.history.forEach(item => {
        item.read = true;
      });
      state.unreadCount = 0;
    },
    
    clearHistory: (state) => {
      state.history = [];
      state.unreadCount = 0;
    },
    
    // Settings
    updateSettings: (state, action: PayloadAction<Partial<NotificationState['settings']>>) => {
      state.settings = { ...state.settings, ...action.payload };
    },
    
    // Bulk operations
    showMultipleToasts: (state, action: PayloadAction<ExtendedToastMessage[]>) => {
      action.payload.forEach(notification => {
        const id = notification.id || generateId();
        const duration = notification.duration || state.settings.defaultDuration;
        
        const toast: ToastMessage = {
          id,
          type: notification.type,
          title: notification.title,
          message: notification.message,
          duration,
        };
        
        state.toasts.push(toast);
        
        // Add to history
        const historyItem: NotificationHistory = {
          id,
          type: notification.type,
          title: notification.title,
          message: notification.message,
          category: notification.category || 'user',
          timestamp: new Date(),
          read: false,
        };
        
        state.history.unshift(historyItem);
        state.unreadCount++;
      });
      
      // Limit toasts
      if (state.toasts.length > state.settings.maxToasts) {
        state.toasts = state.toasts.slice(-state.settings.maxToasts);
      }
      
      // Limit history
      if (state.history.length > 100) {
        state.history = state.history.slice(0, 100);
      }
    },
    
  },
});

// Export actions
export const {
  showToast,
  removeToast,
  clearToasts,
  updateToast,
  showProgressNotification,
  updateProgressNotification,
  removeProgressNotification,
  showSystemNotification,
  dismissSystemNotification,
  removeSystemNotification,
  markAsRead,
  markAllAsRead,
  clearHistory,
  updateSettings,
  showMultipleToasts,
} = notificationSlice.actions;

// Utility selectors (to be used with useAppSelector)
export const getNotificationsByCategory = (state: any, category: string) => 
  state.notifications.history.filter((h: any) => h.category === category);

export const getUnreadNotifications = (state: any) => 
  state.notifications.history.filter((h: any) => !h.read);

// Export helper functions for use in middleware
export { playNotificationSound, requestDesktopPermission, showDesktopNotification };

// Export reducer
export default notificationSlice.reducer;