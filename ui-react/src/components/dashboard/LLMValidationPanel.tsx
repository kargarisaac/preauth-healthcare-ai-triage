import React, { useState, useEffect, useCallback } from 'react';
import {
  Brain,
  CheckCircle2,
  AlertTriangle,
  Info,
  XCircle,
  ChevronDown,
  ChevronRight,
  Play,
  Pause,
  Clock,
  TrendingUp,
  Zap,
  Shield,
  FileText,
  Timer
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import LoadingSpinner from '../ui/LoadingSpinner';
import {
  LLMValidationFunction,
  LLMValidationResult,
  LLMValidationProgress,
  LLMValidationSummary,
  LLMFinding
} from '../../types/llm';

interface LLMValidationPanelProps {
  fileData?: any;
  onValidationComplete?: (results: LLMValidationResult[]) => void;
  className?: string;
}

interface LLMFunctionCardProps {
  func: LLMValidationFunction;
  result?: LLMValidationResult;
  progress?: LLMValidationProgress;
  onExpand: (functionId: string) => void;
  isExpanded: boolean;
}

interface LLMFindingItemProps {
  finding: LLMFinding;
}

const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'clinical':
      return <Shield className="h-4 w-4" />;
    case 'administrative':
      return <FileText className="h-4 w-4" />;
    case 'compliance':
      return <CheckCircle2 className="h-4 w-4" />;
    case 'quality':
      return <TrendingUp className="h-4 w-4" />;
    default:
      return <Brain className="h-4 w-4" />;
  }
};

const getCategoryColor = (category: string) => {
  switch (category) {
    case 'clinical':
      return 'text-red-600 bg-red-50 border-red-200';
    case 'administrative':
      return 'text-blue-600 bg-blue-50 border-blue-200';
    case 'compliance':
      return 'text-green-600 bg-green-50 border-green-200';
    case 'quality':
      return 'text-purple-600 bg-purple-50 border-purple-200';
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="h-5 w-5 text-green-600" />;
    case 'failed':
      return <XCircle className="h-5 w-5 text-red-600" />;
    case 'running':
      return <div className="animate-spin"><LoadingSpinner size="sm" /></div>;
    default:
      return <Clock className="h-5 w-5 text-gray-400" />;
  }
};

const getFindingIcon = (type: string) => {
  switch (type) {
    case 'critical':
      return <XCircle className="h-4 w-4 text-red-600" />;
    case 'warning':
      return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    case 'info':
      return <Info className="h-4 w-4 text-blue-600" />;
    case 'success':
      return <CheckCircle2 className="h-4 w-4 text-green-600" />;
    default:
      return <Info className="h-4 w-4 text-gray-600" />;
  }
};

const LLMFindingItem: React.FC<LLMFindingItemProps> = ({ finding }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getBgColor = (type: string) => {
    switch (type) {
      case 'critical':
        return 'bg-red-50 border-red-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'info':
        return 'bg-blue-50 border-blue-200';
      case 'success':
        return 'bg-green-50 border-green-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className={`border rounded-lg p-3 ${getBgColor(finding.type)} finding-${finding.type}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-2 flex-1">
          {getFindingIcon(finding.type)}
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-gray-900">{finding.message}</p>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-500">
                  {finding.confidence}% confidence
                </span>
                {(finding.evidence || finding.suggestion) && (
                  <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                  </button>
                )}
              </div>
            </div>
            {finding.field && (
              <p className="text-xs text-gray-600 mt-1">Field: {finding.field}</p>
            )}
            {isExpanded && (
              <div className="mt-3 space-y-2">
                {finding.suggestion && (
                  <div className="p-2 bg-white rounded border">
                    <p className="text-xs font-medium text-gray-700">Suggestion:</p>
                    <p className="text-xs text-gray-600">{finding.suggestion}</p>
                  </div>
                )}
                {finding.evidence && finding.evidence.length > 0 && (
                  <div className="p-2 bg-white rounded border">
                    <p className="text-xs font-medium text-gray-700">Evidence:</p>
                    <ul className="text-xs text-gray-600 mt-1 space-y-1">
                      {finding.evidence.map((item, index) => (
                        <li key={index} className="flex items-start space-x-1">
                          <span>•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const LLMFunctionCard: React.FC<LLMFunctionCardProps> = ({
  func,
  result,
  progress,
  onExpand,
  isExpanded
}) => {
  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  };

  return (
    <Card className="p-4 llm-card">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start space-x-3 flex-1">
          <div className={`p-2 rounded-lg border ${getCategoryColor(func.category)}`}>
            {getCategoryIcon(func.category)}
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-sm font-medium text-gray-900">{func.name}</h3>
              <div className="flex items-center space-x-2">
                {result && (
                  <div className="flex items-center space-x-1">
                    {getStatusIcon(result.status)}
                    {result.confidence > 0 && (
                      <span className="text-xs text-gray-600">
                        {result.confidence}%
                      </span>
                    )}
                  </div>
                )}
                <button
                  onClick={() => onExpand(func.id)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </button>
              </div>
            </div>
            <p className="text-xs text-gray-600 mb-2">{func.description}</p>

            {/* Progress Bar */}
            {progress && result?.status === 'running' && (
              <div className="mb-2">
                <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                  <span className="llm-thinking">{progress.currentStep}</span>
                  <span>{progress.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className="confidence-progress h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${progress.progress}%` }}
                  />
                </div>
                {progress.estimatedRemaining > 0 && (
                  <p className="text-xs text-gray-500 mt-1">
                    ~{formatDuration(progress.estimatedRemaining)} remaining
                  </p>
                )}
              </div>
            )}

            {/* Status indicators */}
            <div className="flex items-center space-x-4 text-xs text-gray-500">
              <div className="flex items-center space-x-1">
                <Timer className="h-3 w-3" />
                <span>~{formatDuration(func.estimatedTime)}</span>
              </div>
              <div className="flex items-center space-x-1">
                <span className={`px-2 py-1 rounded-full text-xs ${
                  func.priority === 'high' ? 'bg-red-100 text-red-700' :
                  func.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {func.priority}
                </span>
              </div>
              {result?.executionTime && (
                <div className="flex items-center space-x-1">
                  <Zap className="h-3 w-3" />
                  <span>{formatDuration(result.executionTime)}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-gray-200 pt-3 mt-3">
          {result?.reasoning && (
            <div className="mb-4">
              <h4 className="text-xs font-medium text-gray-700 mb-2">LLM Reasoning:</h4>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-700 leading-relaxed">{result.reasoning}</p>
              </div>
            </div>
          )}

          {result?.findings && result.findings.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-gray-700 mb-2">
                Findings ({result.findings.length})
              </h4>
              <div className="space-y-2">
                {result.findings.map((finding) => (
                  <LLMFindingItem key={finding.id} finding={finding} />
                ))}
              </div>
            </div>
          )}

          {result?.error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <XCircle className="h-4 w-4 text-red-600" />
                <p className="text-xs font-medium text-red-700">Validation Error</p>
              </div>
              <p className="text-xs text-red-600 mt-1">{result.error}</p>
            </div>
          )}
        </div>
      )}
    </Card>
  );
};

export const LLMValidationPanel: React.FC<LLMValidationPanelProps> = ({
  fileData,
  onValidationComplete,
  className = ''
}) => {
  const [isRunning, setIsRunning] = useState(false);
  const [expandedFunctions, setExpandedFunctions] = useState<Set<string>>(new Set());
  const [validationFunctions] = useState<LLMValidationFunction[]>([
    {
      id: 'clinical-accuracy',
      name: 'Clinical Data Accuracy',
      description: 'Validates medical codes, procedures, and clinical consistency',
      category: 'clinical',
      priority: 'high',
      estimatedTime: 45
    },
    {
      id: 'administrative-compliance',
      name: 'Administrative Compliance',
      description: 'Checks policy compliance, authorization requirements, and documentation',
      category: 'administrative',
      priority: 'high',
      estimatedTime: 30
    },
    {
      id: 'data-quality',
      name: 'Data Quality Assessment',
      description: 'Analyzes completeness, consistency, and accuracy of submitted data',
      category: 'quality',
      priority: 'medium',
      estimatedTime: 25
    },
    {
      id: 'fraud-detection',
      name: 'Fraud Risk Analysis',
      description: 'Identifies potential fraud patterns and anomalies in claims data',
      category: 'compliance',
      priority: 'high',
      estimatedTime: 60
    },
    {
      id: 'cost-optimization',
      name: 'Cost Optimization Review',
      description: 'Suggests cost-effective alternatives and identifies savings opportunities',
      category: 'administrative',
      priority: 'medium',
      estimatedTime: 35
    }
  ]);

  const [results, setResults] = useState<Map<string, LLMValidationResult>>(new Map());
  const [progress, setProgress] = useState<Map<string, LLMValidationProgress>>(new Map());
  const [summary, setSummary] = useState<LLMValidationSummary | null>(null);

  const toggleExpansion = useCallback((functionId: string) => {
    setExpandedFunctions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(functionId)) {
        newSet.delete(functionId);
      } else {
        newSet.add(functionId);
      }
      return newSet;
    });
  }, []);

  const startValidation = async () => {
    if (!fileData) return;

    setIsRunning(true);

    // Initialize all functions as pending
    const initialResults = new Map<string, LLMValidationResult>();
    validationFunctions.forEach(func => {
      initialResults.set(func.id, {
        functionId: func.id,
        status: 'pending',
        confidence: 0,
        findings: [],
        reasoning: ''
      });
    });
    setResults(initialResults);

    // Simulate parallel execution with WebSocket-like updates
    const simulateValidation = async (func: LLMValidationFunction) => {
      // Update status to running
      setResults(prev => {
        const newResults = new Map(prev);
        newResults.set(func.id, {
          ...newResults.get(func.id)!,
          status: 'running',
          startTime: new Date()
        });
        return newResults;
      });

      // Simulate progress updates
      const steps = [
        'Analyzing data structure...',
        'Validating business rules...',
        'Checking compliance requirements...',
        'Generating insights...',
        'Finalizing results...'
      ];

      for (let i = 0; i < steps.length; i++) {
        await new Promise(resolve => setTimeout(resolve, (func.estimatedTime * 1000) / steps.length));

        setProgress(prev => {
          const newProgress = new Map(prev);
          newProgress.set(func.id, {
            functionId: func.id,
            progress: ((i + 1) / steps.length) * 100,
            currentStep: steps[i],
            estimatedRemaining: func.estimatedTime * (steps.length - i - 1) / steps.length
          });
          return newProgress;
        });
      }

      // Simulate completion with mock results
      const mockResult: LLMValidationResult = {
        functionId: func.id,
        status: Math.random() > 0.1 ? 'completed' : 'failed',
        startTime: new Date(Date.now() - func.estimatedTime * 1000),
        endTime: new Date(),
        confidence: Math.floor(Math.random() * 30) + 70,
        executionTime: func.estimatedTime + Math.floor(Math.random() * 10) - 5,
        reasoning: `This validation analyzed ${func.description.toLowerCase()} using advanced LLM reasoning. The system examined patterns, cross-referenced with medical databases, and applied regulatory guidelines to provide comprehensive insights.`,
        findings: Array.from({ length: Math.floor(Math.random() * 4) + 1 }, (_, i) => ({
          id: `${func.id}-finding-${i}`,
          type: ['critical', 'warning', 'info', 'success'][Math.floor(Math.random() * 4)] as any,
          category: func.category,
          message: `Finding ${i + 1} for ${func.name}: Sample validation result`,
          confidence: Math.floor(Math.random() * 30) + 70,
          suggestion: Math.random() > 0.5 ? 'Consider reviewing this field for accuracy' : undefined,
          evidence: Math.random() > 0.7 ? ['Supporting evidence item 1', 'Supporting evidence item 2'] : undefined
        }))
      };

      if (mockResult.status === 'failed') {
        mockResult.error = 'Validation failed due to insufficient data quality';
      }

      setResults(prev => {
        const newResults = new Map(prev);
        newResults.set(func.id, mockResult);
        return newResults;
      });

      setProgress(prev => {
        const newProgress = new Map(prev);
        newProgress.delete(func.id);
        return newProgress;
      });
    };

    // Run all validations in parallel
    await Promise.all(validationFunctions.map(simulateValidation));

    setIsRunning(false);

    // Update summary
    const completedResults = Array.from(results.values()).filter(r => r.status === 'completed');
    setSummary({
      totalFunctions: validationFunctions.length,
      completedFunctions: completedResults.length,
      failedFunctions: validationFunctions.length - completedResults.length,
      averageConfidence: completedResults.reduce((sum, r) => sum + r.confidence, 0) / completedResults.length || 0,
      totalFindings: completedResults.reduce((sum, r) => sum + r.findings.length, 0),
      criticalFindings: completedResults.reduce((sum, r) => sum + r.findings.filter(f => f.type === 'critical').length, 0),
      warningFindings: completedResults.reduce((sum, r) => sum + r.findings.filter(f => f.type === 'warning').length, 0),
      estimatedTimeRemaining: 0,
      overallStatus: 'completed'
    });

    if (onValidationComplete) {
      onValidationComplete(Array.from(results.values()));
    }
  };

  const stopValidation = () => {
    setIsRunning(false);
    setProgress(new Map());
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Brain className="h-6 w-6 text-purple-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">LLM Validation & Analysis</h2>
            <p className="text-sm text-gray-600">AI-powered healthcare data validation and insights</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {isRunning ? (
            <Button
              variant="secondary"
              onClick={stopValidation}
              className="flex items-center space-x-2"
            >
              <Pause className="h-4 w-4" />
              <span>Stop</span>
            </Button>
          ) : (
            <Button
              variant="primary"
              onClick={startValidation}
              disabled={!fileData}
              className="flex items-center space-x-2"
            >
              <Play className="h-4 w-4" />
              <span>Start Validation</span>
            </Button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">Overall Confidence</p>
                <p className="text-2xl font-bold text-gray-900">{summary.averageConfidence.toFixed(1)}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-600" />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">Functions Completed</p>
                <p className="text-2xl font-bold text-gray-900">{summary.completedFunctions}/{summary.totalFunctions}</p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-blue-600" />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">Critical Findings</p>
                <p className="text-2xl font-bold text-gray-900">{summary.criticalFindings}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">Total Findings</p>
                <p className="text-2xl font-bold text-gray-900">{summary.totalFindings}</p>
              </div>
              <FileText className="h-8 w-8 text-purple-600" />
            </div>
          </Card>
        </div>
      )}

      {/* Validation Functions */}
      <div className="space-y-4">
        <h3 className="text-md font-medium text-gray-900">Validation Functions</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {validationFunctions.map((func) => (
            <LLMFunctionCard
              key={func.id}
              func={func}
              result={results.get(func.id)}
              progress={progress.get(func.id)}
              onExpand={toggleExpansion}
              isExpanded={expandedFunctions.has(func.id)}
            />
          ))}
        </div>
      </div>

      {/* No file data state */}
      {!fileData && (
        <Card className="p-8 text-center">
          <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Data to Validate</h3>
          <p className="text-gray-600">Upload a healthcare file to begin LLM-powered validation and analysis.</p>
        </Card>
      )}
    </div>
  );
};
