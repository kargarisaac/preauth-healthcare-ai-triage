import React from 'react';

const HowItWorksSection: React.FC = () => {
  const steps = [
    {
      number: 1,
      icon: '🔍',
      title: 'Healthcare AI Platform Ingest™: See the Full Member Picture',
      description: `Our engine ingests claims, labs, and pharmacy data. We normalize formats,
        score data quality, and compare history against clinical guidelines to
        spot care gaps instantly.`
    },
    {
      number: 2,
      icon: '🎯',
      title: 'Healthcare AI Platform Decide™: Shift From Approval to Action',
      description: `Instead of a simple yes/no, our rules and ML models craft an "enriched,
        pre-approved pathway." If a diabetes check is overdue, we bundle it.
        If a lower-cost drug equivalent exists, we suggest it and reward providers who adopt it.`
    },
    {
      number: 3,
      icon: '📊',
      title: 'Healthcare AI Platform Explain™: Trust Through Transparency',
      description: `Every decision comes with a complete audit trail: which rules fired,
        which model version was used, and the clinical citation. This explainability
        builds trust and simplifies compliance.`
    },
    {
      number: 4,
      icon: '🧠',
      title: 'Healthcare AI Platform Intelligence™: Create Localized Intelligence',
      description: `Outcome signals feed reinforcement-learning loops that personalize and
        localize our models to UAE member populations, ensuring the system gets
        smarter and more effective every week.`
    }
  ];

  return (
    <section className="py-20 bg-white" id="how">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-blue-100 text-blue-800 text-sm font-medium mb-6">
            Process
          </div>
          <h2 className="text-4xl font-bold text-gray-900 mb-4">How Healthcare AI Platform Works</h2>
        </div>

        <div className="relative">
          {/* Timeline line - hidden on mobile, visible on desktop */}
          <div className="hidden lg:block absolute left-1/2 transform -translate-x-px h-full w-0.5 bg-gray-200"></div>

          <div className="space-y-12">
            {steps.map((step, index) => (
              <div key={step.number} className="relative">
                {/* Timeline marker */}
                <div className="lg:absolute lg:left-1/2 lg:transform lg:-translate-x-1/2 flex lg:justify-center mb-6 lg:mb-0">
                  <div className="flex items-center justify-center w-12 h-12 bg-primary-500 text-white rounded-full font-bold text-lg shadow-lg">
                    {step.number}
                  </div>
                </div>

                {/* Content */}
                <div className={`lg:grid lg:grid-cols-2 lg:gap-8 items-center ${
                  index % 2 === 0 ? '' : 'lg:grid-cols-2'
                }`}>
                  <div className={`${
                    index % 2 === 0 ? 'lg:text-right lg:pr-8' : 'lg:order-2 lg:pl-8'
                  }`}>
                    <div className="bg-white rounded-2xl p-8 shadow-soft border border-gray-200 hover:shadow-medium transition-shadow">
                      <div className="flex items-center mb-4">
                        <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center text-2xl mr-4">
                          {step.icon}
                        </div>
                        <div className="lg:hidden">
                          <div className="w-8 h-8 bg-primary-500 text-white rounded-full font-bold text-sm flex items-center justify-center">
                            {step.number}
                          </div>
                        </div>
                      </div>
                      <h3 className="text-xl font-bold text-gray-900 mb-4">
                        {step.title}
                      </h3>
                      <p className="text-gray-600 leading-relaxed">
                        {step.description}
                      </p>
                    </div>
                  </div>

                  {/* Spacer for desktop layout */}
                  <div className={`hidden lg:block ${
                    index % 2 === 0 ? 'lg:order-2' : 'lg:order-1'
                  }`}></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorksSection;
