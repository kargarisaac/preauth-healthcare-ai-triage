import React from 'react';
import FileProcessingSection from '@/components/dashboard/FileProcessingSection';

const FileUploadPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          File Processing Center
        </h1>
        <p className="text-gray-600 max-w-3xl mx-auto">
          Upload and process healthcare data files with AI-powered intelligence. 
          Transform XML and CSV files into FHIR-compliant format with comprehensive validation and analysis.
        </p>
      </div>

      <FileProcessingSection />
    </div>
  );
};

export default FileUploadPage;