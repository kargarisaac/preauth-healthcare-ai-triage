#!/usr/bin/env python3
"""
Data Pipeline for XML to JSON Conversion
Converts synthetic XML dataset to JSON format using existing processors
for integration with Claude pre-authorization analysis system.

This script processes all XML files in the synthetic dataset through
the XMLProcessor to create JSON FHIR Bundle outputs that can be
consumed by the Claude multi-agent system.

Usage:
    python data_pipeline.py [--dry-run] [--patient-id PATIENT_ID]

Examples:
    python data_pipeline.py                    # Process all patients
    python data_pipeline.py --patient-id 1     # Process specific patient  
    python data_pipeline.py --dry-run          # Preview what would be processed
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from datetime import datetime
from loguru import logger
import pandas as pd

# Import existing processors  
try:
    from pipelines.xml_processor import XMLProcessor
    from pipelines.csv_processor import CSVProcessor
except ImportError:
    # Handle execution from pipelines directory
    from xml_processor import XMLProcessor
    from csv_processor import CSVProcessor

# Configure logging
logger.remove()  # Remove default handler
logger.add(
    "logs/data_pipeline.log",
    rotation="10 MB", 
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO"
)
logger.add(
    "logs/data_pipeline.log",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
    level="INFO"
)


class DataPipeline:
    """
    Data pipeline for converting synthetic XML dataset to JSON format
    using existing XMLProcessor and CSVProcessor implementations.
    """

    def __init__(self, 
                 source_dir: str = "data/synthetic_dataset",
                 output_dir: str = "data/processed_dataset",
                 enable_validation: bool = True):
        """
        Initialize data pipeline.

        Args:
            source_dir: Directory containing synthetic XML dataset
            output_dir: Directory for JSON outputs
            enable_validation: Enable data quality validation
        """
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.enable_validation = enable_validation
        
        # Initialize processors
        self.xml_processor = XMLProcessor(enable_validation=enable_validation)
        self.csv_processor = CSVProcessor(enable_validation=enable_validation)
        
        # Processing statistics
        self.stats = {
            'total_patients': 0,
            'total_files_processed': 0,
            'eclaim_files': 0,
            'shafafiya_files': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
        logger.info(f"Initialized DataPipeline: {source_dir} → {output_dir}")

    def setup_output_directory(self) -> None:
        """Create output directory structure."""
        logger.info("Setting up output directory structure")
        
        # Create main output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        (self.output_dir / "json_bundles").mkdir(exist_ok=True)
        (self.output_dir / "metadata").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)
        
        logger.info(f"Output directory structure created at {self.output_dir}")

    def detect_xml_format(self, xml_file: Path) -> str:
        """
        Detect XML format (eClaimLink or Shafafiya) from filename.
        
        Args:
            xml_file: Path to XML file
            
        Returns:
            Format type: 'eclaim' or 'shafafiya'
        """
        filename = xml_file.name.lower()
        
        if 'eclaim' in filename:
            return 'eclaim'
        elif 'shafafiya' in filename:
            return 'shafafiya'
        else:
            # Fallback: check file content for format detection
            try:
                with open(xml_file, 'r', encoding='utf-8') as f:
                    content = f.read(500)  # Read first 500 chars
                    if 'Prior.Authorization' in content:
                        return 'shafafiya'
                    elif 'ServiceRequest' in content or 'eClaimLink' in content:
                        return 'eclaim'
            except Exception:
                pass
        
        # Default fallback
        logger.warning(f"Could not detect format for {xml_file}, defaulting to shafafiya")
        return 'shafafiya'

    def process_xml_file(self, xml_file: Path, format_type: str) -> Optional[Dict[str, Any]]:
        """
        Process single XML file to JSON using appropriate processor.
        
        Args:
            xml_file: Path to XML file
            format_type: 'eclaim' or 'shafafiya'
            
        Returns:
            JSON bundle dictionary or None if processing failed
        """
        try:
            logger.info(f"Processing {format_type} file: {xml_file.name}")
            
            if format_type == 'eclaim':
                result = self.xml_processor.process_eclaim_link(str(xml_file))
                self.stats['eclaim_files'] += 1
            elif format_type == 'shafafiya':
                result = self.xml_processor.process_shafafiya(str(xml_file))
                self.stats['shafafiya_files'] += 1
            else:
                raise ValueError(f"Unknown format type: {format_type}")
            
            # Add pipeline metadata
            result['pipeline_metadata'] = {
                'source_file': str(xml_file),
                'format_detected': format_type,
                'pipeline_version': '1.0',
                'processed_timestamp': datetime.now().isoformat(),
                'processor_used': 'XMLProcessor'
            }
            
            logger.info(f"Successfully processed {xml_file.name}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process {xml_file}: {e}")
            self.stats['errors'] += 1
            return None

    def save_json_bundle(self, bundle: Dict[str, Any], output_file: Path) -> bool:
        """
        Save JSON bundle to file.
        
        Args:
            bundle: JSON bundle dictionary
            output_file: Output file path
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save JSON with proper formatting
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(bundle, f, indent=2, ensure_ascii=False, default=str)
            
            logger.debug(f"Saved JSON bundle: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save JSON bundle {output_file}: {e}")
            return False

    def copy_metadata_files(self, patient_dir: Path, output_patient_dir: Path) -> None:
        """
        Copy profile.json and dataset_index.csv to output directory.
        
        Args:
            patient_dir: Source patient directory
            output_patient_dir: Output patient directory
        """
        try:
            # Copy profile.json
            profile_file = patient_dir / 'profile.json'
            if profile_file.exists():
                shutil.copy2(profile_file, output_patient_dir / 'profile.json')
                logger.debug(f"Copied profile.json for patient {patient_dir.name}")
            
            # Copy dataset_index.csv
            index_file = patient_dir / 'dataset_index.csv'
            if index_file.exists():
                shutil.copy2(index_file, output_patient_dir / 'dataset_index.csv')
                logger.debug(f"Copied dataset_index.csv for patient {patient_dir.name}")
                
        except Exception as e:
            logger.warning(f"Failed to copy metadata files for patient {patient_dir.name}: {e}")

    def process_patient(self, patient_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Process all XML files for a specific patient.
        
        Args:
            patient_id: Patient ID (directory name)
            dry_run: If True, only simulate processing
            
        Returns:
            Processing results summary
        """
        patient_dir = self.source_dir / patient_id
        output_patient_dir = self.output_dir / patient_id
        
        if not patient_dir.exists():
            logger.error(f"Patient directory not found: {patient_dir}")
            return {'status': 'error', 'message': 'Patient directory not found'}
        
        logger.info(f"Processing patient {patient_id} ({'DRY RUN' if dry_run else 'LIVE'})")
        
        # Find all XML files
        xml_files = list(patient_dir.glob('*.xml'))
        if not xml_files:
            logger.warning(f"No XML files found for patient {patient_id}")
            return {'status': 'warning', 'message': 'No XML files found'}
        
        processed_files = []
        failed_files = []
        
        if not dry_run:
            # Create output directory
            output_patient_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy metadata files
            self.copy_metadata_files(patient_dir, output_patient_dir)
        
        # Process each XML file
        for xml_file in sorted(xml_files):
            if dry_run:
                # Just detect format and log what would be processed
                format_type = self.detect_xml_format(xml_file)
                logger.info(f"[DRY RUN] Would process {xml_file.name} as {format_type}")
                processed_files.append({
                    'source_file': xml_file.name,
                    'format': format_type,
                    'output_file': f"{xml_file.stem}.json"
                })
            else:
                # Actually process the file
                format_type = self.detect_xml_format(xml_file)
                bundle = self.process_xml_file(xml_file, format_type)
                
                if bundle:
                    # Save JSON bundle
                    json_file = output_patient_dir / f"{xml_file.stem}.json"
                    if self.save_json_bundle(bundle, json_file):
                        processed_files.append({
                            'source_file': xml_file.name,
                            'format': format_type,
                            'output_file': json_file.name,
                            'bundle_id': bundle.get('id'),
                            'services_count': len(bundle.get('services', [])),
                            'activities_count': len(bundle.get('activities', []))
                        })
                        self.stats['total_files_processed'] += 1
                    else:
                        failed_files.append(xml_file.name)
                else:
                    failed_files.append(xml_file.name)
        
        return {
            'status': 'completed' if not failed_files else 'partial',
            'patient_id': patient_id,
            'processed_files': len(processed_files),
            'failed_files': len(failed_files),
            'details': {
                'processed': processed_files,
                'failed': failed_files
            }
        }

    def process_all_patients(self, dry_run: bool = False, 
                           patient_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Process all patients in the synthetic dataset.
        
        Args:
            dry_run: If True, only simulate processing
            patient_filter: If provided, only process this specific patient ID
            
        Returns:
            Complete processing results
        """
        self.stats['start_time'] = datetime.now()
        logger.info(f"Starting batch processing ({'DRY RUN' if dry_run else 'LIVE'})")
        
        if not dry_run:
            self.setup_output_directory()
        
        # Find all patient directories
        patient_dirs = [d for d in self.source_dir.iterdir() 
                       if d.is_dir() and d.name.isdigit()]
        
        if patient_filter:
            patient_dirs = [d for d in patient_dirs if d.name == patient_filter]
            if not patient_dirs:
                logger.error(f"Patient {patient_filter} not found")
                return {'status': 'error', 'message': f'Patient {patient_filter} not found'}
        
        patient_dirs = sorted(patient_dirs, key=lambda x: int(x.name))
        self.stats['total_patients'] = len(patient_dirs)
        
        logger.info(f"Found {len(patient_dirs)} patients to process")
        
        patient_results = {}
        successful_patients = 0
        
        # Process each patient
        for patient_dir in patient_dirs:
            patient_id = patient_dir.name
            result = self.process_patient(patient_id, dry_run)
            patient_results[patient_id] = result
            
            if result['status'] in ['completed', 'partial']:
                successful_patients += 1
        
        self.stats['end_time'] = datetime.now()
        processing_time = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        # Generate summary
        summary = {
            'status': 'completed',
            'dry_run': dry_run,
            'processing_time_seconds': processing_time,
            'statistics': self.stats,
            'patient_results': patient_results,
            'summary': {
                'total_patients': len(patient_dirs),
                'successful_patients': successful_patients,
                'total_files_processed': self.stats['total_files_processed'],
                'eclaim_files': self.stats['eclaim_files'], 
                'shafafiya_files': self.stats['shafafiya_files'],
                'errors': self.stats['errors']
            }
        }
        
        if not dry_run:
            # Save processing summary
            summary_file = self.output_dir / 'metadata' / 'processing_summary.json'
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Processing summary saved to {summary_file}")
        
        logger.info(f"Batch processing completed: {successful_patients}/{len(patient_dirs)} patients successful")
        return summary


def main():
    """Main entry point for data pipeline."""
    parser = argparse.ArgumentParser(description="Convert synthetic XML dataset to JSON format")
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview what would be processed without making changes')
    parser.add_argument('--patient-id', type=str,
                       help='Process only specific patient ID')
    parser.add_argument('--source-dir', type=str, default='data/synthetic_dataset',
                       help='Source directory containing XML files')
    parser.add_argument('--output-dir', type=str, default='data/processed_dataset', 
                       help='Output directory for JSON files')
    parser.add_argument('--disable-validation', action='store_true',
                       help='Disable data quality validation')
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    print("🔄 Nazmito Data Pipeline - XML to JSON Conversion")
    print("=" * 60)
    print(f"📁 Source: {args.source_dir}")
    print(f"📁 Output: {args.output_dir}")
    if args.patient_id:
        print(f"👤 Patient Filter: {args.patient_id}")
    if args.dry_run:
        print("🔍 Mode: DRY RUN (preview only)")
    else:
        print("⚡ Mode: LIVE PROCESSING")
    print("=" * 60)
    
    try:
        # Initialize pipeline
        pipeline = DataPipeline(
            source_dir=args.source_dir,
            output_dir=args.output_dir,
            enable_validation=not args.disable_validation
        )
        
        # Run processing
        results = pipeline.process_all_patients(
            dry_run=args.dry_run,
            patient_filter=args.patient_id
        )
        
        # Display results
        if results['status'] == 'completed':
            summary = results['summary']
            print(f"\n✅ Processing completed successfully!")
            print(f"👥 Patients: {summary['successful_patients']}/{summary['total_patients']}")
            print(f"📄 Files: {summary['total_files_processed']} processed")
            print(f"🏥 eClaimLink: {summary['eclaim_files']} files")
            print(f"🏥 Shafafiya: {summary['shafafiya_files']} files")
            
            if summary['errors'] > 0:
                print(f"⚠️  Errors: {summary['errors']}")
            
            if not args.dry_run:
                print(f"📁 Output saved to: {args.output_dir}")
            
        else:
            print(f"\n❌ Processing failed: {results.get('message', 'Unknown error')}")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Processing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        logger.error(f"Main execution failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())