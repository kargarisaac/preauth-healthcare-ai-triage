import React from 'react';

const ProblemSection: React.FC = () => {
  return (
    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-orange-100 text-orange-800 text-sm font-medium mb-6">
            The Challenge
          </div>
          <h2 className="text-4xl font-bold text-gray-900 mb-8">The Problem</h2>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Problem Flow Visualization */}
          <div className="order-2 lg:order-1">
            <div className="bg-gray-50 rounded-2xl p-8">
              <div className="flex flex-col sm:flex-row items-center justify-center space-y-6 sm:space-y-0 sm:space-x-8">
                <div className="flex flex-col items-center text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center text-3xl mb-3">
                    📄
                  </div>
                  <span className="text-sm font-medium text-gray-700">Documents Upload</span>
                </div>
                
                <div className="hidden sm:block text-2xl text-gray-400 transform rotate-0 sm:rotate-0">
                  →
                </div>
                <div className="sm:hidden text-2xl text-gray-400 transform rotate-90">
                  →
                </div>
                
                <div className="flex flex-col items-center text-center">
                  <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center text-3xl mb-3">
                    👁️
                  </div>
                  <span className="text-sm font-medium text-gray-700">Manual Review</span>
                </div>
                
                <div className="hidden sm:block text-2xl text-gray-400">
                  →
                </div>
                <div className="sm:hidden text-2xl text-gray-400 transform rotate-90">
                  →
                </div>
                
                <div className="flex flex-col items-center text-center">
                  <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center text-3xl mb-3">
                    ⏰
                  </div>
                  <span className="text-sm font-medium text-gray-700">Waiting</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Problem Description */}
          <div className="order-1 lg:order-2">
            <div className="prose prose-lg">
              <p className="text-lg text-gray-600 leading-relaxed">
                Pre‑authorization is supposed to protect payers from unnecessary spend. In reality,
                it became a paperwork bottleneck. Providers upload documents, reviewers scan them,
                and everyone waits. The UAE already has digital rails—Shafafiya in Abu Dhabi,
                eClaimLink in Dubai—but the logic running on those rails is still basic.
                Chronic patients drift through without proactive guidance, and avoidable
                complications eat budgets.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ProblemSection;