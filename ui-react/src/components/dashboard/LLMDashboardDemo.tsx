import React, { useState } from 'react';
import { LLMDashboard } from './LLMDashboard';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { Upload } from 'lucide-react';

/**
 * Demo component showcasing the LLM Dashboard functionality
 * This can be used for testing and development purposes
 */
export const LLMDashboardDemo: React.FC = () => {
  const [fileData, setFileData] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Mock file data for demonstration
  const mockFileData = {
    fileName: 'sample-claim-data.csv',
    size: 1024 * 500, // 500KB
    type: 'text/csv',
    content: {
      claims: 156,
      members: 89,
      procedures: 234,
      totalAmount: 125000.50
    },
    uploadTime: new Date()
  };

  const handleFileUpload = () => {
    setFileData(mockFileData);
    setIsProcessing(true);

    // Simulate processing completion
    setTimeout(() => {
      setIsProcessing(false);
    }, 5000);
  };

  const handleReset = () => {
    setFileData(null);
    setIsProcessing(false);
  };

  return (
    <div className="space-y-6">
      {/* Demo Header */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">LLM Dashboard Demo</h2>
            <p className="text-gray-600">
              Interactive demonstration of AI-powered healthcare data validation
            </p>
          </div>

          <div className="flex items-center space-x-3">
            {!fileData ? (
              <Button
                variant="primary"
                onClick={handleFileUpload}
                className="flex items-center space-x-2"
              >
                <Upload className="h-4 w-4" />
                <span>Upload Demo File</span>
              </Button>
            ) : (
              <Button
                variant="secondary"
                onClick={handleReset}
              >
                Reset Demo
              </Button>
            )}
          </div>
        </div>

        {/* Demo Instructions */}
        {!fileData && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="text-sm font-medium text-blue-900 mb-2">How to use this demo:</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>1. Click "Upload Demo File" to simulate file processing</li>
              <li>2. Switch between dashboard tabs to explore different features</li>
              <li>3. Start LLM validation to see AI analysis in action</li>
              <li>4. View real-time metrics and confidence charts</li>
              <li>5. Export results when validation is complete</li>
            </ul>
          </div>
        )}

        {/* File Status */}
        {fileData && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="text-sm font-medium text-green-900 mb-2">File Loaded:</h3>
            <div className="text-sm text-green-800 space-y-1">
              <p><strong>Name:</strong> {fileData.fileName}</p>
              <p><strong>Size:</strong> {(fileData.size / 1024).toFixed(1)} KB</p>
              <p><strong>Claims:</strong> {fileData.content.claims}</p>
              <p><strong>Members:</strong> {fileData.content.members}</p>
              <p><strong>Total Amount:</strong> ${fileData.content.totalAmount.toLocaleString()}</p>
            </div>
          </div>
        )}
      </Card>

      {/* LLM Dashboard */}
      <LLMDashboard
        fileData={fileData}
        isProcessingActive={isProcessing}
      />
    </div>
  );
};
