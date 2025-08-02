import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import Button from '@components/ui/Button';

const HeroSection: React.FC = () => {
  return (
    <section className="relative py-20 lg:py-32 bg-gradient-to-br from-gray-50 via-white to-gray-100 overflow-hidden">
      {/* Gradient Orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-200 rounded-full opacity-20 blur-3xl animate-pulse-slow"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-200 rounded-full opacity-20 blur-3xl animate-pulse-slow delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-purple-200 rounded-full opacity-10 blur-3xl animate-pulse-slow delay-2000"></div>
      </div>
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Hero Content */}
          <div className="text-center lg:text-left">
            <div className="inline-flex items-center px-4 py-2 rounded-full bg-primary-100 text-primary-800 text-sm font-medium mb-8 animate-fade-in-up">
              <span className="badge-text">Clinical Intelligence Platform</span>
              <div className="ml-2 w-2 h-2 bg-primary-500 rounded-full animate-pulse"></div>
            </div>
            
            <h1 className="text-5xl lg:text-6xl font-bold text-gray-900 mb-6 animate-fade-in-up delay-200">
              Turn Pre-Authorization into{' '}
              <span className="bg-gradient-to-r from-primary-500 to-primary-600 bg-clip-text text-transparent">
                Prevention
              </span>
            </h1>
            
            <p className="text-2xl font-semibold text-gray-700 mb-4 animate-fade-in-up delay-300">
              Clinical Intelligence for UAE Payers
            </p>
            
            <p className="text-lg text-gray-600 mb-8 max-w-xl animate-fade-in-up delay-400">
              Nazmito enriches every authorization with AI and clinical rules. You approve faster,
              touch fewer files, and stop costly chronic complications before they start.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 animate-fade-in-up delay-500">
              <Link to="/dashboard">
                <Button variant="primary" size="lg" className="group">
                  <span>Try Dashboard</span>
                  <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
              <Button variant="secondary" size="lg">
                Book a Demo
              </Button>
            </div>
          </div>
          
          {/* Floating Cards */}
          <div className="relative lg:pl-8">
            <div className="relative z-10">
              {/* Card 1 */}
              <div className="absolute top-0 left-0 bg-white rounded-2xl p-6 shadow-large border border-gray-200 transform rotate-3 hover:rotate-0 transition-transform duration-500 animate-bounce-gentle">
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center text-2xl mr-4">
                    🏥
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900">Smart Processing</div>
                    <div className="text-primary-600 font-bold">90%+ Automated</div>
                  </div>
                </div>
              </div>
              
              {/* Card 2 */}
              <div className="absolute top-20 right-0 bg-white rounded-2xl p-6 shadow-large border border-gray-200 transform -rotate-2 hover:rotate-0 transition-transform duration-500 animate-bounce-gentle delay-500">
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center text-2xl mr-4">
                    ⚡
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900">Lightning Fast</div>
                    <div className="text-primary-600 font-bold">Minutes not Days</div>
                  </div>
                </div>
              </div>
              
              {/* Card 3 */}
              <div className="absolute top-40 left-8 bg-white rounded-2xl p-6 shadow-large border border-gray-200 transform rotate-1 hover:rotate-0 transition-transform duration-500 animate-bounce-gentle delay-1000">
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center text-2xl mr-4">
                    💡
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900">AI Intelligence</div>
                    <div className="text-primary-600 font-bold">Predictive Care</div>
                  </div>
                </div>
              </div>
              
              {/* Spacer to prevent overlap */}
              <div className="h-96 w-full"></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;