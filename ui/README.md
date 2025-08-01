# Nazmito UI - Healthcare Pre-Authorization Dashboard

This directory contains the web interface for Nazmito's healthcare pre-authorization platform, supporting both XML and CSV file processing with AI-powered clinical intelligence.

## Folder Structure

```
ui/
├── landing/                    # Marketing website
│   ├── index.html             # Main landing page
│   ├── styles.css             # Design system and styling
│   └── script.js              # Interactive functionality
├── dashboard/                  # Multi-format processing interface
│   ├── dashboard.html         # Main dashboard interface
│   ├── dashboard.css          # Dashboard-specific styles (including CSV components)
│   └── dashboard.js           # Processing logic with XML and CSV support
├── assets/                     # Shared brand assets
│   └── logo.png               # Nazmito brand logo
└── README.md                   # This documentation file
```

### Landing Page (`/landing/`)
- **Purpose**: Professional marketing website showcasing Nazmito's capabilities
- **Features**: Hero section, feature showcase, testimonials, contact forms
- **Navigation**: Seamless link to dashboard for hands-on experience

### Dashboard (`/dashboard/`)
- **Purpose**: Production-ready multi-format processing interface
- **Features**: XML/CSV upload, intelligent processing, results display, data export
- **Integration**: FastAPI backend for XML, client-side CSV processing
- **CSV Support**: Schema detection, FHIR mapping, quality scoring

## Dashboard Features

### Multi-Format File Processing
- **Drag & Drop Interface**: Upload XML/CSV files by dragging them to the upload area
- **File Validation**: Automatic validation for XML/CSV formats and 10MB size limit
- **Quad Processing Modes**:
  - eClaimLink (Dubai DHA XML)
  - Shafafiya (Abu Dhabi DOH XML)
  - Claims CSV (Healthcare claims data)
  - Clinical CSV (Patient clinical data)
- **Sample Files**: Test with built-in sample files for all formats
- **Smart Format Detection**: Automatic UI adaptation based on file type

### Results Display
Three comprehensive tabs with format-specific content:

1. **📊 Summary Tab**
   - **XML Files**: Clinical assessment, AI confidence scores, key metrics
   - **CSV Files**: Data quality scores, schema analysis, FHIR mapping overview
   - Processing metadata and format-specific insights

2. **🔍 Details Tab**
   - **XML Files**: Financial details, cost breakdown, coverage information
   - **CSV Files**: Data schema breakdown, column-to-FHIR mapping, data preview tables
   - Interactive data exploration with responsive tables

3. **📄 Raw Data Tab**
   - **XML Files**: Complete JSON structure with syntax highlighting
   - **CSV Files**: Raw CSV content with copy functionality and processing metadata
   - Original data preservation with quality metrics

### Key Features
- **Real-time Processing**: Live status updates during XML/CSV processing
- **Intelligent CSV Analysis**: Schema detection, data type identification, quality scoring
- **FHIR Mapping**: Automatic mapping of CSV columns to healthcare data standards
- **Error Handling**: Comprehensive validation with user-friendly error messages
- **Data Export**: Download processed results as JSON for further analysis
- **Responsive Design**: Mobile-first approach with tablet/desktop optimization
- **Professional UI**: Healthcare-focused design with accessibility compliance

## Usage

### Prerequisites
1. **Backend API**: Ensure the FastAPI backend is running at `http://localhost:8000` (for XML processing)
2. **Sample Files**: Verify sample XML files exist in the `/samples` directory
3. **Modern Browser**: Chrome 90+, Firefox 88+, Safari 14+, or Edge 90+

*Note: CSV processing works entirely client-side and doesn't require backend API*

### Starting the Dashboard

#### Option 1: Direct File Access
```bash
# Open dashboard directly in browser (from project root)
open ui/dashboard/dashboard.html
```

#### Option 2: Local Server (Recommended)
```bash
# Start a local HTTP server in the ui directory
cd ui
python3 -m http.server 8080

# Then visit: http://localhost:8080/dashboard/dashboard.html
```

### API Integration

#### XML Processing (Backend)
The dashboard integrates with these FastAPI endpoints:

- `POST /api/process/eclaim` - Process uploaded eClaimLink XML
- `POST /api/process/shafafiya` - Process uploaded Shafafiya XML
- `POST /api/process/sample/eclaim` - Process eClaimLink sample file
- `POST /api/process/sample/shafafiya` - Process Shafafiya sample file
- `GET /api/health` - Health check endpoint

#### CSV Processing (Client-Side)
CSV files are processed entirely in the browser:

- **Schema Detection**: Automatic column type identification
- **FHIR Mapping**: Healthcare data standard mapping
- **Quality Analysis**: Data completeness and consistency scoring
- **No Server Storage**: Secure client-side processing without data transmission

### Workflow

#### XML Files
1. **Upload File**: Drag XML file to upload area or click to browse
2. **Choose Format**: Select eClaimLink or Shafafiya processing
3. **Server Processing**: File sent to backend API for processing
4. **View Results**: Explore clinical and financial data in three tabs
5. **Download**: Export results as JSON for further analysis

#### CSV Files
1. **Upload File**: Drag CSV file to upload area or click to browse
2. **Choose Format**: Select Claims CSV or Clinical CSV processing
3. **Client Processing**: File analyzed locally with schema detection
4. **View Results**: Explore data quality, schema, and FHIR mapping
5. **Export Data**: Copy raw data or download processed results

## Design System

The dashboard extends the main design system defined in `styles.css`:

### Colors
- **Primary**: `#ff6b35` (Nazmito orange)
- **Secondary**: `#1a1a1a` (Dark gray)
- **Surface**: `#fafafa` (Light background)
- **Text**: Hierarchical gray scale

### Typography
- **Primary Font**: Inter (Google Fonts)
- **Monospace**: JetBrains Mono (for code display)
- **Responsive**: Fluid sizing with clamp()

### Components
- **Buttons**: Primary/secondary variants with hover effects
- **Cards**: Elevated surfaces with subtle shadows
- **Tabs**: Clean navigation with active states
- **Metrics**: Visual display of key processing statistics
- **Quality Bars**: Visual data quality indicators for CSV files
- **Schema Tables**: Responsive tables for CSV column analysis
- **Data Type Badges**: Color-coded indicators for different data types

## Browser Support

- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+
- **Mobile**: Responsive design supports all screen sizes
- **Features Used**: CSS Grid, Flexbox, CSS Custom Properties, Fetch API

## Security Considerations

- **File Validation**: Client-side file type and size validation (10MB limit)
- **Error Handling**: Sanitized error messages prevent information leakage
- **CORS**: Backend configured for appropriate cross-origin requests
- **CSV Privacy**: CSV processing happens entirely client-side, no data transmission
- **No Data Storage**: Neither XML nor CSV files are stored on server
- **PHI Protection**: No protected health information persisted in browser storage

## Development

### Customization
- Modify `dashboard.css` for styling changes
- Update `dashboard.js` for functionality enhancements
- Extend API integration by adding new endpoints

### Testing
#### XML Processing
- Test with sample XML files first
- Verify backend API connectivity
- Test error scenarios (large files, invalid XML)

#### CSV Processing
- Test with various CSV formats and structures
- Verify schema detection accuracy
- Test large CSV files (up to 10MB)
- Validate FHIR mapping logic

#### General
- Validate responsive design on different screen sizes
- Test file drag-and-drop functionality
- Verify error handling for unsupported formats

## Integration with Main Website

The dashboard is seamlessly integrated with the main landing page:
- **Navigation**: Dashboard link in main navigation
- **Hero CTA**: "Try Dashboard" button in hero section
- **Consistent Branding**: Shared design language and components
- **Smooth Transitions**: Users can easily move between marketing and functionality

This creates a cohesive user experience from marketing exploration to hands-on XML processing.
