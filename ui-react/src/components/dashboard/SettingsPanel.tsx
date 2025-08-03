import React, { useState } from 'react';
import { 
  Sun, 
  Moon, 
  Monitor, 
  Palette, 
  Accessibility, 
  Bell, 
  Shield,
  Save,
  RotateCcw,
  Check
} from 'lucide-react';
import { clsx } from 'clsx';
import { useTheme, type ThemeMode } from '@contexts/ThemeContext';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { 
  setTheme,
  setHighContrast,
  setReducedMotion,
  setEnableNotifications,
  setEnableSoundNotifications,
  setNotificationDuration,
  updateNotificationSettings,
  resetToDefaults
} from '@/store/slices/userPreferencesSlice';
import Card from '@components/ui/Card';
import Button from '@components/ui/Button';

export default function SettingsPanel() {
  const { theme, systemTheme, actualTheme } = useTheme();
  const dispatch = useAppDispatch();
  const preferences = useAppSelector(state => state.userPreferences);
  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const themeOptions: Array<{
    value: ThemeMode;
    label: string;
    description: string;
    icon: React.ReactNode;
  }> = [
    {
      value: 'light',
      label: 'Light',
      description: 'Classic light interface for bright environments',
      icon: <Sun className="w-5 h-5" />
    },
    {
      value: 'dark',
      label: 'Dark',
      description: 'Dark interface that\'s easy on the eyes',
      icon: <Moon className="w-5 h-5" />
    },
    {
      value: 'system',
      label: 'System',
      description: `Automatically adapts to your device settings (currently ${systemTheme})`,
      icon: <Monitor className="w-5 h-5" />
    }
  ];

  const handleThemeChange = (newTheme: ThemeMode) => {
    dispatch(setTheme(newTheme));
    setHasChanges(true);
  };

  const handleAccessibilityChange = (key: string, value: boolean) => {
    if (key === 'highContrast') {
      dispatch(setHighContrast(value));
    } else if (key === 'reducedMotion') {
      dispatch(setReducedMotion(value));
    }
    setHasChanges(true);
  };

  const handleNotificationChange = (key: string, value: boolean | number) => {
    if (key === 'enableNotifications') {
      dispatch(setEnableNotifications(value as boolean));
    } else if (key === 'enableSoundNotifications') {
      dispatch(setEnableSoundNotifications(value as boolean));
    } else if (key === 'notificationDuration') {
      dispatch(setNotificationDuration(value as number));
    }
    setHasChanges(true);
  };

  const handleNotificationTypeChange = (key: string, value: boolean) => {
    dispatch(updateNotificationSettings({ [key]: value }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    setIsSaving(true);
    // Simulate save operation
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsSaving(false);
    setHasChanges(false);
    
    // Show success notification
    // This would typically dispatch a notification action
    console.log('Settings saved successfully');
  };

  const handleReset = () => {
    dispatch(resetToDefaults());
    setHasChanges(false);
    console.log('Settings reset to defaults');
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Theme Settings */}
      <Card title="Appearance" subtitle="Customize the visual appearance of your dashboard">
        <div className="space-y-6">
          <div>
            <h4 className="text-sm font-medium text-gray-900 dark:text-dark-text-primary mb-4 flex items-center gap-2">
              <Palette className="w-4 h-4" />
              Theme Preference
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {themeOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleThemeChange(option.value)}
                  className={clsx(
                    'relative p-4 rounded-lg border-2 transition-all duration-200 text-left',
                    theme === option.value
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-dark-border-primary hover:border-gray-300 dark:hover:border-dark-border-secondary bg-white dark:bg-dark-bg-secondary'
                  )}
                >
                  {theme === option.value && (
                    <div className="absolute top-2 right-2">
                      <Check className="w-4 h-4 text-primary-600" />
                    </div>
                  )}
                  
                  <div className="flex items-center gap-3 mb-2">
                    <span className={theme === option.value ? 'text-primary-600' : 'text-gray-600 dark:text-dark-text-secondary'}>
                      {option.icon}
                    </span>
                    <span className={clsx(
                      'font-medium',
                      theme === option.value ? 'text-primary-900 dark:text-primary-100' : 'text-gray-900 dark:text-dark-text-primary'
                    )}>
                      {option.label}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-600 dark:text-dark-text-secondary">
                    {option.description}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Preview */}
          <div className="bg-gray-50 dark:bg-dark-bg-tertiary rounded-lg p-4">
            <h5 className="text-sm font-medium text-gray-900 dark:text-dark-text-primary mb-3">
              Current Theme: {actualTheme === 'dark' ? 'Dark' : 'Light'} Mode
            </h5>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white dark:bg-dark-bg-secondary p-3 rounded border border-gray-200 dark:border-dark-border-primary">
                <div className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                  Card Example
                </div>
                <div className="text-xs text-gray-600 dark:text-dark-text-secondary mt-1">
                  This is how cards will appear
                </div>
              </div>
              <div className="bg-primary-500 p-3 rounded text-white">
                <div className="text-sm font-medium">Primary Button</div>
                <div className="text-xs opacity-90 mt-1">Healthcare orange</div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Accessibility Settings */}
      <Card title="Accessibility" subtitle="Configure accessibility features for better usability">
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-gray-900 dark:text-dark-text-primary flex items-center gap-2">
            <Accessibility className="w-4 h-4" />
            Accessibility Options
          </h4>

          <div className="space-y-3">
            <label className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                  High Contrast
                </div>
                <div className="text-sm text-gray-600 dark:text-dark-text-secondary">
                  Increase color contrast for better visibility
                </div>
              </div>
              <input
                type="checkbox"
                checked={preferences.highContrast}
                onChange={(e) => handleAccessibilityChange('highContrast', e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
            </label>

            <label className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                  Reduce Motion
                </div>
                <div className="text-sm text-gray-600 dark:text-dark-text-secondary">
                  Minimize animations and transitions
                </div>
              </div>
              <input
                type="checkbox"
                checked={preferences.reducedMotion}
                onChange={(e) => handleAccessibilityChange('reducedMotion', e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
            </label>
          </div>
        </div>
      </Card>

      {/* Notification Settings */}
      <Card title="Notifications" subtitle="Control when and how you receive notifications">
        <div className="space-y-6">
          <div>
            <h4 className="text-sm font-medium text-gray-900 dark:text-dark-text-primary mb-4 flex items-center gap-2">
              <Bell className="w-4 h-4" />
              General Settings
            </h4>
            
            <div className="space-y-3">
              <label className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                    Enable Notifications
                  </div>
                  <div className="text-sm text-gray-600 dark:text-dark-text-secondary">
                    Receive notifications for important events
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.enableNotifications}
                  onChange={(e) => handleNotificationChange('enableNotifications', e.target.checked)}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
              </label>

              <label className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                    Sound Notifications
                  </div>
                  <div className="text-sm text-gray-600 dark:text-dark-text-secondary">
                    Play sounds for notifications
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.enableSoundNotifications}
                  onChange={(e) => handleNotificationChange('enableSoundNotifications', e.target.checked)}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
              </label>

              <div>
                <label className="block text-sm font-medium text-gray-900 dark:text-dark-text-primary mb-2">
                  Notification Duration
                </label>
                <select
                  value={preferences.notificationDuration}
                  onChange={(e) => handleNotificationChange('notificationDuration', parseInt(e.target.value))}
                  className="input w-40"
                >
                  <option value={3}>3 seconds</option>
                  <option value={5}>5 seconds</option>
                  <option value={10}>10 seconds</option>
                  <option value={15}>15 seconds</option>
                </select>
              </div>
            </div>
          </div>

          <div>
            <h5 className="text-sm font-medium text-gray-900 dark:text-dark-text-primary mb-3">
              Notification Types
            </h5>
            <div className="space-y-3">
              {[
                { key: 'showSuccessNotifications', label: 'Success Messages', description: 'File processing completed' },
                { key: 'showWarningNotifications', label: 'Warning Messages', description: 'Validation issues found' },
                { key: 'showErrorNotifications', label: 'Error Messages', description: 'Processing failures' }
              ].map((item) => (
                <label key={item.key} className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                      {item.label}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-dark-text-secondary">
                      {item.description}
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences[item.key as keyof typeof preferences] as boolean}
                    onChange={(e) => handleNotificationTypeChange(item.key, e.target.checked)}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                </label>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Save Actions */}
      <div className="flex items-center justify-between py-4">
        <Button
          variant="secondary"
          onClick={handleReset}
          className="flex items-center gap-2"
        >
          <RotateCcw className="w-4 h-4" />
          Reset to Defaults
        </Button>

        <Button
          variant="primary"
          onClick={handleSave}
          disabled={!hasChanges}
          loading={isSaving}
          className="flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          {isSaving ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>

      {hasChanges && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-blue-800 dark:text-blue-200">
            <Shield className="w-4 h-4" />
            <span className="text-sm font-medium">
              You have unsaved changes. Remember to save your preferences.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}