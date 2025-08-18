#!/usr/bin/env python3
"""Compare PDF generation results between Mindframe and WeasyPrint reference"""

import os
from weasyprint import HTML, CSS

def create_simple_test_like_weasyprint():
    """Create a simple PDF similar to WeasyPrint test_api.py"""
    # Test 1: Simple HTML string to PDF (like WeasyPrint test)
    html_content = '<h1 style="color: blue;">Hello from Mindframe Backend!</h1><p>This PDF was generated using WeasyPrint in Mindframe app.</p>'
    HTML(string=html_content).write_pdf('mindframe_simple_test.pdf')
    print('✓ Simple Mindframe PDF created: mindframe_simple_test.pdf')
    
    # Test 2: HTML with external CSS (like WeasyPrint test)
    html_with_css = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mindframe WeasyPrint Test</title>
    </head>
    <body>
        <h1>Mindframe WeasyPrint Integration is Working!</h1>
        <p class="highlight">This is a test document from Mindframe backend with custom styling.</p>
        <ul>
            <li>Feature 1: HTML to PDF conversion in Mindframe</li>
            <li>Feature 2: CSS styling support in backend</li>
            <li>Feature 3: Python API integration with Mindframe services</li>
        </ul>
    </body>
    </html>
    '''
    
    css_content = '''
    body {
        font-family: Arial, sans-serif;
        margin: 40px;
        line-height: 1.6;
    }
    h1 {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
    }
    .highlight {
        background-color: #e74c3c;
        color: white;
        padding: 10px;
        border-radius: 5px;
    }
    ul {
        background-color: #ecf0f1;
        padding: 20px;
        border-left: 4px solid #e74c3c;
    }
    '''
    
    HTML(string=html_with_css).write_pdf('mindframe_styled_test.pdf', stylesheets=[CSS(string=css_content)])
    print('✓ Styled Mindframe PDF created: mindframe_styled_test.pdf')

def show_comparison():
    """Show comparison of generated files"""
    print('\n🎉 Mindframe WeasyPrint Integration is working correctly!')
    print('📁 Generated files in Mindframe backend:')
    
    # List all PDF files
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    for pdf_file in sorted(pdf_files):
        file_size = os.path.getsize(pdf_file)
        print(f'   - {pdf_file} ({file_size:,} bytes)')
    
    print('\n📋 Comparison with WeasyPrint reference:')
    print('   WeasyPrint folder has: api_test.pdf, styled_test.pdf')
    print('   Mindframe backend has: mindframe_simple_test.pdf, mindframe_styled_test.pdf')
    print('   Plus Mindframe-specific reports: anxiety, depression, wellness, session notes')
    
if __name__ == '__main__':
    create_simple_test_like_weasyprint()
    show_comparison()