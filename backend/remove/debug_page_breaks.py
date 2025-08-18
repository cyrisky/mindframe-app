#!/usr/bin/env python3
"""Debug page breaks and CSS issues in PDF generation"""

import json
import os
from datetime import datetime
from jinja2 import Template
from weasyprint import HTML, CSS

def load_interpretation_data():
    """Load interpretation data from JSON file"""
    json_path = '/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/ai/interpretation-data/interpretation-personal-values.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def prepare_template_data(interpretation_data):
    """Prepare data for template rendering"""
    dimensions = interpretation_data['results']['dimensions']
    top_n = interpretation_data['results']['topN']
    
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
    
    print(f"Debug: Created {len(top_values)} top_values entries")
    for i, value in enumerate(top_values, 1):
        print(f"  {i}. {value['title']}")
    
    template_data = {
        'client_name': 'John Doe',
        'client_age': '28',
        'test_date': '15 Agustus 2024',
        'report_date': datetime.now().strftime('%d %B %Y'),
        'test_name': interpretation_data['testName'],
        'test_type': interpretation_data['testType'],
        'top_n': top_n,
        'top_values': top_values
    }
    
    return template_data

def create_modified_template():
    """Create a modified template with better page break handling"""
    template_path = '/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/backend/templates/personal_values_report_template.html'
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Modify CSS to handle page breaks better
    modified_css = """
        .value-card {
            background-color: #ffffff;
            border: 1px solid #bdc3c7;
            border-radius: 8px;
            padding: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            page-break-inside: avoid;
            page-break-after: auto;
            margin-bottom: 25px;
        }
        
        .value-card:last-child {
            page-break-after: avoid;
        }
        
        /* Force page break before summary */
        .page-break {
            page-break-before: always;
        }
        
        /* Ensure each value card gets enough space */
        .top-values {
            display: block;
        }
    """
    
    # Replace the existing value-card CSS
    import re
    pattern = r'\.value-card \{[^}]+\}'
    template_content = re.sub(pattern, modified_css, template_content)
    
    return template_content

def test_page_breaks():
    """Test different page break configurations"""
    print("=" * 60)
    print("TESTING PAGE BREAK CONFIGURATIONS")
    print("=" * 60)
    
    # Load data
    interpretation_data = load_interpretation_data()
    template_data = prepare_template_data(interpretation_data)
    
    # Test 1: Original template
    print("\n1. Testing original template...")
    template_path = '/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/backend/templates/personal_values_report_template.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        original_template = f.read()
    
    template = Template(original_template)
    html_content = template.render(**template_data)
    
    # Save HTML for inspection
    with open('debug_original_template.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Generate PDF
    try:
        html_doc = HTML(string=html_content)
        html_doc.write_pdf('debug_original_template.pdf')
        print("   ✅ Original template PDF generated")
    except Exception as e:
        print(f"   ❌ Error generating original PDF: {e}")
    
    # Test 2: Modified template with better page breaks
    print("\n2. Testing modified template with better page breaks...")
    modified_template = create_modified_template()
    
    template = Template(modified_template)
    html_content = template.render(**template_data)
    
    # Save HTML for inspection
    with open('debug_modified_template.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Generate PDF
    try:
        html_doc = HTML(string=html_content)
        html_doc.write_pdf('debug_modified_template.pdf')
        print("   ✅ Modified template PDF generated")
    except Exception as e:
        print(f"   ❌ Error generating modified PDF: {e}")
    
    # Test 3: Force each card on separate page
    print("\n3. Testing with forced page breaks between cards...")
    forced_break_template = original_template.replace(
        '</div>\n            {% endfor %}',
        '</div>\n            {% if not loop.last %}<div class="page-break"></div>{% endif %}\n            {% endfor %}'
    )
    
    template = Template(forced_break_template)
    html_content = template.render(**template_data)
    
    # Save HTML for inspection
    with open('debug_forced_breaks.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Generate PDF
    try:
        html_doc = HTML(string=html_content)
        html_doc.write_pdf('debug_forced_breaks.pdf')
        print("   ✅ Forced breaks PDF generated")
    except Exception as e:
        print(f"   ❌ Error generating forced breaks PDF: {e}")
    
    print("\n" + "=" * 60)
    print("DEBUG FILES GENERATED:")
    print("- debug_original_template.html/pdf")
    print("- debug_modified_template.html/pdf")
    print("- debug_forced_breaks.html/pdf")
    print("=" * 60)

if __name__ == '__main__':
    test_page_breaks()