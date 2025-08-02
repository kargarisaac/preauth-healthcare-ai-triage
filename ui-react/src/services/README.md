# API Services Documentation

This directory contains the comprehensive API service layer for the Nazmito React application, providing seamless integration with the FastAPI backend.

## Overview

The API service layer consists of three main components:

1. **ApiService** - Core HTTP client with interceptors, retry logic, and caching
2. **FileProcessingService** - Specialized service for file upload and processing
3. **HealthService** - Health monitoring and connectivity testing

## Quick Start

```typescript
import {
  apiService,
  fileProcessingService,
  healthService
} from '../services';

// Basic API request
const data await apiService.get('/api/health');

// Process a file
const result = await fileProcessingService.processCSVFile(file);

// Check health
const status = await healthService.checkHealth();
```

## ApiService

The core HTTP client that handles all API communication.

### Features

- ✅ Request/response interceptors with logging
- ✅ Automatic retry logic with exponential backoff
- ✅ Request caching with configurable TTL
- ✅ Timeout handling and cancellation
- ✅ Comprehensive error handling
- ✅ TypeScript support with generics

### Usage

```typescript
import { apiService } from '../services/ApiService';

// GET request with caching
const response = await apiService.get<HealthResponse>('/api/health', {
  cache: true,
  cacheTTL: 300000, // 5 minutes
});

// POST request with custom timeout
const result = await apiService.post('/api/data', {
  name: 'test'
}, {
  timeout: 15000,
  retry: true,
  retryAttempts: 3,
});

// Generic request with full configuration
const data = await apiService.request<MyType>('/api/endpoint', {
  method: 'PUT',
  body: { id: 1, value: 'updated' },
  headers: { 'X-Custom': 'header' },
  timeout: 10000,
  cache: false,
});
```

### Error Handling

The service provides specific error types:

```typescript
import { ApiError, NetworkError, TimeoutError } from '../services/ApiService';

try {
  await apiService.get('/api/data');
} catch (error) {
  if (error instanceof ApiError) {
    console.log(`API Error ${error.status}: ${error.message}`);
    console.log('Details:', error.details);
  } else if (error instanceof NetworkError) {
    console.log('Network connection failed');
  } else if (error instanceof TimeoutError) {
    console.log('Request timed out');
  }
}
```

## FileProcessingService

Specialized service for handling file uploads and processing operations.

### Features

- ✅ File validation before upload
- ✅ Upload progress tracking
- ✅ Support for all backend file formats (XML, CSV)
- ✅ Sample file processing
- ✅ Request cancellation support
- ✅ Comprehensive file format detection

### Usage

```typescript
import { fileProcessingService } from '../services/FileProcessingService';

// Process file with progress tracking
const result = await fileProcessingService.processFile(file, 'csv', {
  onUploadProgress: (progress) => {
    console.log(`Upload: ${progress.percentage}%`);
  },
  timeout: 180000, // 3 minutes
});

// Validate file before processing
const validation = fileProcessingService.validateFileOnly(file, 'eclaim');
if (!validation.isValid) {
  console.log('Validation errors:', validation.errors);
}

// Process sample files
const sampleResult = await fileProcessingService.processSampleFile('claims-csv');

// Get sample files list
const samples = await fileProcessingService.getSampleFiles();
```

### File Validation

```typescript
import { FileValidationError } from '../services/FileProcessingService';

try {
  await fileProcessingService.processEClaimFile(file);
} catch (error) {
  if (error instanceof FileValidationError) {
    console.log('Validation failed:', error.validationResult.errors);
    console.log('Warnings:', error.validationResult.warnings);
  }
}
```

## HealthService

Service for monitoring API health and connectivity.

### Features

- ✅ Periodic health monitoring
- ✅ Connectivity testing
- ✅ Service metrics tracking
- ✅ Real-time status updates
- ✅ Health summary reporting

### Usage

```typescript
import { healthService } from '../services/HealthService';

// Single health check
const status = await healthService.checkHealth();
console.log(`API is ${status.isHealthy ? 'healthy' : 'unhealthy'}`);

// Start monitoring (30-second intervals)
healthService.startMonitoring(30000);

// Subscribe to health updates
const unsubscribe = healthService.subscribe((status) => {
  console.log('Health status updated:', status);
});

// Get service metrics
const metrics = healthService.getMetrics();
console.log(`Uptime: ${metrics.uptime}ms`);
console.log(`Success rate: ${metrics.successfulRequests / metrics.totalRequests * 100}%`);

// Test connectivity
const connectivity = await healthService.testConnectivity(5000);
console.log(`Connected: ${connectivity.isConnected}`);

// Stop monitoring
healthService.stopMonitoring();
unsubscribe();
```

## Configuration

### Environment Variables

```bash
# API Base URL (default: http://localhost:8000/api)
VITE_API_BASE_URL=https://api.nazmito.com/api
```

### Default Settings

```typescript
// API Service defaults
const API_DEFAULTS = {
  timeout: 30000,        // 30 seconds
  retryAttempts: 3,      // 3 retry attempts
  retryDelay: 1000,      // 1 second initial delay
  cacheTTL: 300000,      // 5 minutes cache TTL
};

// File Upload constraints
const FILE_UPLOAD = {
  maxSize: 10 * 1024 * 1024,    // 10MB
  allowedTypes: ['.xml', '.csv', '.pdf', '.json'],
  timeout: 120000,              // 2 minutes
};

// Health monitoring
const HEALTH_DEFAULTS = {
  interval: 30000,              // 30 seconds
  timeout: 10000,               // 10 seconds
};
```

## Error Handling Patterns

### Global Error Handler

```typescript
import { ApiError, NetworkError, TimeoutError } from '../services';

function handleApiError(error: Error): string {
  if (error instanceof ApiError) {
    // Server returned an error response
    return `Server Error: ${error.message}`;
  } else if (error instanceof NetworkError) {
    // Network connectivity issue
    return 'Network connection failed. Please check your internet connection.';
  } else if (error instanceof TimeoutError) {
    // Request timed out
    return 'Request timed out. Please try again.';
  } else {
    // Unknown error
    return 'An unexpected error occurred.';
  }
}
```

### Retry Strategy

```typescript
// Customize retry behavior
const config: RequestConfig = {
  retry: true,
  retryAttempts: 3,
  retryDelay: 1000,     // 1 second base delay
  // Uses exponential backoff: 1s, 2s, 4s
};
```

## Performance Optimization

### Caching Strategy

```typescript
// Cache GET requests for 10 minutes
await apiService.get('/api/reference-data', {
  cache: true,
  cacheTTL: 600000, // 10 minutes
});

// Clear cache when needed
apiService.clearCache();
```

### Request Cancellation

```typescript
const controller = new AbortController();

// Cancel request after 5 seconds
setTimeout(() => controller.abort(), 5000);

await fileProcessingService.processFile(file, 'csv', {
  signal: controller.signal,
});
```

## Integration with React Hooks

The services are designed to work seamlessly with the provided React hooks:

```typescript
import { useFileProcessing, useHealthCheck } from '../hooks/api';

function MyComponent() {
  const { processFile, progress, result } = useFileProcessing();
  const { health, startMonitoring } = useHealthCheck({ autoStart: true });

  // Component logic...
}
```

## Best Practices

1. **Always handle errors appropriately** - Use specific error types for different scenarios
2. **Use caching for reference data** - Cache static data that doesn't change frequently
3. **Implement proper loading states** - Show progress indicators during file uploads
4. **Monitor API health** - Use health monitoring in production environments
5. **Validate files before upload** - Catch validation errors early
6. **Use appropriate timeouts** - Longer timeouts for file processing, shorter for health checks
7. **Cancel requests when needed** - Prevent unnecessary network usage

## Type Safety

All services are fully typed with TypeScript:

```typescript
import type {
  ProcessingResponse,
  CSVProcessResponse,
  HealthResponse,
  FileValidation
} from '../types/api';

// Type-safe API calls
const result: ProcessingResponse = await fileProcessingService.processEClaimFile(file);
const health: HealthResponse = await apiService.get<HealthResponse>('/api/health');
```

This comprehensive API service layer provides everything needed for robust, production-ready communication with the Nazmito FastAPI backend.
