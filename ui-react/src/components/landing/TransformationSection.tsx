import React from 'react';
import { ArrowRight } from 'lucide-react';

const TransformationSection: React.FC = () => {
  return (
    <section className="py-20 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            From Bottleneck to Intelligence Engine
          </h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-center">
          {/* Before Card */}
          <div className="bg-white rounded-2xl p-8 shadow-soft border border-gray-200">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center text-4xl mx-auto mb-4">
                ⛔
              </div>
              <h3 className="text-xl font-bold text-gray-900">Before Healthcare AI Platform</h3>
            </div>

            <ul className="space-y-3">
              <li className="flex items-start">
                <div className="w-2 h-2 bg-red-400 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <span className="text-gray-600">Static rules, manual queues</span>
              </li>
              <li className="flex items-start">
                <div className="w-2 h-2 bg-red-400 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <span className="text-gray-600">Days-long decision times</span>
              </li>
              <li className="flex items-start">
                <div className="w-2 h-2 bg-red-400 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <span className="text-gray-600">Back-and-forth calls with providers</span>
              </li>
              <li className="flex items-start">
                <div className="w-2 h-2 bg-red-400 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <span className="text-gray-600">No proactive guidance for members</span>
              </li>
              <li className="flex items-start">
                <div className="w-2 h-2 bg-red-400 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <span className="text-gray-600">Reactive, frustrating process</span>
              </li>
            </ul>
          </div>

          {/* Arrow */}
          <div className="flex justify-center">
            <div className="w-12 h-12 bg-primary-500 rounded-full flex items-center justify-center shadow-glow transform hover:scale-110 transition-transform">
              <ArrowRight className="w-6 h-6 text-white" />
            </div>
          </div>

          {/* After Card */}
          <div className="bg-white rounded-2xl p-8 shadow-soft border border-primary-200">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center text-4xl mx-auto mb-4">
                ✨
              </div>
              <h3 className="text-xl font-bold text-gray-900">After Healthcare AI Platform</h3>
            </div>

            <ul className="space-y-3">
              <li className="flex items-start">
                <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <span className="text-gray-600">Dynamic, AI-enriched pathways</span>
              </li>
              <li className="flex items-start">
                <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <span className="text-gray-600">Decisions in minutes, not days</span>
              </li>
              <li className="flex items-start">
                <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <span className="text-gray-600">Full transparency with audit trails</span>
              </li>
              <li className="flex items-start">
                <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <span className="text-gray-600">Proactive, bundled care suggestions</span>
              </li>
              <li className="flex items-start">
                <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <span className="text-gray-600">Preventive, efficient, and collaborative</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
};

export default TransformationSection;
