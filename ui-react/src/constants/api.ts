// API Configuration
export const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000/api';

// API Endpoints
export const API_ENDPOINTS = {
  // Health check
  HEALTH: '/health',
  
  // File processing
  PROCESS_ECLAIM: '/process/eclaim',
  PROCESS_SHAFAFIYA: '/process/shafafiya',
  PROCESS_CSV: '/process/csv',
  
  // Sample processing
  PROCESS_SAMPLE_ECLAIM: '/process/sample/eclaim',
  PROCESS_SAMPLE_SHAFAFIYA: '/process/sample/shafafiya',
  PROCESS_SAMPLE_CLAIMS_CSV: '/process/sample/claims-csv',
  PROCESS_SAMPLE_CLINICAL_CSV: '/process/sample/clinical-csv',
  
  // Sample files
  SAMPLES: '/samples',
  SAMPLES_CSV: '/samples/csv',
} as const;

// File upload constraints
export const FILE_UPLOAD = {
  MAX_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_TYPES: ['.xml', '.csv', '.pdf', '.json'],
  ALLOWED_XML_TYPES: ['.xml'],
  ALLOWED_CSV_TYPES: ['.csv'],
} as const;