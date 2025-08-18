import pytest
import weasyprint
import tempfile
import os
from pathlib import Path


class TestWeasyPrintBasic:
    """Basic WeasyPrint functionality tests for mindframe-app."""
    
    def test_weasyprint_installation(self):
        """Test that WeasyPrint is properly installed and accessible."""
        # Test import
        assert weasyprint is not None
        
        # Test version
        version = weasyprint.__version__
        assert version is not None
        print(f"WeasyPrint version: {version}")
        
        # Test basic classes are available
        assert hasattr(weasyprint, 'HTML')
        assert hasattr(weasyprint, 'CSS')
    
    def test_simple_pdf_generation(self):
        """Test basic PDF generation from HTML string."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Document</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>Test Document</h1>
            <p>This is a simple test document.</p>
        </body>
        </html>
        """
        
        # Generate PDF
        html_doc = weasyprint.HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        
        # Verify PDF
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
    
    def test_mindframe_report_template(self):
        """Test PDF generation with a mindframe-style report template."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mindframe Assessment Report</title>
            <meta charset="utf-8">
            <style>
                @page {
                    size: A4;
                    margin: 2cm;
                    @top-center {
                        content: "Mindframe Assessment Report";
                        font-size: 10pt;
                        color: #666;
                    }
                    @bottom-center {
                        content: "Page " counter(page) " of " counter(pages);
                        font-size: 10pt;
                        color: #666;
                    }
                }
                
                body {
                    font-family: 'Helvetica', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                }
                
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    margin-bottom: 30px;
                    border-radius: 8px;
                }
                
                .header h1 {
                    margin: 0 0 10px 0;
                    font-size: 28pt;
                    font-weight: 300;
                }
                
                .header p {
                    margin: 0;
                    font-size: 14pt;
                    opacity: 0.9;
                }
                
                .section {
                    margin-bottom: 25px;
                    padding: 20px;
                    border-left: 4px solid #667eea;
                    background-color: #f8f9fa;
                    border-radius: 0 8px 8px 0;
                }
                
                .section h2 {
                    margin-top: 0;
                    color: #667eea;
                    font-size: 18pt;
                }
                
                .metrics-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin: 20px 0;
                }
                
                .metric-card {
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    border: 1px solid #e9ecef;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                
                .metric-label {
                    font-size: 12pt;
                    color: #666;
                    margin-bottom: 5px;
                }
                
                .metric-value {
                    font-size: 20pt;
                    font-weight: bold;
                    color: #667eea;
                }
                
                .recommendations {
                    background: #e8f4fd;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #0066cc;
                }
                
                .recommendations ul {
                    margin: 10px 0;
                    padding-left: 20px;
                }
                
                .recommendations li {
                    margin-bottom: 8px;
                    line-height: 1.5;
                }
                
                .footer {
                    margin-top: 40px;
                    padding: 20px;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    text-align: center;
                    font-size: 10pt;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Mindframe Assessment Report</h1>
                <p>Comprehensive Mental Health Analysis</p>
                <p>Generated on: January 15, 2024</p>
            </div>
            
            <div class="section">
                <h2>Assessment Overview</h2>
                <p>This report provides comprehensive insights into your mental health assessment results. The analysis is based on validated psychological instruments and provides actionable recommendations for your wellbeing journey.</p>
            </div>
            
            <div class="section">
                <h2>Key Metrics</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Stress Level</div>
                        <div class="metric-value">25%</div>
                        <div style="color: #28a745; font-size: 10pt;">Low Risk</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Anxiety Level</div>
                        <div class="metric-value">45%</div>
                        <div style="color: #ffc107; font-size: 10pt;">Moderate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Depression Risk</div>
                        <div class="metric-value">20%</div>
                        <div style="color: #28a745; font-size: 10pt;">Low Risk</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Overall Wellbeing</div>
                        <div class="metric-value">78%</div>
                        <div style="color: #28a745; font-size: 10pt;">Good</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Detailed Analysis</h2>
                <p><strong>Stress Management:</strong> Your current stress levels are within healthy ranges. You demonstrate good coping mechanisms and stress awareness.</p>
                
                <p><strong>Anxiety Patterns:</strong> Moderate anxiety levels detected. This is common and manageable with appropriate interventions.</p>
                
                <p><strong>Mood Stability:</strong> Your mood patterns show good stability with low risk factors for depression.</p>
                
                <p><strong>Resilience Factors:</strong> Strong resilience indicators suggest good capacity for handling life challenges.</p>
            </div>
            
            <div class="recommendations">
                <h2 style="margin-top: 0; color: #0066cc;">Personalized Recommendations</h2>
                <ul>
                    <li><strong>Mindfulness Practice:</strong> Continue daily mindfulness exercises (10-15 minutes) to maintain stress levels</li>
                    <li><strong>Anxiety Management:</strong> Consider progressive muscle relaxation techniques for anxiety reduction</li>
                    <li><strong>Physical Activity:</strong> Maintain regular exercise routine (3-4 times per week) for mood regulation</li>
                    <li><strong>Sleep Hygiene:</strong> Ensure 7-8 hours of quality sleep for optimal mental health</li>
                    <li><strong>Social Connection:</strong> Engage in meaningful social activities to boost wellbeing</li>
                    <li><strong>Professional Support:</strong> Consider periodic check-ins with a mental health professional</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>Next Steps</h2>
                <p>Based on your assessment results, we recommend:</p>
                <ol>
                    <li>Implement the personalized recommendations above</li>
                    <li>Track your progress using the Mindframe app</li>
                    <li>Schedule a follow-up assessment in 3 months</li>
                    <li>Reach out to our support team if you have any questions</li>
                </ol>
            </div>
            
            <div class="footer">
                <p>This report is generated by Mindframe AI-powered assessment system.</p>
                <p>For support, contact: support@mindframe.app | www.mindframe.app</p>
                <p><em>This report is for informational purposes and does not replace professional medical advice.</em></p>
            </div>
        </body>
        </html>
        """
        
        # Generate PDF
        html_doc = weasyprint.HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        
        # Verify PDF
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
        
        # Verify PDF size is substantial (formatted report should be larger)
        assert len(pdf_bytes) > 5000  # At least 5KB for a well-formatted report
    
    def test_pdf_with_charts_placeholder(self):
        """Test PDF generation with chart placeholders (for future chart integration)."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Report with Charts</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .chart-placeholder {
                    width: 100%;
                    height: 200px;
                    background: linear-gradient(45deg, #f0f0f0 25%, transparent 25%),
                               linear-gradient(-45deg, #f0f0f0 25%, transparent 25%),
                               linear-gradient(45deg, transparent 75%, #f0f0f0 75%),
                               linear-gradient(-45deg, transparent 75%, #f0f0f0 75%);
                    background-size: 20px 20px;
                    background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
                    border: 2px dashed #ccc;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 20px 0;
                    border-radius: 8px;
                }
                .chart-label {
                    background: white;
                    padding: 10px 20px;
                    border-radius: 4px;
                    color: #666;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <h1>Assessment Report with Charts</h1>
            
            <h2>Stress Level Trends</h2>
            <div class="chart-placeholder">
                <div class="chart-label">Stress Level Chart (Coming Soon)</div>
            </div>
            
            <h2>Mood Patterns</h2>
            <div class="chart-placeholder">
                <div class="chart-label">Mood Pattern Chart (Coming Soon)</div>
            </div>
            
            <p>Charts will be integrated in future versions using libraries like Chart.js or D3.js.</p>
        </body>
        </html>
        """
        
        # Generate PDF
        html_doc = weasyprint.HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        
        # Verify PDF
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
    
    def test_save_pdf_to_file(self):
        """Test saving PDF to a temporary file."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head><title>File Test</title></head>
        <body><h1>PDF File Test</h1><p>Testing file output.</p></body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            try:
                # Generate and save PDF
                html_doc = weasyprint.HTML(string=html_content)
                html_doc.write_pdf(tmp_file.name)
                
                # Verify file was created and has content
                assert os.path.exists(tmp_file.name)
                file_size = os.path.getsize(tmp_file.name)
                assert file_size > 0
                
                # Verify it's a valid PDF by reading the header
                with open(tmp_file.name, 'rb') as pdf_file:
                    header = pdf_file.read(4)
                    assert header == b'%PDF'
                    
            finally:
                # Clean up
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
    
    def test_weasyprint_error_handling(self):
        """Test WeasyPrint error handling with various edge cases."""
        # Test with empty HTML
        empty_html = ""
        try:
            html_doc = weasyprint.HTML(string=empty_html)
            pdf_bytes = html_doc.write_pdf()
            # WeasyPrint should handle this gracefully
            assert pdf_bytes is not None
        except Exception:
            # If it fails, that's also acceptable
            pass
        
        # Test with minimal HTML
        minimal_html = "<html><body>Test</body></html>"
        html_doc = weasyprint.HTML(string=minimal_html)
        pdf_bytes = html_doc.write_pdf()
        assert pdf_bytes is not None
        assert pdf_bytes.startswith(b'%PDF')


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])