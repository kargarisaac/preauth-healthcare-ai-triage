import React from 'react';
import { Link } from 'react-router-dom';
import { Target, Zap, DollarSign, TrendingUp } from 'lucide-react';
import Button from '@components/ui/Button';
import logoImage from '@assets/logo.png';

// Import all landing sections
import HeroSection from '@components/landing/HeroSection';
import ProblemSection from '@components/landing/ProblemSection';
import TransformationSection from '@components/landing/TransformationSection';
import HowItWorksSection from '@components/landing/HowItWorksSection';
import UAESection from '@components/landing/UAESection';
import SecuritySection from '@components/landing/SecuritySection';
import PricingSection from '@components/landing/PricingSection';
import StorySection from '@components/landing/StorySection';
import TeamSection from '@components/landing/TeamSection';
import FAQSection from '@components/landing/FAQSection';
import ContactSection from '@components/landing/ContactSection';
import WhyNowSection from '@components/landing/WhyNowSection';

const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white shadow-soft border-b border-gray-200 sticky top-0 z-50 backdrop-blur-sm bg-white/95">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <img src={logoImage} alt="Nazmito" className="h-8 w-8" />
              <div className="ml-2">
                <span className="text-xl font-bold text-gray-900">Nazmito</span>
                <div className="text-xs text-gray-500 hidden lg:block">AI-powered prior-authorization for UAE insurers</div>
              </div>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center space-x-8">
              <a href="#how" className="nav-link text-gray-600 hover:text-gray-900 transition-colors">
                How It Works
              </a>
              <a href="#value" className="nav-link text-gray-600 hover:text-gray-900 transition-colors">
                Advantage
              </a>
              <a href="#pricing" className="nav-link text-gray-600 hover:text-gray-900 transition-colors">
                Pricing
              </a>
              <a href="#faq" className="nav-link text-gray-600 hover:text-gray-900 transition-colors">
                FAQ
              </a>
              <a href="#contact" className="nav-link text-gray-600 hover:text-gray-900 transition-colors">
                Contact
              </a>
              <Link to="/dashboard">
                <Button variant="primary">Dashboard</Button>
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <div className="lg:hidden">
              <Link to="/dashboard">
                <Button variant="primary" size="sm">Dashboard</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main>
        <HeroSection />

        {/* Trust Bar */}
        <section className="py-8 bg-gray-50 border-y border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col md:flex-row items-center justify-center space-y-4 md:space-y-0 md:space-x-8 text-center">
              <div className="flex items-center text-sm font-medium text-gray-600">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                Built for Shafafiya & eClaimLink
              </div>
              <div className="hidden md:block w-1 h-1 bg-gray-400 rounded-full"></div>
              <div className="flex items-center text-sm font-medium text-gray-600">
                <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                PDPL-Ready
              </div>
              <div className="hidden md:block w-1 h-1 bg-gray-400 rounded-full"></div>
              <div className="flex items-center text-sm font-medium text-gray-600">
                <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                Enterprise Security
              </div>
            </div>
          </div>
        </section>

        <ProblemSection />
        <TransformationSection />
        <HowItWorksSection />

        {/* Enhanced Value Proposition Section */}
        <section className="py-20 bg-white" id="value">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <div className="inline-flex items-center px-4 py-2 rounded-full bg-primary-100 text-primary-800 text-sm font-medium mb-6">
                Benefits
              </div>
              <h2 className="text-4xl font-bold text-gray-900 mb-4">The Nazmito Advantage</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              <div className="bg-white rounded-2xl p-8 shadow-soft border border-gray-200 hover:shadow-medium transition-shadow text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <Target className="w-8 h-8 text-blue-600" />
                </div>
                <div className="text-4xl font-bold text-primary-600 mb-2">90%+</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Automate Requests</h3>
                <p className="text-gray-600 leading-relaxed">
                  Our pilot benchmark for in-scope chronic care requests is over 90%
                  straight-through-processing, freeing your team from manual reviews.
                </p>
              </div>

              <div className="bg-white rounded-2xl p-8 shadow-soft border border-gray-200 hover:shadow-medium transition-shadow text-center">
                <div className="w-16 h-16 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <Zap className="w-8 h-8 text-green-600" />
                </div>
                <div className="text-4xl font-bold text-primary-600 mb-2">Minutes</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Cut Decision Time</h3>
                <p className="text-gray-600 leading-relaxed">
                  Move at the speed of data. Providers stop chasing status updates,
                  and members get timely care without administrative friction.
                </p>
              </div>

              <div className="bg-white rounded-2xl p-8 shadow-soft border border-gray-200 hover:shadow-medium transition-shadow text-center">
                <div className="w-16 h-16 bg-orange-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <DollarSign className="w-8 h-8 text-orange-600" />
                </div>
                <div className="text-4xl font-bold text-primary-600 mb-2">MLR↓</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Reduce Chronic Care Spend</h3>
                <p className="text-gray-600 leading-relaxed">
                  By closing guideline gaps proactively, you prevent costly complications
                  down the line. Even a small drop in MLR can translate to millions in savings.
                </p>
              </div>

              <div className="bg-white rounded-2xl p-8 shadow-soft border border-gray-200 hover:shadow-medium transition-shadow text-center">
                <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <TrendingUp className="w-8 h-8 text-purple-600" />
                </div>
                <div className="text-4xl font-bold text-primary-600 mb-2">ROI</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Get Proof, Not Promises</h3>
                <p className="text-gray-600 leading-relaxed">
                  Our dashboards track the metrics that matter: manual-touch rate,
                  turnaround times, and savings proxies. We offer gain-share models
                  based on verified performance.
                </p>
              </div>
            </div>
          </div>
        </section>

        <UAESection />
        <SecuritySection />
        <PricingSection />
        <StorySection />
        <TeamSection />
        <FAQSection />
        <ContactSection />
        <WhyNowSection />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            <div className="lg:col-span-2">
              <div className="flex items-center mb-4">
                <img src={logoImage} alt="Nazmito" className="h-8 w-8" />
                <span className="ml-2 text-xl font-bold text-gray-900">Nazmito</span>
              </div>
              <p className="text-gray-600 mb-6 max-w-md">
                AI-powered clinical intelligence platform transforming pre-authorization
                from reactive gatekeeping to proactive care management.
              </p>
              <div className="text-sm text-gray-500">
                © 2025 Nazmito. All rights reserved.
              </div>
            </div>

            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Product</h4>
              <ul className="space-y-2">
                <li><a href="#how" className="text-gray-600 hover:text-gray-900 transition-colors">How It Works</a></li>
                <li><a href="#value" className="text-gray-600 hover:text-gray-900 transition-colors">Benefits</a></li>
                <li><a href="#pricing" className="text-gray-600 hover:text-gray-900 transition-colors">Pricing</a></li>
                <li><Link to="/dashboard" className="text-gray-600 hover:text-gray-900 transition-colors">Dashboard</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Support</h4>
              <ul className="space-y-2">
                <li><a href="#faq" className="text-gray-600 hover:text-gray-900 transition-colors">FAQ</a></li>
                <li><a href="#contact" className="text-gray-600 hover:text-gray-900 transition-colors">Contact</a></li>
                <li><a href="mailto:kargarisaac@gmail.com" className="text-gray-600 hover:text-gray-900 transition-colors">Email Support</a></li>
              </ul>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
