import React, { useState } from 'react';
import Table, { PatientTable, AuthorizationTable } from '../ui/Table';
import DataGrid, { PatientDataGrid, AuthorizationDataGrid } from '../ui/DataGrid';
import Pagination, { PatientPagination, RecordsPagination } from '../ui/Pagination';
import Badge, { StatusBadge, PriorityBadge } from '../ui/Badge';
import Tooltip, { MedicalTooltip, AuthorizationTooltip } from '../ui/Tooltip';
import Card from '../ui/Card';
import Button from '../ui/Button';
import type { TableColumn, PatientRecord, AuthorizationRecord } from '@/types/ui';

// Sample data for demonstration
const samplePatients: PatientRecord[] = [
  {
    id: '1',
    patientId: 'P001',
    name: 'Ahmed Al-Rashid',
    age: 45,
    gender: 'M',
    status: { code: 'active', label: 'Active', color: 'success' },
    lastVisit: '2024-01-15',
    condition: 'Diabetes Type 2',
    provider: 'Dubai Healthcare City',
    insuranceId: 'INS001',
  },
  {
    id: '2',
    patientId: 'P002',
    name: 'Fatima Al-Zahra',
    age: 32,
    gender: 'F',
    status: { code: 'pending', label: 'Pending Review', color: 'warning' },
    lastVisit: '2024-01-12',
    condition: 'Hypertension',
    provider: 'Abu Dhabi Medical Center',
    insuranceId: 'INS002',
  },
  {
    id: '3',
    patientId: 'P003',
    name: 'Omar Hassan',
    age: 28,
    gender: 'M',
    status: { code: 'active', label: 'Active', color: 'success' },
    lastVisit: '2024-01-10',
    condition: 'Asthma',
    provider: 'Sharjah University Hospital',
    insuranceId: 'INS003',
  },
];

const sampleAuthorizations: AuthorizationRecord[] = [
  {
    id: '1',
    authorizationId: 'AUTH001',
    patientName: 'Ahmed Al-Rashid',
    provider: 'Dubai Healthcare City',
    service: 'MRI Scan',
    status: { code: 'approved', label: 'Approved', color: 'success' },
    requestDate: '2024-01-10',
    approvalDate: '2024-01-12',
    expiryDate: '2024-02-12',
    amount: 2500,
    currency: 'AED',
  },
  {
    id: '2',
    authorizationId: 'AUTH002',
    patientName: 'Fatima Al-Zahra',
    provider: 'Abu Dhabi Medical Center',
    service: 'Cardiac Surgery',
    status: { code: 'pending', label: 'Pending Review', color: 'warning' },
    requestDate: '2024-01-08',
    amount: 45000,
    currency: 'AED',
  },
  {
    id: '3',
    authorizationId: 'AUTH003',
    patientName: 'Omar Hassan',
    provider: 'Sharjah University Hospital',
    service: 'Physiotherapy',
    status: { code: 'denied', label: 'Denied', color: 'error' },
    requestDate: '2024-01-05',
    amount: 800,
    currency: 'AED',
  },
];

const DataDisplayExample: React.FC = () => {
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [selectedPatients, setSelectedPatients] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'table' | 'datagrid' | 'components'>('table');

  // Patient table columns
  const patientColumns: TableColumn<PatientRecord>[] = [
    {
      key: 'patientId',
      title: 'Patient ID',
      dataIndex: 'patientId',
      sortable: true,
      width: 120,
    },
    {
      key: 'name',
      title: 'Patient Name',
      dataIndex: 'name',
      sortable: true,
      render: (value, record) => (
        <MedicalTooltip
          diagnosis={record.condition}
          description={`Last visit: ${record.lastVisit}`}
          severity="medium"
        >
          <span className="font-medium text-gray-900 cursor-help">{value}</span>
        </MedicalTooltip>
      ),
    },
    {
      key: 'age',
      title: 'Age',
      dataIndex: 'age',
      sortable: true,
      width: 80,
      align: 'center',
    },
    {
      key: 'gender',
      title: 'Gender',
      dataIndex: 'gender',
      width: 80,
      align: 'center',
      render: (value) => (
        <Badge size="sm" variant={value === 'M' ? 'info' : 'secondary'}>
          {value === 'M' ? 'Male' : value === 'F' ? 'Female' : 'Other'}
        </Badge>
      ),
    },
    {
      key: 'status',
      title: 'Status',
      dataIndex: 'status',
      sortable: true,
      width: 120,
      render: (status) => <StatusBadge status={status.code} label={status.label} />,
    },
    {
      key: 'condition',
      title: 'Primary Condition',
      dataIndex: 'condition',
      render: (value) => (
        <Tooltip title={`Primary diagnosis: ${value}`}>
          <span className="text-gray-700 cursor-help">{value}</span>
        </Tooltip>
      ),
    },
    {
      key: 'provider',
      title: 'Healthcare Provider',
      dataIndex: 'provider',
      sortable: true,
    },
    {
      key: 'actions',
      title: 'Actions',
      width: 120,
      render: (_, record) => (
        <div className="flex space-x-2">
          <Button size="sm" variant="tertiary">
            View
          </Button>
          <Button size="sm" variant="secondary">
            Edit
          </Button>
        </div>
      ),
    },
  ];

  // Authorization table columns
  const authorizationColumns: TableColumn<AuthorizationRecord>[] = [
    {
      key: 'authorizationId',
      title: 'Auth ID',
      dataIndex: 'authorizationId',
      sortable: true,
      width: 120,
      render: (value, record) => (
        <AuthorizationTooltip
          authId={record.authorizationId}
          status={record.status.label}
          approvalDate={record.approvalDate}
          expiryDate={record.expiryDate}
          amount={record.amount}
          currency={record.currency}
        >
          <span className="font-mono text-sm text-blue-600 cursor-help">{value}</span>
        </AuthorizationTooltip>
      ),
    },
    {
      key: 'patientName',
      title: 'Patient',
      dataIndex: 'patientName',
      sortable: true,
    },
    {
      key: 'service',
      title: 'Service',
      dataIndex: 'service',
      sortable: true,
    },
    {
      key: 'status',
      title: 'Status',
      dataIndex: 'status',
      sortable: true,
      width: 140,
      render: (status) => <StatusBadge status={status.code} label={status.label} />,
    },
    {
      key: 'amount',
      title: 'Amount',
      width: 120,
      align: 'right',
      render: (_, record) => (
        <span className="font-medium">
          {record.currency} {record.amount.toLocaleString()}
        </span>
      ),
    },
    {
      key: 'requestDate',
      title: 'Request Date',
      dataIndex: 'requestDate',
      sortable: true,
      width: 120,
    },
  ];

  const handlePatientSelection = (selectedRowKeys: string[], selectedRows: PatientRecord[]) => {
    setSelectedPatients(selectedRowKeys);
  };

  return (
    <div className="space-y-8 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Data Display Components</h1>
          <p className="text-gray-600 mt-2">
            Comprehensive healthcare data visualization components
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
          {[
            { key: 'table', label: 'Tables' },
            { key: 'datagrid', label: 'DataGrid' },
            { key: 'components', label: 'Components' },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as 'table' | 'datagrid' | 'components')}
              className={clsx(
                'px-4 py-2 rounded-md text-sm font-medium transition-colors',
                activeTab === tab.key
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table Examples */}
      {activeTab === 'table' && (
        <div className="space-y-8">
          {/* Patient Table */}
          <Card title="Patient Records" subtitle="Standard table with sorting and search">
            <PatientTable
              columns={patientColumns}
              data={samplePatients}
              size="md"
              hoverable={true}
              onRowClick={(record) => console.log('Patient clicked:', record)}
            />
          </Card>

          {/* Authorization Table */}
          <Card title="Authorization Records" subtitle="Healthcare authorization management">
            <AuthorizationTable
              columns={authorizationColumns}
              data={sampleAuthorizations}
              size="md"
              hoverable={true}
              onRowClick={(record) => console.log('Authorization clicked:', record)}
            />
          </Card>

          {/* Pagination Example */}
          <Card title="Pagination Examples">
            <div className="space-y-6">
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Patient Pagination</h4>
                <PatientPagination
                  current={currentPage}
                  total={156}
                  pageSize={pageSize}
                  patientCount={156}
                  activePatients={142}
                  onChange={(page, size) => {
                    setCurrentPage(page);
                    setPageSize(size);
                  }}
                />
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Medical Records Pagination</h4>
                <RecordsPagination
                  current={2}
                  total={1247}
                  pageSize={25}
                  recordType="medical records"
                  onChange={(page, size) => console.log('Page change:', page, size)}
                />
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Simple Pagination</h4>
                <Pagination
                  current={3}
                  total={89}
                  pageSize={10}
                  simple={true}
                  showTotal={true}
                  onChange={(page, size) => console.log('Simple page change:', page, size)}
                />
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* DataGrid Examples */}
      {activeTab === 'datagrid' && (
        <div className="space-y-8">
          {/* Patient DataGrid */}
          <Card title="Patient DataGrid" subtitle="Advanced table with virtual scrolling and selection">
            <PatientDataGrid
              columns={patientColumns}
              data={samplePatients}
              virtualScroll={false}
              selectable={true}
              selectedRowKeys={selectedPatients}
              onSelectionChange={handlePatientSelection}
              stickyHeader={true}
              resizable={true}
              onRowClick={(record) => console.log('Patient clicked:', record)}
            />
          </Card>

          {/* Authorization DataGrid */}
          <Card title="Authorization DataGrid" subtitle="High-performance data grid for large datasets">
            <AuthorizationDataGrid
              columns={authorizationColumns}
              data={sampleAuthorizations}
              virtualScroll={false}
              stickyHeader={true}
              resizable={true}
              pagination={{
                current: 1,
                total: 150,
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                onChange: (page, size) => console.log('Pagination:', page, size),
              }}
            />
          </Card>

          {/* Performance Info */}
          <Card title="Performance Features">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900">Virtual Scrolling</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Efficiently renders large datasets (10k+ rows) with smooth scrolling
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 text-green-600 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900">Row Selection</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Multi-select with keyboard shortcuts and bulk operations
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2M7 4h10l1 12H6L7 4z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900">Column Resize</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Resizable columns with persistent widths and fixed columns
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Individual Components */}
      {activeTab === 'components' && (
        <div className="space-y-8">
          {/* Badge Examples */}
          <Card title="Badge Components" subtitle="Status indicators and labels">
            <div className="space-y-6">
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Healthcare Status Badges</h4>
                <div className="flex flex-wrap gap-2">
                  <StatusBadge status="approved" />
                  <StatusBadge status="pending" />
                  <StatusBadge status="denied" />
                  <StatusBadge status="processing" />
                  <StatusBadge status="cancelled" />
                  <StatusBadge status="expired" />
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Priority Badges</h4>
                <div className="flex flex-wrap gap-2">
                  <PriorityBadge priority="low" />
                  <PriorityBadge priority="medium" />
                  <PriorityBadge priority="high" />
                  <PriorityBadge priority="urgent" />
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Badge Sizes & Variants</h4>
                <div className="space-y-3">
                  {(['sm', 'md', 'lg'] as const).map((size) => (
                    <div key={size} className="flex items-center gap-2">
                      <span className="w-12 text-sm text-gray-600">{size.toUpperCase()}:</span>
                      <Badge size={size} variant="default">Default</Badge>
                      <Badge size={size} variant="primary">Primary</Badge>
                      <Badge size={size} variant="success">Success</Badge>
                      <Badge size={size} variant="warning">Warning</Badge>
                      <Badge size={size} variant="error">Error</Badge>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Badge with Count</h4>
                <div className="flex gap-4">
                  <Badge count={5}>
                    <Button>Notifications</Button>
                  </Badge>
                  <Badge count={99}>
                    <Button>Messages</Button>
                  </Badge>
                  <Badge count={1000} overflowCount={999}>
                    <Button>Alerts</Button>
                  </Badge>
                  <Badge dot>
                    <Button>Status</Button>
                  </Badge>
                </div>
              </div>
            </div>
          </Card>

          {/* Tooltip Examples */}
          <Card title="Tooltip Components" subtitle="Contextual information and help">
            <div className="space-y-6">
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Basic Tooltips</h4>
                <div className="flex flex-wrap gap-4">
                  <Tooltip title="This is a top tooltip" placement="top">
                    <Button>Top</Button>
                  </Tooltip>
                  <Tooltip title="This is a bottom tooltip" placement="bottom">
                    <Button>Bottom</Button>
                  </Tooltip>
                  <Tooltip title="This is a left tooltip" placement="left">
                    <Button>Left</Button>
                  </Tooltip>
                  <Tooltip title="This is a right tooltip" placement="right">
                    <Button>Right</Button>
                  </Tooltip>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Medical Tooltips</h4>
                <div className="flex flex-wrap gap-4">
                  <MedicalTooltip
                    diagnosis="Diabetes Mellitus Type 2"
                    icdCode="E11.9"
                    severity="medium"
                    description="Non-insulin dependent diabetes mellitus without complications"
                  >
                    <Badge variant="warning">Diabetes T2</Badge>
                  </MedicalTooltip>
                  
                  <MedicalTooltip
                    diagnosis="Essential Hypertension"
                    icdCode="I10"
                    severity="high"
                    description="Primary hypertension requiring medication management"
                  >
                    <Badge variant="error">Hypertension</Badge>
                  </MedicalTooltip>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Authorization Tooltips</h4>
                <div className="flex flex-wrap gap-4">
                  <AuthorizationTooltip
                    authId="AUTH001"
                    status="Approved"
                    approvalDate="2024-01-12"
                    expiryDate="2024-02-12"
                    amount={2500}
                    currency="AED"
                  >
                    <Badge variant="success">AUTH001</Badge>
                  </AuthorizationTooltip>
                  
                  <AuthorizationTooltip
                    authId="AUTH002"
                    status="Pending Review"
                    amount={45000}
                    currency="AED"
                  >
                    <Badge variant="warning">AUTH002</Badge>
                  </AuthorizationTooltip>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Interactive Tooltips</h4>
                <div className="flex flex-wrap gap-4">
                  <Tooltip trigger="click" title="Click tooltip - click again to close">
                    <Button variant="secondary">Click Tooltip</Button>
                  </Tooltip>
                  <Tooltip trigger="focus" title="Focus tooltip - appears on focus">
                    <Button variant="secondary">Focus Tooltip</Button>
                  </Tooltip>
                </div>
              </div>
            </div>
          </Card>

          {/* Healthcare Use Cases */}
          <Card title="Healthcare Use Cases" subtitle="Real-world examples for medical applications">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Patient Management</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• Patient status tracking with color-coded badges</li>
                  <li>• Medical condition tooltips with ICD codes</li>
                  <li>• Pagination for large patient databases</li>
                  <li>• Sortable tables for efficient data browsing</li>
                </ul>
              </div>
              
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Authorization Processing</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• Authorization status badges with expiry dates</li>
                  <li>• Bulk selection for batch processing</li>
                  <li>• Virtual scrolling for thousands of records</li>
                  <li>• Resizable columns for custom workflows</li>
                </ul>
              </div>
              
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Clinical Data</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• Priority badges for urgent cases</li>
                  <li>• Medical tooltips for diagnostic codes</li>
                  <li>• Searchable tables for quick patient lookup</li>
                  <li>• Responsive design for mobile access</li>
                </ul>
              </div>
              
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Insurance Claims</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• Claim status tracking with timestamps</li>
                  <li>• Amount formatting with currency symbols</li>
                  <li>• Filterable tables for claim processing</li>
                  <li>• Export functionality for reporting</li>
                </ul>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

function clsx(...classes: (string | undefined | null | boolean)[]): string {
  return classes.filter(Boolean).join(' ');
}

export default DataDisplayExample;