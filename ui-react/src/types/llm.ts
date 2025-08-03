export interface LLMValidationFunction {
  id: string;
  name: string;
  description: string;
  category: 'clinical' | 'administrative' | 'compliance' | 'quality';
  priority: 'high' | 'medium' | 'low';
  estimatedTime: number; // in seconds
}

export interface LLMValidationResult {
  functionId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime?: Date;
  endTime?: Date;
  confidence: number; // 0-100
  findings: LLMFinding[];
  reasoning: string;
  executionTime?: number;
  error?: string;
}

export interface LLMFinding {
  id: string;
  type: 'critical' | 'warning' | 'info' | 'success';
  category: string;
  message: string;
  field?: string;
  suggestion?: string;
  confidence: number;
  evidence?: string[];
}

export interface LLMValidationProgress {
  functionId: string;
  progress: number; // 0-100
  currentStep: string;
  estimatedRemaining: number; // in seconds
}

export interface LLMValidationSummary {
  totalFunctions: number;
  completedFunctions: number;
  failedFunctions: number;
  averageConfidence: number;
  totalFindings: number;
  criticalFindings: number;
  warningFindings: number;
  estimatedTimeRemaining: number;
  overallStatus: 'pending' | 'running' | 'completed' | 'failed';
}

export interface LLMValidationWebSocketMessage {
  type: 'progress' | 'result' | 'error' | 'summary';
  data: LLMValidationProgress | LLMValidationResult | { error: string } | LLMValidationSummary;
  timestamp: Date;
}

export interface LLMValidationConfig {
  parallelExecution: boolean;
  maxConcurrentFunctions: number;
  timeoutPerFunction: number; // in seconds
  enableRealTimeUpdates: boolean;
  functions: LLMValidationFunction[];
}
