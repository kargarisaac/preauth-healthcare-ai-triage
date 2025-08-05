import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, CheckCircle, AlertCircle } from 'lucide-react';
import Button from '@/components/ui/Button';
import Breadcrumbs, { type BreadcrumbItem } from '@/components/ui/Breadcrumbs';
import PatientSelector from '@/components/dashboard/PatientSelector';
import FileUploadArea from '@/components/dashboard/FileUploadArea';
import ProcessingStatus from '@/components/dashboard/ProcessingStatus';
import { usePatient } from '@/contexts/PatientContext';
import { useToast } from '@/contexts/ToastContext';
import type { PatientUploadResponse, ProcessingStep, PatientProcessingStatus as ProcessingStatusType } from '@/types/api';

const PatientFileUploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const { 
    selectedPatient, 
    patientsList, 
    isLoading, 
    error, 
    selectPatient, 
    fetchPatients 
  } = usePatient();

  const [currentStep, setCurrentStep] = useState<'select-patient' | 'upload-file' | 'processing'>('select-patient');
  const [processingStep, setProcessingStep] = useState<ProcessingStep>('upload');
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatusType>('idle');
  const [processingProgress, setProcessingProgress] = useState(0);
  const [processingError, setProcessingError] = useState<string | null>(null);

  // Fetch patients on component mount
  useEffect(() => {
    if (patientsList.length === 0) {
      fetchPatients();
    }
  }, [fetchPatients, patientsList.length]);

  // Navigate to next step when patient is selected
  useEffect(() => {
    if (selectedPatient && currentStep === 'select-patient') {
      setCurrentStep('upload-file');
    }
  }, [selectedPatient, currentStep]);

  const breadcrumbItems: BreadcrumbItem[] = [
    { id: 'dashboard', label: 'Dashboard', href: '/dashboard' },
    { id: 'upload', label: 'Upload File', isActive: true }
  ];

  const handlePatientSelect = (patient: any) => {
    selectPatient(patient);
    setCurrentStep('upload-file');
  };

  const handleBackToPatientSelection = () => {
    setCurrentStep('select-patient');
    selectPatient(null);
    setProcessingStatus('idle');
    setProcessingProgress(0);
    setProcessingError(null);
  };

  const handleUploadComplete = async (response: PatientUploadResponse) => {
    if (response.success) {
      setCurrentStep('processing');
      setProcessingStep('process');
      setProcessingStatus('loading');
      setProcessingProgress(0);

      // Simulate processing steps
      const processSteps = [
        { step: 'process' as ProcessingStep, duration: 2000 },
        { step: 'analyze' as ProcessingStep, duration: 3000 }
      ];

      try {
        for (const { step, duration } of processSteps) {
          setProcessingStep(step);
          setProcessingProgress(0);
          
          // Simulate progress
          const progressInterval = setInterval(() => {
            setProcessingProgress(prev => Math.min(prev + 10, 100));
          }, duration / 10);

          await new Promise(resolve => setTimeout(resolve, duration));
          clearInterval(progressInterval);
          setProcessingProgress(100);
          
          // Small delay between steps
          await new Promise(resolve => setTimeout(resolve, 500));
        }

        setProcessingStatus('success');
        
        showToast({
          type: 'success',
          title: 'Processing Complete',
          message: `File processed successfully for ${selectedPatient?.full_name}`,
        });

        // Auto-redirect to patient dashboard after success
        setTimeout(() => {
          navigate(`/dashboard/patients/${selectedPatient?.id}`);
        }, 2000);

      } catch (error) {
        setProcessingStatus('error');
        setProcessingError('Processing failed. Please try again.');
        
        showToast({
          type: 'error',
          title: 'Processing Failed',
          message: 'There was an error processing your file.',
        });
      }
    } else {
      handleUploadError(response.error || 'Upload failed');
    }
  };

  const handleUploadError = (error: string) => {
    setProcessingStatus('error');
    setProcessingError(error);
    
    showToast({
      type: 'error',
      title: 'Upload Failed',
      message: error,
    });
  };

  const getStepIndicator = () => {
    const steps = [
      { id: 'select-patient', label: 'Select Patient', completed: !!selectedPatient },
      { id: 'upload-file', label: 'Upload File', completed: currentStep === 'processing' },
      { id: 'processing', label: 'Process & Analyze', completed: processingStatus === 'success' }
    ];

    return (
      <div className="flex items-center justify-center space-x-4 mb-8">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center">
            <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${
              step.completed 
                ? 'bg-green-100 border-green-500 text-green-700'
                : currentStep === step.id
                ? 'bg-blue-100 border-blue-500 text-blue-700'
                : 'bg-gray-100 border-gray-300 text-gray-500'
            }`}>
              {step.completed ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <span className="text-sm font-medium">{index + 1}</span>
              )}
            </div>
            <span className={`ml-2 text-sm font-medium ${
              step.completed || currentStep === step.id
                ? 'text-gray-900'
                : 'text-gray-500'
            }`}>
              {step.label}
            </span>
            {index < steps.length - 1 && (
              <ArrowRight className="w-4 h-4 mx-4 text-gray-400" />
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumbs */}
      <Breadcrumbs
        items={breadcrumbItems}
        onItemClick={(item) => {
          if (item.href) {
            navigate(item.href);
          }
        }}
      />

      {/* Page Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Patient File Upload
        </h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Upload and process XML healthcare files for specific patients. 
          Follow the simple 3-step process to get AI-powered insights and FHIR-compliant data.
        </p>
      </div>

      {/* Step Indicator */}
      {getStepIndicator()}

      {/* Step Content */}
      <div className="max-w-4xl mx-auto">
        {currentStep === 'select-patient' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Step 1: Select Patient
              </h2>
              <p className="text-gray-600">
                Choose the patient for whom you want to upload and process healthcare data.
              </p>
            </div>

            <PatientSelector
              patients={patientsList}
              selectedPatient={selectedPatient}
              onPatientSelect={handlePatientSelect}
              isLoading={isLoading}
              error={error}
              placeholder="Search and select a patient to continue..."
            />

            {selectedPatient && (
              <div className="mt-6 flex justify-end">
                <Button
                  variant="primary"
                  onClick={() => setCurrentStep('upload-file')}
                  className="flex items-center"
                >
                  Continue to Upload
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            )}
          </div>
        )}

        {currentStep === 'upload-file' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Step 2: Upload XML File
                </h2>
                <p className="text-gray-600">
                  Upload the XML healthcare file for {selectedPatient?.full_name}.
                </p>
              </div>
              <Button
                variant="tertiary"
                onClick={handleBackToPatientSelection}
                className="flex items-center"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Change Patient
              </Button>
            </div>

            <FileUploadArea
              selectedPatient={selectedPatient}
              onUploadComplete={handleUploadComplete}
              onUploadError={handleUploadError}
            />
          </div>
        )}

        {currentStep === 'processing' && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Step 3: Processing & Analysis
                </h2>
                <p className="text-gray-600">
                  Your file is being processed and analyzed. This may take a few moments.
                </p>
              </div>
              {processingStatus !== 'success' && (
                <Button
                  variant="tertiary"
                  onClick={handleBackToPatientSelection}
                  className="flex items-center"
                  disabled={processingStatus === 'loading'}
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Start Over
                </Button>
              )}
            </div>

            <ProcessingStatus
              processingStep={processingStep}
              progress={processingProgress}
              status={processingStatus}
              error={processingError}
            />

            {processingStatus === 'success' && (
              <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <div>
                    <p className="text-sm font-medium text-green-900">
                      Processing completed successfully!
                    </p>
                    <p className="text-xs text-green-700 mt-1">
                      Redirecting to patient dashboard...
                    </p>
                  </div>
                </div>
              </div>
            )}

            {processingStatus === 'error' && (
              <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="w-5 h-5 text-red-600" />
                  <div>
                    <p className="text-sm font-medium text-red-900">
                      Processing failed
                    </p>
                    <p className="text-xs text-red-700 mt-1">
                      {processingError}
                    </p>
                  </div>
                </div>
                <div className="mt-3 flex space-x-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setCurrentStep('upload-file')}
                  >
                    Try Again
                  </Button>
                  <Button
                    variant="tertiary"
                    size="sm"
                    onClick={handleBackToPatientSelection}
                  >
                    Start Over
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientFileUploadPage;