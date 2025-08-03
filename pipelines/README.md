# Data Pipeline Commands

## Batch XML to JSON Conversion

Process XML dataset to JSON using existing processors:

```bash
# Process all synthetic XML files to JSON (from project root)
python -m pipelines.data_pipeline

# Process specific patient dataset
python -m pipelines.data_pipeline --patient-id 1

# Process custom source directory
python -m pipelines.data_pipeline --source-dir data/synthetic_dataset --output-dir data/processed_dataset

# Preview what would be processed (dry run)
python -m pipelines.data_pipeline --dry-run

# Process with custom paths and options
python -m pipelines.data_pipeline --source-dir /path/to/xml/files --output-dir /path/to/json/output --patient-id 3
```

## Claude Pre-Authorization Analysis

Analyze processed JSON files using the Claude multi-agent system:

```bash
# Run analysis on processed JSON data (from project root)
chmod +x claude_preauth_system/preauth_analyze.sh
./claude_preauth_system/preauth_analyze.sh data/processed_dataset/1/abudhabi_11f5688b-6c4a-4c41-baad-71e6a4b82d91_20200214_req01_shafafiya.json data/processed_dataset/1/

# View results
ls analysis_results/analysis_*/
```

## Direct XML/CSV Processing (No AI Analysis)

Direct processing without AI analysis (requires Python commands for processor instantiation).

## Complete Workflow

```bash
# 1. Process XML dataset to JSON (from project root)
python -m pipelines.data_pipeline --source-dir data/synthetic_dataset --output-dir data/processed_dataset

# 2. Run Claude analysis on processed JSON (from project root)
chmod +x claude_preauth_system/preauth_analyze.sh
./claude_preauth_system/preauth_analyze.sh data/processed_dataset/1/abudhabi_11f5688b-6c4a-4c41-baad-71e6a4b82d91_20200214_req01_shafafiya.json data/processed_dataset/1/

# 3. View analysis results
ls analysis_results/analysis_*/
```

## Command Line Options

Available options for `python -m pipelines.data_pipeline`:

- `--source-dir`: Source directory containing XML files (default: `data/synthetic_dataset`)
- `--output-dir`: Output directory for JSON files (default: `data/processed_dataset`) 
- `--patient-id`: Process only specific patient ID (e.g., `--patient-id 1`)
- `--dry-run`: Preview what would be processed without making changes
- `--disable-validation`: Disable data quality validation during processing

## Expected Folder Structure

The data pipeline expects the following directory structure:

### Source Directory Structure
```
data/synthetic_dataset/
├── 1/                          # Patient ID folder
│   ├── profile.json            # Patient profile information
│   ├── *.xml                   # XML files (eClaimLink or Shafafiya format)
│   └── dataset_index.csv       # Optional: file index
├── 2/                          # Another patient
│   ├── profile.json
│   └── *.xml
└── ...
```

### Output Directory Structure
```
data/processed_dataset/
├── 1/                          # Patient ID folder (matches source)
│   ├── profile.json            # Copied from source
│   ├── *.json                  # Converted JSON FHIR Bundles
│   └── ...
├── 2/
│   ├── profile.json
│   ├── *.json
│   └── ...
├── json_bundles/               # All JSON files (flat structure)
├── logs/                       # Processing logs
└── metadata/                   # Processing metadata
    └── processing_summary.json
```

**Note**: Each patient folder must contain a `profile.json` file. XML files are automatically detected and converted to corresponding JSON FHIR Bundle files.