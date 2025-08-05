import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ProcessingStatus } from '../ProcessingStatus';

const mockProcessingSteps = [
  {
    id: 'upload',
    name: 'File Upload',
    status: 'completed' as const,
    timestamp: new Date('2025-08-04T10:00:00Z'),
    duration: 2.5,
  },
  {
    id: 'validation',
    name: 'XML Validation',
    status: 'completed' as const,
    timestamp: new Date('2025-08-04T10:00:05Z'),
    duration: 1.2,
  },
  {
    id: 'processing',
    name: 'FHIR Processing',
    status: 'in_progress' as const,
    timestamp: new Date('2025-08-04T10:00:10Z'),
    progress: 65,
  },
  {
    id: 'analysis',
    name: 'Claude Analysis',
    status: 'pending' as const,
  },
  {
    id: 'completion',
    name: 'Finalization',
    status: 'pending' as const,
  },
];

describe('ProcessingStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all processing steps', () => {
    render(<ProcessingStatus steps={mockProcessingSteps} />);
    
    expect(screen.getByText('File Upload')).toBeInTheDocument();
    expect(screen.getByText('XML Validation')).toBeInTheDocument();
    expect(screen.getByText('FHIR Processing')).toBeInTheDocument();
    expect(screen.getByText('Claude Analysis')).toBeInTheDocument();
    expect(screen.getByText('Finalization')).toBeInTheDocument();
  });

  it('displays correct status indicators', () => {
    render(<ProcessingStatus steps={mockProcessingSteps} />);
    
    // Completed steps should have checkmarks
    const uploadStep = screen.getByTestId('step-upload');
    expect(uploadStep).toContainElement(screen.getByTestId('check-icon'));
    
    const validationStep = screen.getByTestId('step-validation');
    expect(validationStep).toContainElement(screen.getByTestId('check-icon'));
    
    // In-progress step should have spinner
    const processingStep = screen.getByTestId('step-processing');
    expect(processingStep).toContainElement(screen.getByTestId('spinner-icon'));
    
    // Pending steps should have clock icons
    const analysisStep = screen.getByTestId('step-analysis');
    expect(analysisStep).toContainElement(screen.getByTestId('clock-icon'));
  });

  it('shows progress percentage for in-progress steps', () => {
    render(<ProcessingStatus steps={mockProcessingSteps} />);
    
    expect(screen.getByText('65%')).toBeInTheDocument();
  });

  it('displays duration for completed steps', () => {
    render(<ProcessingStatus steps={mockProcessingSteps} />);
    
    expect(screen.getByText('2.5s')).toBeInTheDocument();
    expect(screen.getByText('1.2s')).toBeInTheDocument();
  });

  it('shows timestamps when enabled', () => {
    render(<ProcessingStatus steps={mockProcessingSteps} showTimestamps />);
    
    expect(screen.getByText('10:00:00')).toBeInTheDocument();
    expect(screen.getByText('10:00:05')).toBeInTheDocument();
    expect(screen.getByText('10:00:10')).toBeInTheDocument();
  });

  it('handles error states correctly', () => {
    const stepsWithError = [
      ...mockProcessingSteps.slice(0, 2),
      {
        id: 'processing',
        name: 'FHIR Processing',
        status: 'error' as const,
        timestamp: new Date('2025-08-04T10:00:10Z'),
        error: 'Invalid XML format at line 45',
      },
      ...mockProcessingSteps.slice(3),
    ];
    
    render(<ProcessingStatus steps={stepsWithError} />);
    
    const errorStep = screen.getByTestId('step-processing');
    expect(errorStep).toContainElement(screen.getByTestId('error-icon'));
    expect(screen.getByText('Invalid XML format at line 45')).toBeInTheDocument();
  });

  it('calculates overall progress correctly', () => {
    render(<ProcessingStatus steps={mockProcessingSteps} showOverallProgress />);
    
    // 2 completed + 1 partially complete (65%) out of 5 total
    // (2 + 0.65) / 5 = 0.53 = 53%
    expect(screen.getByText('Overall Progress: 53%')).toBeInTheDocument();
  });

  it('supports expandable step details', () => {
    const stepsWithDetails = mockProcessingSteps.map(step => ({
      ...step,
      details: step.id === 'processing' ? [
        'Parsing XML structure',
        'Extracting FHIR resources',
        'Validating medical codes',
      ] : undefined,
    }));
    
    render(<ProcessingStatus steps={stepsWithDetails} expandable />);
    
    const processingStep = screen.getByTestId('step-processing');
    const expandButton = processingStep.querySelector('[data-testid="expand-button"]');
    
    expect(expandButton).toBeInTheDocument();
    
    fireEvent.click(expandButton!);
    
    expect(screen.getByText('Parsing XML structure')).toBeInTheDocument();
    expect(screen.getByText('Extracting FHIR resources')).toBeInTheDocument();
    expect(screen.getByText('Validating medical codes')).toBeInTheDocument();
  });

  it('shows estimated time remaining', () => {
    const stepsWithEstimates = mockProcessingSteps.map(step => ({
      ...step,
      estimatedDuration: step.status === 'pending' ? 30 : undefined,
    }));
    
    render(<ProcessingStatus steps={stepsWithEstimates} showEstimates />);
    
    expect(screen.getByText('Est. 60s remaining')).toBeInTheDocument(); // 2 pending steps × 30s
  });

  it('handles real-time updates', async () => {
    const { rerender } = render(<ProcessingStatus steps={mockProcessingSteps} />);
    
    expect(screen.getByText('65%')).toBeInTheDocument();
    
    // Update progress
    const updatedSteps = mockProcessingSteps.map(step => 
      step.id === 'processing' 
        ? { ...step, progress: 85 }
        : step
    );
    
    rerender(<ProcessingStatus steps={updatedSteps} />);
    
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  it('displays retry button for failed steps', () => {
    const stepsWithRetry = mockProcessingSteps.map(step => 
      step.id === 'processing'
        ? { ...step, status: 'error' as const, error: 'Network timeout', canRetry: true }
        : step
    );
    
    const mockOnRetry = vi.fn();
    
    render(<ProcessingStatus steps={stepsWithRetry} onRetry={mockOnRetry} />);
    
    const retryButton = screen.getByText('Retry');
    expect(retryButton).toBeInTheDocument();
    
    fireEvent.click(retryButton);
    expect(mockOnRetry).toHaveBeenCalledWith('processing');
  });

  it('shows compact mode correctly', () => {
    render(<ProcessingStatus steps={mockProcessingSteps} compact />);
    
    // In compact mode, should show fewer details
    expect(screen.queryByText('2.5s')).not.toBeInTheDocument();
    expect(screen.queryByText('1.2s')).not.toBeInTheDocument();
    
    // But should still show main status
    expect(screen.getByText('65%')).toBeInTheDocument();
  });

  it('handles cancellation', () => {
    const mockOnCancel = vi.fn();
    
    render(<ProcessingStatus steps={mockProcessingSteps} onCancel={mockOnCancel} cancellable />);
    
    const cancelButton = screen.getByText('Cancel Processing');
    expect(cancelButton).toBeInTheDocument();
    
    fireEvent.click(cancelButton);
    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('displays step dependencies correctly', () => {
    const stepsWithDependencies = mockProcessingSteps.map((step, index) => ({
      ...step,
      dependsOn: index > 0 ? [mockProcessingSteps[index - 1].id] : undefined,
    }));
    
    render(<ProcessingStatus steps={stepsWithDependencies} showDependencies />);
    
    // Should show connecting lines between dependent steps
    const connections = screen.getAllByTestId('step-connection');
    expect(connections).toHaveLength(4); // 4 connections between 5 steps
  });

  it('supports dark mode styling', () => {
    render(<ProcessingStatus steps={mockProcessingSteps} theme="dark" />);
    
    const container = screen.getByTestId('processing-status-container');
    expect(container).toHaveClass('dark:bg-gray-800');
  });

  it('shows success state when all steps complete', () => {
    const completedSteps = mockProcessingSteps.map(step => ({
      ...step,
      status: 'completed' as const,
      timestamp: new Date(),
      duration: Math.random() * 5,
    }));
    
    render(<ProcessingStatus steps={completedSteps} />);
    
    expect(screen.getByText('Processing Complete!')).toBeInTheDocument();
    expect(screen.getByTestId('success-icon')).toBeInTheDocument();
  });

  it('calculates total processing time', () => {
    const completedSteps = mockProcessingSteps.map((step, index) => ({
      ...step,
      status: 'completed' as const,
      timestamp: new Date(`2025-08-04T10:00:${index * 10}Z`),
      duration: 2.0,
    }));
    
    render(<ProcessingStatus steps={completedSteps} showTotalTime />);
    
    expect(screen.getByText(/Total time: \d+\.\ds/)).toBeInTheDocument();
  });

  it('handles empty steps array', () => {
    render(<ProcessingStatus steps={[]} />);
    
    expect(screen.getByText('No processing steps available')).toBeInTheDocument();
  });

  it('supports custom step icons', () => {
    const stepsWithCustomIcons = mockProcessingSteps.map(step => ({
      ...step,
      icon: step.id === 'upload' ? 'upload-cloud' : undefined,
    }));
    
    render(<ProcessingStatus steps={stepsWithCustomIcons} />);
    
    expect(screen.getByTestId('upload-cloud-icon')).toBeInTheDocument();
  });

  it('provides accessibility support', () => {
    render(<ProcessingStatus steps={mockProcessingSteps} />);
    
    // Should have proper ARIA labels
    const processingStep = screen.getByTestId('step-processing');
    expect(processingStep).toHaveAttribute('aria-label', expect.stringContaining('FHIR Processing'));
    
    // Progress should be announced to screen readers
    expect(processingStep).toHaveAttribute('aria-valuenow', '65');
    expect(processingStep).toHaveAttribute('aria-valuemin', '0');
    expect(processingStep).toHaveAttribute('aria-valuemax', '100');
  });
});
