"""API module for Flask endpoints"""

from .app import create_app
from .routes import pdf_routes, health_routes

__all__ = ['create_app', 'pdf_routes', 'health_routes']