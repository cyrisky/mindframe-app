from flask import Flask, request, jsonify, send_file
import os
import tempfile
import json
from datetime import datetime
from typing import Dict, Any

# Import service
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.mongo_personality_service import MongoPersonalityService

app = Flask(__name__)

# Initialize service
service = MongoPersonalityService()

@app.route('/api/personality/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'service': 'personality-api',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/personality/validate', methods=['POST'])
def validate_payload():
    """
    Validate MongoDB payload untuk kepribadian
    
    Returns:
        JSON response dengan hasil validasi
    """
    try:
        # Get JSON data from request
        mongo_payload = request.get_json()
        
        if not mongo_payload:
            return jsonify({
                'error': 'No JSON payload provided'
            }), 400
        
        # Validate payload
        validation_result = service.validate_mongo_payload(mongo_payload)
        
        return jsonify(validation_result)
        
    except Exception as e:
        return jsonify({
            'error': f'Validation error: {str(e)}'
        }), 500

@app.route('/api/personality/preview', methods=['POST'])
def preview_data():
    """
    Preview data yang akan digunakan untuk generate PDF
    
    Returns:
        JSON response dengan data template
    """
    try:
        # Get JSON data from request
        mongo_payload = request.get_json()
        
        if not mongo_payload:
            return jsonify({
                'error': 'No JSON payload provided'
            }), 400
        
        # Validate first
        validation_result = service.validate_mongo_payload(mongo_payload)
        if not validation_result['validation']['valid']:
            return jsonify({
                'error': 'Invalid payload',
                'validation': validation_result['validation']
            }), 400
        
        # Extract and map data
        extracted_data = service.extract_personality_data(mongo_payload)
        template_data = service.map_to_interpretation_format(extracted_data)
        
        return jsonify({
            'success': True,
            'templateData': template_data,
            'extractedData': extracted_data
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Preview error: {str(e)}'
        }), 500

@app.route('/api/personality/generate-pdf', methods=['POST'])
def generate_pdf():
    """
    Generate PDF dari MongoDB payload
    
    Returns:
        PDF file atau error response
    """
    try:
        # Get JSON data from request
        mongo_payload = request.get_json()
        
        if not mongo_payload:
            return jsonify({
                'error': 'No JSON payload provided'
            }), 400
        
        # Get optional parameters
        save_intermediate = request.args.get('save_intermediate', 'false').lower() == 'true'
        
        # Create temporary file for PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            temp_pdf_path = tmp_file.name
        
        try:
            # Process payload to PDF
            result = service.process_mongo_payload_to_pdf(
                mongo_payload,
                temp_pdf_path,
                save_intermediate_files=save_intermediate
            )
            
            if not result['success']:
                return jsonify({
                    'error': result.get('error', 'PDF generation failed'),
                    'validation': result.get('validation')
                }), 400
            
            # Generate filename
            client_name = result.get('client_name', 'Unknown')
            safe_name = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"personality_report_{safe_name.replace(' ', '_')}.pdf"
            
            # Return PDF file
            return send_file(
                temp_pdf_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
            
        finally:
            # Clean up temporary file after sending
            if os.path.exists(temp_pdf_path):
                try:
                    os.unlink(temp_pdf_path)
                except:
                    pass  # Ignore cleanup errors
        
    except Exception as e:
        return jsonify({
            'error': f'PDF generation error: {str(e)}'
        }), 500

@app.route('/api/personality/generate-html', methods=['POST'])
def generate_html():
    """
    Generate HTML dari MongoDB payload (untuk debugging)
    
    Returns:
        HTML content atau error response
    """
    try:
        # Get JSON data from request
        mongo_payload = request.get_json()
        
        if not mongo_payload:
            return jsonify({
                'error': 'No JSON payload provided'
            }), 400
        
        # Validate first
        validation_result = service.validate_mongo_payload(mongo_payload)
        if not validation_result['validation']['valid']:
            return jsonify({
                'error': 'Invalid payload',
                'validation': validation_result['validation']
            }), 400
        
        # Extract and map data
        extracted_data = service.extract_personality_data(mongo_payload)
        template_data = service.map_to_interpretation_format(extracted_data)
        
        # Render HTML
        html_content = service.render_html_template(template_data)
        
        return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        
    except Exception as e:
        return jsonify({
            'error': f'HTML generation error: {str(e)}'
        }), 500

@app.route('/api/personality/mongo-to-pdf', methods=['POST'])
def mongo_to_pdf():
    """
    Generate PDF dari MongoDB payload format asli
    Endpoint khusus untuk format MongoDB seperti yang ada di database
    
    Expected payload format:
    {
        "name": "User Name",
        "email": "user@email.com", 
        "testResult": {
            "kepribadian": {
                "formName": "Tes Kepribadian",
                "score": {
                    "open": 29,
                    "conscientious": 36,
                    "extraversion": 29,
                    "agreeable": 37,
                    "neurotic": 34
                },
                "rank": {
                    "open": "sedang",
                    "conscientious": "sedang", 
                    "extraversion": "sedang",
                    "agreeable": "tinggi",
                    "neurotic": "sedang"
                }
            }
        }
    }
    
    Returns:
        PDF file atau error response
    """
    try:
        # Get JSON data from request
        mongo_payload = request.get_json()
        
        if not mongo_payload:
            return jsonify({
                'error': 'No JSON payload provided'
            }), 400
        
        # Validate required fields
        if 'testResult' not in mongo_payload or 'kepribadian' not in mongo_payload['testResult']:
            return jsonify({
                'error': 'Invalid payload: missing testResult.kepribadian'
            }), 400
        
        kepribadian_data = mongo_payload['testResult']['kepribadian']
        
        if 'score' not in kepribadian_data:
            return jsonify({
                'error': 'Invalid payload: missing score data'
            }), 400
        
        # Convert MongoDB format to service format
        scores = kepribadian_data['score']
        ranks = kepribadian_data.get('rank', {})
        
        # Map MongoDB score keys to service keys and create aspects/recommendations
        mongo_to_service_map = {
            'open': 'keterbukaan',
            'conscientious': 'kehati_hatian', 
            'extraversion': 'ekstraversi',
            'agreeable': 'keramahan',
            'neurotic': 'neurotisisme'
        }
        
        # Create service-compatible payload
        service_payload = {
            'client': {
                'name': mongo_payload.get('name', 'Unknown User'),
                'email': mongo_payload.get('email', 'unknown@email.com')
            },
            'test_date': datetime.now().strftime('%Y-%m-%d'),
            'form': kepribadian_data.get('formName', 'Tes Kepribadian Big Five')
        }
        
        # Convert each dimension
        for mongo_key, service_key in mongo_to_service_map.items():
            if mongo_key in scores:
                score = scores[mongo_key]
                rank = ranks.get(mongo_key, 'sedang')
                
                # Generate basic aspects based on rank
                aspects = []
                if rank == 'tinggi':
                    aspects = [f"Memiliki tingkat {service_key.replace('_', ' ')} yang tinggi", 
                              "Menunjukkan karakteristik yang kuat dalam dimensi ini"]
                elif rank == 'sedang':
                    aspects = [f"Memiliki tingkat {service_key.replace('_', ' ')} yang sedang",
                              "Menunjukkan keseimbangan dalam dimensi ini"]
                else:
                    aspects = [f"Memiliki tingkat {service_key.replace('_', ' ')} yang rendah",
                              "Perlu pengembangan dalam dimensi ini"]
                
                # Generate basic recommendations
                recommendations = [
                    {"title": f"Pengembangan {service_key.replace('_', ' ').title()}", 
                     "description": f"Fokus pada peningkatan aspek {service_key.replace('_', ' ')}"}
                ]
                
                service_payload[service_key] = {
                    'skor': score,
                    'aspek': aspects,
                    'rekomendasi': recommendations
                }
        
        # Generate PDF using existing service
        pdf_bytes = service.process_mongo_payload_to_pdf(service_payload)
        
        if not pdf_bytes:
            return jsonify({
                'error': 'Failed to generate PDF'
            }), 500
        
        # Create temporary file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"personality_report_{timestamp}.pdf"
        temp_pdf_path = os.path.join(tempfile.gettempdir(), filename)
        
        try:
            # Write PDF to temporary file
            with open(temp_pdf_path, 'wb') as f:
                f.write(pdf_bytes)
            
            # Return PDF file
            return send_file(
                temp_pdf_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
            
        finally:
            # Clean up temporary file after sending
            if os.path.exists(temp_pdf_path):
                try:
                    os.unlink(temp_pdf_path)
                except:
                    pass  # Ignore cleanup errors
        
    except Exception as e:
        return jsonify({
            'error': f'PDF generation error: {str(e)}'
        }), 500

@app.route('/api/personality/dimensions', methods=['GET'])
def get_dimensions_info():
    """
    Get informasi tentang dimensi kepribadian yang tersedia
    
    Returns:
        JSON dengan informasi dimensi
    """
    try:
        dimensions_info = {
            'openness': {
                'name': 'Keterbukaan (Openness)',
                'description': 'Keterbukaan terhadap pengalaman baru dan ide-ide kreatif'
            },
            'conscientiousness': {
                'name': 'Kehati-hatian (Conscientiousness)',
                'description': 'Tingkat kedisiplinan, keteraturan, dan tanggung jawab'
            },
            'extraversion': {
                'name': 'Ekstraversi (Extraversion)',
                'description': 'Orientasi terhadap dunia luar dan interaksi sosial'
            },
            'agreeableness': {
                'name': 'Keramahan (Agreeableness)',
                'description': 'Kecenderungan untuk kooperatif dan percaya pada orang lain'
            },
            'neuroticism': {
                'name': 'Neurotisisme (Neuroticism)',
                'description': 'Tingkat stabilitas emosional dan ketahanan terhadap stres'
            }
        }
        
        return jsonify({
            'success': True,
            'dimensions': dimensions_info,
            'total_dimensions': len(dimensions_info)
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting dimensions info: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            '/api/personality/health',
            '/api/personality/validate',
            '/api/personality/preview',
            '/api/personality/generate-pdf',
            '/api/personality/generate-html',
            '/api/personality/mongo-to-pdf',
            '/api/personality/dimensions'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500

if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5001)