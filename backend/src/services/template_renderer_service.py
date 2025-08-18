#!/usr/bin/env python3
"""Template Renderer Service for generating PDF reports"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader, Template
from weasyprint import HTML, CSS

class TemplateRendererService:
    """Service for rendering HTML templates and generating PDFs"""
    
    def __init__(self, templates_dir: str = None):
        """Initialize template renderer service"""
        if templates_dir is None:
            # Default to templates directory in backend
            current_dir = os.path.dirname(os.path.abspath(__file__))
            templates_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'templates')
        
        self.templates_dir = templates_dir
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        
        # Ensure templates directory exists
        os.makedirs(templates_dir, exist_ok=True)
    
    def load_interpretation_data(self, json_path: str) -> Dict[str, Any]:
        """Load interpretation data from JSON file"""
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def prepare_personal_values_data(self, interpretation_data: Dict[str, Any], 
                                   client_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare data for Personal Values template rendering"""
        if client_info is None:
            client_info = {
                'name': 'John Doe',
                'age': '28',
                'test_date': '15 Agustus 2024'
            }
        
        # Extract top values based on the structure
        dimensions = interpretation_data['results']['dimensions']
        top_n = interpretation_data['results']['topN']
        
        # For this example, we'll take the first N dimensions as top values
        # In real implementation, this would be based on actual test scores
        top_values = []
        dimension_keys = list(dimensions.keys())[:top_n]
        
        for key in dimension_keys:
            dimension = dimensions[key]
            top_values.append({
                'key': key,
                'title': dimension['title'],
                'description': dimension['description'],
                'manifestation': dimension['manifestation'],
                'strengthChallenges': dimension['strengthChallenges']
            })
        
        # Prepare template variables
        template_data = {
            'client_name': client_info['name'],
            'client_age': client_info['age'],
            'test_date': client_info['test_date'],
            'report_date': datetime.now().strftime('%d %B %Y'),
            'test_name': interpretation_data.get('testName', 'Personal Values Test'),
            'test_type': interpretation_data.get('testType', 'top-n-dimension'),
            'top_n': top_n,
            'top_values': top_values,
            'all_dimensions': dimensions
        }
        
        return template_data
    
    def render_template(self, template_name: str, template_data: Dict[str, Any]) -> str:
        """Render HTML template with data using Jinja2"""
        template = self.env.get_template(template_name)
        return template.render(**template_data)
    
    def generate_pdf(self, html_content: str, output_path: str = None, 
                    css_content: str = None) -> bytes:
        """Generate PDF from HTML content"""
        stylesheets = []
        if css_content:
            stylesheets.append(CSS(string=css_content))
        
        pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=stylesheets)
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
        
        return pdf_bytes
    
    def generate_personal_values_report(self, interpretation_data_path: str, 
                                      client_info: Dict[str, Any] = None,
                                      output_path: str = None) -> bytes:
        """Generate complete Personal Values PDF report"""
        # Load interpretation data
        interpretation_data = self.load_interpretation_data(interpretation_data_path)
        
        # Prepare template data
        template_data = self.prepare_personal_values_data(interpretation_data, client_info)
        
        # Render template
        html_content = self.render_template('personal_values_report_template.html', template_data)
        
        # Generate PDF
        pdf_bytes = self.generate_pdf(html_content, output_path)
        
        return pdf_bytes
    
    def get_available_templates(self) -> List[str]:
        """Get list of available templates"""
        templates = []
        for file in os.listdir(self.templates_dir):
            if file.endswith('.html'):
                templates.append(file)
        return templates
    
    def validate_template_data(self, template_name: str, template_data: Dict[str, Any]) -> bool:
        """Validate template data against template requirements"""
        try:
            template = self.env.get_template(template_name)
            # Try to render with provided data
            template.render(**template_data)
            return True
        except Exception as e:
            print(f"Template validation failed: {e}")
            return False

# Example usage and testing
if __name__ == '__main__':
    # Initialize service
    renderer = TemplateRendererService()
    
    # Test Personal Values report generation
    interpretation_path = '/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/ai/interpretation-data/interpretation-personal-values.json'
    
    client_info = {
        'name': 'Jane Smith',
        'age': '32',
        'test_date': '13 Agustus 2024'
    }
    
    try:
        pdf_bytes = renderer.generate_personal_values_report(
            interpretation_path, 
            client_info, 
            'personal_values_service_test.pdf'
        )
        
        print('✓ Personal Values Report generated successfully!')
        print(f'✓ PDF size: {len(pdf_bytes):,} bytes')
        print('✓ File saved as: personal_values_service_test.pdf')
        
    except Exception as e:
        print(f'✗ Error generating report: {e}')