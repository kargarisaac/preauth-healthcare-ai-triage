import React from 'react';

// UI State Types
export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
}

export interface ModalState {
  isOpen: boolean;
  title?: string;
  content?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  onClose?: () => void;
}

export interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

export interface NavigationItem {
  id: string;
  label: string;
  icon: string;
  path: string;
  active?: boolean;
}

export interface FileUploadState {
  isDragActive: boolean;
  isUploading: boolean;
  progress: number;
  error?: string;
}

export interface UploadedFile extends File {
  id: string;
  preview?: string;
  status: 'idle' | 'uploading' | 'processing' | 'success' | 'error';
  progress: number;
  error?: string;
}

export interface FileValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export interface FileTypeInfo {
  extension: string;
  sizeFormatted: string;
  typeDescription: string;
  icon: string;
  isHealthcareFormat: boolean;
}

export interface FormFieldProps {
  name: string;
  label?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  helperText?: string;
}

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  variant?: 'default' | 'filled';
  fullWidth?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  options: SelectOption[];
  placeholder?: string;
  fullWidth?: boolean;
}

export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  helperText?: string;
  indeterminate?: boolean;
}

export interface RadioOption {
  value: string | number;
  label: string;
  disabled?: boolean;
  description?: string;
}

export interface RadioGroupProps {
  name: string;
  value: string | number;
  onChange: (value: string | number) => void;
  options: RadioOption[];
  label?: string;
  error?: string;
  helperText?: string;
  disabled?: boolean;
  orientation?: 'horizontal' | 'vertical';
}

export interface FormProps extends React.FormHTMLAttributes<HTMLFormElement> {
  children: React.ReactNode;
  onSubmit?: (event: React.FormEvent<HTMLFormElement>) => void;
  className?: string;
}

export interface FormFieldWrapperProps {
  label?: string;
  error?: string;
  helperText?: string;
  required?: boolean;
  children: React.ReactNode;
  className?: string;
  labelClassName?: string;
}

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'tertiary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

export interface CardProps {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
}

// Navigation Component Types
export interface BreadcrumbItem {
  id: string;
  label: string;
  href?: string;
  icon?: React.ComponentType<{ className?: string }>;
  isActive?: boolean;
  metadata?: {
    patientId?: string;
    recordType?: 'demographics' | 'history' | 'vitals' | 'medications' | 'allergies' | 'procedures';
    visitId?: string;
  };
}

export interface TabItem {
  id: string;
  label: string;
  content?: React.ReactNode;
  icon?: React.ComponentType<{ className?: string }>;
  disabled?: boolean;
  badge?: string | number;
  badgeVariant?: 'default' | 'warning' | 'error' | 'success';
  metadata?: {
    recordType?: 'overview' | 'history' | 'vitals' | 'medications' | 'allergies' | 'procedures' | 'notes';
    priority?: 'low' | 'medium' | 'high' | 'critical';
    lastUpdated?: Date;
    requiresAttention?: boolean;
  };
}

export interface AccordionItem {
  id: string;
  title: string;
  content: React.ReactNode;
  icon?: React.ComponentType<{ className?: string }>;
  disabled?: boolean;
  defaultExpanded?: boolean;
  badge?: string | number;
  badgeVariant?: 'default' | 'warning' | 'error' | 'success';
  metadata?: {
    priority?: 'low' | 'medium' | 'high' | 'critical';
    lastUpdated?: Date;
    status?: 'current' | 'historical' | 'pending' | 'requires_review';
    category?: 'condition' | 'medication' | 'allergy' | 'procedure' | 'vital' | 'note';
  };
}

// Form Component Types
export interface AutocompleteOption {
  id: string;
  label: string;
  description?: string;
  value?: string;
  disabled?: boolean;
  medical?: {
    code?: string;
    system?: string;
    category?: string;
    context?: string;
  };
}

export interface DateRange {
  start?: Date;
  end?: Date;
}

export interface ValidationResult {
  isValid: boolean;
  message?: string;
}

// Data Display Component Types
export interface TableColumn<T = any> {
  key: string;
  title: string;
  dataIndex?: keyof T;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  sortable?: boolean;
  filterable?: boolean;
  width?: string | number;
  align?: 'left' | 'center' | 'right';
  fixed?: 'left' | 'right';
  className?: string;
}

export interface TableProps<T = any> {
  columns: TableColumn<T>[];
  data: T[];
  loading?: boolean;
  rowKey?: string | ((record: T) => string);
  size?: 'sm' | 'md' | 'lg';
  bordered?: boolean;
  hoverable?: boolean;
  striped?: boolean;
  sortable?: boolean;
  filterable?: boolean;
  searchable?: boolean;
  searchPlaceholder?: string;
  onRowClick?: (record: T, index: number) => void;
  onSort?: (sortKey: string, direction: 'asc' | 'desc') => void;
  onFilter?: (filters: Record<string, any>) => void;
  onSearch?: (searchTerm: string) => void;
  className?: string;
  emptyText?: string;
  scroll?: { x?: number; y?: number };
}

export interface DataGridProps<T = any> extends Omit<TableProps<T>, 'scroll'> {
  virtualScroll?: boolean;
  rowHeight?: number;
  overscan?: number;
  stickyHeader?: boolean;
  resizable?: boolean;
  selectable?: boolean;
  selectedRowKeys?: string[];
  onSelectionChange?: (selectedRowKeys: string[], selectedRows: T[]) => void;
  pagination?: PaginationProps | false;
}

export interface PaginationProps {
  current: number;
  total: number;
  pageSize: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  showTotal?: boolean | ((total: number, range: [number, number]) => string);
  pageSizeOptions?: number[];
  size?: 'sm' | 'md' | 'lg';
  simple?: boolean;
  onChange?: (page: number, pageSize: number) => void;
  onShowSizeChange?: (current: number, size: number) => void;
  className?: string;
}

export interface BadgeProps {
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
  count?: number;
  showZero?: boolean;
  overflowCount?: number;
  status?: 'approved' | 'pending' | 'denied' | 'processing' | 'cancelled' | 'expired';
  children?: React.ReactNode;
  className?: string;
}

export interface TooltipProps {
  title: string | React.ReactNode;
  placement?: 'top' | 'top-start' | 'top-end' | 'bottom' | 'bottom-start' | 'bottom-end' | 'left' | 'left-start' | 'left-end' | 'right' | 'right-start' | 'right-end';
  trigger?: 'hover' | 'click' | 'focus' | 'manual';
  visible?: boolean;
  defaultVisible?: boolean;
  onVisibleChange?: (visible: boolean) => void;
  children: React.ReactElement;
  className?: string;
  overlayClassName?: string;
  delay?: number;
  mouseEnterDelay?: number;
  mouseLeaveDelay?: number;
  arrow?: boolean;
  maxWidth?: number;
}

// Healthcare-specific types
export interface HealthcareStatus {
  code: string;
  label: string;
  description?: string;
  color: 'success' | 'warning' | 'error' | 'info' | 'default';
}

export interface PatientRecord {
  id: string;
  patientId: string;
  name: string;
  age: number;
  gender: 'M' | 'F' | 'O';
  status: HealthcareStatus;
  lastVisit: string;
  condition?: string;
  provider: string;
  insuranceId?: string;
}

export interface AuthorizationRecord {
  id: string;
  authorizationId: string;
  patientName: string;
  provider: string;
  service: string;
  status: HealthcareStatus;
  requestDate: string;
  approvalDate?: string;
  expiryDate?: string;
  amount: number;
  currency: string;
}
