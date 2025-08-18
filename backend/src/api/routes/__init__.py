"""API routes package"""

from .health_routes import health_bp
from .pdf_routes import pdf_bp
from .auth_routes import auth_bp
from .template_routes import template_bp
from .report_routes import report_bp

__all__ = ['health_bp', 'pdf_bp', 'auth_bp', 'template_bp', 'report_bp']