import React, { useState, useMemo } from 'react';
import { clsx } from 'clsx';
import Select from '@/components/ui/Select';
import type { PatientInfo } from '@/types/api';
import type { SelectOption } from '@/types/ui';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

interface PatientSelectorProps {
  patients: PatientInfo[];
  selectedPatient: PatientInfo | null;
  onPatientSelect: (patient: PatientInfo | null) => void;
  isLoading?: boolean;
  error?: string | null;
  placeholder?: string;
  className?: string;
}

const PatientSelector: React.FC<PatientSelectorProps> = ({
  patients,
  selectedPatient,
  onPatientSelect,
  isLoading = false,
  error = null,
  placeholder = "Search and select a patient...",
  className
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  // Filter patients based on search term
  const filteredPatients = useMemo(() => {
    if (!searchTerm.trim()) return patients;
    
    const term = searchTerm.toLowerCase();
    return patients.filter(patient =>
      patient.folder_name.toLowerCase().includes(term) ||
      patient.patient_id.toLowerCase().includes(term)
    );
  }, [patients, searchTerm]);

  // Convert patients to select options
  const patientOptions: SelectOption[] = useMemo(() => {
    return filteredPatients.map(patient => ({
      value: patient.patient_id,
      label: `${patient.folder_name} - ${patient.patient_id} (${patient.xml_files} files)`,
      disabled: false
    }));
  }, [filteredPatients]);

  const handlePatientChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const patientId = event.target.value;
    if (!patientId) {
      onPatientSelect(null);
      return;
    }

    const patient = patients.find(p => p.patient_id === patientId);
    if (patient) {
      onPatientSelect(patient);
    }
  };

  const selectedValue = selectedPatient?.patient_id || '';

  if (isLoading) {
    return (
      <div className={clsx('flex items-center space-x-3', className)}>
        <LoadingSpinner size="sm" />
        <span className="text-sm text-gray-600">Loading patients...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={clsx('text-sm text-error-600', className)}>
        Error loading patients: {error}
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="space-y-4">
        {/* Search input for filtering */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Search Patients
          </label>
          <input
            type="text"
            placeholder="Type to search by patient ID or folder name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input w-full"
          />
        </div>

        {/* Patient selector */}
        <div>
          <Select
            label="Select Patient"
            placeholder={placeholder}
            options={patientOptions}
            value={selectedValue}
            onChange={handlePatientChange}
            fullWidth
            required
          />
        </div>

        {/* Patient details display */}
        {selectedPatient && (
          <div className="bg-gray-50 p-4 rounded-lg border">
            <h4 className="font-medium text-gray-900 mb-2">Selected Patient Details</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-700">Patient ID:</span>
                <span className="ml-2 text-gray-900">{selectedPatient.patient_id}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Folder Name:</span>
                <span className="ml-2 text-gray-900">{selectedPatient.folder_name}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Has Profile:</span>
                <span className="ml-2 text-gray-900">{selectedPatient.has_profile ? 'Yes' : 'No'}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">XML Files:</span>
                <span className="ml-2 text-gray-900">{selectedPatient.xml_files}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Processed Files:</span>
                <span className="ml-2 text-gray-900">{selectedPatient.processed_json_files}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Folder Path:</span>
                <span className="ml-2 text-gray-900 text-xs truncate" title={selectedPatient.folder_path}>
                  {selectedPatient.folder_path}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Results count */}
        {searchTerm && (
          <div className="text-sm text-gray-600">
            Showing {filteredPatients.length} of {patients.length} patients
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientSelector;