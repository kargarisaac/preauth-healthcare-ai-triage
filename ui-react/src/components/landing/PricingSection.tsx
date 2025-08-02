import React from 'react';

const PricingSection: React.FC = () => {
  return (
    <section className="py-20 bg-gray-50" id="pricing">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-primary-100 text-primary-800 text-sm font-medium mb-6">
            Pricing
          </div>
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Simple, Transparent Pricing
          </h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 max-w-4xl mx-auto">
          {/* SaaS Model */}
          <div className="bg-white rounded-2xl p-8 shadow-soft border border-gray-200">
            <h3 className="text-2xl font-bold text-gray-900 mb-6">SaaS Model</h3>
            <ul className="space-y-4">
              <li className="flex items-start">
                <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <span className="text-gray-600">Per member per month</span>
              </li>
              <li className="flex items-start">
                <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <span className="text-gray-600">Per request pricing</span>
              </li>
              <li className="flex items-start">
                <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <span className="text-gray-600">Optional gain-share (15–30% of proven savings)</span>
              </li>
              <li className="flex items-start">
                <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                <span className="text-gray-600">Capped pricing model</span>
              </li>
            </ul>
          </div>

          {/* Our Approach */}
          <div className="bg-white rounded-2xl p-8 shadow-soft border border-gray-200">
            <h3 className="text-2xl font-bold text-gray-900 mb-6">Our Approach</h3>
            <div className="prose prose-lg">
              <p className="text-gray-600 leading-relaxed">
                Start with a pilot at a reduced rate, then scale once ROI is clear.
                We believe in proving value before scaling investment.
              </p>
            </div>

            <div className="mt-8 p-6 bg-primary-50 rounded-xl border border-primary-200">
              <div className="flex items-center">
                <div className="text-2xl mr-4">💡</div>
                <div>
                  <h4 className="font-semibold text-primary-900 mb-1">
                    Pilot Program Available
                  </h4>
                  <p className="text-primary-700 text-sm">
                    Contact us to discuss a customized pilot program for your organization.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PricingSection;
