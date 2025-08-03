import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// Types
interface UserPreferencesState {
  // UI Settings
  theme: 'light' | 'dark' | 'system';
  language: 'en' | 'ar';
  direction: 'ltr' | 'rtl';
  
  // Dashboard Layout
  dashboardLayout: 'grid' | 'list' | 'compact';
  sidebarCollapsed: boolean;
  showMinimap: boolean;
  
  // File Processing Defaults
  defaultFileFormat: 'eclaim' | 'shafafiya' | 'csv' | 'auto';
  autoValidation: boolean;
  realTimeUpdates: boolean;
  
  // Validation Preferences
  defaultValidationFunctions: string[];
  validationTimeout: number; // in seconds
  maxConcurrentValidations: number;
  
  // Display Preferences
  dateFormat: 'DD/MM/YYYY' | 'MM/DD/YYYY' | 'YYYY-MM-DD';
  timeFormat: '12h' | '24h';
  currency: 'AED' | 'USD';
  numberFormat: 'US' | 'EU' | 'AR';
  
  // Notification Settings
  enableNotifications: boolean;
  enableSoundNotifications: boolean;
  notificationDuration: number; // in seconds
  showSuccessNotifications: boolean;
  showWarningNotifications: boolean;
  showErrorNotifications: boolean;
  
  // Performance Settings
  enableVirtualization: boolean;
  itemsPerPage: number;
  cacheTimeout: number; // in minutes
  enableOfflineMode: boolean;
  
  // Accessibility
  reducedMotion: boolean;
  highContrast: boolean;
  fontSize: 'small' | 'medium' | 'large';
  
  // Advanced Settings
  debugMode: boolean;
  enableAnalytics: boolean;
  autoSave: boolean;
  autoSaveInterval: number; // in seconds
  
  // Recent Selections
  recentFormats: string[];
  recentValidationSets: Array<{
    id: string;
    name: string;
    functionIds: string[];
    lastUsed: Date;
  }>;
}

const initialState: UserPreferencesState = {
  // UI Settings
  theme: 'system',
  language: 'en',
  direction: 'ltr',
  
  // Dashboard Layout
  dashboardLayout: 'grid',
  sidebarCollapsed: false,
  showMinimap: true,
  
  // File Processing Defaults
  defaultFileFormat: 'auto',
  autoValidation: true,
  realTimeUpdates: true,
  
  // Validation Preferences
  defaultValidationFunctions: [],
  validationTimeout: 300, // 5 minutes
  maxConcurrentValidations: 3,
  
  // Display Preferences
  dateFormat: 'DD/MM/YYYY',
  timeFormat: '24h',
  currency: 'AED',
  numberFormat: 'US',
  
  // Notification Settings
  enableNotifications: true,
  enableSoundNotifications: false,
  notificationDuration: 5,
  showSuccessNotifications: true,
  showWarningNotifications: true,
  showErrorNotifications: true,
  
  // Performance Settings
  enableVirtualization: true,
  itemsPerPage: 50,
  cacheTimeout: 30,
  enableOfflineMode: false,
  
  // Accessibility
  reducedMotion: false,
  highContrast: false,
  fontSize: 'medium',
  
  // Advanced Settings
  debugMode: false,
  enableAnalytics: true,
  autoSave: true,
  autoSaveInterval: 30,
  
  // Recent Selections
  recentFormats: [],
  recentValidationSets: [],
};

// Slice
const userPreferencesSlice = createSlice({
  name: 'userPreferences',
  initialState,
  reducers: {
    // UI Settings
    setTheme: (state, action: PayloadAction<UserPreferencesState['theme']>) => {
      state.theme = action.payload;
    },
    
    setLanguage: (state, action: PayloadAction<UserPreferencesState['language']>) => {
      state.language = action.payload;
      state.direction = action.payload === 'ar' ? 'rtl' : 'ltr';
    },
    
    // Dashboard Layout
    setDashboardLayout: (state, action: PayloadAction<UserPreferencesState['dashboardLayout']>) => {
      state.dashboardLayout = action.payload;
    },
    
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload;
    },
    
    toggleMinimap: (state) => {
      state.showMinimap = !state.showMinimap;
    },
    
    // File Processing Defaults
    setDefaultFileFormat: (state, action: PayloadAction<UserPreferencesState['defaultFileFormat']>) => {
      state.defaultFileFormat = action.payload;
      
      // Add to recent formats
      if (action.payload !== 'auto') {
        const format = action.payload;
        state.recentFormats = [format, ...state.recentFormats.filter(f => f !== format)].slice(0, 5);
      }
    },
    
    setAutoValidation: (state, action: PayloadAction<boolean>) => {
      state.autoValidation = action.payload;
    },
    
    setRealTimeUpdates: (state, action: PayloadAction<boolean>) => {
      state.realTimeUpdates = action.payload;
    },
    
    // Validation Preferences
    setDefaultValidationFunctions: (state, action: PayloadAction<string[]>) => {
      state.defaultValidationFunctions = action.payload;
    },
    
    setValidationTimeout: (state, action: PayloadAction<number>) => {
      state.validationTimeout = Math.max(30, Math.min(1800, action.payload)); // 30s to 30min
    },
    
    setMaxConcurrentValidations: (state, action: PayloadAction<number>) => {
      state.maxConcurrentValidations = Math.max(1, Math.min(10, action.payload));
    },
    
    // Display Preferences
    setDateFormat: (state, action: PayloadAction<UserPreferencesState['dateFormat']>) => {
      state.dateFormat = action.payload;
    },
    
    setTimeFormat: (state, action: PayloadAction<UserPreferencesState['timeFormat']>) => {
      state.timeFormat = action.payload;
    },
    
    setCurrency: (state, action: PayloadAction<UserPreferencesState['currency']>) => {
      state.currency = action.payload;
    },
    
    setNumberFormat: (state, action: PayloadAction<UserPreferencesState['numberFormat']>) => {
      state.numberFormat = action.payload;
    },
    
    // Notification Settings
    setEnableNotifications: (state, action: PayloadAction<boolean>) => {
      state.enableNotifications = action.payload;
    },
    
    setEnableSoundNotifications: (state, action: PayloadAction<boolean>) => {
      state.enableSoundNotifications = action.payload;
    },
    
    setNotificationDuration: (state, action: PayloadAction<number>) => {
      state.notificationDuration = Math.max(1, Math.min(30, action.payload));
    },
    
    updateNotificationSettings: (state, action: PayloadAction<{
      showSuccessNotifications?: boolean;
      showWarningNotifications?: boolean;
      showErrorNotifications?: boolean;
    }>) => {
      Object.assign(state, action.payload);
    },
    
    // Performance Settings
    setEnableVirtualization: (state, action: PayloadAction<boolean>) => {
      state.enableVirtualization = action.payload;
    },
    
    setItemsPerPage: (state, action: PayloadAction<number>) => {
      state.itemsPerPage = Math.max(10, Math.min(200, action.payload));
    },
    
    setCacheTimeout: (state, action: PayloadAction<number>) => {
      state.cacheTimeout = Math.max(1, Math.min(1440, action.payload)); // 1min to 24hrs
    },
    
    setEnableOfflineMode: (state, action: PayloadAction<boolean>) => {
      state.enableOfflineMode = action.payload;
    },
    
    // Accessibility
    setReducedMotion: (state, action: PayloadAction<boolean>) => {
      state.reducedMotion = action.payload;
    },
    
    setHighContrast: (state, action: PayloadAction<boolean>) => {
      state.highContrast = action.payload;
    },
    
    setFontSize: (state, action: PayloadAction<UserPreferencesState['fontSize']>) => {
      state.fontSize = action.payload;
    },
    
    // Advanced Settings
    setDebugMode: (state, action: PayloadAction<boolean>) => {
      state.debugMode = action.payload;
    },
    
    setEnableAnalytics: (state, action: PayloadAction<boolean>) => {
      state.enableAnalytics = action.payload;
    },
    
    setAutoSave: (state, action: PayloadAction<boolean>) => {
      state.autoSave = action.payload;
    },
    
    setAutoSaveInterval: (state, action: PayloadAction<number>) => {
      state.autoSaveInterval = Math.max(10, Math.min(300, action.payload)); // 10s to 5min
    },
    
    // Recent Selections
    addRecentValidationSet: (state, action: PayloadAction<{
      name: string;
      functionIds: string[];
    }>) => {
      const { name, functionIds } = action.payload;
      const id = Date.now().toString();
      
      const validationSet = {
        id,
        name,
        functionIds,
        lastUsed: new Date(),
      };
      
      // Remove existing set with same name
      state.recentValidationSets = state.recentValidationSets.filter(
        set => set.name !== name
      );
      
      // Add to beginning and keep only last 10
      state.recentValidationSets = [validationSet, ...state.recentValidationSets].slice(0, 10);
    },
    
    updateRecentValidationSetUsage: (state, action: PayloadAction<string>) => {
      const setId = action.payload;
      const setIndex = state.recentValidationSets.findIndex(set => set.id === setId);
      
      if (setIndex > -1) {
        const validationSet = state.recentValidationSets[setIndex];
        validationSet.lastUsed = new Date();
        
        // Move to beginning
        state.recentValidationSets.splice(setIndex, 1);
        state.recentValidationSets.unshift(validationSet);
      }
    },
    
    removeRecentValidationSet: (state, action: PayloadAction<string>) => {
      state.recentValidationSets = state.recentValidationSets.filter(
        set => set.id !== action.payload
      );
    },
    
    // Bulk updates
    updatePreferences: (state, action: PayloadAction<Partial<UserPreferencesState>>) => {
      Object.assign(state, action.payload);
    },
    
    resetToDefaults: (state) => {
      Object.assign(state, initialState);
    },
    
    // Export/Import
    exportPreferences: (state) => {
      return { ...state };
    },
    
    importPreferences: (state, action: PayloadAction<Partial<UserPreferencesState>>) => {
      // Validate and merge preferences
      const validatedPreferences = { ...action.payload };
      
      // Ensure numeric values are within bounds
      if (validatedPreferences.validationTimeout) {
        validatedPreferences.validationTimeout = Math.max(30, Math.min(1800, validatedPreferences.validationTimeout));
      }
      if (validatedPreferences.maxConcurrentValidations) {
        validatedPreferences.maxConcurrentValidations = Math.max(1, Math.min(10, validatedPreferences.maxConcurrentValidations));
      }
      if (validatedPreferences.itemsPerPage) {
        validatedPreferences.itemsPerPage = Math.max(10, Math.min(200, validatedPreferences.itemsPerPage));
      }
      
      Object.assign(state, validatedPreferences);
    },
  },
});

// Export actions
export const {
  setTheme,
  setLanguage,
  setDashboardLayout,
  toggleSidebar,
  setSidebarCollapsed,
  toggleMinimap,
  setDefaultFileFormat,
  setAutoValidation,
  setRealTimeUpdates,
  setDefaultValidationFunctions,
  setValidationTimeout,
  setMaxConcurrentValidations,
  setDateFormat,
  setTimeFormat,
  setCurrency,
  setNumberFormat,
  setEnableNotifications,
  setEnableSoundNotifications,
  setNotificationDuration,
  updateNotificationSettings,
  setEnableVirtualization,
  setItemsPerPage,
  setCacheTimeout,
  setEnableOfflineMode,
  setReducedMotion,
  setHighContrast,
  setFontSize,
  setDebugMode,
  setEnableAnalytics,
  setAutoSave,
  setAutoSaveInterval,
  addRecentValidationSet,
  updateRecentValidationSetUsage,
  removeRecentValidationSet,
  updatePreferences,
  resetToDefaults,
  exportPreferences,
  importPreferences,
} = userPreferencesSlice.actions;

// Export reducer
export default userPreferencesSlice.reducer;