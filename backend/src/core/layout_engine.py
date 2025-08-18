"""Layout engine for advanced CSS layout support"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class LayoutType(Enum):
    """Supported layout types"""
    FLEXBOX = "flexbox"
    GRID = "grid"
    FLOAT = "float"
    BLOCK = "block"
    INLINE = "inline"
    TABLE = "table"


class PageSize(Enum):
    """Standard page sizes"""
    A4 = "A4"
    A3 = "A3"
    A5 = "A5"
    LETTER = "Letter"
    LEGAL = "Legal"
    TABLOID = "Tabloid"


@dataclass
class LayoutConfig:
    """Configuration for layout settings"""
    page_size: PageSize = PageSize.A4
    orientation: str = "portrait"  # portrait or landscape
    margins: Dict[str, str] = None
    columns: int = 1
    column_gap: str = "20px"
    line_height: float = 1.5
    font_size: str = "12pt"
    font_family: str = "Arial, sans-serif"
    
    def __post_init__(self):
        if self.margins is None:
            self.margins = {
                "top": "2cm",
                "right": "2cm",
                "bottom": "2cm",
                "left": "2cm"
            }


class LayoutEngine:
    """Advanced layout engine for PDF generation"""
    
    def __init__(self):
        """Initialize layout engine"""
        self.default_config = LayoutConfig()
        self.custom_styles = {}
        
    def get_report_layout_config(self) -> Dict[str, Any]:
        """Get default layout configuration for psychological reports"""
        return {
            "page_config": self._get_page_config(),
            "typography": self._get_typography_config(),
            "spacing": self._get_spacing_config(),
            "colors": self._get_color_scheme(),
            "layout_classes": self._get_layout_classes()
        }
    
    def _get_page_config(self) -> Dict[str, str]:
        """Get page configuration CSS"""
        return {
            "size": f"{self.default_config.page_size.value} {self.default_config.orientation}",
            "margin_top": self.default_config.margins["top"],
            "margin_right": self.default_config.margins["right"],
            "margin_bottom": self.default_config.margins["bottom"],
            "margin_left": self.default_config.margins["left"]
        }
    
    def _get_typography_config(self) -> Dict[str, str]:
        """Get typography configuration"""
        return {
            "base_font_family": self.default_config.font_family,
            "base_font_size": self.default_config.font_size,
            "base_line_height": str(self.default_config.line_height),
            "heading_font_family": "Georgia, serif",
            "monospace_font_family": "Courier New, monospace"
        }
    
    def _get_spacing_config(self) -> Dict[str, str]:
        """Get spacing configuration"""
        return {
            "section_margin": "20px 0",
            "paragraph_margin": "10px 0",
            "list_margin": "15px 0",
            "table_margin": "15px 0",
            "header_margin": "0 0 15px 0"
        }
    
    def _get_color_scheme(self) -> Dict[str, str]:
        """Get color scheme for reports"""
        return {
            "primary": "#2c3e50",
            "secondary": "#3498db",
            "accent": "#e74c3c",
            "success": "#27ae60",
            "warning": "#f39c12",
            "danger": "#e74c3c",
            "light": "#ecf0f1",
            "dark": "#2c3e50",
            "text_primary": "#2c3e50",
            "text_secondary": "#7f8c8d",
            "border": "#bdc3c7",
            "background": "#ffffff"
        }
    
    def _get_layout_classes(self) -> Dict[str, str]:
        """Get CSS classes for common layout patterns"""
        return {
            "container": """
                max-width: 100%;
                margin: 0 auto;
                padding: 0 15px;
            """,
            "row": """
                display: flex;
                flex-wrap: wrap;
                margin: 0 -15px;
            """,
            "col": """
                flex: 1;
                padding: 0 15px;
            """,
            "col-half": """
                flex: 0 0 50%;
                padding: 0 15px;
            """,
            "col-third": """
                flex: 0 0 33.333%;
                padding: 0 15px;
            """,
            "col-quarter": """
                flex: 0 0 25%;
                padding: 0 15px;
            """,
            "text-center": "text-align: center;",
            "text-left": "text-align: left;",
            "text-right": "text-align: right;",
            "text-justify": "text-align: justify;",
            "mb-1": "margin-bottom: 0.25rem;",
            "mb-2": "margin-bottom: 0.5rem;",
            "mb-3": "margin-bottom: 1rem;",
            "mb-4": "margin-bottom: 1.5rem;",
            "mb-5": "margin-bottom: 3rem;",
            "mt-1": "margin-top: 0.25rem;",
            "mt-2": "margin-top: 0.5rem;",
            "mt-3": "margin-top: 1rem;",
            "mt-4": "margin-top: 1.5rem;",
            "mt-5": "margin-top: 3rem;",
            "p-1": "padding: 0.25rem;",
            "p-2": "padding: 0.5rem;",
            "p-3": "padding: 1rem;",
            "p-4": "padding: 1.5rem;",
            "p-5": "padding: 3rem;"
        }
    
    def generate_css_grid(self, columns: int, gap: str = "20px", 
                         areas: Optional[List[str]] = None) -> str:
        """Generate CSS Grid layout
        
        Args:
            columns: Number of columns
            gap: Gap between grid items
            areas: Optional grid template areas
            
        Returns:
            CSS grid styles
        """
        css = f"""
            display: grid;
            grid-template-columns: repeat({columns}, 1fr);
            gap: {gap};
        """
        
        if areas:
            grid_areas = '\n'.join([f'    "{area}"' for area in areas])
            css += f"""
            grid-template-areas:
{grid_areas};
            """
        
        return css.strip()
    
    def generate_flexbox_layout(self, direction: str = "row", 
                               justify: str = "flex-start",
                               align: str = "stretch",
                               wrap: str = "nowrap") -> str:
        """Generate Flexbox layout
        
        Args:
            direction: Flex direction (row, column, etc.)
            justify: Justify content value
            align: Align items value
            wrap: Flex wrap value
            
        Returns:
            CSS flexbox styles
        """
        return f"""
            display: flex;
            flex-direction: {direction};
            justify-content: {justify};
            align-items: {align};
            flex-wrap: {wrap};
        """.strip()
    
    def generate_table_layout(self, columns: List[str], 
                             border: bool = True,
                             striped: bool = False) -> Dict[str, str]:
        """Generate table layout styles
        
        Args:
            columns: List of column widths (e.g., ['25%', '50%', '25%'])
            border: Whether to include borders
            striped: Whether to include striped rows
            
        Returns:
            Dictionary of CSS styles for table elements
        """
        styles = {
            "table": """
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            """,
            "th": """
                background-color: #f8f9fa;
                font-weight: bold;
                padding: 12px;
                text-align: left;
            """,
            "td": """
                padding: 12px;
                vertical-align: top;
            """
        }
        
        if border:
            border_style = "border: 1px solid #dee2e6;"
            styles["table"] += f"\n{border_style}"
            styles["th"] += f"\n{border_style}"
            styles["td"] += f"\n{border_style}"
        
        if striped:
            styles["tr:nth-child(even)"] = "background-color: #f8f9fa;"
        
        # Add column width styles
        for i, width in enumerate(columns, 1):
            styles[f"col:nth-child({i})"] = f"width: {width};"
        
        return styles
    
    def generate_responsive_layout(self, breakpoints: Dict[str, str]) -> str:
        """Generate responsive layout with media queries
        
        Args:
            breakpoints: Dictionary of breakpoint names and CSS
            
        Returns:
            CSS with media queries
        """
        media_queries = {
            "mobile": "(max-width: 767px)",
            "tablet": "(min-width: 768px) and (max-width: 1023px)",
            "desktop": "(min-width: 1024px)",
            "print": "print"
        }
        
        css_parts = []
        for breakpoint, styles in breakpoints.items():
            if breakpoint in media_queries:
                media_query = media_queries[breakpoint]
                css_parts.append(f"@media {media_query} {{\n{styles}\n}}")
        
        return "\n\n".join(css_parts)
    
    def generate_print_styles(self) -> str:
        """Generate print-specific styles"""
        return """
            @media print {
                @page {
                    margin: 2cm;
                    size: A4 portrait;
                }
                
                body {
                    font-size: 12pt;
                    line-height: 1.4;
                    color: black;
                }
                
                .no-print {
                    display: none !important;
                }
                
                .page-break {
                    page-break-before: always;
                }
                
                .avoid-break {
                    page-break-inside: avoid;
                }
                
                h1, h2, h3, h4, h5, h6 {
                    page-break-after: avoid;
                }
                
                table {
                    page-break-inside: auto;
                }
                
                tr {
                    page-break-inside: avoid;
                    page-break-after: auto;
                }
                
                thead {
                    display: table-header-group;
                }
                
                tfoot {
                    display: table-footer-group;
                }
            }
        """.strip()
    
    def create_layout_config(self, **kwargs) -> LayoutConfig:
        """Create custom layout configuration
        
        Args:
            **kwargs: Layout configuration parameters
            
        Returns:
            LayoutConfig instance
        """
        config_dict = {
            "page_size": kwargs.get("page_size", PageSize.A4),
            "orientation": kwargs.get("orientation", "portrait"),
            "margins": kwargs.get("margins"),
            "columns": kwargs.get("columns", 1),
            "column_gap": kwargs.get("column_gap", "20px"),
            "line_height": kwargs.get("line_height", 1.5),
            "font_size": kwargs.get("font_size", "12pt"),
            "font_family": kwargs.get("font_family", "Arial, sans-serif")
        }
        
        return LayoutConfig(**config_dict)
    
    def apply_layout_config(self, config: LayoutConfig) -> str:
        """Apply layout configuration and return CSS
        
        Args:
            config: Layout configuration
            
        Returns:
            CSS styles based on configuration
        """
        css_parts = []
        
        # Page setup
        page_css = f"""
            @page {{
                size: {config.page_size.value} {config.orientation};
                margin-top: {config.margins['top']};
                margin-right: {config.margins['right']};
                margin-bottom: {config.margins['bottom']};
                margin-left: {config.margins['left']};
            }}
        """
        css_parts.append(page_css)
        
        # Body styles
        body_css = f"""
            body {{
                font-family: {config.font_family};
                font-size: {config.font_size};
                line-height: {config.line_height};
            }}
        """
        css_parts.append(body_css)
        
        # Column layout if specified
        if config.columns > 1:
            column_css = f"""
                .content {{
                    column-count: {config.columns};
                    column-gap: {config.column_gap};
                }}
            """
            css_parts.append(column_css)
        
        return "\n".join(css_parts)