import React from 'react';
import { Mail, Phone, ArrowRight } from 'lucide-react';

const ContactSection: React.FC = () => {
  return (
    <section className="py-20 bg-gray-50" id="contact">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-3xl shadow-large overflow-hidden">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-0">
            {/* Contact Info */}
            <div className="p-12 lg:p-16">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                Let's Talk
              </h2>
              <p className="text-xl text-gray-600 mb-8">
                Ready to transform your pre-authorization process? Get in touch to schedule a demo.
              </p>
              
              <div className="space-y-6">
                <a
                  href="mailto:kargarisaac@gmail.com"
                  className="flex items-center p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors group"
                >
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center group-hover:bg-blue-200 transition-colors">
                    <Mail className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-500">Email</div>
                    <div className="text-lg font-semibold text-gray-900">kargarisaac@gmail.com</div>
                  </div>
                </a>
                
                <a
                  href="tel:+358451571107"
                  className="flex items-center p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors group"
                >
                  <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center group-hover:bg-green-200 transition-colors">
                    <Phone className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-500">Phone</div>
                    <div className="text-lg font-semibold text-gray-900">+358 45 157 1107</div>
                  </div>
                </a>
              </div>
            </div>
            
            {/* CTA Section */}
            <div className="bg-gradient-to-br from-primary-500 to-primary-600 p-12 lg:p-16 flex items-center">
              <div className="text-center w-full">
                <div className="text-6xl mb-6">🚀</div>
                <h3 className="text-3xl font-bold text-white mb-4">
                  Ready to Get Started?
                </h3>
                <p className="text-primary-100 mb-8 text-lg">
                  Schedule a personalized demo and see how Nazmito can transform your pre-authorization process.
                </p>
                
                <a
                  href="mailto:kargarisaac@gmail.com?subject=Demo%20Request&body=Hi%20Isaac,%0D%0A%0D%0AI'm%20interested%20in%20scheduling%20a%20demo%20of%20Nazmito.%0D%0A%0D%0AOrganization:%20%0D%0ARole:%20%0D%0APreferred%20date/time:%20%0D%0A%0D%0AThanks!"
                  className="inline-flex items-center px-8 py-4 bg-white text-primary-600 font-semibold rounded-xl hover:bg-gray-50 transition-colors shadow-soft hover:shadow-medium group"
                >
                  <span>Request a Demo</span>
                  <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                </a>
                
                <div className="mt-6 text-primary-200 text-sm">
                  Usually reply within 2 hours
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ContactSection;