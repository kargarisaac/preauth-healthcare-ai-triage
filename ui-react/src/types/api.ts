// API Response Types (matching FastAPI backend models exactly)

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
 * Patient information for patient selection - matches backend PatientInfo model
 */
export interface PatientInfo {
  patient_id: string;
  folder_name: string;
  folder_path: string;
  has_profile: boolean;
  xml_files: number;
  processed_json_files: number;
}

/**
 * Patient resolution information
 */
export interface PatientResolution {
  patient_id?: string;
  patient_folder?: string;
  id_source: string;
}

/**
 * XML processing metadata - matches backend XMLProcessingMetadata model
 */
export interface XMLProcessingMetadata {
  filename: string;
  file_size?: number;
  source: string;
  processing_timestamp?: string;
  bundle_id?: string;
  patient_resolution: PatientResolution;
}

/**
 * XML processing response - matches backend XMLProcessResponse model
 */
export interface XMLProcessResponse {
  success: boolean;
  patient_id?: string;
  data?: Record<string, any>; // FHIR Bundle data
  metadata: any; // Processing metadata
  error?: string;
}

/**
 * Claude analysis results - matches backend ClaudeAnalysisResults model
 */
export interface ClaudeAnalysisResults {
  patient_id: string;
  claude_analysis: Record<string, any>;
  cost_usd: number;
  processing_time_seconds: number;
  historical_files_count: number;
  analysis_metadata: Record<string, any>;
  agent_results: Record<string, any>;
  timestamp: string;
}

/**
 * Analysis response - matches backend AnalysisResponse model
 */
export interface AnalysisResponse {
  success: boolean;
  patient_id: string;
  analysis?: Record<string, any>;
  recommendations: Array<Record<string, any>>;
  confidence_score?: number;
  error?: string;
}

/**
 * System status - matches backend SystemStatus model
 */
export interface SystemStatus {
  status: string;
  timestamp: string;
  version: string;
  xml_processing_available: boolean;
  claude_analysis_available: boolean;
  patient_index_size: number;
  supported_sources: string[];
}

/**
 * Patient dashboard data - matches backend DashboardData model
 */
export interface DashboardData {
  patient_info: PatientInfo;
  recent_files: Array<Record<string, any>>;
  analysis_history: Array<Record<string, any>>;
  summary_stats: Record<string, any>;
}

/**
 * Error response model - matches backend ErrorResponse model
 */
export interface ErrorResponse {
  error: string;
  details?: string;
  timestamp: string;
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
 * Patient-specific processing steps
 */
export type ProcessingStep = 'upload' | 'process' | 'analyze';

/**
 * Patient-specific processing status
 */
export type PatientProcessingStatus = 'idle' | 'loading' | 'success' | 'error';

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

// Legacy type aliases for backward compatibility
export type PatientUploadResponse = XMLProcessResponse;
export type PatientProcessResponse = XMLProcessResponse;  
export type PatientAnalysisResponse = AnalysisResponse;