import { useEffect } from 'react';
import { RequestHistory } from './RequestHistory';
import { setupMockData } from '@/utils/mockData';

export function RequestHistoryDemo() {
  useEffect(() => {
    // Setup mock data for development
    setupMockData();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Request History Demo</h1>
          <p className="text-gray-600 mt-2">
            This is a demonstration of the comprehensive request history and search functionality.
            Mock data has been generated for testing purposes.
          </p>
        </div>
        
        <RequestHistory />
      </div>
    </div>
  );
}