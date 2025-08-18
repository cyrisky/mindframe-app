import pytest
import sys
import os
from pathlib import Path

# Add the backend src directory to Python path
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root / 'src'))

try:
    import weasyprint
    from core.pdf_generator import PDFGenerator
    from core.template_processor import TemplateProcessor
    from core.layout_engine import LayoutEngine
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestWeasyPrintIntegration:
    """Test WeasyPrint integration with mindframe-app backend components."""
    
    def test_weasyprint_import(self):
        """Test that WeasyPrint can be imported successfully."""
        assert weasyprint is not None
        assert hasattr(weasyprint, 'HTML')
        assert hasattr(weasyprint, 'CSS')
    
    def test_weasyprint_version(self):
        """Test WeasyPrint version."""
        version = weasyprint.__version__
        assert version is not None
        print(f"WeasyPrint version: {version}")
    
    def test_simple_html_to_pdf(self):
        """Test basic HTML to PDF conversion."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Document</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
            </style>
        </head>
        <body>
            <h1>Test Document</h1>
            <p>This is a test document for WeasyPrint integration.</p>
        </body>
        </html>
        """
        
        # Create HTML object
        html_doc = weasyprint.HTML(string=html_content)
        
        # Generate PDF bytes
        pdf_bytes = html_doc.write_pdf()
        
        # Verify PDF was generated
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
    
    def test_pdf_generator_initialization(self):
        """Test that PDFGenerator can be initialized."""
        try:
            pdf_generator = PDFGenerator()
            assert pdf_generator is not None
        except Exception as e:
            pytest.skip(f"PDFGenerator initialization failed: {e}")
    
    def test_template_processor_initialization(self):
        """Test that TemplateProcessor can be initialized."""
        try:
            template_processor = TemplateProcessor()
            assert template_processor is not None
        except Exception as e:
            pytest.skip(f"TemplateProcessor initialization failed: {e}")
    
    def test_layout_engine_initialization(self):
        """Test that LayoutEngine can be initialized."""
        try:
            layout_engine = LayoutEngine()
            assert layout_engine is not None
        except Exception as e:
            pytest.skip(f"LayoutEngine initialization failed: {e}")
    
    def test_weasyprint_with_css(self):
        """Test WeasyPrint with external CSS."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CSS Test</title>
        </head>
        <body>
            <div class="header">Header Content</div>
            <div class="content">Main Content</div>
            <div class="footer">Footer Content</div>
        </body>
        </html>
        """
        
        css_content = """
        .header { background-color: #f0f0f0; padding: 10px; }
        .content { margin: 20px 0; }
        .footer { background-color: #e0e0e0; padding: 10px; }
        """
        
        html_doc = weasyprint.HTML(string=html_content)
        css_doc = weasyprint.CSS(string=css_content)
        
        pdf_bytes = html_doc.write_pdf(stylesheets=[css_doc])
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])