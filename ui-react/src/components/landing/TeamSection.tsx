import React from 'react';
import isaacPhoto from '@assets/isaac.jpeg';

const TeamSection: React.FC = () => {
  return (
    <section className="py-20 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-blue-100 text-blue-800 text-sm font-medium mb-6">
            Leadership
          </div>
          <h2 className="text-4xl font-bold text-gray-900 mb-4">Team & Advisors</h2>
        </div>

        <div className="space-y-12">
          {/* Founder Card */}
          <div className="bg-white rounded-2xl p-8 lg:p-12 shadow-soft border border-gray-200">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
              <div className="lg:col-span-1">
                <div className="text-center lg:text-left">
                  <div className="w-32 h-32 rounded-full mx-auto lg:mx-0 mb-6 overflow-hidden">
                    <img
                      src={isaacPhoto}
                      alt="Isaac Kargar"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Isaac Kargar
                  </h3>
                  <p className="text-primary-600 font-medium mb-4">
                    Founder & CEO
                  </p>
                  <p className="text-sm text-gray-600 font-medium">
                    AI Scientist & Healthcare Technology Expert
                  </p>
                </div>
              </div>

              <div className="lg:col-span-3">
                <div className="space-y-4 text-gray-700">
                  <p>
                    AI Scientist with 10+ years of experience in machine learning, large language models,
                    and multi-agent systems. PhD in Machine Learning and Robotics.
                  </p>
                  <p>
                    Isaac has led high-impact AI initiatives in healthcare, autonomous systems,
                    and enterprise software—most recently at In-Parallel and Resoniks. His work includes
                    developing AI Agentic Systems, Knowledge Graphs, Graph-based RAG systems,
                    anomaly detection, and policy learning in autonomous driving, with publications
                    in IEEE Transactions on Intelligent Vehicles, Frontiers in Robotics and AI, and IV Symposium.
                  </p>
                  <p>
                    He brings a deep understanding of applied AI, healthtech, and cloud-scale deployment.
                  </p>
                </div>

                {/* Expertise Tags */}
                <div className="mt-6 flex flex-wrap gap-2">
                  {[
                    'Machine Learning',
                    'Healthcare AI',
                    'LLMs',
                    'Multi-Agent Systems',
                    'Knowledge Graphs',
                    'RAG Systems',
                    'Autonomous Systems'
                  ].map((skill, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Advisors Section */}
          <div className="bg-white rounded-2xl p-8 shadow-soft border border-gray-200">
            <div className="text-center">
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Advisors</h3>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Senior leaders from DHA/ADHICS, Daman, and major TPAs. (Full bios available on request.)
              </p>

              <div className="mt-8 flex justify-center space-x-4">
                <div className="bg-gray-100 rounded-full p-4">
                  <div className="text-2xl">🏥</div>
                </div>
                <div className="bg-gray-100 rounded-full p-4">
                  <div className="text-2xl">🏛️</div>
                </div>
                <div className="bg-gray-100 rounded-full p-4">
                  <div className="text-2xl">🏢</div>
                </div>
              </div>

              <div className="mt-4 text-sm text-gray-500">
                DHA/ADHICS • Daman • Major TPAs
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default TeamSection;
