#!/bin/bash

# Nazmito AI Pre-Authorization Analysis System
# User-friendly bash wrapper for the Python orchestrator
# 
# Usage: ./preauth_analyze <current_request.json> <patient_folder>
# Example: ./preauth_analyze ../data/processed_data/11f5688b-6c4a-4c41-baad-71e6a4b82d91/abudhabi_11f5688b-6c4a-4c41-baad-71e6a4b82d91_20200214_req01_shafafiya.json ../data/processed_data/11f5688b-6c4a-4c41-baad-71e6a4b82d91/

set -e  # Exit on any error

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORCHESTRATOR="$SCRIPT_DIR/orchestrator.py"
PYTHON_CMD="python3"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "${CYAN}🏥 Nazmito AI Pre-Authorization Analysis System${NC}"
    echo -e "${CYAN}===============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ Error: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  Warning: $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_usage() {
    echo "Usage: $0 <current_request.json> <patient_folder>"
    echo ""
    echo "Arguments:"
    echo "  current_request.json   Path to the current pre-authorization request JSON file (FHIR Bundle)"
    echo "  patient_folder         Path to the patient's historical data folder"
    echo ""
    echo "Examples:"
    echo "  $0 ../data/processed_data/11f5688b-6c4a-4c41-baad-71e6a4b82d91/abudhabi_11f5688b-6c4a-4c41-baad-71e6a4b82d91_20200214_req01_shafafiya.json ../data/processed_data/11f5688b-6c4a-4c41-baad-71e6a4b82d91/"
    echo "  $0 /path/to/current_request.json /path/to/patient_folder/"
    echo ""
    echo "Requirements:"
    echo "  - Python 3.7+ with Claude Code SDK installed"
    echo "  - Patient folder must contain profile.json"
    echo "  - Current request must be a valid FHIR Bundle JSON file"
    echo ""
    echo "Data Format:"
    echo "  - JSON files should be generated using pipelines/data_pipeline.py (XML→JSON conversion)"
    echo "  - Patient folders are UUID-based (e.g., 11f5688b-6c4a-4c41-baad-71e6a4b82d91)"
    echo "  - Historical files in FHIR Bundle JSON format"
    echo ""
    echo "Output:"
    echo "  - Comprehensive analysis report in analysis_results/analysis_TIMESTAMP/"
    echo "  - Individual agent reports for detailed review"
    echo "  - Processing logs in logs/preauth_orchestrator.log"
}

# Validation functions
check_python() {
    if ! command -v $PYTHON_CMD &> /dev/null; then
        print_error "Python 3 is not installed or not in PATH"
        print_info "Please install Python 3.7+ to use this system"
        exit 1
    fi
    
    local python_version=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    print_info "Using Python $python_version"
}

check_orchestrator() {
    if [[ ! -f "$ORCHESTRATOR" ]]; then
        print_error "Python orchestrator not found at: $ORCHESTRATOR"
        print_info "Please ensure the orchestrator script is available"
        exit 1
    fi
}

validate_json_file() {
    local json_file="$1"
    
    if [[ ! -f "$json_file" ]]; then
        print_error "JSON file not found: $json_file"
        return 1
    fi
    
    # Basic JSON validation and FHIR Bundle check
    if ! $PYTHON_CMD -c "
import json
try:
    with open('$json_file', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Validate FHIR Bundle structure
    if not isinstance(data, dict):
        print('JSON validation failed: Not a valid JSON object')
        exit(1)
    
    if data.get('resourceType') != 'Bundle':
        print('FHIR validation failed: Not a valid FHIR Bundle')
        exit(1)
        
    print('JSON FHIR Bundle validation successful')
    print(f'Bundle ID: {data.get(\"id\", \"unknown\")}')
    print(f'Source: {data.get(\"meta\", {}).get(\"source\", \"unknown\")}')
    
except json.JSONDecodeError as e:
    print(f'JSON validation failed: {e}')
    exit(1)
except Exception as e:
    print(f'Validation failed: {e}')
    exit(1)
" 2>/dev/null; then
        print_error "Invalid JSON file or FHIR Bundle: $json_file"
        return 1
    fi
    
    return 0
}

validate_patient_folder() {
    local patient_folder="$1"
    
    if [[ ! -d "$patient_folder" ]]; then
        print_error "Patient folder not found: $patient_folder"
        return 1
    fi
    
    # Check for required files (dataset_index.csv is now optional)
    local required_files=("profile.json")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$patient_folder/$file" ]]; then
            print_error "Required file missing: $patient_folder/$file"
            return 1
        fi
    done
    
    # Check for additional JSON files (patient history)
    local json_count=$(find "$patient_folder" -name "*.json" -not -name "profile.json" | wc -l)
    if [[ $json_count -gt 0 ]]; then
        print_info "Found $json_count additional JSON files for patient history"
    fi
    
    return 0
}

create_directories() {
    # Ensure required directories exist
    mkdir -p "logs"
    mkdir -p "analysis_results"
    print_info "Created necessary directories"
}

run_analysis() {
    local json_file="$1"
    local patient_folder="$2"
    
    print_info "Starting comprehensive pre-authorization analysis..."
    print_info "FHIR Bundle: $json_file"
    print_info "Patient data: $patient_folder"
    echo ""
    
    # Run the Python orchestrator
    if $PYTHON_CMD "$ORCHESTRATOR" "$json_file" "$patient_folder"; then
        echo ""
        print_success "Analysis completed successfully!"
        print_info "Check the output directory for detailed reports"
        
        # Find and display the most recent analysis results directory
        local latest_output=$(find analysis_results -name "analysis_*" -type d | sort | tail -n 1)
        if [[ -n "$latest_output" ]]; then
            print_info "Latest analysis results: $latest_output"
            
            # Display key files if they exist
            if [[ -f "$latest_output/comprehensive_final_report.md" ]]; then
                print_success "Final report: $latest_output/comprehensive_final_report.md"
            fi
            
            if [[ -f "$latest_output/analysis_metadata.json" ]]; then
                print_success "Metadata: $latest_output/analysis_metadata.json"
            fi
            
            # Count individual agent reports
            local agent_reports=$(find "$latest_output" -name "*_analysis.md" | wc -l)
            if [[ $agent_reports -gt 0 ]]; then
                print_success "Individual agent reports: $agent_reports files"
            fi
        fi
        
    else
        echo ""
        print_error "Analysis failed - check logs for details"
        print_info "Log file: logs/preauth_orchestrator.log"
        exit 1
    fi
}

# Main script logic
main() {
    print_header
    
    # Check arguments
    if [[ $# -ne 2 ]]; then
        print_error "Invalid number of arguments"
        echo ""
        print_usage
        exit 1
    fi
    
    local json_file="$1"
    local patient_folder="$2"
    
    # Convert relative paths to absolute paths
    json_file=$(realpath "$json_file" 2>/dev/null || echo "$json_file")
    patient_folder=$(realpath "$patient_folder" 2>/dev/null || echo "$patient_folder")
    
    print_info "Performing system checks..."
    
    # System checks
    check_python
    check_orchestrator
    create_directories
    
    print_info "Validating input files..."
    
    # Input validation
    if ! validate_json_file "$json_file"; then
        print_error "JSON file validation failed"
        exit 1
    fi
    print_success "JSON file validation passed"
    
    if ! validate_patient_folder "$patient_folder"; then
        print_error "Patient folder validation failed"
        exit 1
    fi
    print_success "Patient folder validation passed"
    
    # Check for Claude Code SDK
    if ! $PYTHON_CMD -c "import claude_code_sdk" 2>/dev/null; then
        print_warning "Claude Code SDK not detected"
        print_info "Install with: pip install claude-code-sdk"
        print_info "Proceeding anyway - orchestrator will handle SDK validation"
    else
        print_success "Claude Code SDK detected"
    fi
    
    echo ""
    print_info "All validations passed - starting analysis..."
    echo ""
    
    # Run the analysis
    run_analysis "$json_file" "$patient_folder"
}

# Handle interruption gracefully
trap 'print_warning "Analysis interrupted by user"; exit 130' INT

# Help option
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    print_header
    echo ""
    print_usage
    exit 0
fi

# Version option
if [[ "$1" == "-v" || "$1" == "--version" ]]; then
    print_header
    echo ""
    print_info "Version: 1.1.0"
    print_info "Python Orchestrator: orchestrator.py (enhanced with embedded agents)"
    print_info "Specialized Agents: 5 self-contained medical analysis agents"
    exit 0
fi

# Run main function
main "$@"