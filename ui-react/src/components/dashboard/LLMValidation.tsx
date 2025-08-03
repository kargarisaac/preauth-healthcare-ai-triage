import React from 'react';
import {
  Brain,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Info,
  TrendingUp,
  FileText,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import Card from '../ui/Card';

interface LLMValidationResult {
  overall_quality_score: number;
  confidence_score: number;
  validation_passed: boolean;
  critical_issues: number;
  warning_issues: number;
  info_issues: number;
  total_issues: number;
  top_issues: string[];
  recommendations: string[];
  processing_time_ms: number;
  model_used: string;
  reasoning?: string;
  grade: string;
}

interface LLMValidationProps {
  validationResult: LLMValidationResult;
  className?: string;
}

interface LLMValidationToggleProps {
  enabled: boolean;
  onChange: (enabled: boolean) => void;
  disabled?: boolean;
  className?: string;
}

export const LLMValidationToggle: React.FC<LLMValidationToggleProps> = ({
  enabled,
  onChange,
  disabled = false,
  className = ''
}) => {
  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      <div className="flex items-center space-x-2">
        <label className="flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => onChange(e.target.checked)}
            disabled={disabled}
            className="sr-only"
          />
          <div className={`relative w-11 h-6 rounded-full transition-colors ${
            enabled
              ? 'bg-blue-600'
              : 'bg-gray-200'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}>
            <div className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
              enabled ? 'translate-x-5' : 'translate-x-0'
            }`} />
          </div>
        </label>
        <div className="flex items-center space-x-2">
          <Brain className={`h-4 w-4 ${enabled ? 'text-blue-600' : 'text-gray-400'}`} />
          <span className={`text-sm font-medium ${enabled ? 'text-gray-900' : 'text-gray-500'}`}>
            AI Validation
          </span>
        </div>
      </div>
      {enabled && (
        <span className="text-xs text-gray-500 bg-blue-50 px-2 py-1 rounded-full">
          +$0.10 per file
        </span>
      )}
    </div>
  );
};

export const LLMValidationResultDisplay: React.FC<LLMValidationProps> = ({
  validationResult,
  className = ''
}) => {
  const [expanded, setExpanded] = React.useState(false);

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A':
        return 'text-green-700 bg-green-100 border-green-200';
      case 'B':
        return 'text-blue-700 bg-blue-100 border-blue-200';
      case 'C':
        return 'text-yellow-700 bg-yellow-100 border-yellow-200';
      case 'D':
        return 'text-orange-700 bg-orange-100 border-orange-200';
      case 'F':
        return 'text-red-700 bg-red-100 border-red-200';
      default:
        return 'text-gray-700 bg-gray-100 border-gray-200';
    }
  };

  const getStatusIcon = () => {
    if (validationResult.validation_passed) {
      return <CheckCircle2 className="h-5 w-5 text-green-600" />;
    } else {
      return <XCircle className="h-5 w-5 text-red-600" />;
    }
  };

  const getIssueIcon = (type: 'critical' | 'warning' | 'info') => {
    switch (type) {
      case 'critical':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'info':
        return <Info className="h-4 w-4 text-blue-600" />;
    }
  };

  return (
    <Card className={`p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Brain className="h-5 w-5 text-purple-600" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900">AI Validation Results</h3>
            <p className="text-xs text-gray-600">
              Processed in {validationResult.processing_time_ms}ms using {validationResult.model_used}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <div className={`px-3 py-1 rounded-full border text-sm font-bold ${getGradeColor(validationResult.grade)}`}>
            Grade {validationResult.grade}
          </div>
        </div>
      </div>

      {/* Quality Score */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Overall Quality Score</span>
          <span className="text-sm font-bold text-gray-900">
            {(validationResult.overall_quality_score * 100).toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              validationResult.overall_quality_score >= 0.8
                ? 'bg-green-500'
                : validationResult.overall_quality_score >= 0.6
                ? 'bg-yellow-500'
                : 'bg-red-500'
            }`}
            style={{ width: `${validationResult.overall_quality_score * 100}%` }}
          />
        </div>
      </div>

      {/* Issues Summary */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center p-3 bg-red-50 rounded-lg border border-red-100">
          <div className="flex items-center justify-center mb-1">
            {getIssueIcon('critical')}
          </div>
          <div className="text-lg font-bold text-red-700">{validationResult.critical_issues}</div>
          <div className="text-xs text-red-600">Critical</div>
        </div>

        <div className="text-center p-3 bg-yellow-50 rounded-lg border border-yellow-100">
          <div className="flex items-center justify-center mb-1">
            {getIssueIcon('warning')}
          </div>
          <div className="text-lg font-bold text-yellow-700">{validationResult.warning_issues}</div>
          <div className="text-xs text-yellow-600">Warnings</div>
        </div>

        <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-100">
          <div className="flex items-center justify-center mb-1">
            {getIssueIcon('info')}
          </div>
          <div className="text-lg font-bold text-blue-700">{validationResult.info_issues}</div>
          <div className="text-xs text-blue-600">Info</div>
        </div>
      </div>

      {/* Top Issues (if any) */}
      {validationResult.top_issues.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Key Issues Found</h4>
          <div className="space-y-2">
            {validationResult.top_issues.slice(0, 3).map((issue, index) => (
              <div key={index} className="flex items-start space-x-2 p-2 bg-gray-50 rounded border">
                <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                <span className="text-xs text-gray-700">{issue}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {validationResult.recommendations.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Recommendations</h4>
          <div className="space-y-2">
            {validationResult.recommendations.slice(0, 3).map((rec, index) => (
              <div key={index} className="flex items-start space-x-2 p-2 bg-green-50 rounded border border-green-100">
                <TrendingUp className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                <span className="text-xs text-gray-700">{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Expandable Details */}
      {validationResult.reasoning && (
        <div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
          >
            {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            <span>AI Analysis Details</span>
          </button>

          {expanded && (
            <div className="mt-3 p-3 bg-gray-50 rounded border">
              <div className="mb-3">
                <h5 className="text-xs font-medium text-gray-700 mb-1">AI Confidence Score</h5>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-purple-500 h-1.5 rounded-full transition-all duration-300"
                      style={{ width: `${validationResult.confidence_score * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-600">
                    {(validationResult.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              <div>
                <h5 className="text-xs font-medium text-gray-700 mb-1">Analysis Reasoning</h5>
                <p className="text-xs text-gray-600 leading-relaxed">{validationResult.reasoning}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
};
