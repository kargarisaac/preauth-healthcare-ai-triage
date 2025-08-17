import React from 'react';
import { RequestHistory } from '@/components/dashboard/RequestHistory';
import Card from '@/components/ui/Card';
import {
  BarChart3,
  Clock,
  DollarSign,
  CheckCircle,
} from 'lucide-react';

const RequestHistoryDemo: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Request Management</h1>
          <p className="text-gray-600 mt-1">
            Comprehensive view of all healthcare pre-authorization requests with advanced search and filtering
          </p>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100 text-blue-600">
              <BarChart3 className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">1,247</div>
              <div className="text-sm text-gray-600">Total Requests</div>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100 text-green-600">
              <CheckCircle className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">892</div>
              <div className="text-sm text-gray-600">Approved</div>
              <div className="text-xs text-green-600">71.5% approval rate</div>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
              <Clock className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">234</div>
              <div className="text-sm text-gray-600">Pending Review</div>
              <div className="text-xs text-yellow-600">Avg 2.3 days</div>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-100 text-purple-600">
              <DollarSign className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">2.4M</div>
              <div className="text-sm text-gray-600">AED Processed</div>
              <div className="text-xs text-purple-600">This month</div>
            </div>
          </div>
        </Card>
      </div>


      {/* Main Request History Component */}
      <RequestHistory className="mt-8" />
    </div>
  );
};

export default RequestHistoryDemo;
