import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Download,
  Brain,
  TrendingUp,
  AlertTriangle,
  DollarSign,
  FileText,
  Activity,
  CheckCircle,
  XCircle,
  Clock,
  User,
  Heart,
  Pill
} from 'lucide-react';
import { Card, Button, Badge, Accordion } from '../ui';
import type { PatientInfo } from '../../types/api';

interface AnalysisResults {
  id: string;
  patient_id: string;
  analysis_date: string;
  confidence_score: number;
  clinical_summary: {
    primary_diagnosis: string;
    secondary_conditions: string[];
    medications: string[];
    procedures: string[];
    risk_factors: string[];
  };
  risk_assessment: {
    overall_risk: 'low' | 'medium' | 'high' | 'critical';
    risk_score: number;
    risk_factors: Array<{
      factor: string;
      impact: 'low' | 'medium' | 'high';
      description: string;
    }>;
    recommendations: string[];
  };
  recommendations: Array<{
    category: 'clinical' | 'preventive' | 'lifestyle' | 'follow_up';
    priority: 'low' | 'medium' | 'high' | 'urgent';
    title: string;
    description: string;
    expected_outcome: string;
    timeframe: string;
  }>;
  cost_analysis: {
    estimated_total_cost: number;
    cost_breakdown: Array<{
      category: string;
      amount: number;
      percentage: number;
    }>;
    potential_savings: number;
    savings_opportunities: string[];
  };
  quality_metrics: {
    data_completeness: number;
    clinical_coherence: number;
    guideline_adherence: number;
    cost_effectiveness: number;
  };
  agent_insights: Array<{
    agent_name: string;
    specialty: string;
    findings: string[];
    recommendations: string[];
    confidence: number;
  }>;
}

interface AnalysisResultsViewerProps {
  analysisResults: AnalysisResults;
  patient: PatientInfo;
  onExport?: (format: 'pdf' | 'json' | 'csv') => void;
  className?: string;
}

const AnalysisResultsViewer: React.FC<AnalysisResultsViewerProps> = ({
  analysisResults,
  patient,
  onExport,
  className = ''
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['clinical_summary'])
  );

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-AE', {
      style: 'currency',
      currency: 'AED',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-AE', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const handleExport = (format: 'pdf' | 'json' | 'csv') => {
    onExport?.(format);
  };

  const SectionHeader: React.FC<{
    id: string;
    title: string;
    icon: React.ReactNode;
    badge?: React.ReactNode;
  }> = ({ id, title, icon, badge }) => (
    <button
      onClick={() => toggleSection(id)}
      className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors rounded-lg border border-gray-200"
    >
      <div className="flex items-center space-x-3">
        {icon}
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        {badge}
      </div>
      {expandedSections.has(id) ? (
        <ChevronUp className="h-5 w-5 text-gray-500" />
      ) : (
        <ChevronDown className="h-5 w-5 text-gray-500" />
      )}
    </button>
  );

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Analysis Header */}
      <Card className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
              <Brain className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Multi-Agent Analysis Results</h1>
              <p className="text-gray-600">Patient: {patient.full_name} (ID: {patient.id})</p>
              <p className="text-sm text-gray-500">
                Analysis completed on {formatDate(analysisResults.analysis_date)}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <Badge 
              variant={analysisResults.confidence_score >= 0.9 ? 'success' : 
                      analysisResults.confidence_score >= 0.7 ? 'warning' : 'error'}
            >
              {(analysisResults.confidence_score * 100).toFixed(1)}% Confidence
            </Badge>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleExport('pdf')}
            >
              <Download className="h-4 w-4 mr-2" />
              Export Report
            </Button>
          </div>
        </div>
      </Card>

      {/* Clinical Summary */}
      <div className="space-y-4">
        <SectionHeader
          id="clinical_summary"
          title="Clinical Summary"
          icon={<Heart className="h-5 w-5 text-red-500" />}
        />
        
        {expandedSections.has('clinical_summary') && (
          <Card className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold text-gray-900 mb-3">Primary Diagnosis</h4>
                <p className="text-gray-700 bg-blue-50 p-3 rounded-lg">
                  {analysisResults.clinical_summary.primary_diagnosis}
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-3">Risk Factors</h4>
                <div className="space-y-2">
                  {analysisResults.clinical_summary.risk_factors.map((factor, index) => (
                    <Badge key={index} variant="warning" size="sm">
                      {factor}
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-3">Secondary Conditions</h4>
                <ul className="space-y-1">
                  {analysisResults.clinical_summary.secondary_conditions.map((condition, index) => (
                    <li key={index} className="text-sm text-gray-600 flex items-center">
                      <div className="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
                      {condition}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-3">Current Medications</h4>
                <div className="space-y-1">
                  {analysisResults.clinical_summary.medications.map((medication, index) => (
                    <div key={index} className="flex items-center text-sm text-gray-600">
                      <Pill className="h-3 w-3 mr-2 text-blue-500" />
                      {medication}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* Risk Assessment */}
      <div className="space-y-4">
        <SectionHeader
          id="risk_assessment"
          title="Risk Assessment"
          icon={<AlertTriangle className="h-5 w-5 text-orange-500" />}
          badge={
            <Badge className={getRiskColor(analysisResults.risk_assessment.overall_risk)}>
              {analysisResults.risk_assessment.overall_risk.toUpperCase()} RISK
            </Badge>
          }
        />
        
        {expandedSections.has('risk_assessment') && (
          <Card className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1">
                <div className="text-center">
                  <div className="text-4xl font-bold text-gray-900 mb-2">
                    {analysisResults.risk_assessment.risk_score}/100
                  </div>
                  <p className="text-sm text-gray-600">Overall Risk Score</p>
                </div>
              </div>

              <div className="lg:col-span-2">
                <h4 className="font-semibold text-gray-900 mb-4">Risk Factors</h4>
                <div className="space-y-3">
                  {analysisResults.risk_assessment.risk_factors.map((risk, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="font-medium text-gray-900">{risk.factor}</h5>
                        <Badge variant={risk.impact === 'high' ? 'error' : risk.impact === 'medium' ? 'warning' : 'default'}>
                          {risk.impact} impact
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600">{risk.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-6">
              <h4 className="font-semibold text-gray-900 mb-3">Recommendations</h4>
              <ul className="space-y-2">
                {analysisResults.risk_assessment.recommendations.map((rec, index) => (
                  <li key={index} className="flex items-start text-sm text-gray-700">
                    <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          </Card>
        )}
      </div>

      {/* Recommendations */}
      <div className="space-y-4">
        <SectionHeader
          id="recommendations"
          title="Clinical Recommendations"
          icon={<FileText className="h-5 w-5 text-blue-500" />}
          badge={<Badge variant="info">{analysisResults.recommendations.length} items</Badge>}
        />
        
        {expandedSections.has('recommendations') && (
          <Card className="p-6">
            <div className="space-y-4">
              {analysisResults.recommendations.map((rec, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <Badge variant="default">{rec.category}</Badge>
                      <Badge className={getPriorityColor(rec.priority)}>
                        {rec.priority} priority
                      </Badge>
                    </div>
                    <span className="text-xs text-gray-500">{rec.timeframe}</span>
                  </div>
                  
                  <h4 className="font-semibold text-gray-900 mb-2">{rec.title}</h4>
                  <p className="text-sm text-gray-600 mb-3">{rec.description}</p>
                  
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="text-sm text-green-800">
                      <span className="font-medium">Expected Outcome:</span> {rec.expected_outcome}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* Cost Analysis */}
      <div className="space-y-4">
        <SectionHeader
          id="cost_analysis"
          title="Cost Analysis"
          icon={<DollarSign className="h-5 w-5 text-green-500" />}
          badge={
            <Badge variant="success">
              {formatCurrency(analysisResults.cost_analysis.potential_savings)} potential savings
            </Badge>
          }
        />
        
        {expandedSections.has('cost_analysis') && (
          <Card className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold text-gray-900 mb-4">Cost Breakdown</h4>
                <div className="space-y-3">
                  {analysisResults.cost_analysis.cost_breakdown.map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium text-gray-900">{item.category}</span>
                      <div className="text-right">
                        <div className="text-sm font-semibold text-gray-900">
                          {formatCurrency(item.amount)}
                        </div>
                        <div className="text-xs text-gray-500">{item.percentage}%</div>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-900">
                      {formatCurrency(analysisResults.cost_analysis.estimated_total_cost)}
                    </div>
                    <p className="text-sm text-blue-700">Estimated Total Cost</p>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-4">Savings Opportunities</h4>
                <ul className="space-y-2">
                  {analysisResults.cost_analysis.savings_opportunities.map((opportunity, index) => (
                    <li key={index} className="flex items-start text-sm text-gray-700">
                      <TrendingUp className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                      {opportunity}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* Agent Insights */}
      <div className="space-y-4">
        <SectionHeader
          id="agent_insights"
          title="Multi-Agent Insights"
          icon={<Brain className="h-5 w-5 text-purple-500" />}
          badge={<Badge variant="info">{analysisResults.agent_insights.length} agents</Badge>}
        />
        
        {expandedSections.has('agent_insights') && (
          <Card className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {analysisResults.agent_insights.map((agent, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="font-semibold text-gray-900">{agent.agent_name}</h4>
                      <p className="text-sm text-gray-600">{agent.specialty}</p>
                    </div>
                    <Badge variant={agent.confidence >= 0.8 ? 'success' : 'warning'}>
                      {(agent.confidence * 100).toFixed(0)}%
                    </Badge>
                  </div>
                  
                  <div className="space-y-3">
                    <div>
                      <h5 className="text-sm font-medium text-gray-700 mb-2">Key Findings</h5>
                      <ul className="space-y-1">
                        {agent.findings.map((finding, idx) => (
                          <li key={idx} className="text-xs text-gray-600 flex items-start">
                            <div className="w-1.5 h-1.5 bg-blue-400 rounded-full mr-2 mt-1.5 flex-shrink-0"></div>
                            {finding}
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    <div>
                      <h5 className="text-sm font-medium text-gray-700 mb-2">Recommendations</h5>
                      <ul className="space-y-1">
                        {agent.recommendations.map((rec, idx) => (
                          <li key={idx} className="text-xs text-gray-600 flex items-start">
                            <CheckCircle className="h-3 w-3 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* Export Actions */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Export this analysis report in different formats
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="secondary" size="sm" onClick={() => handleExport('json')}>
              JSON
            </Button>
            <Button variant="secondary" size="sm" onClick={() => handleExport('csv')}>
              CSV
            </Button>
            <Button variant="primary" size="sm" onClick={() => handleExport('pdf')}>
              PDF Report
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default AnalysisResultsViewer;