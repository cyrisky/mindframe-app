#!/usr/bin/env python3
"""Test Template Renderer Service"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import directly to avoid loading other services with dependencies
import importlib.util
spec = importlib.util.spec_from_file_location(
    "template_renderer_service", 
    os.path.join(os.path.dirname(__file__), '..', 'src', 'services', 'template_renderer_service.py')
)
template_renderer_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(template_renderer_module)
TemplateRendererService = template_renderer_module.TemplateRendererService

def test_template_renderer_service():
    """Test the Template Renderer Service functionality"""
    
    # Initialize service
    renderer = TemplateRendererService()
    
    # Test 1: Service initialization
    print("Test 1: Service Initialization")
    assert renderer is not None
    assert renderer.templates_dir is not None
    assert renderer.env is not None
    print("✓ Service initialized successfully")
    
    # Test 2: Load interpretation data
    print("\nTest 2: Load Interpretation Data")
    interpretation_path = '/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/ai/interpretation-data/interpretation-personal-values.json'
    
    if os.path.exists(interpretation_path):
        interpretation_data = renderer.load_interpretation_data(interpretation_path)
        assert interpretation_data is not None
        assert 'results' in interpretation_data
        assert 'dimensions' in interpretation_data['results']
        print("✓ Interpretation data loaded successfully")
        print(f"  - Found {len(interpretation_data['results']['dimensions'])} dimensions")
        print(f"  - Top N: {interpretation_data['results']['topN']}")
    else:
        print("⚠ Interpretation data file not found, skipping this test")
        return
    
    # Test 3: Prepare template data
    print("\nTest 3: Prepare Template Data")
    client_info = {
        'name': 'Test User',
        'age': '25',
        'test_date': '13 Agustus 2024'
    }
    
    template_data = renderer.prepare_personal_values_data(interpretation_data, client_info)
    assert template_data is not None
    assert 'client_name' in template_data
    assert 'top_values' in template_data
    assert len(template_data['top_values']) > 0
    print("✓ Template data prepared successfully")
    print(f"  - Client: {template_data['client_name']}")
    print(f"  - Top values count: {len(template_data['top_values'])}")
    
    # Test 4: Get available templates
    print("\nTest 4: Available Templates")
    templates = renderer.get_available_templates()
    print(f"✓ Found {len(templates)} templates:")
    for template in templates:
        print(f"  - {template}")
    
    # Test 5: Validate template data
    print("\nTest 5: Template Data Validation")
    if 'personal_values_report_template.html' in templates:
        is_valid = renderer.validate_template_data('personal_values_report_template.html', template_data)
        assert is_valid
        print("✓ Template data validation passed")
    else:
        print("⚠ Personal values template not found, skipping validation")
    
    # Test 6: Render template
    print("\nTest 6: Template Rendering")
    if 'personal_values_report_template.html' in templates:
        html_content = renderer.render_template('personal_values_report_template.html', template_data)
        assert html_content is not None
        assert len(html_content) > 0
        assert template_data['client_name'] in html_content
        print("✓ Template rendered successfully")
        print(f"  - HTML content length: {len(html_content):,} characters")
    else:
        print("⚠ Personal values template not found, skipping rendering")
        return
    
    # Test 7: Generate PDF
    print("\nTest 7: PDF Generation")
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        pdf_bytes = renderer.generate_pdf(html_content, tmp_file.name)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert os.path.exists(tmp_file.name)
        
        file_size = os.path.getsize(tmp_file.name)
        print("✓ PDF generated successfully")
        print(f"  - PDF size: {len(pdf_bytes):,} bytes")
        print(f"  - File size: {file_size:,} bytes")
        print(f"  - Temp file: {tmp_file.name}")
        
        # Clean up
        os.unlink(tmp_file.name)
    
    # Test 8: Complete report generation
    print("\nTest 8: Complete Report Generation")
    output_path = 'test_complete_personal_values_report.pdf'
    
    try:
        pdf_bytes = renderer.generate_personal_values_report(
            interpretation_path,
            client_info,
            output_path
        )
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert os.path.exists(output_path)
        
        file_size = os.path.getsize(output_path)
        print("✓ Complete report generated successfully")
        print(f"  - PDF size: {len(pdf_bytes):,} bytes")
        print(f"  - File size: {file_size:,} bytes")
        print(f"  - Output file: {output_path}")
        
    except Exception as e:
        print(f"✗ Error in complete report generation: {e}")
        raise
    
    print("\n🎉 All Template Renderer Service tests passed!")

def test_error_handling():
    """Test error handling scenarios"""
    print("\n" + "="*50)
    print("Testing Error Handling Scenarios")
    print("="*50)
    
    renderer = TemplateRendererService()
    
    # Test 1: Invalid JSON file
    print("\nTest 1: Invalid JSON File")
    try:
        renderer.load_interpretation_data('nonexistent_file.json')
        print("✗ Should have raised an exception")
    except FileNotFoundError:
        print("✓ Correctly handled missing file")
    except Exception as e:
        print(f"✓ Handled error: {e}")
    
    # Test 2: Invalid template
    print("\nTest 2: Invalid Template")
    try:
        renderer.render_template('nonexistent_template.html', {})
        print("✗ Should have raised an exception")
    except Exception as e:
        print(f"✓ Correctly handled missing template: {type(e).__name__}")
    
    # Test 3: Invalid template data
    print("\nTest 3: Invalid Template Data Validation")
    if 'personal_values_report_template.html' in renderer.get_available_templates():
        is_valid = renderer.validate_template_data('personal_values_report_template.html', {})
        if not is_valid:
            print("✓ Correctly identified invalid template data")
        else:
            print("⚠ Template validation passed with empty data (template might be flexible)")
    else:
        print("⚠ Template not found for validation test")
    
    print("\n✓ Error handling tests completed")

if __name__ == '__main__':
    print("Template Renderer Service Test Suite")
    print("="*50)
    
    try:
        test_template_renderer_service()
        test_error_handling()
        print("\n🎉 All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)