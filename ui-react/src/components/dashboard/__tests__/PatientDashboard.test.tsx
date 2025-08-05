import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { PatientDashboard } from '../PatientDashboard';
import { apiService } from '../../../services/apiService';

// Mock the API service
vi.mock('../../../services/apiService', () => ({
  apiService: {
    getPatientDashboard: vi.fn(),
    analyzePatient: vi.fn(),
  },
}));

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ patientId: 'patient-123' }),
    useNavigate: () => vi.fn(),
  };
});

const mockDashboardData = {
  patient_info: {
    patient_id: 'patient-123',
    folder_name: 'Ahmed_Al_Mansoori',
    folder_path: '/data/patients/1',
    has_profile: true,
    xml_files: 3,
    processed_json_files: 2,
  },
  recent_files: [
    {
      filename: 'diabetes_monitoring_2025.xml',
      upload_date: '2025-08-04T09:30:00Z',
      file_size: 15420,
      source: 'eclaim',
      processed: true,
      processed_date: '2025-08-04T09:32:15Z',
    },
    {
      filename: 'routine_checkup_2025.xml',
      upload_date: '2025-08-03T14:15:00Z',
      file_size: 12800,
      source: 'shafafiya',
      processed: true,
      processed_date: '2025-08-03T14:17:30Z',
    },
    {
      filename: 'prescription_refill_2025.xml',
      upload_date: '2025-08-01T11:45:00Z',
      file_size: 8950,
      source: 'eclaim',
      processed: false,
      processed_date: null,
    },
  ],
  analysis_history: [
    {
      id: 'analysis-001',
      timestamp: '2025-08-04T10:00:00Z',
      cost_usd: 0.75,
      confidence_score: 0.88,
      summary: 'Diabetes management analysis completed',
      recommendations: ['Approve HbA1c test', 'Schedule follow-up in 3 months'],
    },
    {
      id: 'analysis-002',
      timestamp: '2025-08-03T15:30:00Z',
      cost_usd: 0.42,
      confidence_score: 0.92,
      summary: 'Routine checkup analysis',
      recommendations: ['Continue current treatment', 'Monitor blood pressure'],
    },
  ],
  summary_stats: {
    total_xml_files: 3,
    total_processed_files: 2,
    total_historical_records: 15,
    processing_success_rate: 0.67,
    last_activity: '2025-08-04T09:30:00Z',
    has_profile: true,
    claude_analysis_available: true,
    patient_name: 'Ahmed Al Mansoori',
    insurance_company: 'Dubai Health Insurance',
    member_id: 'DH123456',
  },
};

const mockAnalysisResult = {
  success: true,
  patient_id: 'patient-123',
  analysis: {
    summary: 'Comprehensive diabetes management analysis',
    cost_usd: 1.25,
    agent_results: {
      clinical_analyzer: {
        findings: ['Type 2 diabetes confirmed', 'HbA1c monitoring required'],
      },
      recommendation_agent: {
        recommendations: ['Approve HbA1c test', 'Schedule endocrinologist consultation'],
      },
    },
  },
  recommendations: ['Approve HbA1c test', 'Schedule endocrinologist consultation'],
  confidence_score: 0.91,
};

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('PatientDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (apiService.getPatientDashboard as any).mockResolvedValue(mockDashboardData);
    (apiService.analyzePatient as any).mockResolvedValue(mockAnalysisResult);
  });

  it('renders loading state initially', () => {
    renderWithRouter(<PatientDashboard />);
    
    expect(screen.getByText('Loading patient dashboard...')).toBeInTheDocument();
  });

  it('displays patient information correctly', async () => {
    renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Dubai Health Insurance')).toBeInTheDocument();
    expect(screen.getByText('DH123456')).toBeInTheDocument();
  });

  it('shows summary statistics', async () => {
    renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument(); // total XML files
    });
    
    expect(screen.getByText('2')).toBeInTheDocument(); // processed files
    expect(screen.getByText('67%')).toBeInTheDocument(); // success rate
    expect(screen.getByText('15')).toBeInTheDocument(); // historical records
  });

  it('displays recent files with processing status', async () => {
    renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('diabetes_monitoring_2025.xml')).toBeInTheDocument();
    });
    
    expect(screen.getByText('routine_checkup_2025.xml')).toBeInTheDocument();
    expect(screen.getByText('prescription_refill_2025.xml')).toBeInTheDocument();
    
    // Check processing status indicators
    const processedFiles = screen.getAllByText('Processed');
    expect(processedFiles).toHaveLength(2);
    
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('shows file details on hover/click', async () => {
    renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('diabetes_monitoring_2025.xml')).toBeInTheDocument();
    });
    
    const firstFile = screen.getByText('diabetes_monitoring_2025.xml');
    fireEvent.click(firstFile);
    
    expect(screen.getByText('15.0 KB')).toBeInTheDocument();
    expect(screen.getByText('eClaimLink')).toBeInTheDocument();
    expect(screen.getByText('Aug 4, 2025 09:30')).toBeInTheDocument();
  });

  it('displays analysis history', async () => {
    renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Diabetes management analysis completed')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Routine checkup analysis')).toBeInTheDocument();
    
    // Check analysis details
    expect(screen.getByText('$0.75')).toBeInTheDocument();
    expect(screen.getByText('88%')).toBeInTheDocument(); // confidence score
    expect(screen.getByText('92%')).toBeInTheDocument(); // confidence score for second analysis
  });

  it('handles new analysis request', async () => {
    renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    const analyzeButton = screen.getByText('Run New Analysis');
    fireEvent.click(analyzeButton);
    
    expect(screen.getByText('Starting analysis...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(apiService.analyzePatient).toHaveBeenCalledWith(
        'patient-123',
        expect.objectContaining({
          cost_limit_usd: expect.any(Number),
          include_history: true,
        })
      );
    });
  });

  it('shows analysis results modal', async () => {
    renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    const analyzeButton = screen.getByText('Run New Analysis');
    fireEvent.click(analyzeButton);
    
    await waitFor(() => {
      expect(screen.getByText('Analysis Complete')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Comprehensive diabetes management analysis')).toBeInTheDocument();
    expect(screen.getByText('Cost: $1.25')).toBeInTheDocument();
    expect(screen.getByText('Confidence: 91%')).toBeInTheDocument();
    
    // Check recommendations
    expect(screen.getByText('Approve HbA1c test')).toBeInTheDocument();
    expect(screen.getByText('Schedule endocrinologist consultation')).toBeInTheDocument();
  });

  it('handles analysis errors gracefully', async () => {
    (apiService.analyzePatient as any).mockRejectedValue(new Error('Analysis failed'));
    
    renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    const analyzeButton = screen.getByText('Run New Analysis');
    fireEvent.click(analyzeButton);
    
    await waitFor(() => {
      expect(screen.getByText('Analysis Failed')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Analysis failed')).toBeInTheDocument();
  });

  it('shows cost limit configuration', async () => {
    renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    const settingsButton = screen.getByText('Analysis Settings');
    fireEvent.click(settingsButton);
    
    expect(screen.getByText('Cost Limit')).toBeInTheDocument();
    expect(screen.getByDisplayValue('2.00')).toBeInTheDocument(); // Default cost limit
    
    const costInput = screen.getByDisplayValue('2.00');
    fireEvent.change(costInput, { target: { value: '5.00' } });
    
    const saveButton = screen.getByText('Save Settings');
    fireEvent.click(saveButton);
    
    // Should save the new cost limit
    expect(screen.getByDisplayValue('5.00')).toBeInTheDocument();
  });

  it('supports data export functionality', async () => {
    const mockDownload = vi.fn();
    global.URL.createObjectURL = vi.fn(() => 'mock-url');
    global.URL.revokeObjectURL = vi.fn();
    
    // Mock createElement and click for download
    const mockAnchor = {
      href: '',
      download: '',
      click: mockDownload,
    };
    vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any);
    
    renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    const exportButton = screen.getByText('Export Data');
    fireEvent.click(exportButton);
    
    expect(mockDownload).toHaveBeenCalled();
  });

  it('handles dashboard refresh', async () => {
    renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);
    
    // Should call API again
    await waitFor(() => {
      expect(apiService.getPatientDashboard).toHaveBeenCalledTimes(2);
    });
  });

  it('shows error state when dashboard loading fails', async () => {
    (apiService.getPatientDashboard as any).mockRejectedValue(new Error('API Error'));
    
    renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Error loading dashboard')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Please try again later')).toBeInTheDocument();
  });

  it('displays patient profile indicators', async () => {
    renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    // Should show profile status
    expect(screen.getByText('Profile Complete')).toBeInTheDocument();
    expect(screen.getByTestId('profile-complete-icon')).toBeInTheDocument();
  });

  it('shows Claude analysis availability status', async () => {
    renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Claude Analysis Available')).toBeInTheDocument();
    expect(screen.getByTestId('claude-available-icon')).toBeInTheDocument();
  });

  it('handles navigation back to patient list', async () => {
    const mockNavigate = vi.fn();
    vi.mocked(require('react-router-dom').useNavigate).mockReturnValue(mockNavigate);
    
    renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    const backButton = screen.getByText('← Back to Patients');
    fireEvent.click(backButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/patients');
  });

  it('supports real-time updates', async () => {
    const { rerender } = renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    // Simulate real-time update with new file
    const updatedData = {
      ...mockDashboardData,
      recent_files: [
        {
          filename: 'new_upload_2025.xml',
          upload_date: '2025-08-04T15:00:00Z',
          file_size: 9800,
          source: 'eclaim',
          processed: false,
          processed_date: null,
        },
        ...mockDashboardData.recent_files,
      ],
      summary_stats: {
        ...mockDashboardData.summary_stats,
        total_xml_files: 4,
      },
    };
    
    (apiService.getPatientDashboard as any).mockResolvedValue(updatedData);
    
    // Trigger refresh or real-time update
    rerender(<PatientDashboard key="updated" />);
    
    await waitFor(() => {
      expect(screen.getByText('new_upload_2025.xml')).toBeInTheDocument();
    });
    
    expect(screen.getByText('4')).toBeInTheDocument(); // Updated file count
  });

  it('provides accessibility support', async () => {
    renderWithRouter(<PatientDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    // Check ARIA labels
    const mainContent = screen.getByRole('main');
    expect(mainContent).toHaveAttribute('aria-label', expect.stringContaining('Patient dashboard'));
    
    // Check button accessibility
    const analyzeButton = screen.getByText('Run New Analysis');
    expect(analyzeButton).toHaveAttribute('aria-describedby');
    
    // Check table accessibility
    const fileTable = screen.getByRole('table');
    expect(fileTable).toHaveAttribute('aria-label', 'Recent files');
  });
});
