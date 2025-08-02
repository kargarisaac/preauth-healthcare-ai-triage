export interface PWAInstallPrompt {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
}

let deferredPrompt: PWAInstallPrompt | null = null;

// Initialize PWA features
export const initPWA = () => {
  // Listen for install prompt
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e as any;
    showInstallButton();
  });
  
  // Listen for app installed
  window.addEventListener('appinstalled', () => {
    console.log('PWA was installed');
    hideInstallButton();
    deferredPrompt = null;
  });
};

// Check if app can be installed
export const canInstallPWA = (): boolean => {
  return deferredPrompt !== null;
};

// Trigger install prompt
export const installPWA = async (): Promise<boolean> => {
  if (!deferredPrompt) {
    return false;
  }
  
  try {
    await deferredPrompt.prompt();
    const choiceResult = await deferredPrompt.userChoice;
    
    if (choiceResult.outcome === 'accepted') {
      console.log('User accepted the install prompt');
      return true;
    } else {
      console.log('User dismissed the install prompt');
      return false;
    }
  } catch (error) {
    console.error('Install prompt failed:', error);
    return false;
  } finally {
    deferredPrompt = null;
  }
};

// Check if running as PWA
export const isPWA = (): boolean => {
  return window.matchMedia('(display-mode: standalone)').matches || 
         (window.navigator as any).standalone === true;
};

// Show install button
const showInstallButton = () => {
  const event = new CustomEvent('pwa-install-available');
  window.dispatchEvent(event);
};

// Hide install button
const hideInstallButton = () => {
  const event = new CustomEvent('pwa-install-completed');
  window.dispatchEvent(event);
};

// Cache API responses
export const cacheResponse = async (url: string, response: Response) => {
  if ('caches' in window) {
    try {
      const cache = await caches.open('api-cache-v1');
      await cache.put(url, response.clone());
    } catch (error) {
      console.warn('Failed to cache response:', error);
    }
  }
};

// Get cached response
export const getCachedResponse = async (url: string): Promise<Response | null> => {
  if ('caches' in window) {
    try {
      const cache = await caches.open('api-cache-v1');
      return await cache.match(url);
    } catch (error) {
      console.warn('Failed to get cached response:', error);
    }
  }
  return null;
};

// Network status detection
export const getNetworkStatus = () => {
  return {
    online: navigator.onLine,
    effectiveType: (navigator as any).connection?.effectiveType,
    downlink: (navigator as any).connection?.downlink,
    rtt: (navigator as any).connection?.rtt,
  };
};

// Listen for network changes
export const onNetworkChange = (callback: (online: boolean) => void) => {
  const handleOnline = () => callback(true);
  const handleOffline = () => callback(false);
  
  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);
  
  // Return cleanup function
  return () => {
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
  };
};