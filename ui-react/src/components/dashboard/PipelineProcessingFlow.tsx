import React, { useState, useCallback, useRef } from 'react';
import { clsx } from 'clsx';
import {
  Upload,
  FileText,
  Zap,
  CheckCircle,
  X,
  Loader2,
  Eye,
  Download,
  Clock,
  DollarSign,
  AlertTriangle,
  Target,
  FileCheck,
  Brain,
  Stethoscope,
  ClipboardList,
  Gavel,
  FileType,
  Play
} from 'lucide-react';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import { useToast } from '@/contexts/ToastContext';
import type { PipelineProcessResponse } from '@/types/api';
import PipelineResultsViewer from './PipelineResultsViewer';
import DossierViewer from './DossierViewer';

interface PipelineProcessingFlowProps {
  className?: string;
}

const pipelinePhases = [
  {
    id: 'intake',
    name: 'Data Intake',
    description: 'XML parsing and canonical mapping',
    icon: FileText,
    color: 'blue'
  },
  {
    id: 'clinical_summary',
    name: 'Clinical Summary',
    description: 'Medical data aggregation and FHIR conversion',
    icon: Stethoscope,
    color: 'green'
  },
  {
    id: 'evidence',
    name: 'Evidence Retrieval',
    description: 'Clinical guidelines and policy lookup',
    icon: Brain,
    color: 'purple'
  },
  {
    id: 'checklist',
    name: 'Policy Evaluation',
    description: 'Criteria assessment and compliance scoring',
    icon: ClipboardList,
    color: 'orange'
  },
  {
    id: 'decision',
    name: 'Decision Synthesis',
    description: 'Final authorization determination',
    icon: Gavel,
    color: 'red'
  },
  {
    id: 'dossier',
    name: 'Dossier Generation',
    description: 'Professional report compilation',
    icon: FileType,
    color: 'indigo'
  }
];

const PipelineProcessingFlow: React.FC<PipelineProcessingFlowProps> = ({ className }) => {
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [selectedFormat, setSelectedFormat] = useState<'auto' | 'eclaim' | 'shafafiya'>('auto');
  const [selectedMode, setSelectedMode] = useState<'deterministic' | 'hybrid' | 'agentic'>('hybrid');
  const [dragOver, setDragOver] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentPhase, setCurrentPhase] = useState<string>('');
  const [phaseProgress, setPhaseProgress] = useState<Record<string, boolean>>({});
  const [pipelineResults, setPipelineResults] = useState<PipelineProcessResponse | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [showDossier, setShowDossier] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { showToast } = useToast();

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const handleFileSelect = useCallback((file: File) => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (extension !== 'xml' && extension !== 'csv') {
      showToast({
        type: 'error',
        title: 'Invalid file type',
        message: 'Only XML and CSV files are supported'
      });
      return;
    }
    setCurrentFile(file);
    
    // Auto-detect format based on filename
    if (selectedFormat === 'auto') {
      const name = file.name.toLowerCase();
      if (name.includes('eclaim') || name.includes('dubai')) {
        setSelectedFormat('eclaim');
      } else if (name.includes('shafafiya') || name.includes('abudhabi')) {
        setSelectedFormat('shafafiya');
      }
    }
  }, [selectedFormat, showToast]);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const simulatePhaseProgress = useCallback((phases: string[]) => {
    let currentIndex = 0;
    
    const updatePhase = () => {
      if (currentIndex < phases.length) {
        const phase = phases[currentIndex];
        setCurrentPhase(phase);
        
        setTimeout(() => {
          setPhaseProgress(prev => ({ ...prev, [phase]: true }));
          currentIndex++;
          if (currentIndex < phases.length) {
            setTimeout(updatePhase, 800);
          } else {
            setCurrentPhase('');
          }
        }, 1500);
      }
    };
    
    updatePhase();
  }, []);

  const handleProcess = useCallback(async () => {
    if (!currentFile) return;

    setIsProcessing(true);
    setPhaseProgress({});
    setCurrentPhase('');
    setPipelineResults(null);

    try {
      const formData = new FormData();
      formData.append('file', currentFile);
      formData.append('source', selectedFormat === 'auto' ? 'eclaim' : selectedFormat);
      formData.append('mode', selectedMode);

      // Start phase simulation
      simulatePhaseProgress(pipelinePhases.map(p => p.id));

      const response = await fetch('/api/pipeline/process', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `HTTP error! status: ${response.status}`);
      }

      const result: PipelineProcessResponse = await response.json();
      setPipelineResults(result);

      showToast({
        type: 'success',
        title: 'Pipeline Complete',
        message: `Processed in ${result.metadata.processing_time_seconds.toFixed(2)}s • Cost: $${result.metadata.cost_usd.toFixed(3)}`,
      });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Processing failed';
      showToast({
        type: 'error',
        title: 'Pipeline Failed',
        message: errorMessage,
      });
    } finally {
      setIsProcessing(false);
    }
  }, [currentFile, selectedFormat, selectedMode, simulatePhaseProgress, showToast]);

  const handleSampleProcess = useCallback(async (sampleType: 'diabetes' | 'osteoarthritis' | 'parkinsons') => {
    setIsProcessing(true);
    setPhaseProgress({});
    setCurrentPhase('');
    setPipelineResults(null);

    try {
      // Start phase simulation
      simulatePhaseProgress(pipelinePhases.map(p => p.id));

      const response = await fetch(`/api/process/sample/${sampleType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mode: selectedMode }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: PipelineProcessResponse = await response.json();
      setPipelineResults(result);

      showToast({
        type: 'success',
        title: 'Sample Processed',
        message: `${sampleType} sample processed successfully`,
      });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Processing failed';
      showToast({
        type: 'error',
        title: 'Processing Failed',
        message: errorMessage,
      });
    } finally {
      setIsProcessing(false);
    }
  }, [selectedMode, simulatePhaseProgress, showToast]);

  const getDecisionBadgeColor = (outcome: string) => {
    switch (outcome) {
      case 'APPROVE': return 'bg-green-100 text-green-800 border-green-200';
      case 'DENY': return 'bg-red-100 text-red-800 border-red-200';
      case 'REVIEW': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          AI-Powered Pre-Authorization Pipeline
        </h2>
        <p className="text-gray-600 max-w-3xl mx-auto">
          Upload healthcare data for intelligent processing through our 6-phase pipeline.
          From intake to decision, get comprehensive analysis with professional dossiers.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* File Upload Section */}
        <div className="lg:col-span-2 space-y-6">
          <Card title="Upload Healthcare Data" className="h-fit">
            <div className="space-y-4">
              {/* Drag & Drop Area */}
              <div
                className={clsx(
                  'border-2 border-dashed rounded-lg p-8 text-center transition-all cursor-pointer',
                  dragOver
                    ? 'border-blue-400 bg-blue-50'
                    : currentFile
                    ? 'border-green-300 bg-green-50'
                    : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
                )}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
              >
                {currentFile ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-center">
                      <FileText className="w-12 h-12 text-green-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">{currentFile.name}</p>
                      <p className="text-sm text-gray-600">
                        {formatFileSize(currentFile.size)} • Ready for pipeline processing
                      </p>
                    </div>
                    <Button
                      variant="tertiary"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        setCurrentFile(null);
                      }}
                    >
                      <X className="w-4 h-4 mr-2" />
                      Remove
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <Upload className="w-12 h-12 text-gray-400 mx-auto" />
                    <div>
                      <p className="text-lg font-medium text-gray-900">
                        Drop your healthcare file here
                      </p>
                      <p className="text-blue-600 hover:text-blue-700 cursor-pointer font-medium">
                        or click to browse
                      </p>
                    </div>
                    <p className="text-sm text-gray-500">
                      Supports XML (eClaimLink, Shafafiya) and CSV files up to 10MB
                    </p>
                  </div>
                )}
              </div>

              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".xml,.csv"
                onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])}
              />

              {/* Processing Options */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Format Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Source Format
                  </label>
                  <select
                    value={selectedFormat}
                    onChange={(e) => setSelectedFormat(e.target.value as any)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isProcessing}
                  >
                    <option value="auto">Auto-detect</option>
                    <option value="eclaim">eClaimLink (Dubai)</option>
                    <option value="shafafiya">Shafafiya (Abu Dhabi)</option>
                  </select>
                </div>

                {/* Processing Mode */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Processing Mode
                  </label>
                  <select
                    value={selectedMode}
                    onChange={(e) => setSelectedMode(e.target.value as any)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isProcessing}
                  >
                    <option value="deterministic">Deterministic ($0.00)</option>
                    <option value="hybrid">Hybrid (&lt; $0.10)</option>
                    <option value="agentic">Agentic (&lt; $0.25)</option>
                  </select>
                </div>
              </div>

              {/* Process Button */}
              <Button
                variant="primary"
                onClick={handleProcess}
                disabled={!currentFile || isProcessing}
                className="w-full"
                size="lg"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Processing Pipeline...
                  </>
                ) : (
                  <>
                    <Zap className="w-5 h-5 mr-2" />
                    Start Pipeline Processing
                  </>
                )}
              </Button>
            </div>
          </Card>

          {/* Pipeline Progress */}
          {isProcessing && (
            <Card title="Pipeline Progress" className="h-fit">
              <div className="space-y-4">
                {pipelinePhases.map((phase, index) => {
                  const isActive = currentPhase === phase.id;
                  const isCompleted = phaseProgress[phase.id];
                  const isUpcoming = !isActive && !isCompleted;

                  return (
                    <div key={phase.id} className="flex items-center space-x-4">
                      <div
                        className={clsx(
                          'w-10 h-10 rounded-full flex items-center justify-center border-2',
                          isCompleted
                            ? 'bg-green-100 border-green-500 text-green-700'
                            : isActive
                            ? 'bg-blue-100 border-blue-500 text-blue-700'
                            : 'bg-gray-100 border-gray-300 text-gray-500'
                        )}
                      >
                        {isCompleted ? (
                          <CheckCircle className="w-5 h-5" />
                        ) : isActive ? (
                          <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                          <phase.icon className="w-5 h-5" />
                        )}
                      </div>
                      <div className="flex-1">
                        <p className={clsx(
                          'font-medium',
                          isCompleted ? 'text-green-900' : isActive ? 'text-blue-900' : 'text-gray-600'
                        )}>
                          {phase.name}
                        </p>
                        <p className="text-sm text-gray-500">{phase.description}</p>
                      </div>
                      {isActive && (
                        <div className="text-sm text-blue-600 font-medium">Processing...</div>
                      )}
                      {isCompleted && (
                        <div className="text-sm text-green-600 font-medium">Complete</div>
                      )}
                    </div>
                  );
                })}
              </div>
            </Card>
          )}

          {/* Results Summary */}
          {pipelineResults && (
            <Card title="Pipeline Results" className="h-fit">
              <div className="space-y-4">
                {/* Decision Outcome */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <Gavel className="w-6 h-6 text-gray-600" />
                    <div>
                      <p className="font-medium text-gray-900">Authorization Decision</p>
                      <p className="text-sm text-gray-600">
                        Confidence: {(pipelineResults.decision.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                  <div className={clsx(
                    'px-3 py-1 rounded-full text-sm font-medium border',
                    getDecisionBadgeColor(pipelineResults.decision.outcome)
                  )}>
                    {pipelineResults.decision.outcome}
                  </div>
                </div>

                {/* Key Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <Clock className="w-5 h-5 text-blue-600 mx-auto mb-1" />
                    <p className="text-xs text-blue-600 font-medium">Processing Time</p>
                    <p className="text-lg font-bold text-blue-900">
                      {pipelineResults.metadata.processing_time_seconds.toFixed(1)}s
                    </p>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <DollarSign className="w-5 h-5 text-green-600 mx-auto mb-1" />
                    <p className="text-xs text-green-600 font-medium">Cost</p>
                    <p className="text-lg font-bold text-green-900">
                      ${pipelineResults.metadata.cost_usd.toFixed(3)}
                    </p>
                  </div>
                  <div className="text-center p-3 bg-purple-50 rounded-lg">
                    <Target className="w-5 h-5 text-purple-600 mx-auto mb-1" />
                    <p className="text-xs text-purple-600 font-medium">Compliance Score</p>
                    <p className="text-lg font-bold text-purple-900">
                      {(pipelineResults.checklist.compliance_score * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div className="text-center p-3 bg-orange-50 rounded-lg">
                    <FileCheck className="w-5 h-5 text-orange-600 mx-auto mb-1" />
                    <p className="text-xs text-orange-600 font-medium">Mode</p>
                    <p className="text-lg font-bold text-orange-900 capitalize">
                      {pipelineResults.metadata.mode}
                    </p>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex space-x-3">
                  <Button
                    variant="primary"
                    onClick={() => setShowResults(true)}
                    className="flex-1"
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    View Full Results
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => setShowDossier(true)}
                    className="flex-1"
                  >
                    <FileType className="w-4 h-4 mr-2" />
                    View Dossier
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>

        {/* Sample Files & Quick Actions */}
        <div className="space-y-6">
          <Card title="Sample Processing" className="h-fit">
            <div className="space-y-3">
              <p className="text-sm text-gray-600 mb-4">
                Test the pipeline with sample policy cases from our demo suite.
              </p>

              {[
                { id: 'diabetes', name: 'Diabetes Technology', policy: 'Patient_007', score: '100%' },
                { id: 'osteoarthritis', name: 'Knee Osteoarthritis', policy: 'Patient_005', score: '20%' },
                { id: 'parkinsons', name: 'Parkinson\'s DBS', policy: 'Patient_011', score: '18%' }
              ].map((sample) => (
                <div
                  key={sample.id}
                  className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:border-gray-300 hover:bg-gray-50 transition-all"
                >
                  <div className="flex-1">
                    <div className="font-medium text-sm text-gray-900">
                      {sample.name}
                    </div>
                    <div className="text-xs text-gray-600">
                      {sample.policy} • Expected: {sample.score}
                    </div>
                  </div>
                  <Button
                    variant="tertiary"
                    size="sm"
                    onClick={() => handleSampleProcess(sample.id as any)}
                    disabled={isProcessing}
                  >
                    <Play className="w-3 h-3" />
                  </Button>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Processing Modes" className="h-fit">
            <div className="space-y-3">
              <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                <h4 className="font-medium text-blue-900 text-sm">Deterministic</h4>
                <p className="text-xs text-blue-700">Policy rules only, $0 cost, fastest</p>
              </div>
              <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                <h4 className="font-medium text-green-900 text-sm">Hybrid (Recommended)</h4>
                <p className="text-xs text-green-700">Smart LLM routing, &lt;$0.10, balanced</p>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                <h4 className="font-medium text-purple-900 text-sm">Agentic</h4>
                <p className="text-xs text-purple-700">Full AI agents, &lt;$0.25, comprehensive</p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Results Modal */}
      {showResults && pipelineResults && (
        <PipelineResultsViewer
          isOpen={showResults}
          onClose={() => setShowResults(false)}
          results={pipelineResults}
        />
      )}

      {/* Dossier Modal */}
      {showDossier && pipelineResults && (
        <DossierViewer
          isOpen={showDossier}
          onClose={() => setShowDossier(false)}
          analysisId={pipelineResults.analysis_id}
          dossierData={pipelineResults.dossier}
        />
      )}
    </div>
  );
};

export default PipelineProcessingFlow;