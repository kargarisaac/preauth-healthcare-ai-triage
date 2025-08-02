import React from 'react';
import { RequestHistory } from '@/components/dashboard/RequestHistory';
import Card from '@/components/ui/Card';
import { 
  BarChart3, 
  TrendingUp, 
  Clock, 
  DollarSign,
  Users,
  CheckCircle,
  AlertTriangle,
  XCircle
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

      {/* Features Overview */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Key Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="flex items-start space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Users className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">Virtual Scrolling</h3>
              <p className="text-sm text-gray-600">Handle thousands of requests with smooth performance</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">Advanced Search</h3>
              <p className="text-sm text-gray-600">Real-time search with highlighting and filters</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <AlertTriangle className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">Bulk Operations</h3>
              <p className="text-sm text-gray-600">Approve, deny, or assign multiple requests at once</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <BarChart3 className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">Export & Reports</h3>
              <p className="text-sm text-gray-600">Export to CSV, Excel, or PDF formats</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <XCircle className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">Status Tracking</h3>
              <p className="text-sm text-gray-600">Real-time status updates with audit trails</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="p-2 bg-indigo-100 rounded-lg">
              <Clock className="h-5 w-5 text-indigo-600" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">Mobile Responsive</h3>
              <p className="text-sm text-gray-600">Optimized for desktop and mobile devices</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Main Request History Component */}
      <RequestHistory className="mt-8" />
    </div>
  );
};

export default RequestHistoryDemo;