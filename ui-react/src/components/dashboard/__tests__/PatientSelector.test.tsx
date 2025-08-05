import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { PatientSelector } from '../PatientSelector';
import { apiService } from '../../../services/apiService';

// Mock the API service
vi.mock('../../../services/apiService', () => ({
  apiService: {
    getPatients: vi.fn(),
  },
}));

const mockPatients = [
  {
    patient_id: 'patient-123',
    folder_name: 'Ahmed_Al_Mansoori',
    folder_path: '/data/patients/1',
    has_profile: true,
    xml_files: 3,
    processed_json_files: 2,
  },
  {
    patient_id: 'patient-456',
    folder_name: 'Fatima_Al_Zahra',
    folder_path: '/data/patients/2',
    has_profile: true,
    xml_files: 1,
    processed_json_files: 1,
  },
  {
    patient_id: 'patient-789',
    folder_name: 'Omar_Mohammed',
    folder_path: '/data/patients/3',
    has_profile: false,
    xml_files: 0,
    processed_json_files: 0,
  },
];

describe('PatientSelector', () => {
  const mockOnSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (apiService.getPatients as any).mockResolvedValue(mockPatients);
  });

  it('renders loading state initially', () => {
    render(<PatientSelector onSelect={mockOnSelect} />);
    
    expect(screen.getByText('Loading patients...')).toBeInTheDocument();
  });

  it('renders patient list after loading', async () => {
    render(<PatientSelector onSelect={mockOnSelect} />);
    
    await waitFor(() => {
      expect(screen.getByText('Select Patient')).toBeInTheDocument();
    });
    
    // Check that patients are displayed
    expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    expect(screen.getByText('Fatima Al Zahra')).toBeInTheDocument();
    expect(screen.getByText('Omar Mohammed')).toBeInTheDocument();
  });

  it('displays patient information correctly', async () => {
    render(<PatientSelector onSelect={mockOnSelect} />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    // Check patient data details
    const ahmedCard = screen.getByText('Ahmed Al Mansoori').closest('[data-testid="patient-card"]');
    expect(ahmedCard).toContainElement(screen.getByText('3 XML files'));
    expect(ahmedCard).toContainElement(screen.getByText('2 processed'));
    expect(ahmedCard).toContainElement(screen.getByText('Has Profile'));
  });

  it('handles patient selection', async () => {
    render(<PatientSelector onSelect={mockOnSelect} />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    // Click on first patient
    fireEvent.click(screen.getByText('Ahmed Al Mansoori'));
    
    expect(mockOnSelect).toHaveBeenCalledWith(mockPatients[0]);
  });

  it('shows visual indicator for patients without profiles', async () => {
    render(<PatientSelector onSelect={mockOnSelect} />);
    
    await waitFor(() => {
      expect(screen.getByText('Omar Mohammed')).toBeInTheDocument();
    });
    
    const omarCard = screen.getByText('Omar Mohammed').closest('[data-testid="patient-card"]');
    expect(omarCard).toContainElement(screen.getByText('No Profile'));
    expect(omarCard).toHaveClass('opacity-60'); // Dimmed for incomplete data
  });

  it('filters patients by search term', async () => {
    render(<PatientSelector onSelect={mockOnSelect} showSearch />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    // Search for "Ahmed"
    const searchInput = screen.getByPlaceholderText('Search patients...');
    fireEvent.change(searchInput, { target: { value: 'Ahmed' } });
    
    // Only Ahmed should be visible
    expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    expect(screen.queryByText('Fatima Al Zahra')).not.toBeInTheDocument();
    expect(screen.queryByText('Omar Mohammed')).not.toBeInTheDocument();
  });

  it('handles API error gracefully', async () => {
    (apiService.getPatients as any).mockRejectedValue(new Error('API Error'));
    
    render(<PatientSelector onSelect={mockOnSelect} />);
    
    await waitFor(() => {
      expect(screen.getByText('Error loading patients')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Please try again later')).toBeInTheDocument();
  });

  it('shows empty state when no patients available', async () => {
    (apiService.getPatients as any).mockResolvedValue([]);
    
    render(<PatientSelector onSelect={mockOnSelect} />);
    
    await waitFor(() => {
      expect(screen.getByText('No patients found')).toBeInTheDocument();
    });
  });

  it('displays refresh button on error', async () => {
    (apiService.getPatients as any).mockRejectedValue(new Error('Network Error'));
    
    render(<PatientSelector onSelect={mockOnSelect} />);
    
    await waitFor(() => {
      expect(screen.getByText('Error loading patients')).toBeInTheDocument();
    });
    
    const refreshButton = screen.getByText('Retry');
    expect(refreshButton).toBeInTheDocument();
    
    // Test retry functionality
    (apiService.getPatients as any).mockResolvedValue(mockPatients);
    fireEvent.click(refreshButton);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
  });

  it('sorts patients by name by default', async () => {
    render(<PatientSelector onSelect={mockOnSelect} />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    const patientCards = screen.getAllByTestId('patient-card');
    const patientNames = patientCards.map(card => 
      card.querySelector('[data-testid="patient-name"]')?.textContent
    );
    
    expect(patientNames).toEqual(['Ahmed Al Mansoori', 'Fatima Al Zahra', 'Omar Mohammed']);
  });

  it('highlights selected patient', async () => {
    render(<PatientSelector onSelect={mockOnSelect} selectedPatientId="patient-123" />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    const ahmedCard = screen.getByText('Ahmed Al Mansoori').closest('[data-testid="patient-card"]');
    expect(ahmedCard).toHaveClass('ring-2', 'ring-blue-500'); // Selected styling
  });

  it('shows loading indicator during refresh', async () => {
    (apiService.getPatients as any).mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve(mockPatients), 100))
    );
    
    render(<PatientSelector onSelect={mockOnSelect} />);
    
    expect(screen.getByText('Loading patients...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    }, { timeout: 200 });
  });

  it('supports keyboard navigation', async () => {
    render(<PatientSelector onSelect={mockOnSelect} />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    const firstPatientCard = screen.getByText('Ahmed Al Mansoori').closest('[data-testid="patient-card"]');
    
    // Focus and press Enter
    firstPatientCard?.focus();
    fireEvent.keyDown(firstPatientCard!, { key: 'Enter', code: 'Enter' });
    
    expect(mockOnSelect).toHaveBeenCalledWith(mockPatients[0]);
  });

  it('displays patient statistics correctly', async () => {
    render(<PatientSelector onSelect={mockOnSelect} showStats />);
    
    await waitFor(() => {
      expect(screen.getByText('Ahmed Al Mansoori')).toBeInTheDocument();
    });
    
    // Check statistics display
    expect(screen.getByText('Total: 3 patients')).toBeInTheDocument();
    expect(screen.getByText('With profiles: 2')).toBeInTheDocument();
    expect(screen.getByText('With data: 2')).toBeInTheDocument();
  });
});
