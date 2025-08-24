"""Job queue routes for PDF generation jobs"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import logging
from typing import Dict, Any, Optional
from pydantic import ValidationError

from ...utils.decorators import rate_limit
from ...utils.input_validation import validate_json, ValidationError as InputValidationError
from ...models.request_models import PDFJobSubmissionRequest, JobStatusRequest
from ...utils.logging_utils import LoggingUtils
from ...utils.error_handler import raise_validation_error, raise_not_found
from job_queue.jobs import submit_pdf_job, get_job_status

# Create blueprint
job_bp = Blueprint('jobs', __name__)
logger = LoggingUtils.get_logger(__name__)


@job_bp.route('/pdf/submit', methods=['POST'])
@rate_limit('5 per minute')
@validate_json(pydantic_model=PDFJobSubmissionRequest)
def submit_pdf_generation_job():
    """Submit a PDF generation job
    
    Request JSON:
        {
            "code": "TEST123",
            "product_id": "PROD456",
            "user_email": "user@example.com",
            "user_name": "John Doe",
            "callback_url": "https://example.com/webhook" (optional)
        }
    
    Returns:
        JSON response with job ID and status
    """
    try:
        # Access validated data
        validated_data = request.validated_data
        
        logger.info(f"Submitting PDF job for code: {validated_data['code']}, product: {validated_data['product_id']}")
        
        # Submit job to queue
        job_result = submit_pdf_job(
            code=validated_data['code'],
            product_id=validated_data['product_id'],
            user_email=validated_data['user_email'],
            user_name=validated_data['user_name'],
            callback_url=validated_data.get('callback_url')
        )
        
        logger.info(f"PDF job submitted successfully with ID: {job_result['job_id']}")
        
        return jsonify({
            'success': True,
            'job_id': job_result['job_id'],
            'status': job_result['status'],
            'message': 'PDF generation job submitted successfully',
            'estimated_completion': job_result.get('estimated_completion'),
            'created_at': job_result.get('created_at')
        }), 201
        
    except ValidationError as e:
        logger.warning(f"Validation error in PDF job submission: {str(e)}")
        return jsonify({
            'error': 'Validation failed',
            'details': e.errors()
        }), 400
        
    except InputValidationError as e:
        logger.warning(f"Input validation error in PDF job submission: {str(e)}")
        return jsonify({
            'error': 'Invalid input',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error in PDF job submission: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to submit PDF generation job'
        }), 500


@job_bp.route('/status/<job_id>', methods=['GET'])
@rate_limit('20 per minute')
def get_pdf_job_status(job_id: str):
    """Get the status of a PDF generation job
    
    Args:
        job_id: The job ID to check status for
    
    Returns:
        JSON response with job status and details
    """
    try:
        if not job_id or not job_id.strip():
            return jsonify({
                'error': 'Invalid job ID',
                'message': 'Job ID cannot be empty'
            }), 400
        
        logger.info(f"Checking status for job ID: {job_id}")
        
        # Get job status
        job_status = get_job_status(job_id.strip())
        
        if not job_status:
            logger.warning(f"Job not found: {job_id}")
            return jsonify({
                'error': 'Job not found',
                'message': f'No job found with ID: {job_id}'
            }), 404
        
        logger.info(f"Job status retrieved for ID {job_id}: {job_status.get('status')}")
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': job_status['status'],
            'progress': job_status.get('progress', 0),
            'message': job_status.get('message', ''),
            'result': job_status.get('result'),
            'error': job_status.get('error'),
            'created_at': job_status.get('created_at'),
            'updated_at': job_status.get('updated_at'),
            'completed_at': job_status.get('completed_at')
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in job status check: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve job status'
        }), 500


@job_bp.route('/status', methods=['POST'])
@rate_limit('20 per minute')
@validate_json(pydantic_model=JobStatusRequest)
def get_pdf_job_status_post():
    """Get the status of a PDF generation job via POST
    
    Request JSON:
        {
            "job_id": "job_123456"
        }
    
    Returns:
        JSON response with job status and details
    """
    try:
        # Access validated data
        validated_data = request.validated_data
        job_id = validated_data['job_id']
        
        logger.info(f"Checking status for job ID (POST): {job_id}")
        
        # Get job status
        job_status = get_job_status(job_id)
        
        if not job_status:
            logger.warning(f"Job not found: {job_id}")
            return jsonify({
                'error': 'Job not found',
                'message': f'No job found with ID: {job_id}'
            }), 404
        
        logger.info(f"Job status retrieved for ID {job_id}: {job_status.get('status')}")
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': job_status['status'],
            'progress': job_status.get('progress', 0),
            'message': job_status.get('message', ''),
            'result': job_status.get('result'),
            'error': job_status.get('error'),
            'created_at': job_status.get('created_at'),
            'updated_at': job_status.get('updated_at'),
            'completed_at': job_status.get('completed_at')
        }), 200
        
    except ValidationError as e:
        logger.warning(f"Validation error in job status check: {str(e)}")
        return jsonify({
            'error': 'Validation failed',
            'details': e.errors()
        }), 400
        
    except InputValidationError as e:
        logger.warning(f"Input validation error in job status check: {str(e)}")
        return jsonify({
            'error': 'Invalid input',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error in job status check: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve job status'
        }), 500


@job_bp.route('/health', methods=['GET'])
def job_queue_health():
    """Health check endpoint for job queue system
    
    Returns:
        JSON response with job queue health status
    """
    try:
        # Basic health check - could be expanded to check Redis connectivity
        return jsonify({
            'success': True,
            'service': 'job_queue',
            'status': 'healthy',
            'timestamp': LoggingUtils.get_timestamp()
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'success': False,
            'service': 'job_queue',
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': LoggingUtils.get_timestamp()
        }), 503


# Error handlers for this blueprint
@job_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors for job routes"""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested job endpoint was not found',
        'status_code': 404
    }), 404


@job_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors for job routes"""
    return jsonify({
        'error': 'Method Not Allowed',
        'message': 'The requested method is not allowed for this endpoint',
        'status_code': 405
    }), 405


@job_bp.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle rate limit exceeded errors"""
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests. Please try again later.',
        'status_code': 429
    }), 429