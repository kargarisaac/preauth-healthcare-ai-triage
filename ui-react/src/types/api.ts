// API Response Types (matching FastAPI backend models)

/**
 * Generic API response wrapper
 */
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  metadata?: ProcessingMetadata;
  error?: string;
}

/**
 * Processing response for XML files (eClaimLink and Shafafiya)
 */
export interface ProcessingResponse {
  success: boolean;
  data?: Record<string, any>; // Processed canonical JSON data
  metadata: ProcessingMetadata;
  error?: string;
}

/**
 * CSV processing response with extended metadata
 */
export interface CSVProcessResponse {
  success: boolean;
  data?: Record<string, any>; // Processed canonical JSON data
  metadata: CSVProcessingMetadata;
  error?: string;
}

/**
 * Base processing metadata
 */
export interface ProcessingMetadata {
  filename: string;
  file_size_bytes: number;
  processing_time_seconds: number;
  format: string;
  api_version: string;
  processor_version: string;
}

/**
 * Extended metadata for CSV processing
 */
export interface CSVProcessingMetadata extends ProcessingMetadata {
  csv_type: string; // "Claims", "Clinical", or "Mixed"
  total_records: number;
  detected_columns: number;
  detected_resources: number;
  resource_types: string[];
  data_quality_score: number;
}

/**
 * Health check response
 */
export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}

/**
 * Sample file information
 */
export interface SampleFile {
  name: string;
  format: string; // "eClaimLink", "Shafafiya", "Claims CSV", "Clinical CSV"
  size: number;
  path: string;
  file_type: string; // "xml" or "csv"
}

/**
 * Error response model
 */
export interface ErrorResponse {
  success: boolean; // Always false for error responses
  error: string;
  details?: string;
  timestamp: string;
}

/**
 * FHIR Resource types that can be generated
 */
export type FHIRResourceType =
  | 'Bundle'
  | 'Claim'
  | 'ServiceRequest'
  | 'Observation'
  | 'MedicationStatement'
  | 'Condition'
  | 'Procedure'
  | 'Patient'
  | 'Practitioner'
  | 'Organization';

/**
 * File processing status
 */
export type ProcessingStatus =
  | 'idle'
  | 'uploading'
  | 'processing'
  | 'completed'
  | 'error';

/**
 * Supported file formats
 */
export type SupportedFormat =
  | 'eclaim'
  | 'shafafiya'
  | 'csv'
  | 'claims-csv'
  | 'clinical-csv';

/**
 * Upload progress information
 */
export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

/**
 * File validation result
 */
export interface FileValidation {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  fileInfo: {
    name: string;
    size: number;
    type: string;
    lastModified: number;
  };
}
