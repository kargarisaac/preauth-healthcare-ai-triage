import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { VitePWA } from 'vite-plugin-pwa';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    react({
      // Use Vite's built-in JSX transformation (no need for Babel plugins)
      jsxRuntime: 'automatic',
    }),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        clientsClaim: true,
        skipWaiting: true,
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        // Enhanced caching strategies for healthcare app
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.nazmito\.com\//,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60, // 1 hour
              },
              // Cache key customization handled by default
            },
          },
          {
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'images-cache',
              expiration: {
                maxEntries: 200,
                maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
              },
            },
          },
          {
            urlPattern: /\.(?:woff|woff2|eot|ttf|otf)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'fonts-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
              },
            },
          },
        ],
      },
      manifest: {
        name: 'Nazmito - Healthcare Pre-Authorization Intelligence',
        short_name: 'Nazmito',
        description: 'AI-powered pre-authorization platform for UAE healthcare insurance',
        theme_color: '#1E40AF',
        background_color: '#FFFFFF',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: '/vite.svg',
            sizes: '192x192',
            type: 'image/svg+xml'
          }
        ],
        shortcuts: [
          {
            name: 'Process Files',
            short_name: 'Process',
            description: 'Quick access to file processing',
            url: '/dashboard/upload',
            icons: [{ src: '/vite.svg', sizes: '192x192' }]
          },
          {
            name: 'Request History',
            short_name: 'History',
            description: 'View processing history',
            url: '/dashboard/history',
            icons: [{ src: '/vite.svg', sizes: '192x192' }]
          }
        ]
      }
    }),
    // Bundle analyzer for production builds
    process.env.ANALYZE && visualizer({
      filename: 'dist/stats.html',
      open: true,
      gzipSize: true,
      brotliSize: true,
    }),
  ].filter(Boolean),
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@services': path.resolve(__dirname, './src/services'),
      '@types': path.resolve(__dirname, './src/types'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@constants': path.resolve(__dirname, './src/constants'),
      '@contexts': path.resolve(__dirname, './src/contexts'),
      '@assets': path.resolve(__dirname, './src/assets'),
    }
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: process.env.NODE_ENV === 'development',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: process.env.NODE_ENV === 'production',
        drop_debugger: true,
        pure_funcs: process.env.NODE_ENV === 'production' ? ['console.log', 'console.warn'] : [],
        passes: 2,
      },
      mangle: {
        safari10: true,
      },
      format: {
        comments: false,
      },
    },
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Core vendor chunk
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
            return 'vendor-react';
          }
          
          // Router chunk
          if (id.includes('node_modules/react-router')) {
            return 'vendor-router';
          }
          
          // State management
          if (id.includes('node_modules/@reduxjs') || id.includes('node_modules/react-redux')) {
            return 'vendor-redux';
          }
          
          // UI and icons
          if (id.includes('node_modules/lucide-react') || id.includes('node_modules/clsx')) {
            return 'vendor-ui';
          }
          
          // Charts and visualization
          if (id.includes('node_modules/recharts') || id.includes('node_modules/d3')) {
            return 'vendor-charts';
          }
          
          // Healthcare-specific heavy libraries
          if (id.includes('node_modules/@uiw/react-json-view')) {
            return 'vendor-json';
          }
          
          // File processing utilities
          if (id.includes('node_modules/file-saver') || 
              id.includes('node_modules/html2canvas') || 
              id.includes('node_modules/jspdf')) {
            return 'vendor-files';
          }
          
          // Virtual scrolling
          if (id.includes('node_modules/react-window')) {
            return 'vendor-virtualization';
          }
          
          // Date utilities
          if (id.includes('node_modules/date-fns')) {
            return 'vendor-dates';
          }
          
          // Performance monitoring
          if (id.includes('node_modules/web-vitals')) {
            return 'vendor-performance';
          }
          
          // Healthcare components chunk
          if (id.includes('/src/components/healthcare/') || 
              id.includes('/src/components/dashboard/')) {
            return 'healthcare-components';
          }
          
          // Landing page chunk
          if (id.includes('/src/components/landing/') || 
              id.includes('/src/pages/Landing/')) {
            return 'landing';
          }
          
          // Analytics chunk
          if (id.includes('/src/pages/Analytics/') ||
              id.includes('/src/components/analytics/')) {
            return 'analytics';
          }
          
          // Other vendor libraries
          if (id.includes('node_modules/')) {
            return 'vendor-misc';
          }
        },
        // Optimize chunk naming with content hash
        chunkFileNames: (chunkInfo) => {
          const name = chunkInfo.name || 'chunk';
          return `js/${name}-[hash].js`;
        },
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.');
          const ext = info[info.length - 1];
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `images/[name]-[hash][extname]`;
          }
          if (/css/i.test(ext)) {
            return `css/[name]-[hash][extname]`;
          }
          if (/woff2?|eot|ttf|otf/i.test(ext)) {
            return `fonts/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        }
      },
      // External dependencies that should be loaded from CDN in production
      external: process.env.CDN_MODE ? [
        'react',
        'react-dom',
      ] : [],
    },
    chunkSizeWarningLimit: 500, // Stricter size limit
    cssCodeSplit: true,
    reportCompressedSize: false, // Faster builds
    // Enable experimental features
    target: 'esnext',
    modulePreload: {
      polyfill: false, // Don't polyfill module preload for better performance
    },
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'clsx',
      'lucide-react',
      'date-fns',
      '@reduxjs/toolkit',
      'react-redux',
      'use-debounce',
      'react-intersection-observer',
      'web-vitals',
    ],
    exclude: [
      '@vitejs/plugin-react',
      // Large libraries that should be lazy loaded
      'html2canvas',
      'jspdf',
      '@uiw/react-json-view',
    ],
    // Force specific dependencies to be pre-bundled
    force: ['react-window', 'react-window-infinite-loader'],
  },
  esbuild: {
    // Remove console.log in production
    drop: process.env.NODE_ENV === 'production' ? ['console', 'debugger'] : undefined,
    // Legal comments
    legalComments: 'none',
    // Target modern browsers for better optimization
    target: 'esnext',
  },
  
  // Enhanced development server
  preview: {
    port: 4173,
    strictPort: true,
  },
  
  // Performance hints
  define: {
    __DEV__: JSON.stringify(process.env.NODE_ENV === 'development'),
    __PROD__: JSON.stringify(process.env.NODE_ENV === 'production'),
    __VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
  },
});
