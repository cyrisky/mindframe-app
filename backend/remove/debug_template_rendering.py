#!/usr/bin/env python3
"""Debug script to test template rendering with actual Jinja2"""

import json
import os
from datetime import datetime
from jinja2 import Template
from weasyprint import HTML

def load_interpretation_data():
    """Load interpretation data from JSON file"""
    json_path = '/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/ai/interpretation-data/interpretation-personal-values.json'
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def prepare_template_data(interpretation_data):
    """Prepare data for template rendering"""
    # Extract top 3 values based on the structure
    dimensions = interpretation_data['results']['dimensions']
    top_n = interpretation_data['results']['topN']
    
    # For this example, we'll take the first 3 dimensions as top values
    # In real implementation, this would be based on actual test scores
    top_values = []
    dimension_keys = list(dimensions.keys())[:top_n]
    
    print(f"Debug: top_n = {top_n}")
    print(f"Debug: dimension_keys = {dimension_keys}")
    
    for key in dimension_keys:
        dimension = dimensions[key]
        top_values.append({
            'title': dimension['title'],
            'description': dimension['description'],
            'manifestation': dimension['manifestation'],
            'strengthChallenges': dimension['strengthChallenges']
        })
    
    print(f"Debug: top_values count = {len(top_values)}")
    for i, value in enumerate(top_values, 1):
        print(f"Debug: {i}. {value['title']}")
    
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

def render_template_with_jinja2(template_data):
    """Render HTML template with Jinja2 (proper way)"""
    template_path = '/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/backend/templates/personal_values_report_template.html'
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Use Jinja2 template
    template = Template(template_content)
    html_content = template.render(**template_data)
    
    return html_content

def test_template_rendering():
    """Test template rendering with Jinja2"""
    print("=" * 60)
    print("TESTING TEMPLATE RENDERING WITH JINJA2")
    print("=" * 60)
    
    # Load interpretation data
    interpretation_data = load_interpretation_data()
    
    # Prepare template data
    template_data = prepare_template_data(interpretation_data)
    
    # Render template with Jinja2
    html_content = render_template_with_jinja2(template_data)
    
    # Count how many value-card divs are in the rendered HTML
    value_card_count = html_content.count('class="value-card rank-')
    print(f"\nRendered HTML contains {value_card_count} value cards")
    
    # Check for each rank
    for i in range(1, 4):
        rank_count = html_content.count(f'class="value-card rank-{i}"')
        print(f"Rank {i} cards: {rank_count}")
    
    # Generate PDF
    print("\nGenerating PDF...")
    pdf_bytes = HTML(string=html_content).write_pdf()
    
    # Save to file for inspection
    output_file = 'debug_personal_values_report.pdf'
    with open(output_file, 'wb') as f:
        f.write(pdf_bytes)
    
    file_size = os.path.getsize(output_file)
    print(f"✓ PDF created: {output_file}")
    print(f"✓ PDF file size: {file_size:,} bytes")
    
    # Save HTML for inspection too
    html_file = 'debug_personal_values_report.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✓ HTML saved: {html_file}")
    
    return html_content, pdf_bytes

if __name__ == '__main__':
    test_template_rendering()