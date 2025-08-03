# Data Display Components

A comprehensive set of React components for displaying healthcare data with excellent performance, accessibility, and user experience.

## Components Overview

### Table
Sortable, filterable data tables optimized for healthcare data presentation.

**Features:**
- Sorting and filtering capabilities
- Search functionality
- Responsive design
- Accessibility compliant (ARIA, keyboard navigation)
- Healthcare-specific variants (PatientTable, AuthorizationTable, MedicalRecordsTable)

**Basic Usage:**
```tsx
import { Table, PatientTable } from '@/components/ui';

const columns = [
  { key: 'id', title: 'ID', dataIndex: 'id', sortable: true },
  { key: 'name', title: 'Name', dataIndex: 'name', sortable: true },
  { key: 'status', title: 'Status', dataIndex: 'status', render: (status) => <StatusBadge status={status} /> }
];

<Table columns={columns} data={data} searchable hoverable />
<PatientTable columns={patientColumns} data={patients} />
```

### DataGrid
Advanced table component with virtual scrolling for large datasets.

**Features:**
- Virtual scrolling for 10k+ rows
- Column resizing and reordering
- Row selection with bulk operations
- Sticky headers
- Integrated pagination
- Performance optimizations

**Basic Usage:**
```tsx
import { DataGrid, PatientDataGrid } from '@/components/ui';

<DataGrid 
  columns={columns} 
  data={largeDataset}
  virtualScroll={true}
  selectable={true}
  stickyHeader={true}
  resizable={true}
/>

<PatientDataGrid 
  columns={patientColumns} 
  data={patients}
  onSelectionChange={(keys, rows) => console.log('Selected:', keys)}
/>
```

### Pagination
Flexible pagination component with healthcare-specific variants.

**Features:**
- Standard, simple, and custom pagination modes
- Page size selector
- Quick jump functionality
- Healthcare-specific display options
- Mobile responsive

**Basic Usage:**
```tsx
import { Pagination, PatientPagination, RecordsPagination } from '@/components/ui';

<Pagination 
  current={1} 
  total={100} 
  pageSize={10}
  showSizeChanger
  showQuickJumper
  onChange={(page, size) => handlePageChange(page, size)}
/>

<PatientPagination 
  current={1} 
  total={250} 
  pageSize={25}
  patientCount={250}
  activePatients={230}
/>

<RecordsPagination 
  current={1} 
  total={1500} 
  pageSize={50}
  recordType="medical records"
/>
```

### Badge
Status indicators and labels for healthcare applications.

**Features:**
- Multiple variants (success, warning, error, info, default)
- Healthcare status badges (approved, pending, denied, etc.)
- Priority badges for medical cases
- Dot and count badges
- Multiple sizes

**Basic Usage:**
```tsx
import { Badge, StatusBadge, PriorityBadge } from '@/components/ui';

<Badge variant="success">Active</Badge>
<Badge variant="warning" size="lg">Pending</Badge>
<Badge count={5}><Button>Notifications</Button></Badge>
<Badge dot><Button>Status</Button></Badge>

<StatusBadge status="approved" />
<StatusBadge status="pending" />
<StatusBadge status="denied" />

<PriorityBadge priority="urgent" />
<PriorityBadge priority="high" />
```

### Tooltip
Contextual help and information display with healthcare-specific variants.

**Features:**
- Multiple trigger modes (hover, click, focus)
- Flexible positioning (12 placement options)
- Medical condition tooltips with ICD codes
- Authorization information tooltips
- Responsive and accessible

**Basic Usage:**
```tsx
import { Tooltip, MedicalTooltip, AuthorizationTooltip } from '@/components/ui';

<Tooltip title="Helpful information" placement="top">
  <Button>Hover me</Button>
</Tooltip>

<MedicalTooltip
  diagnosis="Diabetes Mellitus Type 2"
  icdCode="E11.9"
  severity="medium"
  description="Non-insulin dependent diabetes"
>
  <Badge variant="warning">Diabetes T2</Badge>
</MedicalTooltip>

<AuthorizationTooltip
  authId="AUTH001"
  status="Approved"
  approvalDate="2024-01-12"
  amount={2500}
  currency="AED"
>
  <Badge variant="success">AUTH001</Badge>
</AuthorizationTooltip>
```

## Healthcare Use Cases

### Patient Management
- Patient lists with status indicators
- Medical condition displays with diagnostic codes
- Treatment history tables
- Insurance information panels

### Authorization Processing
- Pre-authorization request tables
- Approval status tracking
- Bulk authorization processing
- Expiry date monitoring

### Clinical Data
- Lab results display
- Diagnostic report tables
- Treatment plan tracking
- Clinical note organization

### Insurance Claims
- Claim status monitoring
- Amount and coverage display
- Provider information tables
- Payment tracking

## Performance Considerations

### Virtual Scrolling
- Automatically enabled for datasets > 100 rows (Table) or > 200 rows (DataGrid)
- Configurable row height and overscan
- Smooth scrolling performance with thousands of records

### Memory Management
- Efficient rendering with React.memo optimizations
- Lazy loading of cell content
- Automatic cleanup of event listeners

### Network Optimization
- Built-in debouncing for search and filter operations
- Optimistic updates for selection changes
- Minimal re-renders on data updates

## Accessibility Features

### Keyboard Navigation
- Full keyboard support for all interactive elements
- Arrow key navigation in tables
- Tab order management
- Focus indicators

### Screen Reader Support
- Proper ARIA labels and roles
- Table headers and captions
- Status announcements
- Sort order indicators

### Visual Accessibility
- High contrast mode support
- Scalable text and icons
- Color-blind friendly status indicators
- Reduced motion preferences

## Responsive Design

### Mobile Optimization
- Touch-friendly interaction targets
- Horizontal scrolling for wide tables
- Collapsible columns on small screens
- Mobile-first pagination controls

### Tablet Support
- Optimized for iPad and Android tablets
- Touch gesture support
- Adaptive column widths
- Context-sensitive tooltips

## Styling and Theming

### CSS Classes
All components use the established Tailwind CSS design system with custom component classes:

```css
/* Table Components */
.table-container { /* Wrapper styles */ }
.table-header-cell { /* Header cell styles */ }
.table-row-hover { /* Hover effects */ }

/* Badge Components */
.badge-success { /* Success variant */ }
.badge-warning { /* Warning variant */ }

/* Pagination Components */
.pagination-button-active { /* Active page */ }
.pagination-info { /* Page info display */ }
```

### Healthcare Color Scheme
- **Success**: Green tones for approved/active states
- **Warning**: Amber tones for pending/review states
- **Error**: Red tones for denied/critical states
- **Info**: Blue tones for informational states
- **Default**: Gray tones for neutral states

## Integration Examples

### Complete Patient Dashboard
```tsx
import { PatientDataGrid, StatusBadge, MedicalTooltip } from '@/components/ui';

const PatientDashboard = () => {
  const columns = [
    {
      key: 'patientId',
      title: 'Patient ID',
      dataIndex: 'patientId',
      sortable: true
    },
    {
      key: 'name',
      title: 'Patient Name',
      dataIndex: 'name',
      render: (value, record) => (
        <MedicalTooltip
          diagnosis={record.primaryDiagnosis}
          icdCode={record.icdCode}
          severity={record.severity}
        >
          <span className="font-medium cursor-help">{value}</span>
        </MedicalTooltip>
      )
    },
    {
      key: 'status',
      title: 'Status',
      dataIndex: 'status',
      render: (status) => <StatusBadge status={status} />
    }
  ];

  return (
    <PatientDataGrid
      columns={columns}
      data={patients}
      selectable={true}
      virtualScroll={true}
      pagination={{
        current: page,
        total: totalPatients,
        pageSize: 25,
        onChange: handlePageChange
      }}
    />
  );
};
```

### Authorization Processing Interface
```tsx
import { AuthorizationTable, AuthorizationTooltip, PriorityBadge } from '@/components/ui';

const AuthorizationManager = () => {
  const columns = [
    {
      key: 'authId',
      title: 'Authorization ID',
      dataIndex: 'authorizationId',
      render: (value, record) => (
        <AuthorizationTooltip
          authId={record.authorizationId}
          status={record.status}
          amount={record.amount}
          currency={record.currency}
        >
          <code className="text-blue-600 cursor-help">{value}</code>
        </AuthorizationTooltip>
      )
    },
    {
      key: 'priority',
      title: 'Priority',
      dataIndex: 'priority',
      render: (priority) => <PriorityBadge priority={priority} />
    },
    {
      key: 'status',
      title: 'Status',
      dataIndex: 'status',
      render: (status) => <StatusBadge status={status} />
    }
  ];

  return (
    <AuthorizationTable
      columns={columns}
      data={authorizations}
      onRowClick={handleAuthClick}
      searchable={true}
    />
  );
};
```

## Best Practices

### Performance
1. Use virtual scrolling for datasets > 500 rows
2. Implement pagination for better user experience
3. Debounce search and filter operations
4. Use React.memo for custom cell renderers

### Accessibility
1. Always provide meaningful ARIA labels
2. Ensure keyboard navigation works
3. Use semantic HTML elements
4. Test with screen readers

### Healthcare Data
1. Always display amounts with currency
2. Use consistent date formatting
3. Provide context through tooltips
4. Use color-coded status indicators

### Mobile Experience
1. Test on actual devices
2. Ensure touch targets are at least 44px
3. Provide horizontal scrolling for wide tables
4. Consider data prioritization on small screens