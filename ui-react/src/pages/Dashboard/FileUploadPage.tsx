import React, { useState } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/SimpleTabs';
import PipelineProcessingFlow from '@/components/dashboard/PipelineProcessingFlow';
import { AnalyticsOverview } from '@/components/dashboard/AnalyticsOverview';
import { useProcessing } from '@/contexts/ProcessingContext';
import { BarChart3, Workflow } from 'lucide-react';

const FileUploadPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('pipeline');
  const { dashboardSummary, fetchDashboardSummary } = useProcessing();

  // Fetch dashboard summary on mount
  React.useEffect(() => {
    fetchDashboardSummary();
  }, [fetchDashboardSummary]);

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Pre-Authorization Processing Center
        </h1>
        <p className="text-gray-600 max-w-3xl mx-auto">
          Process healthcare pre-authorization requests with AI-powered decision support.
          Upload XML/CSV files for comprehensive clinical analysis and policy evaluation.
        </p>
      </div>

      <div className="w-full">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="pipeline" className="flex items-center space-x-2">
              <Workflow className="w-4 h-4" />
              <span>Process New Requests</span>
            </TabsTrigger>
            <TabsTrigger value="analytics" className="flex items-center space-x-2">
              <BarChart3 className="w-4 h-4" />
              <span>Processing Analytics</span>
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="pipeline" className="mt-6">
            <PipelineProcessingFlow />
          </TabsContent>
          
          <TabsContent value="analytics" className="mt-6">
            <AnalyticsOverview 
              data={null} 
              pipelineData={dashboardSummary}
              isLoading={false}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default FileUploadPage;
