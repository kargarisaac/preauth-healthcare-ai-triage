import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

const FAQSection: React.FC = () => {
  const [openItems, setOpenItems] = useState<number[]>([]);

  const faqs = [
    {
      question: 'Do you replace our current TPA portal?',
      answer: 'No. We sit alongside or integrate into it. Think "intelligence layer," not "portal replacement."'
    },
    {
      question: 'How long to integrate?',
      answer: 'A lightweight API or SFTP batch can go live in 4–6 weeks. We\'ve budgeted an "integration sprint" in every pilot.'
    },
    {
      question: 'Who owns the decision?',
      answer: 'You do. Healthcare AI Platform is decision support. We provide rationale and audit trails; you keep the final call.'
    },
    {
      question: 'How do you prove savings?',
      answer: 'We agree on KPIs up front (manual rate, turnaround, proxy MLR markers). We run a baseline, then show the delta after deployment.'
    }
  ];

  const toggleItem = (index: number) => {
    setOpenItems(prev =>
      prev.includes(index)
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  return (
    <section className="py-20 bg-white" id="faq">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-green-100 text-green-800 text-sm font-medium mb-6">
            FAQ
          </div>
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Frequently Asked Questions
          </h2>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, index) => {
            const isOpen = openItems.includes(index);

            return (
              <div
                key={index}
                className="bg-white rounded-2xl shadow-soft border border-gray-200 overflow-hidden hover:shadow-medium transition-shadow"
              >
                <button
                  className="w-full px-8 py-6 text-left flex items-center justify-between focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-inset"
                  onClick={() => toggleItem(index)}
                >
                  <h4 className="text-lg font-semibold text-gray-900 pr-4">
                    {faq.question}
                  </h4>
                  <div className="flex-shrink-0">
                    {isOpen ? (
                      <ChevronUp className="w-5 h-5 text-primary-500" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </button>

                <div
                  className={`overflow-hidden transition-all duration-300 ease-in-out ${
                    isOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
                  }`}
                >
                  <div className="px-8 pb-6">
                    <div className="border-t border-gray-200 pt-4">
                      <p className="text-gray-600 leading-relaxed">
                        {faq.answer}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-12 text-center">
          <p className="text-gray-600 mb-6">
            Have more questions? We'd love to help.
          </p>
          <a
            href="mailto:contact@healthcare-preauth.com?subject=Healthcare%20AI%20Platform%20Questions"
            className="inline-flex items-center px-6 py-3 bg-primary-500 text-white font-medium rounded-lg hover:bg-primary-600 transition-colors shadow-soft hover:shadow-medium"
          >
            Contact Us
          </a>
        </div>
      </div>
    </section>
  );
};

export default FAQSection;
