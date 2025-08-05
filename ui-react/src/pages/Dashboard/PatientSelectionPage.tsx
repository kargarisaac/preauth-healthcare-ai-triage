import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import PatientSelector from '@/components/dashboard/PatientSelector';
import { usePatient } from '@/contexts/PatientContext';

const PatientSelectionPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    selectedPatient,
    patientsList,
    isLoading,
    error,
    selectPatient,
    fetchPatients,
  } = usePatient();

  // Fetch patients on component mount
  useEffect(() => {
    if (patientsList.length === 0) {
      fetchPatients();
    }
  }, [fetchPatients, patientsList.length]);

  const handleContinue = () => {
    if (selectedPatient) {
      // Navigate to patient dashboard for the selected patient
      navigate(`/dashboard/patient/${selectedPatient.patient_id}`);
    }
  };

  const handleCreateNewPatient = () => {
    // Navigate to file upload without selected patient (new patient flow)
    navigate('/dashboard/upload');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Patient Selection
          </h1>
          <p className="text-lg text-gray-600">
            Select an existing patient or create a new patient record
          </p>
        </div>

        {/* Main Content */}
        <div className="space-y-6">
          {/* Patient Selection Card */}
          <Card 
            title="Select Existing Patient"
            subtitle="Choose from existing patient records to upload files or view data"
            padding="lg"
          >
            <PatientSelector
              patients={patientsList}
              selectedPatient={selectedPatient}
              onPatientSelect={selectPatient}
              isLoading={isLoading}
              error={error}
              className="mb-6"
            />

            <div className="flex justify-between items-center pt-4 border-t border-gray-200">
              <Button
                variant="secondary"
                onClick={() => navigate('/dashboard')}
              >
                Back to Dashboard
              </Button>
              
              <Button
                variant="primary"
                onClick={handleContinue}
                disabled={!selectedPatient}
              >
                Continue with Selected Patient
              </Button>
            </div>
          </Card>

          {/* Create New Patient Option */}
          <Card 
            title="Create New Patient"
            subtitle="Upload files to create a new patient record"
            padding="lg"
          >
            <div className="text-center">
              <p className="text-gray-600 mb-6">
                If the patient is not in the system, you can create a new record by uploading their healthcare files.
              </p>
              
              <Button
                variant="primary"
                onClick={handleCreateNewPatient}
              >
                Create New Patient Record
              </Button>
            </div>
          </Card>

          {/* Statistics Card */}
          {patientsList.length > 0 && (
            <Card 
              title="System Statistics"
              padding="lg"
            >
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary-600 mb-1">
                    {patientsList.length}
                  </div>
                  <div className="text-sm text-gray-600">Total Patients</div>
                </div>
                
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary-600 mb-1">
                    {patientsList.reduce((sum, patient) => sum + patient.xml_files, 0)}
                  </div>
                  <div className="text-sm text-gray-600">Total XML Files</div>
                </div>
                
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary-600 mb-1">
                    {patientsList.reduce((sum, patient) => sum + patient.processed_json_files, 0)}
                  </div>
                  <div className="text-sm text-gray-600">Processed Files</div>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default PatientSelectionPage;