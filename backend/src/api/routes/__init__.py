"""API routes package"""

from .health_routes import health_bp
from .pdf_routes import pdf_bp
from .auth_routes import auth_bp
from .template_routes import template_bp
from .report_routes import report_bp
from .interpretation_routes import interpretation_bp
from .admin_routes import admin_bp
from .job_routes import job_bp

__all__ = ['health_bp', 'pdf_bp', 'auth_bp', 'template_bp', 'report_bp', 'interpretation_bp', 'admin_bp', 'job_bp']