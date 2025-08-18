#!/usr/bin/env python3
"""Test Personal Values template with real data"""

import json
import os
from datetime import datetime
from weasyprint import HTML, CSS
from jinja2 import Template

class TestPersonalValuesTemplate:
    """Test Personal Values PDF generation with template"""
    
    def load_interpretation_data(self):
        """Load interpretation data from JSON file"""
        json_path = '/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/ai/interpretation-data/interpretation-personal-values.json'
        
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def prepare_template_data(self, interpretation_data):
        """Prepare data for template rendering"""
        # Extract top 3 values based on the structure
        dimensions = interpretation_data['results']['dimensions']
        top_n = interpretation_data['results']['topN']
        
        # For this example, we'll take the first 3 dimensions as top values
        # In real implementation, this would be based on actual test scores
        top_values = []
        dimension_keys = list(dimensions.keys())[:top_n]
        
        print(f"Debug: Preparing {len(dimension_keys)} top values: {dimension_keys}")
        
        for key in dimension_keys:
            dimension = dimensions[key]
            top_values.append({
                'title': dimension['title'],
                'description': dimension['description'],
                'manifestation': dimension['manifestation'],
                'strengthChallenges': dimension['strengthChallenges']
            })
        
        print(f"Debug: Created {len(top_values)} top_values entries:")
        for i, value in enumerate(top_values, 1):
            print(f"  {i}. {value['title']}")
        
        # Prepare template variables
        template_data = {
            'client_name': 'John Doe',  # This would come from user data
            'client_age': '28',
            'test_date': '15 Agustus 2024',
            'report_date': datetime.now().strftime('%d %B %Y'),
            'test_name': interpretation_data['testName'],
            'test_type': interpretation_data['testType'],
            'top_n': top_n,
            'top_values': top_values
        }
        
        return template_data
    
    def render_template(self, template_data):
        """Render HTML template with Jinja2"""
        template_path = '/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/backend/templates/personal_values_report_template.html'
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Use Jinja2 template for proper rendering
        template = Template(template_content)
        html_content = template.render(**template_data)
        
        return html_content
    
    def test_personal_values_report_generation(self):
        """Test generating Personal Values report PDF with real data"""
        # Load interpretation data
        interpretation_data = self.load_interpretation_data()
        
        # Prepare template data
        template_data = self.prepare_template_data(interpretation_data)
        
        # Render template
        html_content = self.render_template(template_data)
        
        # Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        # Save to file for inspection
        output_filename = 'test_complete_personal_values_report_FIXED.pdf'
        with open(output_filename, 'wb') as f:
            f.write(pdf_bytes)
        print(f'✓ Personal Values Report PDF created: {output_filename}')
        
        # Verify PDF was generated
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
        
        # Verify file exists and has reasonable size
        assert os.path.exists('personal_values_report.pdf')
        file_size = os.path.getsize('personal_values_report.pdf')
        assert file_size > 10000  # Should be at least 10KB for a proper report
        
        print(f'✓ PDF file size: {file_size:,} bytes')
        print('✓ Personal Values template test completed successfully!')

if __name__ == '__main__':
    test = TestPersonalValuesTemplate()
    test.test_personal_values_report_generation()