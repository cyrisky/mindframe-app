#!/usr/bin/env python3
"""
API endpoint untuk Personal Values PDF generation dari MongoDB payload
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
import tempfile
from datetime import datetime
from typing import Dict, Any

# Import service
from ..services.mongo_personal_values_service import MongoPersonalValuesService

app = Flask(__name__)
CORS(app)

# Initialize service
service = MongoPersonalValuesService(
    template_dir="/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/backend/templates"
)

@app.route('/api/personal-values/generate-pdf', methods=['POST'])
def generate_personal_values_pdf():
    """
    Generate PDF dari MongoDB payload Personal Values
    
    Expected JSON payload:
    {
        "mongoData": { ... }, // Full MongoDB document
        "options": {
            "saveIntermediateFiles": false, // Optional
            "customOutputName": "custom_name.pdf" // Optional
        }
    }
    
    Returns:
    - Success: PDF file download
    - Error: JSON error response
    """
    try:
        # Parse request
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No JSON data provided",
                "code": "INVALID_REQUEST"
            }), 400
        
        mongo_data = data.get("mongoData")
        options = data.get("options", {})
        
        if not mongo_data:
            return jsonify({
                "error": "mongoData is required",
                "code": "MISSING_MONGO_DATA"
            }), 400
        
        # Validate MongoDB payload
        validation = service.validate_mongo_payload(mongo_data)
        
        if not validation["valid"]:
            return jsonify({
                "error": "Invalid MongoDB payload",
                "code": "VALIDATION_FAILED",
                "details": validation["errors"],
                "warnings": validation.get("warnings", [])
            }), 400
        
        # Generate output filename
        custom_name = options.get("customOutputName")
        if custom_name:
            if not custom_name.endswith('.pdf'):
                custom_name += '.pdf'
            output_filename = custom_name
        else:
            # Generate filename dari client info
            client_name = mongo_data.get("name", "unknown")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"personal_values_{client_name}_{timestamp}.pdf"
        
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, output_filename)
        
        # Process MongoDB payload ke PDF
        result = service.process_mongo_payload_to_pdf(
            mongo_data,
            output_path,
            save_intermediate_files=options.get("saveIntermediateFiles", False)
        )
        
        if not result["success"]:
            return jsonify({
                "error": "Failed to generate PDF",
                "code": "PDF_GENERATION_FAILED",
                "details": result["error"]
            }), 500
        
        # Return PDF file
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "details": str(e)
        }), 500

@app.route('/api/personal-values/validate', methods=['POST'])
def validate_personal_values_payload():
    """
    Validate MongoDB payload untuk Personal Values
    
    Expected JSON payload:
    {
        "mongoData": { ... } // Full MongoDB document
    }
    
    Returns:
    JSON validation result
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No JSON data provided",
                "code": "INVALID_REQUEST"
            }), 400
        
        mongo_data = data.get("mongoData")
        
        if not mongo_data:
            return jsonify({
                "error": "mongoData is required",
                "code": "MISSING_MONGO_DATA"
            }), 400
        
        # Validate payload
        validation = service.validate_mongo_payload(mongo_data)
        
        # Extract additional info jika valid
        additional_info = {}
        if validation["valid"]:
            try:
                extracted_data = service.extract_personal_values_from_mongo(mongo_data)
                scores = extracted_data["scores"]
                top_values = service.get_top_n_values(scores, 3)
                
                additional_info = {
                    "clientInfo": extracted_data["clientInfo"],
                    "formInfo": {
                        "formId": extracted_data["formId"],
                        "formName": extracted_data["formName"]
                    },
                    "topValues": [
                        {"key": key, "score": score, "rank": i+1}
                        for i, (key, score) in enumerate(top_values)
                    ],
                    "totalScores": len(scores)
                }
            except Exception as e:
                validation["warnings"].append(f"Could not extract additional info: {str(e)}")
        
        return jsonify({
            "validation": validation,
            "additionalInfo": additional_info
        })
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "details": str(e)
        }), 500

@app.route('/api/personal-values/preview', methods=['POST'])
def preview_personal_values_data():
    """
    Preview data yang akan digunakan untuk generate PDF
    
    Expected JSON payload:
    {
        "mongoData": { ... } // Full MongoDB document
    }
    
    Returns:
    JSON dengan template data yang akan digunakan
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No JSON data provided",
                "code": "INVALID_REQUEST"
            }), 400
        
        mongo_data = data.get("mongoData")
        
        if not mongo_data:
            return jsonify({
                "error": "mongoData is required",
                "code": "MISSING_MONGO_DATA"
            }), 400
        
        # Validate payload
        validation = service.validate_mongo_payload(mongo_data)
        
        if not validation["valid"]:
            return jsonify({
                "error": "Invalid MongoDB payload",
                "code": "VALIDATION_FAILED",
                "details": validation["errors"]
            }), 400
        
        # Extract dan map data
        extracted_data = service.extract_personal_values_from_mongo(mongo_data)
        mapped_data = service.map_to_interpretation_format(extracted_data)
        template_data = service.generate_template_data(mapped_data)
        
        return jsonify({
            "templateData": template_data,
            "mappedData": mapped_data,
            "extractedData": extracted_data
        })
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "details": str(e)
        }), 500

@app.route('/api/personal-values/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    try:
        # Check if interpretation data is loaded
        interpretation_loaded = bool(service.interpretation_data)
        
        # Check if template directory exists
        template_dir_exists = os.path.exists(service.template_dir)
        
        return jsonify({
            "status": "healthy",
            "service": "Personal Values PDF Generator",
            "checks": {
                "interpretationDataLoaded": interpretation_loaded,
                "templateDirectoryExists": template_dir_exists,
                "interpretationDataPath": service.interpretation_data_path,
                "templateDirectory": service.template_dir
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "code": "NOT_FOUND"
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": "Method not allowed",
        "code": "METHOD_NOT_ALLOWED"
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "code": "INTERNAL_ERROR"
    }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)