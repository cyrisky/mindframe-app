"""PDF Generator using WeasyPrint core functionality"""

import io
import os
from typing import Optional, Dict, Any, Union
from pathlib import Path

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from jinja2 import Environment, FileSystemLoader, Template

from .template_processor import TemplateProcessor
from .layout_engine import LayoutEngine


class PDFGenerator:
    """Main PDF generation class using WeasyPrint"""
    
    def __init__(self, template_dir: Optional[str] = None, font_config: Optional[FontConfiguration] = None):
        """Initialize PDF generator
        
        Args:
            template_dir: Directory containing HTML templates
            font_config: Custom font configuration for WeasyPrint
        """
        self.template_processor = TemplateProcessor(template_dir)
        self.layout_engine = LayoutEngine()
        self.font_config = font_config or FontConfiguration()
        
    def generate_from_html(self, html_content: str, css_content: Optional[str] = None, 
                          output_path: Optional[str] = None) -> Union[bytes, None]:
        """Generate PDF from HTML string
        
        Args:
            html_content: HTML content as string
            css_content: Optional CSS content as string
            output_path: Optional path to save PDF file
            
        Returns:
            PDF bytes if output_path is None, otherwise None
        """
        try:
            # Create HTML document
            html_doc = HTML(string=html_content)
            
            # Prepare stylesheets
            stylesheets = []
            if css_content:
                stylesheets.append(CSS(string=css_content))
                
            # Generate PDF
            if output_path:
                html_doc.write_pdf(output_path, stylesheets=stylesheets, 
                                 font_config=self.font_config)
                return None
            else:
                return html_doc.write_pdf(stylesheets=stylesheets, 
                                        font_config=self.font_config)
                
        except Exception as e:
            raise PDFGenerationError(f"Failed to generate PDF: {str(e)}") from e
    
    def generate_from_template(self, template_name: str, context: Dict[str, Any],
                             css_files: Optional[list] = None,
                             output_path: Optional[str] = None) -> Union[bytes, None]:
        """Generate PDF from template with context data
        
        Args:
            template_name: Name of the template file
            context: Data to render in template
            css_files: List of CSS file paths
            output_path: Optional path to save PDF file
            
        Returns:
            PDF bytes if output_path is None, otherwise None
        """
        try:
            # Process template
            html_content = self.template_processor.render_template(template_name, context)
            
            # Load CSS files
            stylesheets = []
            if css_files:
                for css_file in css_files:
                    if os.path.exists(css_file):
                        stylesheets.append(CSS(filename=css_file))
                    else:
                        raise FileNotFoundError(f"CSS file not found: {css_file}")
            
            # Create HTML document
            html_doc = HTML(string=html_content)
            
            # Generate PDF
            if output_path:
                html_doc.write_pdf(output_path, stylesheets=stylesheets,
                                 font_config=self.font_config)
                return None
            else:
                return html_doc.write_pdf(stylesheets=stylesheets,
                                        font_config=self.font_config)
                
        except Exception as e:
            raise PDFGenerationError(f"Failed to generate PDF from template: {str(e)}") from e
    
    def generate_from_url(self, url: str, css_content: Optional[str] = None,
                         output_path: Optional[str] = None) -> Union[bytes, None]:
        """Generate PDF from URL
        
        Args:
            url: URL to convert to PDF
            css_content: Optional additional CSS
            output_path: Optional path to save PDF file
            
        Returns:
            PDF bytes if output_path is None, otherwise None
        """
        try:
            # Create HTML document from URL
            html_doc = HTML(url=url)
            
            # Prepare stylesheets
            stylesheets = []
            if css_content:
                stylesheets.append(CSS(string=css_content))
            
            # Generate PDF
            if output_path:
                html_doc.write_pdf(output_path, stylesheets=stylesheets,
                                 font_config=self.font_config)
                return None
            else:
                return html_doc.write_pdf(stylesheets=stylesheets,
                                        font_config=self.font_config)
                
        except Exception as e:
            raise PDFGenerationError(f"Failed to generate PDF from URL: {str(e)}") from e
    
    def generate_psychological_report(self, report_data: Dict[str, Any],
                                    template_name: str = "psychological_report.html",
                                    output_path: Optional[str] = None) -> Union[bytes, None]:
        """Generate psychological test report PDF
        
        Args:
            report_data: Dictionary containing report data
            template_name: Template file name for the report
            output_path: Optional path to save PDF file
            
        Returns:
            PDF bytes if output_path is None, otherwise None
        """
        try:
            # Validate required report data
            required_fields = ['patient_name', 'test_date', 'test_results']
            for field in required_fields:
                if field not in report_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add default styling and layout configuration
            report_context = {
                **report_data,
                'layout_config': self.layout_engine.get_report_layout_config(),
                'generation_timestamp': self._get_timestamp()
            }
            
            # Generate PDF using template
            return self.generate_from_template(
                template_name=template_name,
                context=report_context,
                css_files=["shared/templates/styles/report.css"],
                output_path=output_path
            )
            
        except Exception as e:
            raise PDFGenerationError(f"Failed to generate psychological report: {str(e)}") from e
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for report generation"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def set_font_config(self, font_config: FontConfiguration) -> None:
        """Update font configuration
        
        Args:
            font_config: New font configuration
        """
        self.font_config = font_config
    
    def add_font_directory(self, font_dir: str) -> None:
        """Add font directory to configuration
        
        Args:
            font_dir: Path to font directory
        """
        if os.path.exists(font_dir):
            self.font_config.add_font_directory(font_dir)
        else:
            raise FileNotFoundError(f"Font directory not found: {font_dir}")


class PDFGenerationError(Exception):
    """Custom exception for PDF generation errors"""
    pass