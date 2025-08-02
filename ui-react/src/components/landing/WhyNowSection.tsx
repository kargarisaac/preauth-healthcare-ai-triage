import React from 'react';

const WhyNowSection: React.FC = () => {
  return (
    <section className="py-20 bg-primary-500">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h3 className="text-3xl font-bold text-white mb-6">
            Why Now?
          </h3>
          <p className="text-xl text-primary-100 leading-relaxed">
            Automation works: US payers already run 12M+ AI-approved requests yearly.
            UAE rails and PDPL enforcement make clinical intelligence possible here, now.
          </p>
          
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white bg-opacity-10 rounded-2xl p-6 backdrop-blur-sm">
              <div className="text-4xl mb-4">🇺🇸</div>
              <div className="text-2xl font-bold text-white mb-2">12M+</div>
              <div className="text-primary-100 text-sm">AI-approved requests yearly in US</div>
            </div>
            
            <div className="bg-white bg-opacity-10 rounded-2xl p-6 backdrop-blur-sm">
              <div className="text-4xl mb-4">🇦🇪</div>
              <div className="text-2xl font-bold text-white mb-2">UAE Rails</div>
              <div className="text-primary-100 text-sm">Digital infrastructure ready</div>
            </div>
            
            <div className="bg-white bg-opacity-10 rounded-2xl p-6 backdrop-blur-sm">
              <div className="text-4xl mb-4">⚖️</div>
              <div className="text-2xl font-bold text-white mb-2">PDPL</div>
              <div className="text-primary-100 text-sm">Compliance framework established</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default WhyNowSection;