"""
Simplified Dossier Generation - Basic HTML output only.
Following CLAUDE.md principles.
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class DossierGenerator:
    """Simple dossier generator for HTML reports."""
    
    def __init__(self):
        self.template_dir = Path(__file__).parent / "templates"
    
    def generate_html_dossier(
        self,
        processing_result: Dict[str, Any],
        output_path: str
    ) -> Dict[str, Any]:
        """Generate a simple HTML dossier."""
        try:
            # Create basic HTML content
            html_content = self._create_basic_html(processing_result)
            
            # Write to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                "success": True,
                "output_path": str(output_file),
                "format": "html"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_basic_html(self, result: Dict[str, Any]) -> str:
        """Create basic HTML content."""
        patient_id = result.get("patient_id", "Unknown")
        decision = result.get("decision", {})
        summary = result.get("summary", {})
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pre-Authorization Dossier - {patient_id}</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .decision {{ padding: 15px; border-radius: 5px; }}
                .approved {{ background-color: #d4edda; color: #155724; }}
                .denied {{ background-color: #f8d7da; color: #721c24; }}
                .pending {{ background-color: #fff3cd; color: #856404; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Pre-Authorization Dossier</h1>
                <p><strong>Patient ID:</strong> {patient_id}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>Authorization Decision</h2>
                <div class="decision {decision.get('status', 'pending').lower()}">
                    <p><strong>Status:</strong> {decision.get('status', 'Pending')}</p>
                    <p><strong>Rationale:</strong> {decision.get('rationale', 'No rationale provided')}</p>
                </div>
            </div>
            
            <div class="section">
                <h2>Clinical Summary</h2>
                <p>{summary.get('diagnosis', 'No diagnosis available')}</p>
                <p><strong>Procedures:</strong> {', '.join(summary.get('procedures', []))}</p>
            </div>
            
            <div class="section">
                <h2>Raw Data</h2>
                <pre>{json.dumps(result, indent=2)}</pre>
            </div>
        </body>
        </html>
        """
        
        return html


class DossierConfig:
    """Simple config class."""
    def __init__(self):
        self.format_type = "html"
        self.include_raw_data = True