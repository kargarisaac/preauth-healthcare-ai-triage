import React from 'react';

const StorySection: React.FC = () => {
  return (
    <section className="py-20 bg-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-purple-100 text-purple-800 text-sm font-medium mb-6">
            Our Mission
          </div>
          <h2 className="text-4xl font-bold text-gray-900 mb-8">Our Story</h2>
        </div>

        <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl p-8 lg:p-12">
          <div className="prose prose-lg mx-auto">
            <p className="text-lg text-gray-700 leading-relaxed text-center">
              Healthcare AI Platform started with a simple question: why isn't the pre‑auth step used to
              prevent problems instead of just policing them? Our founding team saw a
              global pattern of huge data exhaust and little clinical intelligence in
              insurance processes. We built Healthcare AI Platform to flip that script, starting with the UAE.
            </p>
          </div>

          <div className="mt-12 flex justify-center">
            <div className="bg-white rounded-xl p-6 shadow-soft border border-gray-200 max-w-md">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center text-2xl mr-4">
                  💡
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-1">
                    Our Vision
                  </h4>
                  <p className="text-gray-600 text-sm">
                    Transform healthcare authorization from reactive gatekeeping to proactive care intelligence.
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

export default StorySection;
