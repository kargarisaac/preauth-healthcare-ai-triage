#!/bin/bash

# Nazmito AI Pre-Authorization Analysis System
# User-friendly bash wrapper for the Python orchestrator
# 
# Usage: ./preauth_analyze <current_request.xml> <patient_folder>
# Example: ./preauth_analyze data/current_request.xml data/patient_123/

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
    echo "Usage: $0 <current_request.xml> <patient_folder>"
    echo ""
    echo "Arguments:"
    echo "  current_request.xml    Path to the current pre-authorization request XML file"
    echo "  patient_folder         Path to the patient's historical data folder"
    echo ""
    echo "Examples:"
    echo "  $0 data/current_request.xml data/patient_folder_10/"
    echo "  $0 /path/to/request.xml /path/to/patient_data/"
    echo ""
    echo "Requirements:"
    echo "  - Python 3.7+ with Claude Code SDK installed"
    echo "  - Patient folder must contain profile.json and dataset_index.csv"
    echo "  - Current request must be a valid XML file"
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

validate_xml_file() {
    local xml_file="$1"
    
    if [[ ! -f "$xml_file" ]]; then
        print_error "XML file not found: $xml_file"
        return 1
    fi
    
    # Basic XML validation
    if ! $PYTHON_CMD -c "
import xml.etree.ElementTree as ET
try:
    ET.parse('$xml_file')
    print('XML validation successful')
except ET.ParseError as e:
    print(f'XML validation failed: {e}')
    exit(1)
" 2>/dev/null; then
        print_error "Invalid XML file: $xml_file"
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
    
    # Check for required files
    local required_files=("profile.json" "dataset_index.csv")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$patient_folder/$file" ]]; then
            print_error "Required file missing: $patient_folder/$file"
            return 1
        fi
    done
    
    return 0
}

create_directories() {
    # Ensure required directories exist
    mkdir -p "logs"
    mkdir -p "analysis_results"
    print_info "Created necessary directories"
}

run_analysis() {
    local xml_file="$1"
    local patient_folder="$2"
    
    print_info "Starting comprehensive pre-authorization analysis..."
    print_info "Request file: $xml_file"
    print_info "Patient data: $patient_folder"
    echo ""
    
    # Run the Python orchestrator
    if $PYTHON_CMD "$ORCHESTRATOR" "$xml_file" "$patient_folder"; then
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
    
    local xml_file="$1"
    local patient_folder="$2"
    
    # Convert relative paths to absolute paths
    xml_file=$(realpath "$xml_file" 2>/dev/null || echo "$xml_file")
    patient_folder=$(realpath "$patient_folder" 2>/dev/null || echo "$patient_folder")
    
    print_info "Performing system checks..."
    
    # System checks
    check_python
    check_orchestrator
    create_directories
    
    print_info "Validating input files..."
    
    # Input validation
    if ! validate_xml_file "$xml_file"; then
        print_error "XML file validation failed"
        exit 1
    fi
    print_success "XML file validation passed"
    
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
    run_analysis "$xml_file" "$patient_folder"
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
    print_info "Version: 1.0.0"
    print_info "Python Orchestrator: claude_preauth_orchestrator_20250803.py"
    print_info "Specialized Agents: 5 medical analysis agents"
    exit 0
fi

# Run main function
main "$@"