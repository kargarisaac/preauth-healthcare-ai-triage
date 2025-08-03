import React, { useState } from 'react';
import {
  Form,
  FormField,
  Input,
  Select,
  Checkbox,
  RadioGroup,
  Button,
  Card
} from '../ui';

/**
 * Example showcasing how to use the form components together for healthcare data entry.
 * This demonstrates a typical pre-authorization form for UAE healthcare insurance.
 */
const FormExamples: React.FC = () => {
  const [formData, setFormData] = useState({
    patientId: '',
    insuranceProvider: '',
    treatmentType: '',
    urgency: 'normal',
    consentGiven: false,
    additionalNotes: ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const insuranceProviders = [
    { value: 'dha', label: 'Dubai Health Authority' },
    { value: 'adh', label: 'Abu Dhabi Health Department' },
    { value: 'thiqa', label: 'Thiqa Insurance' },
    { value: 'nic', label: 'National Insurance Company' },
    { value: 'axa', label: 'AXA Gulf' }
  ];

  const treatmentTypes = [
    { value: 'consultation', label: 'General Consultation' },
    { value: 'diagnostic', label: 'Diagnostic Tests' },
    { value: 'surgery', label: 'Surgical Procedure' },
    { value: 'emergency', label: 'Emergency Treatment' },
    { value: 'specialist', label: 'Specialist Consultation' }
  ];

  const urgencyOptions = [
    { 
      value: 'normal', 
      label: 'Normal', 
      description: 'Standard processing time (3-5 business days)' 
    },
    { 
      value: 'urgent', 
      label: 'Urgent', 
      description: 'Expedited processing (24-48 hours)' 
    },
    { 
      value: 'emergency', 
      label: 'Emergency', 
      description: 'Immediate approval required' 
    }
  ];

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    
    // Basic validation
    const newErrors: Record<string, string> = {};
    
    if (!formData.patientId.trim()) {
      newErrors.patientId = 'Patient ID is required';
    }
    
    if (!formData.insuranceProvider) {
      newErrors.insuranceProvider = 'Please select an insurance provider';
    }
    
    if (!formData.treatmentType) {
      newErrors.treatmentType = 'Please select a treatment type';
    }
    
    if (!formData.consentGiven) {
      newErrors.consentGiven = 'Patient consent is required for processing';
    }

    setErrors(newErrors);
    
    if (Object.keys(newErrors).length === 0) {
      console.log('Form submitted:', formData);
      alert('Pre-authorization request submitted successfully!');
    }
  };

  const updateFormData = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-8">
      <Card title="Healthcare Pre-Authorization Form" subtitle="UAE Insurance Processing">
        <Form onSubmit={handleSubmit} className="space-y-6">
          {/* Patient Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Patient Information</h3>
            
            <Input
              label="Patient ID"
              type="text"
              placeholder="Enter patient identification number"
              value={formData.patientId}
              onChange={(e) => updateFormData('patientId', e.target.value)}
              error={errors.patientId}
              required
              helperText="Enter the patient's unique identifier"
            />
          </div>

          {/* Insurance Details */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Insurance Details</h3>
            
            <Select
              label="Insurance Provider"
              options={insuranceProviders}
              placeholder="Select insurance provider"
              value={formData.insuranceProvider}
              onChange={(e) => updateFormData('insuranceProvider', e.target.value)}
              error={errors.insuranceProvider}
              required
              helperText="Choose the patient's primary insurance provider"
            />
          </div>

          {/* Treatment Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Treatment Information</h3>
            
            <Select
              label="Treatment Type"
              options={treatmentTypes}
              placeholder="Select type of treatment"
              value={formData.treatmentType}
              onChange={(e) => updateFormData('treatmentType', e.target.value)}
              error={errors.treatmentType}
              required
            />
            
            <RadioGroup
              name="urgency"
              label="Processing Urgency"
              value={formData.urgency}
              onChange={(value) => updateFormData('urgency', value)}
              options={urgencyOptions}
              orientation="vertical"
              helperText="Select the appropriate processing urgency for this request"
            />
          </div>

          {/* Additional Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Additional Information</h3>
            
            <FormField label="Additional Notes" helperText="Any additional context or special instructions">
              <textarea
                className="input min-h-24 resize-y"
                placeholder="Enter any additional notes or special instructions..."
                value={formData.additionalNotes}
                onChange={(e) => updateFormData('additionalNotes', e.target.value)}
                rows={4}
              />
            </FormField>
          </div>

          {/* Consent */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Consent & Confirmation</h3>
            
            <Checkbox
              label="I confirm that the patient has given consent for this pre-authorization request and agrees to the terms and conditions"
              checked={formData.consentGiven}
              onChange={(e) => updateFormData('consentGiven', e.target.checked)}
              error={errors.consentGiven}
              required
              helperText="This consent is required for processing the pre-authorization request"
            />
          </div>

          {/* Submit */}
          <div className="flex gap-4 pt-6 border-t border-gray-200">
            <Button
              type="submit"
              variant="primary"
              className="flex-1"
            >
              Submit Pre-Authorization Request
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setFormData({
                  patientId: '',
                  insuranceProvider: '',
                  treatmentType: '',
                  urgency: 'normal',
                  consentGiven: false,
                  additionalNotes: ''
                });
                setErrors({});
              }}
            >
              Reset Form
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default FormExamples;