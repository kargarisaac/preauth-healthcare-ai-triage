import React from 'react';

const UAESection: React.FC = () => {
  const complianceBadges = [
    'PDPL Ready',
    'ISO 27001',
    'ADHICS',
    'Local Data'
  ];

  return (
    <section className="py-20 bg-gradient-to-br from-blue-50 to-indigo-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* UAE Visual */}
          <div className="order-2 lg:order-1">
            <div className="relative bg-white rounded-2xl p-8 shadow-soft">
              <div className="relative w-full h-64 bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl overflow-hidden">
                {/* UAE Map representation */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-4xl text-gray-400 mb-4">🗺️</div>
                </div>

                {/* Location Pins */}
                <div className="absolute top-1/3 left-1/4 transform -translate-x-1/2 -translate-y-1/2">
                  <div className="bg-blue-500 rounded-full p-3 shadow-lg hover:scale-110 transition-transform cursor-pointer">
                    <div className="text-white text-xl">🏛️</div>
                  </div>
                  <div className="bg-blue-500 text-white text-xs font-medium px-2 py-1 rounded mt-2 text-center shadow-md">
                    Shafafiya
                  </div>
                </div>

                <div className="absolute top-1/2 right-1/3 transform translate-x-1/2 -translate-y-1/2">
                  <div className="bg-primary-500 rounded-full p-3 shadow-lg hover:scale-110 transition-transform cursor-pointer">
                    <div className="text-white text-xl">🏢</div>
                  </div>
                  <div className="bg-primary-500 text-white text-xs font-medium px-2 py-1 rounded mt-2 text-center shadow-md">
                    eClaimLink
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* UAE Content */}
          <div className="order-1 lg:order-2">
            <h2 className="text-4xl font-bold text-gray-900 mb-6">
              Built for the UAE
            </h2>
            <div className="prose prose-lg mb-8">
              <p className="text-lg text-gray-600 leading-relaxed">
                We integrate with Shafafiya and eClaimLink, design for PDPL, ADHICS,
                and ISO 27001 from day one, and keep your data local. Reinforcement-learning
                models adapt to UAE demographics and bilingual (Arabic & English) clinical context.
              </p>
            </div>

            {/* Compliance Badges */}
            <div className="flex flex-wrap gap-3">
              {complianceBadges.map((badge, index) => (
                <div
                  key={index}
                  className="inline-flex items-center px-4 py-2 rounded-full bg-white text-gray-700 text-sm font-medium shadow-soft border border-gray-200 hover:shadow-medium transition-shadow"
                >
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  {badge}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default UAESection;
