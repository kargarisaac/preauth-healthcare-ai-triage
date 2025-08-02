import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.tsx';
import './styles/tailwind.css';
import { initPerformanceMonitoring, markPerformance } from './utils/performance';
import { initPWA } from './utils/pwa';

// Mark performance timing for initial load
markPerformance('app-start');

// Initialize performance monitoring
initPerformanceMonitoring();

// Initialize PWA features
initPWA();

// Optimize rendering
const rootElement = document.getElementById('root');
if (!rootElement) throw new Error('Root element not found');

const root = ReactDOM.createRoot(rootElement);

// Mark when React starts rendering
markPerformance('react-render-start');

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);

// Mark when initial render is complete
if ('requestIdleCallback' in window) {
  requestIdleCallback(() => {
    markPerformance('react-render-complete');
  });
}

// Report loading performance after everything is ready
window.addEventListener('load', () => {
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => {
      // Log performance metrics in development
      if (process.env.NODE_ENV === 'development') {
        console.log('App fully loaded');
        
        // Log performance entries
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        if (navigation) {
          console.log('Performance metrics:', {
            'DNS Lookup': navigation.domainLookupEnd - navigation.domainLookupStart,
            'TCP Connection': navigation.connectEnd - navigation.connectStart,
            'Request': navigation.responseStart - navigation.requestStart,
            'Response': navigation.responseEnd - navigation.responseStart,
            'DOM Processing': navigation.domContentLoadedEventStart - navigation.responseEnd,
            'Load Complete': navigation.loadEventEnd - navigation.loadEventStart,
            'Total': navigation.loadEventEnd - navigation.navigationStart
          });
        }
      }
    });
  }
});