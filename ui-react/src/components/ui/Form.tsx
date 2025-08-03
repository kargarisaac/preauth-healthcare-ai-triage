import React from 'react';
import { clsx } from 'clsx';
import type { FormProps } from '@/types/ui';

/**
 * Form wrapper component that provides consistent form layout and validation handling.
 * Includes proper semantic structure and accessibility features for healthcare forms.
 * 
 * @example
 * ```tsx
 * <Form onSubmit={handleSubmit} className="space-y-6">
 *   <Input label="Patient ID" type="text" required />
 *   <Select label="Insurance Provider" options={providers} required />
 *   <Button type="submit" variant="primary">Submit Claim</Button>
 * </Form>
 * ```
 */
const Form: React.FC<FormProps> = ({
  children,
  onSubmit,
  className,
  ...props
}) => {
  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    // Prevent default form submission
    event.preventDefault();
    
    // Call custom onSubmit handler if provided
    if (onSubmit) {
      onSubmit(event);
    }
  };

  const formClasses = clsx(
    'w-full',
    // Default spacing between form fields
    'space-y-6',
    className
  );

  return (
    <form
      className={formClasses}
      onSubmit={handleSubmit}
      noValidate // We'll handle validation ourselves for better UX
      {...props}
    >
      {children}
    </form>
  );
};

export default Form;