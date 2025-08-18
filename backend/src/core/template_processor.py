"""Template processing module using Jinja2"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
from jinja2.exceptions import TemplateError


class TemplateProcessor:
    """Template processor for HTML templates using Jinja2"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """Initialize template processor
        
        Args:
            template_dir: Directory containing templates
        """
        self.template_dir = template_dir or "shared/templates"
        self.env = self._setup_environment()
        
    def _setup_environment(self) -> Environment:
        """Setup Jinja2 environment with custom filters and functions"""
        # Create environment with file system loader
        if os.path.exists(self.template_dir):
            loader = FileSystemLoader(self.template_dir)
        else:
            # Fallback to current directory if template dir doesn't exist
            loader = FileSystemLoader(".")
            
        env = Environment(
            loader=loader,
            autoescape=True,  # Enable auto-escaping for security
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        env.filters['format_date'] = self._format_date
        env.filters['format_score'] = self._format_score
        env.filters['format_percentage'] = self._format_percentage
        env.filters['capitalize_words'] = self._capitalize_words
        env.filters['safe_html'] = self._safe_html
        
        # Add custom functions
        env.globals['get_score_interpretation'] = self._get_score_interpretation
        env.globals['generate_chart_data'] = self._generate_chart_data
        env.globals['format_test_results'] = self._format_test_results
        
        return env
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render template with context data
        
        Args:
            template_name: Name of the template file
            context: Data to render in template
            
        Returns:
            Rendered HTML string
            
        Raises:
            TemplateProcessingError: If template rendering fails
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
            
        except TemplateNotFound as e:
            raise TemplateProcessingError(f"Template not found: {template_name}") from e
        except TemplateError as e:
            raise TemplateProcessingError(f"Template rendering error: {str(e)}") from e
        except Exception as e:
            raise TemplateProcessingError(f"Unexpected error rendering template: {str(e)}") from e
    
    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render template from string
        
        Args:
            template_string: Template content as string
            context: Data to render in template
            
        Returns:
            Rendered HTML string
        """
        try:
            template = self.env.from_string(template_string)
            return template.render(**context)
            
        except TemplateError as e:
            raise TemplateProcessingError(f"String template rendering error: {str(e)}") from e
        except Exception as e:
            raise TemplateProcessingError(f"Unexpected error rendering string template: {str(e)}") from e
    
    def list_templates(self) -> List[str]:
        """List available templates
        
        Returns:
            List of template file names
        """
        try:
            return self.env.list_templates()
        except Exception as e:
            raise TemplateProcessingError(f"Error listing templates: {str(e)}") from e
    
    def template_exists(self, template_name: str) -> bool:
        """Check if template exists
        
        Args:
            template_name: Name of the template file
            
        Returns:
            True if template exists, False otherwise
        """
        try:
            self.env.get_template(template_name)
            return True
        except TemplateNotFound:
            return False
    
    def add_template_directory(self, directory: str) -> None:
        """Add additional template directory
        
        Args:
            directory: Path to template directory
        """
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Template directory not found: {directory}")
            
        # Update loader with multiple directories
        current_paths = []
        if hasattr(self.env.loader, 'searchpath'):
            current_paths = list(self.env.loader.searchpath)
            
        current_paths.append(directory)
        self.env.loader = FileSystemLoader(current_paths)
    
    # Custom filter functions
    def _format_date(self, date_value, format_string: str = "%Y-%m-%d") -> str:
        """Format date value"""
        if not date_value:
            return ""
        try:
            if hasattr(date_value, 'strftime'):
                return date_value.strftime(format_string)
            return str(date_value)
        except Exception:
            return str(date_value)
    
    def _format_score(self, score_value, decimal_places: int = 1) -> str:
        """Format score value"""
        try:
            if score_value is None:
                return "N/A"
            return f"{float(score_value):.{decimal_places}f}"
        except (ValueError, TypeError):
            return str(score_value)
    
    def _format_percentage(self, value, decimal_places: int = 1) -> str:
        """Format value as percentage"""
        try:
            if value is None:
                return "N/A"
            return f"{float(value):.{decimal_places}f}%"
        except (ValueError, TypeError):
            return str(value)
    
    def _capitalize_words(self, text: str) -> str:
        """Capitalize each word in text"""
        if not text:
            return ""
        return " ".join(word.capitalize() for word in str(text).split())
    
    def _safe_html(self, html_content: str) -> str:
        """Mark HTML content as safe (disable auto-escaping)"""
        from markupsafe import Markup
        return Markup(html_content)
    
    # Custom global functions
    def _get_score_interpretation(self, score: float, test_type: str) -> str:
        """Get interpretation for test score"""
        # This would typically be more sophisticated based on test type
        if test_type.lower() == "iq":
            if score >= 130:
                return "Very Superior"
            elif score >= 120:
                return "Superior"
            elif score >= 110:
                return "High Average"
            elif score >= 90:
                return "Average"
            elif score >= 80:
                return "Low Average"
            elif score >= 70:
                return "Borderline"
            else:
                return "Extremely Low"
        
        # Default interpretation
        if score >= 80:
            return "Above Average"
        elif score >= 60:
            return "Average"
        elif score >= 40:
            return "Below Average"
        else:
            return "Significantly Below Average"
    
    def _generate_chart_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chart data for visualization"""
        # This would generate data suitable for chart libraries
        chart_data = {
            "labels": list(data.keys()),
            "values": list(data.values()),
            "type": "bar"  # Default chart type
        }
        return chart_data
    
    def _format_test_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format test results for display"""
        formatted_results = []
        for result in results:
            formatted_result = {
                "test_name": result.get("name", "Unknown Test"),
                "score": self._format_score(result.get("score")),
                "interpretation": self._get_score_interpretation(
                    result.get("score", 0), 
                    result.get("type", "general")
                ),
                "percentile": self._format_percentage(result.get("percentile")),
                "date_administered": self._format_date(result.get("date"))
            }
            formatted_results.append(formatted_result)
        return formatted_results


class TemplateProcessingError(Exception):
    """Custom exception for template processing errors"""
    pass