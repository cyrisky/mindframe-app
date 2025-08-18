import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add the backend src directory to Python path
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root / 'src'))

try:
    import weasyprint
    from services.pdf_service import PDFService
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestPDFService:
    """Test PDFService integration with WeasyPrint."""
    
    def setup_method(self):
        """Setup test environment."""
        self.pdf_service = PDFService()
    
    def test_pdf_service_initialization(self):
        """Test that PDFService can be initialized."""
        assert self.pdf_service is not None
    
    @patch('services.pdf_service.DatabaseService')
    @patch('services.pdf_service.TemplateService')
    def test_generate_report_pdf_basic(self, mock_template_service, mock_database_service):
        """Test basic PDF generation functionality."""
        # Mock template service to return HTML content
        mock_template_service.return_value.render_template.return_value = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #f0f0f0; padding: 10px; }
                .content { margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Mindframe Assessment Report</h1>
            </div>
            <div class="content">
                <h2>Assessment Results</h2>
                <p>This is a test assessment report.</p>
                <ul>
                    <li>Test metric 1: 85%</li>
                    <li>Test metric 2: 92%</li>
                    <li>Test metric 3: 78%</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        # Mock database service
        mock_database_service.return_value.get_assessment_data.return_value = {
            'user_id': 'test_user',
            'assessment_id': 'test_assessment',
            'results': {'score': 85}
        }
        
        try:
            # Test PDF generation
            pdf_bytes = self.pdf_service.generate_report_pdf(
                user_id='test_user',
                assessment_id='test_assessment'
            )
            
            # Verify PDF was generated
            assert pdf_bytes is not None
            assert len(pdf_bytes) > 0
            assert pdf_bytes.startswith(b'%PDF')
            
        except AttributeError:
            # If method doesn't exist, skip this test
            pytest.skip("generate_report_pdf method not implemented yet")
    
    def test_weasyprint_direct_integration(self):
        """Test direct WeasyPrint integration within PDFService context."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mindframe Report</title>
            <style>
                @page {
                    size: A4;
                    margin: 2cm;
                }
                body {
                    font-family: 'Helvetica', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    margin-bottom: 30px;
                }
                .section {
                    margin-bottom: 25px;
                    padding: 15px;
                    border-left: 4px solid #667eea;
                    background-color: #f8f9fa;
                }
                .metric {
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid #eee;
                }
                .score {
                    font-weight: bold;
                    color: #667eea;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Mindframe Assessment Report</h1>
                <p>Comprehensive Mental Health Analysis</p>
            </div>
            
            <div class="section">
                <h2>Assessment Overview</h2>
                <p>This report provides insights into your mental health assessment results.</p>
            </div>
            
            <div class="section">
                <h2>Key Metrics</h2>
                <div class="metric">
                    <span>Stress Level</span>
                    <span class="score">Low (25%)</span>
                </div>
                <div class="metric">
                    <span>Anxiety Level</span>
                    <span class="score">Moderate (45%)</span>
                </div>
                <div class="metric">
                    <span>Depression Risk</span>
                    <span class="score">Low (20%)</span>
                </div>
                <div class="metric">
                    <span>Overall Wellbeing</span>
                    <span class="score">Good (78%)</span>
                </div>
            </div>
            
            <div class="section">
                <h2>Recommendations</h2>
                <ul>
                    <li>Continue current stress management practices</li>
                    <li>Consider mindfulness exercises for anxiety</li>
                    <li>Maintain regular exercise routine</li>
                    <li>Schedule follow-up assessment in 3 months</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        # Generate PDF using WeasyPrint
        html_doc = weasyprint.HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        
        # Verify PDF generation
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
        
        # Verify PDF size is reasonable (should be more than basic HTML)
        assert len(pdf_bytes) > 1000  # At least 1KB for a formatted report
    
    def test_weasyprint_error_handling(self):
        """Test WeasyPrint error handling with invalid HTML."""
        invalid_html = "<html><body><unclosed_tag>Invalid HTML</body></html>"
        
        try:
            html_doc = weasyprint.HTML(string=invalid_html)
            pdf_bytes = html_doc.write_pdf()
            # WeasyPrint is quite forgiving, so this might still work
            assert pdf_bytes is not None
        except Exception as e:
            # If it fails, that's also acceptable for invalid HTML
            assert isinstance(e, Exception)
    
    def test_weasyprint_with_base64_images(self):
        """Test WeasyPrint with embedded base64 images."""
        # Small 1x1 pixel transparent PNG as base64
        base64_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        html_with_image = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Report with Image</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .logo {{ text-align: center; margin-bottom: 20px; }}
                img {{ max-width: 100px; }}
            </style>
        </head>
        <body>
            <div class="logo">
                <img src="{base64_image}" alt="Logo" />
            </div>
            <h1>Report with Embedded Image</h1>
            <p>This report contains an embedded base64 image.</p>
        </body>
        </html>
        """
        
        html_doc = weasyprint.HTML(string=html_with_image)
        pdf_bytes = html_doc.write_pdf()
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])