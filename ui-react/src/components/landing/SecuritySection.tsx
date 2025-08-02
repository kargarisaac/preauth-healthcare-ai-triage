import React from 'react';

const SecuritySection: React.FC = () => {
  const milestones = [
    {
      month: 'Month 3',
      title: 'PDPL/DHA Analysis',
      description: 'Gap analysis complete; DPO appointed'
    },
    {
      month: 'Month 6',
      title: 'ISO 27001',
      description: 'Audit kickoff'
    },
    {
      month: 'Month 9',
      title: 'ADHICS',
      description: 'Attestation complete'
    },
    {
      month: 'Month 12',
      title: 'SOC 2 Type I',
      description: 'Certification achieved'
    }
  ];

  return (
    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-green-100 text-green-800 text-sm font-medium mb-6">
            Security
          </div>
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Security & Compliance
          </h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Encryption at rest (AES‑256) and in transit (TLS 1.2+). Role-based access
            and least-privilege. Immutable logs for audits.
          </p>
        </div>
        
        {/* Security Timeline */}
        <div className="mb-12">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {milestones.map((milestone, index) => (
              <div key={index} className="relative">
                {/* Connection line - hidden on mobile */}
                {index < milestones.length - 1 && (
                  <div className="hidden lg:block absolute top-6 left-full w-full h-0.5 bg-gray-200 z-0"></div>
                )}
                
                <div className="relative bg-white rounded-2xl p-6 shadow-soft border border-gray-200 hover:shadow-medium transition-shadow z-10">
                  <div className="text-center">
                    <div className="inline-flex items-center justify-center w-12 h-12 bg-primary-100 text-primary-600 rounded-full font-bold text-sm mb-4">
                      {index + 1}
                    </div>
                    <div className="text-sm font-medium text-primary-600 mb-2">
                      {milestone.month}
                    </div>
                    <h4 className="text-lg font-bold text-gray-900 mb-2">
                      {milestone.title}
                    </h4>
                    <p className="text-sm text-gray-600">
                      {milestone.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Security Note */}
        <div className="bg-gray-50 rounded-2xl p-8 text-center">
          <div className="max-w-2xl mx-auto">
            <div className="text-4xl mb-4">🔒</div>
            <p className="text-lg text-gray-700 leading-relaxed">
              Every decision is stamped with rule ID, model version, timestamp,
              and any reviewer override for full auditability.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default SecuritySection;