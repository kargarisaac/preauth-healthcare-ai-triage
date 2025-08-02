import { clsx, type ClassValue } from 'clsx';

/**
 * Utility function for conditionally joining class names
 * Combines clsx functionality for conditional classes
 */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export default cn;
