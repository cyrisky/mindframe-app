"""PDF generation API routes"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from pydantic import ValidationError
from ...core.pdf_generator import PDFGenerator, PDFGenerationError
from ...services.pdf_service import PDFService
from ...services.template_service import TemplateService
from ...utils.decorators import rate_limit, require_api_key
from ...utils.input_validation import validate_json, ValidationError as InputValidationError
from ...models.request_models import PDFFromHtmlRequest, PDFFromTemplateRequest, PsychologicalReportRequest


pdf_bp = Blueprint('pdf', __name__)


@pdf_bp.route('/pdf/generate', methods=['POST'])
@rate_limit('10 per minute')
@validate_json(pydantic_model=PDFFromHtmlRequest)
def generate_pdf():
    """Generate PDF from HTML content
    
    Request JSON:
        {
            "html_content": "<html>...</html>",
            "css_content": "body { margin: 0; }" (optional),
            "options": {
                "page_size": "A4",
                "orientation": "portrait",
                "margins": {...}
            } (optional)
        }
    
    Returns:
        PDF file or JSON with download URL
    """
    try:
        # Access validated data
        validated_data = request.validated_data
        html_content = validated_data['html_content']
        css_content = validated_data.get('css_content')
        options = validated_data.get('options', {})
        
        # Initialize PDF service
        pdf_service = PDFService()
        
        # Generate PDF
        result = pdf_service.generate_pdf_from_html(
            html_content=html_content,
            css_content=css_content,
            options=options
        )
        
        if request.args.get('download') == 'true':
            # Return PDF file directly
            return send_file(
                result['file_path'],
                as_attachment=True,
                download_name=result['filename'],
                mimetype='application/pdf'
            )
        else:
            # Return JSON with file info
            return jsonify({
                'success': True,
                'pdf_id': result['pdf_id'],
                'filename': result['filename'],
                'file_size': result['file_size'],
                'download_url': f"/api/v1/pdf/download/{result['pdf_id']}",
                'generated_at': result['generated_at']
            })
            
    except ValidationError as e:
        current_app.logger.warning(f"Validation error in PDF generation: {str(e)}")
        return jsonify({
            'error': 'Validation failed',
            'details': e.errors()
        }), 400
        
    except InputValidationError as e:
        current_app.logger.warning(f"Input validation error in PDF generation: {str(e)}")
        return jsonify({
            'error': 'Invalid input',
            'message': str(e)
        }), 400
        
    except PDFGenerationError as e:
        current_app.logger.error(f"PDF generation error: {str(e)}")
        return jsonify({
            'error': 'PDF generation failed',
            'message': str(e)
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Unexpected error in PDF generation: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500


@pdf_bp.route('/pdf/generate-from-template', methods=['POST'])
@rate_limit('10 per minute')
@validate_json(pydantic_model=PDFFromTemplateRequest)
def generate_pdf_from_template():
    """Generate PDF from template
    
    Request JSON:
        {
            "template_name": "psychological_report.html",
            "data": {
                "patient_name": "John Doe",
                "test_date": "2024-01-15",
                "test_results": [...]
            },
            "options": {...} (optional)
        }
    
    Returns:
        PDF file or JSON with download URL
    """
    try:
        # Access validated data
        validated_data = request.validated_data
        template_name = validated_data['template_name']
        template_data = validated_data['data']
        options = validated_data.get('options', {})
        
        # Initialize PDF service
        pdf_service = PDFService()
        
        # Generate PDF from template
        result = pdf_service.generate_pdf_from_template(
            template_name=template_name,
            template_data=template_data,
            options=options
        )
        
        if request.args.get('download') == 'true':
            # Return PDF file directly
            return send_file(
                result['file_path'],
                as_attachment=True,
                download_name=result['filename'],
                mimetype='application/pdf'
            )
        else:
            # Return JSON with file info
            return jsonify({
                'success': True,
                'pdf_id': result['pdf_id'],
                'filename': result['filename'],
                'file_size': result['file_size'],
                'download_url': f"/api/v1/pdf/download/{result['pdf_id']}",
                'generated_at': result['generated_at']
            })
            
    except ValidationError as e:
        current_app.logger.warning(f"Validation error in PDF template generation: {str(e)}")
        return jsonify({
            'error': 'Validation failed',
            'details': e.errors()
        }), 400
        
    except InputValidationError as e:
        current_app.logger.warning(f"Input validation error in PDF template generation: {str(e)}")
        return jsonify({
            'error': 'Invalid input',
            'message': str(e)
        }), 400
        
    except PDFGenerationError as e:
        current_app.logger.error(f"PDF generation error: {str(e)}")
        return jsonify({
            'error': 'PDF generation failed',
            'message': str(e)
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Unexpected error in PDF generation: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500


@pdf_bp.route('/pdf/generate-report', methods=['POST'])
@rate_limit('5 per minute')
@validate_json(pydantic_model=PsychologicalReportRequest)
def generate_psychological_report():
    """Generate psychological test report PDF
    
    Request JSON:
        {
            "patient_info": {
                "name": "John Doe",
                "age": 25,
                "gender": "Male",
                "test_date": "2024-01-15"
            },
            "test_results": [
                {
                    "test_name": "IQ Test",
                    "score": 120,
                    "percentile": 85,
                    "interpretation": "Above Average"
                }
            ],
            "template_options": {
                "include_charts": true,
                "include_recommendations": true
            }
        }
    
    Returns:
        PDF file or JSON with download URL
    """
    try:
        # Access validated data
        validated_data = request.validated_data
        patient_info = validated_data['patient_info']
        test_results = validated_data['test_results']
        template_options = validated_data.get('template_options', {})
        
        # Initialize PDF service
        pdf_service = PDFService()
        
        # Generate psychological report
        result = pdf_service.generate_psychological_report(
            patient_info=patient_info,
            test_results=test_results,
            template_options=template_options
        )
        
        if request.args.get('download') == 'true':
            # Return PDF file directly
            return send_file(
                result['file_path'],
                as_attachment=True,
                download_name=result['filename'],
                mimetype='application/pdf'
            )
        else:
            # Return JSON with file info
            return jsonify({
                'success': True,
                'pdf_id': result['pdf_id'],
                'filename': result['filename'],
                'file_size': result['file_size'],
                'download_url': f"/api/v1/pdf/download/{result['pdf_id']}",
                'generated_at': result['generated_at'],
                'report_type': 'psychological_report'
            })
            
    except ValidationError as e:
        current_app.logger.warning(f"Validation error in psychological report generation: {str(e)}")
        return jsonify({
            'error': 'Validation failed',
            'details': e.errors()
        }), 400
        
    except InputValidationError as e:
        current_app.logger.warning(f"Input validation error in psychological report generation: {str(e)}")
        return jsonify({
            'error': 'Invalid input',
            'message': str(e)
        }), 400
        
    except PDFGenerationError as e:
        current_app.logger.error(f"Report generation error: {str(e)}")
        return jsonify({
            'error': 'Report generation failed',
            'message': str(e)
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Unexpected error in report generation: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500


@pdf_bp.route('/pdf/download/<pdf_id>', methods=['GET'])
def download_pdf(pdf_id):
    """Download generated PDF by ID
    
    Args:
        pdf_id: Unique identifier for the PDF
        
    Returns:
        PDF file
    """
    try:
        pdf_service = PDFService()
        file_info = pdf_service.get_pdf_info(pdf_id)
        
        if not file_info:
            return jsonify({
                'error': 'PDF not found',
                'message': f'PDF with ID {pdf_id} not found'
            }), 404
        
        if not os.path.exists(file_info['file_path']):
            return jsonify({
                'error': 'File not found',
                'message': 'PDF file no longer exists on server'
            }), 404
        
        return send_file(
            file_info['file_path'],
            as_attachment=True,
            download_name=file_info['filename'],
            mimetype='application/pdf'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error downloading PDF {pdf_id}: {str(e)}")
        return jsonify({
            'error': 'Download failed',
            'message': 'An error occurred while downloading the PDF'
        }), 500


@pdf_bp.route('/pdf/list', methods=['GET'])
def list_pdfs():
    """List generated PDFs
    
    Query parameters:
        - limit: Number of PDFs to return (default: 20)
        - offset: Number of PDFs to skip (default: 0)
        - type: Filter by PDF type (optional)
        
    Returns:
        JSON list of PDF information
    """
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        pdf_type = request.args.get('type')
        
        pdf_service = PDFService()
        pdfs = pdf_service.list_pdfs(
            limit=limit,
            offset=offset,
            pdf_type=pdf_type
        )
        
        return jsonify({
            'success': True,
            'pdfs': pdfs,
            'total': len(pdfs),
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        current_app.logger.error(f"Error listing PDFs: {str(e)}")
        return jsonify({
            'error': 'Failed to list PDFs',
            'message': 'An error occurred while retrieving PDF list'
        }), 500


@pdf_bp.route('/pdf/delete/<pdf_id>', methods=['DELETE'])
def delete_pdf(pdf_id):
    """Delete generated PDF
    
    Args:
        pdf_id: Unique identifier for the PDF
        
    Returns:
        JSON confirmation
    """
    try:
        pdf_service = PDFService()
        success = pdf_service.delete_pdf(pdf_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'PDF {pdf_id} deleted successfully'
            })
        else:
            return jsonify({
                'error': 'PDF not found',
                'message': f'PDF with ID {pdf_id} not found'
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"Error deleting PDF {pdf_id}: {str(e)}")
        return jsonify({
            'error': 'Delete failed',
            'message': 'An error occurred while deleting the PDF'
        }), 500


@pdf_bp.route('/templates/list', methods=['GET'])
def list_templates():
    """List available PDF templates
    
    Returns:
        JSON list of available templates
    """
    try:
        template_service = TemplateService()
        templates = template_service.list_templates()
        
        return jsonify({
            'success': True,
            'templates': templates
        })
        
    except Exception as e:
        current_app.logger.error(f"Error listing templates: {str(e)}")
        return jsonify({
            'error': 'Failed to list templates',
            'message': 'An error occurred while retrieving template list'
        }), 500


@pdf_bp.route('/templates/<template_name>/preview', methods=['POST'])
def preview_template(template_name):
    """Preview template with sample data
    
    Args:
        template_name: Name of the template to preview
        
    Request JSON:
        {
            "data": {...} (optional sample data)
        }
        
    Returns:
        HTML preview of the template
    """
    try:
        data = request.get_json() or {}
        sample_data = data.get('data', {})
        
        template_service = TemplateService()
        html_preview = template_service.preview_template(
            template_name=template_name,
            sample_data=sample_data
        )
        
        return html_preview, 200, {'Content-Type': 'text/html'}
        
    except Exception as e:
        current_app.logger.error(f"Error previewing template {template_name}: {str(e)}")
        return jsonify({
            'error': 'Preview failed',
            'message': f'An error occurred while previewing template {template_name}'
        }), 500