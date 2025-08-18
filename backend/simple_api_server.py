#!/usr/bin/env python3
"""
Simple API Server for MongoDB to PDF Testing
Flask server sederhana tanpa dependency yang tidak perlu
"""

import os
import sys
import json
import tempfile
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from flask import Flask, request, jsonify, send_file
    from flask_cors import CORS
except ImportError:
    print("❌ Flask or flask_cors not installed")
    print("Run: pip install flask flask_cors")
    sys.exit(1)

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    print("❌ WeasyPrint not installed (PDF features will be disabled)")
    print("Run: pip install weasyprint")
    HTML = None
    WEASYPRINT_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
    print("✅ PyPDF2 available for PDF merging")
except ImportError:
    print("❌ PyPDF2 not installed (PDF merging features will be disabled)")
    print("Run: pip install PyPDF2")
    PyPDF2 = None
    PYPDF2_AVAILABLE = False

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=['http://localhost:3000'], supports_credentials=True)

# MongoDB Configuration
MONGO_CONNECTION_STRING = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGO_WORKFLOW_DATABASE = "workflow"
MONGO_MINDFRAME_DATABASE = "mindframe"
MONGO_TEST_COLLECTION = "psikotes_v2"  # For test data in workflow database
MONGO_INTERPRETATION_COLLECTION = "interpretations"  # For interpretation data in mindframe database
MONGO_PRODUCT_CONFIG_COLLECTION = "product_configs"  # For product configurations in mindframe database

# Initialize MongoDB client
try:
    mongo_client = MongoClient(MONGO_CONNECTION_STRING)
    mongo_workflow_db = mongo_client[MONGO_WORKFLOW_DATABASE]
    mongo_mindframe_db = mongo_client[MONGO_MINDFRAME_DATABASE]
    mongo_collection = mongo_workflow_db[MONGO_TEST_COLLECTION]  # Test data from workflow/psikotes_v2
    mongo_interpretation_collection = mongo_mindframe_db[MONGO_INTERPRETATION_COLLECTION]  # Interpretations from mindframe/interpretations
    mongo_product_config_collection = mongo_mindframe_db[MONGO_PRODUCT_CONFIG_COLLECTION]  # Product configs from mindframe/product_configs
    
    # Test the connection
    mongo_client.admin.command('ping')
    print("✅ MongoDB connection established")
    
    # Test collection access
    test_count = mongo_collection.count_documents({})
    interpretation_count = mongo_interpretation_collection.count_documents({})
    product_config_count = mongo_product_config_collection.count_documents({})
    print(f"📊 Found {test_count} documents in {MONGO_WORKFLOW_DATABASE}/{MONGO_TEST_COLLECTION} collection")
    print(f"📊 Found {interpretation_count} documents in {MONGO_MINDFRAME_DATABASE}/{MONGO_INTERPRETATION_COLLECTION} collection")
    print(f"📊 Found {product_config_count} documents in {MONGO_MINDFRAME_DATABASE}/{MONGO_PRODUCT_CONFIG_COLLECTION} collection")
    
    # Debug: List all product configs with detailed logging
    print("🔍 Querying product configs...")
    all_product_configs = list(mongo_product_config_collection.find({}, {'productId': 1, 'isActive': 1}))
    print(f"🔍 Raw query result: {all_product_configs}")
    print(f"🔍 Number of configs found: {len(all_product_configs)}")
    
    # Also try a different query to see if there's a filter issue
    all_configs_no_filter = list(mongo_product_config_collection.find({}))
    print(f"🔍 All configs (no filter): {len(all_configs_no_filter)} documents")
    for config in all_configs_no_filter:
        print(f"   - {config.get('productId', 'NO_PRODUCT_ID')}: {config.get('isActive', 'NO_ACTIVE_STATUS')} (ObjectId: {config.get('_id', 'NO_ID')})")
    
    print(f"🔍 Available product configs: {all_product_configs}")
    
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    mongo_client = None
    mongo_workflow_db = None
    mongo_mindframe_db = None
    mongo_collection = None
    mongo_interpretation_collection = None
    mongo_product_config_collection = None

# Load interpretation data and template
def load_interpretation_data_from_mongo(test_name=None):
    """
    Load interpretation data from MongoDB based on testName
    """
    try:
        if mongo_interpretation_collection is None:
            print("❌ MongoDB interpretation collection not available")
            return None
            
        # If no test_name provided, default to 'kepribadian'
        if test_name is None:
            test_name = "kepribadian"
            
        # Find the interpretation document for the specified test
        interpretation_doc = mongo_interpretation_collection.find_one({"testName": test_name})
        
        if not interpretation_doc:
            print(f"❌ No interpretation data found for '{test_name}' test in MongoDB")
            return None
            
        # Remove MongoDB-specific fields
        if '_id' in interpretation_doc:
            del interpretation_doc['_id']
            
        print(f"✅ Interpretation data loaded from MongoDB for '{test_name}' test")
        return interpretation_doc
        
    except Exception as e:
        print(f"❌ Error loading interpretation data from MongoDB: {e}")
        return None

def load_resources():
    """Load interpretation data from MongoDB and setup Jinja2 environment"""
    try:
        # Load interpretation data from MongoDB
        interpretation_data = load_interpretation_data_from_mongo()
        
        if not interpretation_data:
            print("❌ Failed to load interpretation data from MongoDB")
            return None, None
        
        # Setup Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
        return interpretation_data, jinja_env
        
    except Exception as e:
        print(f"❌ Error loading resources: {e}")
        return None, None

# Load resources at startup
interpretation_data, jinja_env = load_resources()

if not interpretation_data or not jinja_env:
    print("❌ Failed to load required resources")
    sys.exit(1)

# Root path handler to prevent CORS errors
@app.route('/', methods=['GET', 'OPTIONS'])
def root():
    """Root endpoint with CORS support"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    response_data = {
        'message': 'MongoDB to PDF API Server',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'generate_report': '/api/generate-report',
            'interpretations': '/api/interpretations',
            'routes': '/api/routes'
        }
    }
    
    response = jsonify(response_data)
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'MongoDB to PDF API'
    })

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """
    Generate PDF report from MongoDB data using code and template
    Payload: { "code": "jmCGjMOStFLa9nPz", "template": "kepribadian" }
    """
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        if 'code' not in data or 'template' not in data:
            return jsonify({'error': 'Missing required fields: code and template'}), 400
        
        code = data['code']
        template_type = data['template']
        
        print(f"📥 Received request for code: {code}, template: {template_type}")
        
        # Check MongoDB connection
        if mongo_collection is None:
            return jsonify({'error': 'MongoDB connection not available'}), 500
        
        # Query MongoDB for data
        try:
            print(f"🔍 Querying MongoDB for code: {code}")
            mongo_data = mongo_collection.find_one({'code': code})
            print(f"🔍 Query result: {mongo_data}")
            if not mongo_data:
                print(f"❌ No data found for code: {code}")
                return jsonify({'error': f'No data found for code: {code}'}), 404
            
            print(f"📊 Found data for: {mongo_data.get('name', 'Unknown')}")
        except Exception as e:
            print(f"❌ Database query error: {str(e)}")
            return jsonify({'error': f'Database query failed: {str(e)}'}), 500
        
        # Route to appropriate template handler
        if template_type == 'kepribadian':
            return process_personality_template(mongo_data)
        elif template_type == 'personal_values':
            return process_personal_values_template(mongo_data)
        elif template_type == 'motivationBoost':
            return process_motivation_boost_template(mongo_data)
        elif template_type == 'petaPerilaku':
            return process_peta_perilaku_template(mongo_data)
        else:
            return jsonify({'error': f'Unknown template type: {template_type}'}), 400
            
    except Exception as e:
        print(f"❌ Error in generate_report: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/generate-product-report', methods=['POST'])
def generate_product_report():
    """
    Generate combined PDF report for a product (e.g., minatBakatUmum)
    Expected payload: {"code": "rb5YrWGWJXOHoj6r", "product": "minatBakatUmum"}
    """
    try:
        if not mongo_client:
            return jsonify({'error': 'MongoDB connection not available'}), 500
            
        if not WEASYPRINT_AVAILABLE:
            return jsonify({'error': 'PDF generation not available (WeasyPrint not installed)'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        code = data.get('code')
        product_id = data.get('product')
        
        if not code or not product_id:
            return jsonify({'error': 'Both "code" and "product" are required'}), 400
        
        # Get product configuration
        print(f"🔍 Looking for product config: productId='{product_id}', isActive=True")
        product_config = mongo_product_config_collection.find_one({'productId': product_id, 'isActive': True})
        print(f"📋 Product config found: {product_config is not None}")
        if product_config:
            print(f"✅ Product config details: {product_config.get('productId', 'N/A')}")
        else:
            # Debug: Check what product configs exist
            all_configs = list(mongo_product_config_collection.find({}, {'productId': 1, 'isActive': 1}))
            print(f"🔍 Available product configs: {all_configs}")
            return jsonify({'error': f'Product configuration not found: {product_id}'}), 404
        
        # Get test results from workflow database
        test_data = mongo_collection.find_one({'code': code})
        if not test_data:
            return jsonify({'error': f'Test data not found for code: {code}'}), 404
        
        # Validate that all required tests are completed
        test_results = test_data.get('testResult', {})
        missing_tests = []
        for test_config in product_config['tests']:
            if test_config['required'] and test_config['testType'] not in test_results:
                missing_tests.append(test_config['testType'])
        
        if missing_tests:
            return jsonify({
                'error': f'Missing required test results: {", ".join(missing_tests)}'
            }), 400
        
        # Generate combined PDF
        result = generate_combined_pdf(test_data, product_config)
        
        if result['success']:
            return send_file(
                result['file_path'],
                as_attachment=True,
                download_name=result['filename'],
                mimetype='application/pdf'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        print(f"❌ Error in generate_product_report: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/merge-pdfs', methods=['POST'])
def merge_pdfs():
    """
    Merge multiple existing PDF files into a single combined PDF
    Payload: {
        "pdf_files": ["file1.pdf", "file2.pdf", "file3.pdf"],
        "output_filename": "combined_report.pdf" (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        pdf_files = data.get('pdf_files', [])
        output_filename = data.get('output_filename')
        
        if not pdf_files or len(pdf_files) < 2:
            return jsonify({
                'success': False,
                'error': 'At least 2 PDF files are required for merging'
            }), 400
        
        # Convert relative filenames to full paths
        results_dir = os.path.join(os.path.dirname(__file__), 'generated_results')
        pdf_file_paths = []
        
        for pdf_file in pdf_files:
            # Handle both full paths and relative filenames
            if os.path.isabs(pdf_file):
                pdf_file_paths.append(pdf_file)
            else:
                pdf_file_paths.append(os.path.join(results_dir, pdf_file))
        
        # Merge PDFs
        result = merge_existing_pdfs(pdf_file_paths, output_filename)
        
        if result['success']:
            return send_file(
                result['file_path'],
                as_attachment=True,
                download_name=result['filename'],
                mimetype='application/pdf'
            )
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def generate_combined_pdf(test_data, product_config):
    """
    Generate a combined PDF by merging individual PDFs based on product configuration
    Uses PyPDF2 to merge individual test PDFs into a single document
    """
    try:
        # Create results directory if it doesn't exist
        results_dir = '/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/generated_results'
        os.makedirs(results_dir, exist_ok=True)
        
        # Generate filename for final combined PDF
        user_name = test_data.get('name', 'User')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{product_config['productId']}_{user_name}_{timestamp}.pdf"
        file_path = os.path.join(results_dir, filename)
        
        # Sort tests by order
        sorted_tests = sorted(product_config['tests'], key=lambda x: x['order'])
        
        # Generate individual PDFs and collect their paths
        individual_pdf_paths = []
        test_results = test_data.get('testResult', {})
        
        print(f"🔄 Starting PDF merging pipeline for {len(sorted_tests)} tests...")
        
        # Generate cover page PDF
        cover_pdf_path = generate_cover_page_pdf(test_data, product_config, results_dir, timestamp)
        if cover_pdf_path:
            individual_pdf_paths.append(cover_pdf_path)
            print(f"✅ Cover page PDF generated: {os.path.basename(cover_pdf_path)}")
        
        # Generate introduction PDF if configured
        if 'introduction' in product_config.get('staticContent', {}):
            intro_pdf_path = generate_introduction_pdf(product_config['staticContent']['introduction'], results_dir, timestamp)
            if intro_pdf_path:
                individual_pdf_paths.append(intro_pdf_path)
                print(f"✅ Introduction PDF generated: {os.path.basename(intro_pdf_path)}")
        
        # Generate individual test PDFs
        for test_config in sorted_tests:
            test_type = test_config['testType']
            if test_type in test_results:
                # Create a mock mongo_data object for the existing template functions
                mock_mongo_data = {
                    'name': test_data.get('name', 'User'),
                    'email': test_data.get('email', ''),
                    'testResult': {test_type: test_results[test_type]}
                }
                
                # Generate individual PDF using existing process functions
                pdf_path = generate_individual_test_pdf(mock_mongo_data, test_type, results_dir, timestamp)
                if pdf_path:
                    individual_pdf_paths.append(pdf_path)
                    print(f"✅ Individual PDF generated for {test_type}: {os.path.basename(pdf_path)}")
        
        # Generate closing PDF if configured
        if 'closing' in product_config.get('staticContent', {}):
            closing_pdf_path = generate_closing_pdf(product_config['staticContent']['closing'], results_dir, timestamp)
            if closing_pdf_path:
                individual_pdf_paths.append(closing_pdf_path)
                print(f"✅ Closing PDF generated: {os.path.basename(closing_pdf_path)}")
        
        # Merge all PDFs using PyPDF2
        if not PYPDF2_AVAILABLE:
            raise Exception("PyPDF2 is not available for PDF merging")
        
        if not individual_pdf_paths:
            raise Exception("No individual PDFs were generated to merge")
        
        print(f"🔄 Merging {len(individual_pdf_paths)} PDFs into final document...")
        
        # Create PDF merger
        merger = PyPDF2.PdfMerger()
        
        # Add each PDF to the merger
        for pdf_path in individual_pdf_paths:
            if os.path.exists(pdf_path):
                merger.append(pdf_path)
                print(f"📄 Added to merger: {os.path.basename(pdf_path)}")
            else:
                print(f"⚠️ Warning: PDF file not found: {pdf_path}")
        
        # Write the merged PDF
        with open(file_path, 'wb') as output_file:
            merger.write(output_file)
        
        merger.close()
        
        # Optional: Clean up individual PDFs (comment out if you want to keep them)
        cleanup_individual_pdfs = True  # Set to False to keep individual PDFs
        if cleanup_individual_pdfs:
            for pdf_path in individual_pdf_paths:
                try:
                    if os.path.exists(pdf_path) and pdf_path != file_path:
                        os.remove(pdf_path)
                        print(f"🗑️ Cleaned up: {os.path.basename(pdf_path)}")
                except Exception as cleanup_error:
                    print(f"⚠️ Warning: Could not clean up {pdf_path}: {cleanup_error}")
        
        print(f"✅ Combined PDF successfully generated: {filename}")
        print(f"📊 Final PDF size: {os.path.getsize(file_path)} bytes")
        
        return {
            'success': True,
            'file_path': file_path,
            'filename': filename,
            'merged_pdfs_count': len(individual_pdf_paths)
        }
        
    except Exception as e:
        print(f"❌ Error generating combined PDF: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def generate_cover_page_pdf(test_data, product_config, results_dir, timestamp):
    """
    Generate a cover page PDF
    """
    try:
        cover_html = generate_cover_page(test_data, product_config)
        cover_filename = f"cover_{product_config['productId']}_{timestamp}.pdf"
        cover_path = os.path.join(results_dir, cover_filename)
        
        html_doc = HTML(string=cover_html)
        html_doc.write_pdf(cover_path)
        
        return cover_path
    except Exception as e:
        print(f"❌ Error generating cover page PDF: {str(e)}")
        return None

def generate_introduction_pdf(intro_config, results_dir, timestamp):
    """
    Generate an introduction PDF
    """
    try:
        intro_html = generate_introduction_section(intro_config)
        intro_filename = f"intro_{timestamp}.pdf"
        intro_path = os.path.join(results_dir, intro_filename)
        
        html_doc = HTML(string=intro_html)
        html_doc.write_pdf(intro_path)
        
        return intro_path
    except Exception as e:
        print(f"❌ Error generating introduction PDF: {str(e)}")
        return None

def generate_closing_pdf(closing_config, results_dir, timestamp):
    """
    Generate a closing PDF
    """
    try:
        closing_html = generate_closing_section(closing_config)
        closing_filename = f"closing_{timestamp}.pdf"
        closing_path = os.path.join(results_dir, closing_filename)
        
        html_doc = HTML(string=closing_html)
        html_doc.write_pdf(closing_path)
        
        return closing_path
    except Exception as e:
        print(f"❌ Error generating closing PDF: {str(e)}")
        return None

def generate_individual_test_pdf(mongo_data, test_type, results_dir, timestamp):
    """
    Generate individual test PDF and return file path
    This is specifically for the PDF merging pipeline
    """
    try:
        # Map test types to their corresponding generation functions
        generation_functions = {
            'kepribadian': generate_personality_pdf,
            'personalValues': generate_personal_values_pdf,
            'motivationBoost': generate_motivation_boost_pdf,
            'minatBakat': generate_minat_bakat_pdf,
            'petaPerilaku': generate_peta_perilaku_pdf
        }
        
        if test_type not in generation_functions:
            print(f"❌ Unknown test type: {test_type}")
            return None
        
        # Call the appropriate generation function
        generation_function = generation_functions[test_type]
        pdf_path = generation_function(mongo_data, results_dir, timestamp)
        
        return pdf_path
        
    except Exception as e:
        print(f"❌ Error generating individual test PDF for {test_type}: {str(e)}")
        return None

def generate_minat_bakat_pdf(mongo_data, results_dir, timestamp):
    """
    Generate minat bakat PDF and return file path
    """
    try:
        # Load interpretation data for 'minatBakat' template from MongoDB
        mb_interpretation_data = load_interpretation_data_from_mongo('minatBakat')
        if not mb_interpretation_data:
            print("❌ Failed to load interpretation data for minatBakat template")
            return None
        
        # Prepare template data
        template_data = {
            'client_name': mongo_data.get('name', 'Unknown'),
            'client_age': mongo_data.get('age', '25'),
            'test_date': datetime.now().strftime('%d %B %Y'),
            'report_date': datetime.now().strftime('%d %B %Y'),
            'test_name': mb_interpretation_data.get('testName', 'Minat Bakat'),
            'test_type': mb_interpretation_data.get('testType', 'Career Interest & Talent Assessment'),
            'overview': mb_interpretation_data.get('overview', 'Analisis minat dan bakat karier'),
            'dimensions': mb_interpretation_data.get('results', {}).get('dimensions', [])
        }
        
        # Load and render template
        template = jinja_env.get_template('reports/minat_bakat_report_template.html')
        html_content = template.render(**template_data)
        
        # Generate PDF
        filename = f"minat_bakat_{timestamp}.pdf"
        pdf_path = os.path.join(results_dir, filename)
        
        html_obj = HTML(string=html_content)
        html_obj.write_pdf(pdf_path)
        
        print(f"✅ Minat Bakat PDF generated: {filename}")
        return pdf_path
        
    except Exception as e:
        print(f"❌ Error generating minat bakat PDF: {str(e)}")
        return None

def generate_motivation_boost_pdf(mongo_data, results_dir, timestamp):
    """
    Generate motivation boost PDF and return file path
    """
    try:
        # Load interpretation data for 'motivationBoost' template from MongoDB
        mb_interpretation_data = load_interpretation_data_from_mongo('motivationBoost')
        if not mb_interpretation_data:
            print("❌ Failed to load interpretation data for motivationBoost template")
            return None
        
        # Prepare template data
        template_data = {
            'client_name': mongo_data.get('name', 'Unknown'),
            'test_date': datetime.now().strftime('%d %B %Y'),
            'report_date': datetime.now().strftime('%d %B %Y'),
            'test_name': mb_interpretation_data.get('testName', 'Motivation Boost'),
            'test_type': mb_interpretation_data.get('testType', 'Motivation Assessment'),
            'overview': mb_interpretation_data.get('overview', 'Analisis motivasi'),
            'dimensions': mb_interpretation_data.get('results', {}).get('dimensions', [])
        }
        
        # Load and render template
        template = jinja_env.get_template('reports/motivation_boost_report_template.html')
        html_content = template.render(**template_data)
        
        # Generate PDF
        filename = f"motivation_boost_{timestamp}.pdf"
        pdf_path = os.path.join(results_dir, filename)
        
        html_obj = HTML(string=html_content)
        html_obj.write_pdf(pdf_path)
        
        print(f"✅ Motivation Boost PDF generated: {filename}")
        return pdf_path
        
    except Exception as e:
        print(f"❌ Error generating motivation boost PDF: {str(e)}")
        return None

def generate_peta_perilaku_pdf(mongo_data, results_dir, timestamp):
    """
    Generate peta perilaku PDF and return file path
    """
    try:
        # Load interpretation data for 'petaPerilaku' template from MongoDB
        pp_interpretation_data = load_interpretation_data_from_mongo('petaPerilaku')
        if not pp_interpretation_data:
            print("❌ Failed to load interpretation data for petaPerilaku template")
            return None
        
        # Prepare template data
        template_data = {
            'client_name': mongo_data.get('name', 'Unknown'),
            'test_date': datetime.now().strftime('%d %B %Y'),
            'report_date': datetime.now().strftime('%d %B %Y'),
            'test_name': pp_interpretation_data.get('testName', 'Peta Perilaku'),
            'test_type': pp_interpretation_data.get('testType', 'Behavioral Assessment'),
            'overview': pp_interpretation_data.get('overview', 'Analisis peta perilaku'),
            'dimensions': pp_interpretation_data.get('results', {}).get('dimensions', [])
        }
        
        # Load and render template
        template = jinja_env.get_template('reports/peta_perilaku_report_template.html')
        html_content = template.render(**template_data)
        
        # Generate PDF
        filename = f"peta_perilaku_{timestamp}.pdf"
        pdf_path = os.path.join(results_dir, filename)
        
        html_obj = HTML(string=html_content)
        html_obj.write_pdf(pdf_path)
        
        print(f"✅ Peta Perilaku PDF generated: {filename}")
        return pdf_path
        
    except Exception as e:
        print(f"❌ Error generating peta perilaku PDF: {str(e)}")
        return None

# Placeholder functions for other test types
def generate_personality_pdf(mongo_data, results_dir, timestamp):
    """Generate personality PDF using the same logic as mongo_to_pdf_logic but return file path"""
    try:
        # Validate required fields in mongo_data
        if 'testResult' not in mongo_data or 'kepribadian' not in mongo_data['testResult']:
            print(f"❌ Invalid MongoDB data structure for personality template")
            return None
        
        # Load interpretation data for 'kepribadian' template
        interpretation_data = load_interpretation_data_from_mongo('kepribadian')
        if not interpretation_data:
            print(f"❌ Failed to load interpretation data for kepribadian template")
            return None
        
        # Extract personality data
        personality_data = mongo_data['testResult']['kepribadian']
        
        # Process scores and ranks
        scores = personality_data.get('score', {})
        ranks = personality_data.get('rank', {})
        
        # Determine levels and extract interpretations
        personality_scores = []
        for trait in ['open', 'conscientious', 'extraversion', 'agreeable', 'neurotic']:
            score = scores.get(trait, 0)
            rank = ranks.get(trait, 'sedang')
            
            # Find interpretation for this trait and level
            trait_interpretation = interpretation_data.get('interpretations', {}).get(trait, {})
            level_data = trait_interpretation.get(rank, {})
            
            personality_scores.append({
                'trait': trait,
                'score': score,
                'rank': rank,
                'interpretation': level_data.get('interpretation', ''),
                'recommendation': level_data.get('recommendation', '')
            })
        
        # Generate HTML using Jinja2
        template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Personality Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { text-align: center; margin-bottom: 30px; }
                .trait-section { margin-bottom: 25px; padding: 15px; border: 1px solid #ddd; }
                .trait-title { font-weight: bold; font-size: 18px; color: #333; }
                .score { color: #666; margin: 5px 0; }
                .interpretation { margin: 10px 0; line-height: 1.6; }
                .recommendation { margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-left: 4px solid #007bff; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Laporan Kepribadian</h1>
                <p>Nama: {{ name }}</p>
            </div>
            
            {% for trait_data in personality_scores %}
            <div class="trait-section">
                <div class="trait-title">{{ trait_data.trait|title }}</div>
                <div class="score">Skor: {{ trait_data.score }} ({{ trait_data.rank|title }})</div>
                <div class="interpretation">{{ trait_data.interpretation }}</div>
                {% if trait_data.recommendation %}
                <div class="recommendation">
                    <strong>Rekomendasi:</strong> {{ trait_data.recommendation }}
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </body>
        </html>
        """
        
        from jinja2 import Template
        template = Template(template_str)
        html_content = template.render(
            name=mongo_data.get('name', 'Unknown'),
            personality_scores=personality_scores
        )
        
        # Generate PDF using WeasyPrint
        pdf_filename = f"personality_{timestamp}.pdf"
        pdf_path = os.path.join(results_dir, pdf_filename)
        
        # Convert HTML to PDF
        HTML(string=html_content).write_pdf(pdf_path)
        
        print(f"✅ Generated personality PDF: {pdf_path}")
        return pdf_path
        
    except Exception as e:
        print(f"❌ Error generating personality PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def generate_personal_values_pdf(mongo_data, results_dir, timestamp):
    """Placeholder for personal values PDF generation"""
    print(f"⚠️ Personal Values PDF generation not implemented yet")
    return None

def merge_existing_pdfs(pdf_file_paths, output_filename=None):
    """
    Merge multiple existing PDF files into a single combined PDF
    """
    try:
        if not PYPDF2_AVAILABLE:
            return {
                'success': False,
                'error': 'PyPDF2 not available for PDF merging'
            }
        
        # Validate that all files exist
        for file_path in pdf_file_paths:
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': f'File not found: {file_path}'
                }
        
        # Create results directory if it doesn't exist
        results_dir = os.path.join(os.path.dirname(__file__), 'generated_results')
        os.makedirs(results_dir, exist_ok=True)
        
        # Generate output filename if not provided
        if not output_filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f'combined_report_{timestamp}.pdf'
        
        output_path = os.path.join(results_dir, output_filename)
        
        # Create PDF merger
        pdf_merger = PyPDF2.PdfMerger()
        
        # Add each PDF file to the merger
        for file_path in pdf_file_paths:
            print(f"📄 Adding PDF: {os.path.basename(file_path)}")
            with open(file_path, 'rb') as pdf_file:
                pdf_merger.append(pdf_file)
        
        # Write the merged PDF
        with open(output_path, 'wb') as output_file:
            pdf_merger.write(output_file)
        
        pdf_merger.close()
        
        # Get file size
        file_size = os.path.getsize(output_path)
        
        print(f"✅ Combined PDF created: {output_filename} ({file_size} bytes)")
        
        return {
            'success': True,
            'file_path': output_path,
            'filename': output_filename,
            'file_size': file_size,
            'merged_files': [os.path.basename(path) for path in pdf_file_paths]
        }
        
    except Exception as e:
        print(f"❌ Error merging PDFs: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def generate_cover_page(test_data, product_config):
    """
    Generate HTML for the cover page using external template
    """
    cover_config = product_config.get('staticContent', {}).get('coverPage', {})
    user_name = test_data.get('name', 'User')
    current_date = datetime.now().strftime('%d %B %Y')
    product_name = product_config.get('productName', 'Laporan Psikotes')
    
    template = jinja_env.get_template('layout/cover_page_template.html')
    html = template.render(
        cover_config=cover_config,
        user_name=user_name,
        current_date=current_date,
        product_name=product_name
    )
    return html


def generate_introduction_section(intro_config):
    """
    Generate HTML for the introduction section using external template
    """
    template = jinja_env.get_template('layout/introduction_section_template.html')
    html = template.render(intro_config=intro_config)
    return html


def generate_closing_section(closing_config):
    """
    Generate HTML for the closing section using external template
    """
    template = jinja_env.get_template('layout/closing_section_template.html')
    html = template.render(closing_config=closing_config)
    return html


def generate_test_html(mongo_data, test_type):
    """
    Generate HTML for a specific test using existing template functions
    """
    try:
        if test_type == 'kepribadian':
            result = process_personality_template(mongo_data)
        elif test_type == 'personal_values':
            result = process_personal_values_template(mongo_data)
        elif test_type == 'motivationBoost':
            result = process_motivation_boost_template(mongo_data)
        elif test_type == 'minatBakat':
            result = process_minat_bakat_template(mongo_data)
        elif test_type == 'petaPerilaku':
            result = process_peta_perilaku_template(mongo_data)
        else:
            return None
        
        # Extract HTML from the result (assuming the functions return HTML content)
        if isinstance(result, dict) and 'html_content' in result:
            return f'<div class="test-section" style="page-break-before: always;">{result["html_content"]}</div>'
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error generating HTML for test {test_type}: {str(e)}")
        return None


def combine_html_sections(html_sections, product_config):
    """
    Combine all HTML sections into a single document
    """
    css_styles = """
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        .cover-page {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 80vh;
        }
        .test-section {
            margin-bottom: 40px;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        .page-break {
            page-break-before: always;
        }
    </style>
    """
    
    html_document = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{product_config.get('productName', 'Laporan Psikotes')}</title>
        {css_styles}
    </head>
    <body>
        {''.join(html_sections)}
    </body>
    </html>
    """
    
    return html_document


def process_personality_template(mongo_data):
    """
    Process personality template with MongoDB data
    """
    try:
        # Validate required fields in mongo_data
        if 'testResult' not in mongo_data or 'kepribadian' not in mongo_data['testResult']:
            return jsonify({'error': 'Invalid MongoDB data structure for personality template'}), 400
        
        # Load interpretation data for 'kepribadian' template
        interpretation_data = load_interpretation_data_from_mongo('kepribadian')
        if not interpretation_data:
            return jsonify({'error': 'Failed to load interpretation data for kepribadian template'}), 500
        
        # Use the existing mongo_to_pdf logic with dynamic interpretation data
        return mongo_to_pdf_logic(mongo_data, interpretation_data)
        
    except Exception as e:
        print(f"❌ Error in process_personality_template: {str(e)}")
        return jsonify({'error': f'Template processing failed: {str(e)}'}), 500

def process_personal_values_template(mongo_data):
    """
    Process personal values template with MongoDB data
    """
    try:
        # Validate required fields in mongo_data
        if 'testResult' not in mongo_data or 'personalValues' not in mongo_data['testResult']:
            return jsonify({'error': 'Invalid MongoDB data structure for personal values template'}), 400
        
        # Extract personal values data
        personal_values_data = mongo_data['testResult']['personalValues']
        
        if 'result' not in personal_values_data or 'score' not in personal_values_data['result']:
            return jsonify({'error': 'Invalid personal values data structure'}), 400
        
        # Load interpretation data for 'personalValues' template from MongoDB
        pv_interpretation_data = load_interpretation_data_from_mongo('personalValues')
        if not pv_interpretation_data:
            return jsonify({'error': 'Failed to load interpretation data for personal_values template'}), 500
        
        # Extract scores and get top values
        scores = personal_values_data['result']['score']
        
        # Sort scores to get top values
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_n = pv_interpretation_data['results']['topN']
        top_values_data = sorted_scores[:top_n]
        
        # Map to interpretation format
        dimensions = pv_interpretation_data['results']['dimensions']
        top_values = []
        
        # Key mapping for personal values
        key_mapping = {
            'universalism': 'universalism',
            'security': 'security',
            'self_direction': 'selfDirection',
            'benevolence': 'benevolence',
            'achievement': 'achievement',
            'hedonism': 'hedonism',
            'power': 'power',
            'stimulation': 'stimulation',
            'tradition': 'tradition',
            'conformity': 'conformity'
        }
        
        for value_key, score in top_values_data:
            mapped_key = key_mapping.get(value_key, value_key)
            if mapped_key in dimensions:
                dimension = dimensions[mapped_key]
                top_values.append({
                    'key': value_key,
                    'score': score,
                    'title': dimension['title'],
                    'description': dimension['description'],
                    'manifestation': dimension['manifestation'],
                    'strengthChallenges': dimension['strengthChallenges']
                })
        
        # Prepare template data
        template_data = {
            'client_name': mongo_data.get('name', 'Unknown'),
            'client_age': '28',  # Default age, could be extracted from data if available
            'test_date': datetime.now().strftime('%d %B %Y'),
            'report_date': datetime.now().strftime('%d %B %Y'),
            'test_name': pv_interpretation_data['testName'],
            'test_type': pv_interpretation_data['testType'],
            'top_n': top_n,
            'top_values': top_values
        }
        
        # Load and render template
        template = jinja_env.get_template('reports/personal_values_report_template.html')
        html_content = template.render(**template_data)
        
        # Generate PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"personal_values_report_{mongo_data.get('name', 'unknown')}_{timestamp}.pdf"
        
        # Generate PDF using WeasyPrint
        html_obj = HTML(string=html_content)
        pdf_bytes = html_obj.write_pdf()
        
        # Save PDF to generated_results folder
        root_path = os.path.dirname(os.path.dirname(__file__))
        generated_results_path = os.path.join(root_path, 'generated_results')
        
        # Ensure generated_results directory exists
        os.makedirs(generated_results_path, exist_ok=True)
        
        pdf_path = os.path.join(generated_results_path, filename)
        
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"💾 Personal values PDF saved to generated_results: {filename}")
        
        # Create temporary file for download
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(pdf_bytes)
        temp_file.close()
        
        # Return PDF file
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"❌ Error in process_personal_values_template: {str(e)}")
        return jsonify({'error': f'Personal values template processing failed: {str(e)}'}), 500

def process_motivation_boost_template(mongo_data):
    """
    Process motivation boost template with MongoDB data
    """
    try:
        # Load interpretation data for 'motivationBoost' template from MongoDB
        mb_interpretation_data = load_interpretation_data_from_mongo('motivationBoost')
        if not mb_interpretation_data:
            return jsonify({'error': 'Failed to load interpretation data for motivationBoost template'}), 500
        
        # Prepare template data
        template_data = {
            'client_name': mongo_data.get('name', 'Unknown'),
            'client_age': '28',  # Default age
            'test_date': datetime.now().strftime('%d %B %Y'),
            'report_date': datetime.now().strftime('%d %B %Y'),
            'test_name': mb_interpretation_data.get('testName', 'Motivation Boost'),
            'test_type': mb_interpretation_data.get('testType', 'Motivation Assessment'),
            'overview': mb_interpretation_data.get('overview', 'Analisis motivasi komprehensif'),
            'dimensions': mb_interpretation_data.get('results', {}).get('dimensions', [])
        }
        
        # Load and render template
        template = jinja_env.get_template('reports/motivation_boost_report_template.html')
        html_content = template.render(**template_data)
        
        # Generate PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"motivation_boost_report_{mongo_data.get('name', 'unknown')}_{timestamp}.pdf"
        
        # Generate PDF using WeasyPrint
        html_obj = HTML(string=html_content)
        pdf_bytes = html_obj.write_pdf()
        
        # Save PDF to generated_results folder
        root_path = os.path.dirname(os.path.dirname(__file__))
        generated_results_path = os.path.join(root_path, 'generated_results')
        os.makedirs(generated_results_path, exist_ok=True)
        
        pdf_path = os.path.join(generated_results_path, filename)
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"💾 Motivation boost PDF saved to generated_results: {filename}")
        
        # Create temporary file for download
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(pdf_bytes)
        temp_file.close()
        
        # Return PDF file
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"❌ Error in process_motivation_boost_template: {str(e)}")
        return jsonify({'error': f'Motivation boost template processing failed: {str(e)}'}), 500

def process_minat_bakat_template(mongo_data):
    """
    Process minat bakat template with MongoDB data (general career interest assessment)
    """
    try:
        # Load interpretation data for 'minatBakat' template from MongoDB
        mb_interpretation_data = load_interpretation_data_from_mongo('minatBakat')
        if not mb_interpretation_data:
            return jsonify({'error': 'Failed to load interpretation data for minatBakat template'}), 500
        
        # Prepare template data
        template_data = {
            'client_name': mongo_data.get('name', 'Unknown'),
            'client_age': mongo_data.get('age', '25'),  # Default age for general assessment
            'test_date': datetime.now().strftime('%d %B %Y'),
            'report_date': datetime.now().strftime('%d %B %Y'),
            'test_name': mb_interpretation_data.get('testName', 'Minat Bakat'),
            'test_type': mb_interpretation_data.get('testType', 'Career Interest & Talent Assessment'),
            'overview': mb_interpretation_data.get('overview', 'Analisis minat dan bakat karier'),
            'dimensions': mb_interpretation_data.get('results', {}).get('dimensions', [])
        }
        
        # Load and render template
        template = jinja_env.get_template('reports/minat_bakat_report_template.html')
        html_content = template.render(**template_data)
        
        # Generate PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"minat_bakat_report_{mongo_data.get('name', 'unknown')}_{timestamp}.pdf"
        
        # Generate PDF using WeasyPrint
        html_obj = HTML(string=html_content)
        pdf_bytes = html_obj.write_pdf()
        
        # Save PDF to generated_results folder
        root_path = os.path.dirname(os.path.dirname(__file__))
        generated_results_path = os.path.join(root_path, 'generated_results')
        os.makedirs(generated_results_path, exist_ok=True)
        
        pdf_path = os.path.join(generated_results_path, filename)
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"💾 Minat bakat PDF saved to generated_results: {filename}")
        
        # Create temporary file for download
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(pdf_bytes)
        temp_file.close()
        
        # Return PDF file
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"❌ Error in process_minat_bakat_template: {str(e)}")
        return jsonify({'error': f'Minat bakat template processing failed: {str(e)}'}), 500

def process_peta_perilaku_template(mongo_data):
    """
    Process peta perilaku template with MongoDB data
    """
    try:
        # Load interpretation data for 'petaPerilaku' template from MongoDB
        pp_interpretation_data = load_interpretation_data_from_mongo('petaPerilaku')
        if not pp_interpretation_data:
            return jsonify({'error': 'Failed to load interpretation data for petaPerilaku template'}), 500
        
        # Prepare template data
        template_data = {
            'client_name': mongo_data.get('name', 'Unknown'),
            'client_age': '28',  # Default age
            'test_date': datetime.now().strftime('%d %B %Y'),
            'report_date': datetime.now().strftime('%d %B %Y'),
            'test_name': pp_interpretation_data.get('testName', 'Peta Perilaku'),
            'test_type': pp_interpretation_data.get('testType', 'Behavioral Mapping Assessment'),
            'overview': pp_interpretation_data.get('overview', 'Analisis peta perilaku dan gaya komunikasi'),
            'dimensions': pp_interpretation_data.get('results', {}).get('dimensions', [])
        }
        
        # Load and render template
        template = jinja_env.get_template('reports/peta_perilaku_report_template.html')
        html_content = template.render(**template_data)
        
        # Generate PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"peta_perilaku_report_{mongo_data.get('name', 'unknown')}_{timestamp}.pdf"
        
        # Generate PDF using WeasyPrint
        html_obj = HTML(string=html_content)
        pdf_bytes = html_obj.write_pdf()
        
        # Save PDF to generated_results folder
        root_path = os.path.dirname(os.path.dirname(__file__))
        generated_results_path = os.path.join(root_path, 'generated_results')
        os.makedirs(generated_results_path, exist_ok=True)
        
        pdf_path = os.path.join(generated_results_path, filename)
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"💾 Peta perilaku PDF saved to generated_results: {filename}")
        
        # Create temporary file for download
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(pdf_bytes)
        temp_file.close()
        
        # Return PDF file
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"❌ Error in process_peta_perilaku_template: {str(e)}")
        return jsonify({'error': f'Peta perilaku template processing failed: {str(e)}'}), 500

@app.route('/api/personality/mongo-to-pdf', methods=['POST'])
def mongo_to_pdf():
    """
    Legacy endpoint - Convert MongoDB personality data to PDF
    """
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        return mongo_to_pdf_logic(data)
        
    except Exception as e:
        print(f"❌ Error in mongo_to_pdf: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

def mongo_to_pdf_logic(data, interpretation_data_param=None):
    """
    Convert MongoDB personality data to PDF
    """
    try:
        # Use the passed data parameter instead of getting JSON again
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        print(f"📥 Received request from: {data.get('name', 'Unknown')}")
        
        # Validate required fields
        if 'testResult' not in data or 'kepribadian' not in data['testResult']:
            return jsonify({'error': 'Invalid payload structure'}), 400
        
        # Extract personality data
        personality_data = data['testResult']['kepribadian']
        scores = personality_data['score']
        ranks = personality_data['rank']
        
        # Map to standard format
        personality_mapping = {
            'openness': scores['open'],
            'conscientiousness': scores['conscientious'],
            'extraversion': scores['extraversion'],
            'agreeableness': scores['agreeable'],
            'neuroticism': scores['neurotic']
        }
        
        print(f"📊 Processing scores: {personality_mapping}")
        
        # Determine levels based on scores
        def get_level(score):
            if score <= 20:
                return 'rendah'
            elif score <= 35:
                return 'sedang'
            else:
                return 'tinggi'
        
        levels = {dim: get_level(score) for dim, score in personality_mapping.items()}
        
        # Use parameter interpretation_data_param or fallback to global interpretation_data
        current_interpretation_data = interpretation_data_param if interpretation_data_param is not None else interpretation_data
        
        # Extract interpretations from the correct JSON structure
        interpretations = {}
        recommendations = {}
        
        for dimension, level in levels.items():
            try:
                # Access the correct path in interpretation_data
                dim_data = current_interpretation_data['results']['dimensions'][dimension][level]
                interpretations[dimension] = dim_data.get('interpretation', f'Interpretasi {dimension} level {level}')
                recommendations[dimension] = dim_data.get('rekomendasi', f'Rekomendasi {dimension} level {level}')
            except (KeyError, TypeError):
                interpretations[dimension] = f'Interpretasi {dimension} level {level}'
                recommendations[dimension] = f'Rekomendasi {dimension} level {level}'
        
        # Create dimensions array for template
        dimensions = []
        dimension_names = {
            'openness': 'Keterbukaan (Openness)',
            'conscientiousness': 'Kehati-hatian (Conscientiousness)',
            'extraversion': 'Ekstraversi (Extraversion)',
            'agreeableness': 'Keramahan (Agreeableness)',
            'neuroticism': 'Neurotisisme (Neuroticism)'
        }
        
        for dim_key in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
            # Get interpretation data for this dimension and level
            dim_data = current_interpretation_data['results']['dimensions'][dim_key][levels[dim_key]]
            
            dimension = {
                'key': dim_key,
                'title': dimension_names[dim_key],
                'score': personality_mapping[dim_key],
                'level': levels[dim_key],
                'level_label': levels[dim_key].title(),
                'interpretation': interpretations[dim_key],
                'aspects': dim_data['aspekKehidupan'],
                'recommendations': dim_data['rekomendasi']
            }
            dimensions.append(dimension)
        
        # Generate overview
        overview_parts = []
        for dim in dimensions:
            overview_parts.append(f"{dim['title']}: {dim['level_label']} ({dim['score']})")
        overview = "Berdasarkan hasil tes kepribadian, profil Anda menunjukkan: " + ", ".join(overview_parts) + "."
        
        # Create template data matching the Jinja2 template structure
        template_data = {
            'client_name': data.get('name', 'Unknown'),
            'client_email': data.get('email', ''),
            'test_date': datetime.now().strftime('%d %B %Y'),
            'form_name': personality_data.get('formName', 'Tes Kepribadian'),
            'dimensions': dimensions,
            'overview': overview,
            'current_year': datetime.now().year
        }
        
        # Render HTML using Jinja2
        template = jinja_env.get_template('reports/personality_report_template.html')
        rendered_html = template.render(template_data)
        
        # Save rendered HTML for debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_debug_filename = f"debug_rendered_{timestamp}.html"
        
        # Save debug HTML to generated_results folder
        root_path = os.path.dirname(os.path.dirname(__file__))
        generated_results_path = os.path.join(root_path, 'generated_results')
        os.makedirs(generated_results_path, exist_ok=True)
        
        html_debug_path = os.path.join(generated_results_path, html_debug_filename)
        with open(html_debug_path, 'w', encoding='utf-8') as f:
            f.write(rendered_html)
        print(f"🐛 Debug HTML saved to generated_results: {html_debug_filename}")
        
        print("📄 Generating PDF...")
        
        # Generate PDF using WeasyPrint
        html_obj = HTML(string=rendered_html)
        pdf_bytes = html_obj.write_pdf()
        
        print(f"✅ PDF generated ({len(pdf_bytes):,} bytes)")
        
        # Save PDF to generated_results folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"personality_report_{data.get('name', 'unknown')}_{timestamp}.pdf"
        
        # Save to generated_results folder (in project root)
        root_path = os.path.dirname(os.path.dirname(__file__))
        generated_results_path = os.path.join(root_path, 'generated_results')
        
        # Ensure generated_results directory exists
        os.makedirs(generated_results_path, exist_ok=True)
        
        pdf_path = os.path.join(generated_results_path, pdf_filename)
        
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"💾 PDF saved to generated_results: {pdf_filename}")
        
        # Create temporary file for download
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(pdf_bytes)
        temp_file.close()
        
        # Return PDF as download
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=pdf_filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"❌ Error processing request: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== INTERPRETATIONS CRUD ENDPOINTS ====================

@app.route('/api/interpretations', methods=['GET', 'OPTIONS'])
def get_interpretations():
    """Get all interpretations"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        if mongo_interpretation_collection is None:
            return jsonify({'error': 'Database connection not available'}), 500
        
        # Get query parameters
        test_name = request.args.get('testName')
        
        # Build query
        query = {}
        if test_name:
            query['testName'] = test_name
        
        # Get interpretations
        interpretations = list(mongo_interpretation_collection.find(query))
        
        # Convert ObjectId to string
        for interpretation in interpretations:
            interpretation['_id'] = str(interpretation['_id'])
        
        response_data = {
            'success': True,
            'interpretations': interpretations,
            'total': len(interpretations)
        }
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    except Exception as e:
        print(f"❌ Error getting interpretations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/interpretations/<interpretation_id>', methods=['GET', 'OPTIONS'])
def get_interpretation_by_id(interpretation_id):
    """Get interpretation by ID"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        if mongo_interpretation_collection is None:
            return jsonify({'error': 'Database connection not available'}), 500
        
        # Find interpretation
        interpretation = mongo_interpretation_collection.find_one({'_id': ObjectId(interpretation_id)})
        
        if not interpretation:
            return jsonify({'error': 'Interpretation not found'}), 404
        
        # Convert ObjectId to string
        interpretation['_id'] = str(interpretation['_id'])
        
        response_data = {
            'success': True,
            'interpretation': interpretation
        }
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    except Exception as e:
        print(f"❌ Error getting interpretation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/interpretations/test/<test_name>', methods=['GET', 'OPTIONS'])
def get_interpretation_by_test_name(test_name):
    """Get interpretation by test name"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        if mongo_interpretation_collection is None:
            return jsonify({'error': 'Database connection not available'}), 500
        
        # Find interpretation by test name
        interpretation = mongo_interpretation_collection.find_one({'testName': test_name})
        
        if not interpretation:
            return jsonify({'error': 'Interpretation not found'}), 404
        
        # Convert ObjectId to string
        interpretation['_id'] = str(interpretation['_id'])
        
        response_data = {
            'success': True,
            'interpretation': interpretation
        }
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    except Exception as e:
        print(f"❌ Error getting interpretation by test name: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/interpretations', methods=['POST', 'OPTIONS'])
def create_interpretation():
    """Create new interpretation"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        if mongo_interpretation_collection is None:
            return jsonify({'error': 'Database connection not available'}), 500
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if 'testName' not in data:
            return jsonify({'error': 'testName is required'}), 400
        
        # Check for dimensions in different possible locations
        dimensions = None
        if 'dimensions' in data:
            dimensions = data['dimensions']
        elif 'results' in data and 'dimensions' in data['results']:
            dimensions = data['results']['dimensions']
            # Move dimensions to root level for consistency
            data['dimensions'] = dimensions
        
        if not dimensions:
            return jsonify({'error': 'dimensions is required'}), 400
        
        # Add timestamps and default values
        data['createdAt'] = datetime.utcnow()
        data['updatedAt'] = datetime.utcnow()
        
        # Set default isActive to True if not provided
        if 'isActive' not in data:
            data['isActive'] = True
        
        # Insert interpretation
        result = mongo_interpretation_collection.insert_one(data)
        
        # Get the created interpretation
        created_interpretation = mongo_interpretation_collection.find_one({'_id': result.inserted_id})
        created_interpretation['_id'] = str(created_interpretation['_id'])
        
        response_data = {
            'success': True,
            'interpretation': created_interpretation,
            'message': 'Interpretation created successfully'
        }
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.status_code = 201
        return response
    
    except Exception as e:
        print(f"❌ Error creating interpretation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/interpretations/<interpretation_id>', methods=['PUT', 'OPTIONS'])
def update_interpretation(interpretation_id):
    """Update interpretation"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'PUT,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        if mongo_interpretation_collection is None:
            return jsonify({'error': 'Database connection not available'}), 500
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Add update timestamp
        data['updatedAt'] = datetime.utcnow()
        
        # Update interpretation
        result = mongo_interpretation_collection.update_one(
            {'_id': ObjectId(interpretation_id)},
            {'$set': data}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Interpretation not found'}), 404
        
        # Get the updated interpretation
        updated_interpretation = mongo_interpretation_collection.find_one({'_id': ObjectId(interpretation_id)})
        updated_interpretation['_id'] = str(updated_interpretation['_id'])
        
        response_data = {
            'success': True,
            'interpretation': updated_interpretation,
            'message': 'Interpretation updated successfully'
        }
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    except Exception as e:
        print(f"❌ Error updating interpretation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/interpretations/<interpretation_id>', methods=['DELETE', 'OPTIONS'])
def delete_interpretation(interpretation_id):
    """Delete interpretation"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        if mongo_interpretation_collection is None:
            return jsonify({'error': 'Database connection not available'}), 500
        
        # Delete interpretation
        result = mongo_interpretation_collection.delete_one({'_id': ObjectId(interpretation_id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Interpretation not found'}), 404
        
        response_data = {
            'success': True,
            'message': 'Interpretation deleted successfully'
        }
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    except Exception as e:
        print(f"❌ Error deleting interpretation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/interpretations/<interpretation_id>/duplicate', methods=['POST', 'OPTIONS'])
def duplicate_interpretation(interpretation_id):
    """Duplicate interpretation"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        if mongo_interpretation_collection is None:
            return jsonify({'error': 'Database connection not available'}), 500
        
        data = request.get_json()
        
        if not data or 'testName' not in data:
            return jsonify({'error': 'testName is required'}), 400
        
        # Find original interpretation
        original = mongo_interpretation_collection.find_one({'_id': ObjectId(interpretation_id)})
        
        if not original:
            return jsonify({'error': 'Interpretation not found'}), 404
        
        # Create duplicate
        duplicate_data = original.copy()
        del duplicate_data['_id']  # Remove original ID
        
        # Use the provided test name
        duplicate_data['testName'] = data['testName']
        duplicate_data['createdAt'] = datetime.utcnow()
        duplicate_data['updatedAt'] = datetime.utcnow()
        
        # Insert duplicate
        result = mongo_interpretation_collection.insert_one(duplicate_data)
        
        # Get the created duplicate
        created_duplicate = mongo_interpretation_collection.find_one({'_id': result.inserted_id})
        created_duplicate['_id'] = str(created_duplicate['_id'])
        
        response = jsonify({
            'success': True,
            'interpretation': created_duplicate,
            'message': 'Interpretation duplicated successfully'
        })
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response, 201
    
    except Exception as e:
        print(f"❌ Error duplicating interpretation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    """Simple login endpoint for testing"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # Simple validation - in production, use proper authentication
        if email and password:
            # Mock successful login - return format expected by frontend
            return jsonify({
                'user': {
                    'id': '1',
                    'email': email,
                    'firstName': 'Test',
                    'lastName': 'User',
                    'role': 'user',
                    'isActive': True,
                    'isEmailVerified': True,
                    'createdAt': '2024-01-01T00:00:00Z',
                    'updatedAt': '2024-01-01T00:00:00Z'
                },
                'token': 'mock-jwt-token',
                'refreshToken': 'mock-refresh-token',
                'expiresIn': 3600
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/auth/logout', methods=['POST', 'OPTIONS'])
def logout():
    """Simple logout endpoint"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    return jsonify({
        'success': True,
        'message': 'Logout successful'
    }), 200

@app.route('/api/auth/profile', methods=['GET', 'OPTIONS'])
def get_profile():
    """Handle profile requests"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    try:
        # Mock profile data
        return jsonify({
            'id': '1',
            'email': 'user@example.com',
            'firstName': 'John',
            'lastName': 'Doe',
            'role': 'user',
            'isActive': True,
            'isEmailVerified': True,
            'createdAt': '2024-01-01T00:00:00Z',
            'updatedAt': '2024-01-01T00:00:00Z'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Templates endpoints for dashboard
@app.route('/api/templates', methods=['GET', 'OPTIONS'])
def get_templates():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    # Mock templates data - structure matches TemplateSearchResult
    templates_data = {
        'templates': [],
        'total': 0,
        'page': 1,
        'limit': 10,
        'hasMore': False
    }
    
    response = jsonify(templates_data)
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/api/templates/recent', methods=['GET', 'OPTIONS'])
def get_recent_templates():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    # Mock recent templates data - return array directly as expected by frontend
    recent_templates_data = []
    
    response = jsonify(recent_templates_data)
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Reports endpoints for dashboard
@app.route('/api/reports', methods=['GET', 'OPTIONS'])
def get_reports():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    # Mock reports data - structure matches ReportSearchResult
    reports_data = {
        'reports': [],
        'total': 0,
        'page': 1,
        'limit': 10,
        'hasMore': False
    }
    
    response = jsonify(reports_data)
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/api/reports/recent', methods=['GET', 'OPTIONS'])
def get_recent_reports():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    # Mock recent reports data - return array directly as expected by frontend
    recent_reports_data = []
    
    response = jsonify(recent_reports_data)
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/api/reports/status/<status>', methods=['GET', 'OPTIONS'])
def get_reports_by_status(status):
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    
    # Mock data for different statuses
    mock_reports = {
        "processing": [],
        "completed": [
            {
                "id": "report_001",
                "name": "Personality Assessment Report",
                "status": "completed",
                "created_at": "2024-01-15T10:30:00Z",
                "template_type": "kepribadian"
            }
        ],
        "failed": []
    }
    
    # Return array directly for getReportsByStatus as expected by frontend
    reports_data = mock_reports.get(status, [])
    
    response = jsonify(reports_data)
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/api/routes', methods=['GET'])
def list_routes():
    """
    List available API routes
    """
    routes = [
        {'method': 'GET', 'endpoint': '/health', 'description': 'Health check'},
        {'method': 'POST', 'endpoint': '/api/personality/mongo-to-pdf', 'description': 'Convert MongoDB personality data to PDF'},
        {'method': 'POST', 'endpoint': '/api/auth/login', 'description': 'User login'},
        {'method': 'POST', 'endpoint': '/api/auth/logout', 'description': 'User logout'},
        {'method': 'GET', 'endpoint': '/api/routes', 'description': 'List available routes'}
    ]
    return jsonify({'routes': routes})


# Product Configuration API Endpoints (Admin Only)
@app.route('/api/admin/product-configs', methods=['GET'])
def get_product_configs():
    """
    Get all product configurations (Admin only)
    """
    try:
        if mongo_product_config_collection is None:
            return jsonify({'error': 'Database connection not available'}), 500
        
        # Get all product configurations
        configs = list(mongo_product_config_collection.find({}))
        
        # Convert MongoDB documents to frontend format
        formatted_configs = []
        for config in configs:
            formatted_config = {
                '_id': str(config.get('_id', '')),
                'productName': config.get('productId', ''),  # Map productId to productName
                'displayName': config.get('productName', ''),  # Map productName to displayName
                'description': config.get('description', ''),
                'testCombinations': [],
                'staticContent': config.get('staticContent', {
                    'introduction': '',
                    'conclusion': '',
                    'coverPageTitle': '',
                    'coverPageSubtitle': ''
                }),
                'isActive': config.get('isActive', True),
                'createdAt': config.get('createdAt', ''),
                'updatedAt': config.get('updatedAt', '')
            }
            
            # Convert tests to testCombinations format
            if 'tests' in config:
                for test in config['tests']:
                    formatted_config['testCombinations'].append({
                        'testName': test.get('testType', ''),
                        'order': test.get('order', 0),
                        'isRequired': test.get('required', True),
                        'displayName': test.get('testType', '').replace('_', ' ').title()
                    })
            
            formatted_configs.append(formatted_config)
        
        return jsonify(formatted_configs), 200
        
    except Exception as e:
        print(f"❌ Error fetching product configs: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/admin/product-configs', methods=['POST'])
def create_product_config():
    """
    Create a new product configuration (Admin only)
    """
    try:
        if mongo_product_config_collection is None:
            return jsonify({'error': 'Database connection not available'}), 500
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['productName', 'displayName', 'testCombinations']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate testCombinations structure
        if not isinstance(data['testCombinations'], list) or len(data['testCombinations']) == 0:
            return jsonify({'error': 'testCombinations must be a non-empty array'}), 400
        
        for test in data['testCombinations']:
            if not all(key in test for key in ['testName', 'order', 'isRequired']):
                return jsonify({'error': 'Each test must have testName, order, and isRequired fields'}), 400
        
        # Check if productName already exists
        existing_config = mongo_product_config_collection.find_one({'productId': data['productName']})
        if existing_config:
            return jsonify({'error': 'Product name already exists'}), 409
        
        # Convert frontend format to backend format
        backend_data = {
            'productId': data['productName'],  # Map productName to productId
            'productName': data['displayName'],  # Map displayName to productName
            'description': data.get('description', ''),
            'tests': [],
            'staticContent': data.get('staticContent', {
                'introduction': '',
                'conclusion': '',
                'coverPageTitle': '',
                'coverPageSubtitle': ''
            }),
            'isActive': True,
            'createdAt': datetime.now(),
            'updatedAt': datetime.now()
        }
        
        # Convert testCombinations to tests format
        for test in data['testCombinations']:
            backend_data['tests'].append({
                'testType': test['testName'],
                'order': test['order'],
                'required': test['isRequired']
            })
        
        # Insert the configuration
        result = mongo_product_config_collection.insert_one(backend_data)
        
        print(f"✅ Product config created: {data['productName']}")
        
        # Return the created config in frontend format
        created_config = {
            '_id': str(result.inserted_id),
            'productName': data['productName'],
            'displayName': data['displayName'],
            'description': data.get('description', ''),
            'testCombinations': data['testCombinations'],
            'staticContent': data.get('staticContent', {}),
            'isActive': True,
            'createdAt': backend_data['createdAt'].isoformat(),
            'updatedAt': backend_data['updatedAt'].isoformat()
        }
        
        return jsonify(created_config), 201
        
    except Exception as e:
        print(f"❌ Error creating product config: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/admin/product-configs/<product_id>', methods=['PUT'])
def update_product_config(product_id):
    """
    Update an existing product configuration (Admin only)
    """
    try:
        if mongo_product_config_collection is None:
            return jsonify({'error': 'Database connection not available'}), 500
        
        data = request.get_json()
        
        # Check if product exists by _id
        from bson import ObjectId
        try:
            existing_config = mongo_product_config_collection.find_one({'_id': ObjectId(product_id)})
        except:
            return jsonify({'error': 'Invalid product ID format'}), 400
            
        if not existing_config:
            return jsonify({'error': 'Product configuration not found'}), 404
        
        # Validate testCombinations structure if provided
        if 'testCombinations' in data:
            if not isinstance(data['testCombinations'], list) or len(data['testCombinations']) == 0:
                return jsonify({'error': 'testCombinations must be a non-empty array'}), 400
            
            for test in data['testCombinations']:
                if not all(key in test for key in ['testName', 'order', 'isRequired']):
                    return jsonify({'error': 'Each test must have testName, order, and isRequired fields'}), 400
        
        # Convert frontend format to backend format
        backend_update = {
            'updatedAt': datetime.now()
        }
        
        if 'productName' in data:
            backend_update['productId'] = data['productName']
        if 'displayName' in data:
            backend_update['productName'] = data['displayName']
        if 'description' in data:
            backend_update['description'] = data['description']
        if 'staticContent' in data:
            backend_update['staticContent'] = data['staticContent']
        if 'isActive' in data:
            backend_update['isActive'] = data['isActive']
        
        # Convert testCombinations to tests format
        if 'testCombinations' in data:
            backend_update['tests'] = []
            for test in data['testCombinations']:
                backend_update['tests'].append({
                    'testType': test['testName'],
                    'order': test['order'],
                    'required': test['isRequired']
                })
        
        # Update the configuration
        result = mongo_product_config_collection.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': backend_update}
        )
        
        if result.modified_count > 0 or result.matched_count > 0:
            # Get the updated config and return in frontend format
            updated_config = mongo_product_config_collection.find_one({'_id': ObjectId(product_id)})
            
            formatted_config = {
                '_id': str(updated_config['_id']),
                'productName': updated_config.get('productId', ''),
                'displayName': updated_config.get('productName', ''),
                'description': updated_config.get('description', ''),
                'testCombinations': [],
                'staticContent': updated_config.get('staticContent', {}),
                'isActive': updated_config.get('isActive', True),
                'createdAt': updated_config.get('createdAt', ''),
                'updatedAt': updated_config.get('updatedAt', '')
            }
            
            # Convert tests to testCombinations format
            if 'tests' in updated_config:
                for test in updated_config['tests']:
                    formatted_config['testCombinations'].append({
                        'testName': test.get('testType', ''),
                        'order': test.get('order', 0),
                        'isRequired': test.get('required', True),
                        'displayName': test.get('testType', '').replace('_', ' ').title()
                    })
            
            print(f"✅ Product config updated: {product_id}")
            return jsonify(formatted_config), 200
        else:
            return jsonify({'error': 'Failed to update product configuration'}), 500
        
    except Exception as e:
        print(f"❌ Error updating product config: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/admin/product-configs/<product_id>', methods=['DELETE'])
def delete_product_config(product_id):
    """
    Delete a product configuration (Admin only)
    """
    try:
        if mongo_product_config_collection is None:
            return jsonify({'error': 'Database connection not available'}), 500
        
        # Check if product exists by _id
        from bson import ObjectId
        try:
            existing_config = mongo_product_config_collection.find_one({'_id': ObjectId(product_id)})
        except:
            return jsonify({'error': 'Invalid product ID format'}), 400
            
        if not existing_config:
            return jsonify({'error': 'Product configuration not found'}), 404
        
        # Delete the configuration
        result = mongo_product_config_collection.delete_one({'_id': ObjectId(product_id)})
        
        if result.deleted_count > 0:
            print(f"✅ Product config deleted: {product_id}")
            return jsonify({
                'success': True,
                'message': 'Product configuration deleted successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to delete product configuration'}), 500
        
    except Exception as e:
        print(f"❌ Error deleting product config: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/admin/available-tests', methods=['GET'])
def get_available_tests():
    """
    Get list of available test types from mindframe.interpretations collection
    """
    try:
        if mongo_interpretation_collection is None:
            return jsonify({'error': 'Database connection not available'}), 500
        
        # Get unique test names from interpretations collection
        pipeline = [
            {
                '$group': {
                    '_id': '$testName',
                    'displayName': {'$first': '$displayName'},
                    'description': {'$first': '$description'}
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'testName': '$_id',
                    'displayName': {'$ifNull': ['$displayName', '$_id']},
                    'description': {'$ifNull': ['$description', '']}
                }
            },
            {
                '$sort': {'testName': 1}
            }
        ]
        
        available_tests = list(mongo_interpretation_collection.aggregate(pipeline))
        
        print(f"✅ Found {len(available_tests)} available tests from interpretations collection")
        
        return jsonify(available_tests), 200
        
    except Exception as e:
        print(f"❌ Error getting available tests: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/admin/product-configs/<product_id>/toggle', methods=['PATCH'])
def toggle_product_config(product_id):
    """
    Toggle the active status of a product configuration
    """
    try:
        if mongo_product_config_collection is None:
            return jsonify({'error': 'Database connection not available'}), 500
        
        # Check if product exists by _id
        from bson import ObjectId
        try:
            existing_config = mongo_product_config_collection.find_one({'_id': ObjectId(product_id)})
        except:
            return jsonify({'error': 'Invalid product ID format'}), 400
            
        if not existing_config:
            return jsonify({'error': 'Product configuration not found'}), 404
        
        # Toggle the isActive status
        current_status = existing_config.get('isActive', True)
        new_status = not current_status
        
        # Update the configuration
        result = mongo_product_config_collection.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': {'isActive': new_status, 'updatedAt': datetime.now()}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Product config toggled: {product_id} -> {new_status}")
            return jsonify({
                'success': True,
                'isActive': new_status,
                'message': f'Product configuration {"activated" if new_status else "deactivated"} successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to toggle product configuration'}), 500
        
    except Exception as e:
        print(f"❌ Error toggling product config: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/admin/product-configs/<product_id>', methods=['GET'])
def get_product_config_by_id(product_id):
    """
    Get a specific product configuration by ID (Admin only)
    """
    try:
        if mongo_product_config_collection is None:
            return jsonify({'error': 'Database connection not available'}), 500
        
        # Find the product configuration by _id
        from bson import ObjectId
        try:
            config = mongo_product_config_collection.find_one({'_id': ObjectId(product_id)})
        except:
            return jsonify({'error': 'Invalid product ID format'}), 400
        
        if not config:
            return jsonify({'error': 'Product configuration not found'}), 404
        
        # Convert to frontend format
        formatted_config = {
            '_id': str(config['_id']),
            'productName': config.get('productId', ''),
            'displayName': config.get('productName', ''),
            'description': config.get('description', ''),
            'testCombinations': [],
            'staticContent': config.get('staticContent', {}),
            'isActive': config.get('isActive', True),
            'createdAt': config.get('createdAt', ''),
            'updatedAt': config.get('updatedAt', '')
        }
        
        # Convert tests to testCombinations format
        if 'tests' in config:
            for test in config['tests']:
                formatted_config['testCombinations'].append({
                    'testName': test.get('testType', ''),
                    'order': test.get('order', 0),
                    'isRequired': test.get('required', True),
                    'displayName': test.get('testType', '').replace('_', ' ').title()
                })
        
        print(f"✅ Product config retrieved: {product_id}")
        return jsonify(formatted_config), 200
        
    except Exception as e:
        print(f"❌ Error getting product config: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/product-configs/<product_id>', methods=['GET'])
def get_product_config(product_id):
    """
    Get a specific product configuration by productId (for public use)
    """
    try:
        if mongo_product_config_collection is None:
            return jsonify({'error': 'Database connection not available'}), 500
        
        # Get the product configuration by productId
        config = mongo_product_config_collection.find_one({'productId': product_id}, {'_id': 0})
        
        if not config:
            return jsonify({'error': 'Product configuration not found'}), 404
        
        return jsonify({
            'success': True,
            'data': config
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching product config: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


# Test endpoint removed - functionality confirmed working

if __name__ == '__main__':
    print("🚀 Starting MongoDB to PDF API Server")
    print("=" * 60)
    print("📋 Server Information:")
    print("   🌐 Host: localhost")
    print("   🔌 Port: 5001")
    print("   📡 New Endpoint: POST /api/generate-report")
    print("   📡 Legacy Endpoint: POST /api/personality/mongo-to-pdf")
    print("   🏥 Health Check: GET /health")
    print("   📋 Routes List: GET /api/routes")
    
    print("\n📝 New Simple Payload Example (Recommended):")
    simple_payload = {
        "code": "jmCGjMOStFLa9nPz",
        "template": "kepribadian"
    }
    print(json.dumps(simple_payload, indent=2))
    
    print("\n📝 Legacy MongoDB Payload Example:")
    legacy_payload = {
        "_id": {"$oid": "688a41c682760799c056b7fa"},
        "name": "Cris",
        "email": "cris@mail.com",
        "testResult": {
            "kepribadian": {
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
    print(json.dumps(legacy_payload, indent=2))
    
    print("\n🎯 Postman Testing (New Endpoint):")
    print("   1. Method: POST")
    print("   2. URL: http://localhost:5001/api/generate-report")
    print("   3. Headers: Content-Type: application/json")
    print("   4. Body: { \"code\": \"jmCGjMOStFLa9nPz\", \"template\": \"kepribadian\" }")
    print("   5. Expected: PDF download + saved to generated_results folder")
    
    print("\n🔥 Starting server...")
    print("   Press Ctrl+C to stop")
    print("=" * 60)
    
    app.run(host='localhost', port=5001, debug=True)