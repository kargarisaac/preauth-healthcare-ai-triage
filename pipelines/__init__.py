"""
Healthcare Data Processing Pipeline.

This package provides robust processing capabilities for healthcare data from
UAE healthcare systems, supporting both XML and CSV formats with comprehensive
data quality analysis and schema detection.

Usage:
    from pipelines import EclaimLinkProcessor, ShafafiyaProcessor, CSVProcessor

    # XML Processing
    eclaim_processor = EclaimLinkProcessor()
    shafafiya_processor = ShafafiyaProcessor()
    result = eclaim_processor.process_eclaim_link("samples/eclaim_link_request.xml")
    result = shafafiya_processor.process_shafafiya("samples/shafafiya_prior_auth_request.xml")

    # CSV Processing with data quality analysis
    csv_processor = CSVProcessor()
    result = csv_processor.process_csv("data/healthcare_claims.csv")
"""

from .xml_processor import EclaimLinkProcessor, ShafafiyaProcessor
from .csv_processor import CSVProcessor

# Package version
__version__ = "1.0.0"
__author__ = "Nazmito Healthcare Platform"

# Export public API
__all__ = [
    "EclaimLinkProcessor",
    "ShafafiyaProcessor",
    "CSVProcessor",
    "__version__",
    "__author__",
]
