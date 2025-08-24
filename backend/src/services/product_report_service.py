"""Product report service for generating combined PDF reports based on product configurations"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import tempfile
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from ..utils.logging_utils import LoggingUtils

logger = LoggingUtils.get_logger(__name__)


class ProductReportService:
    """Service for generating product-based combined PDF reports"""
    
    def __init__(self):
        self.logger = LoggingUtils.get_logger(__name__)
        self.db_service = None
        self.pdf_service = None
        self.google_drive_service = None
        self._initialized = False
        self.jinja_env = None
    
    def initialize(self, db_service=None, pdf_service=None, google_drive_service=None) -> bool:
        """Initialize product report service"""
        try:
            self.db_service = db_service
            self.pdf_service = pdf_service
            self.google_drive_service = google_drive_service
            
            # Initialize separate MongoDB connections for different databases
            from pymongo import MongoClient
            import os
            
            mongo_connection_string = os.getenv('MONGODB_URI')
            self.mongo_client = MongoClient(mongo_connection_string)
            self.workflow_db = self.mongo_client['workflow']
            self.mindframe_db = self.mongo_client['mindframe']
            
            # No longer need to create results directory - using temporary files
            
            # Initialize Jinja2 environment
            # Navigate from src/services to backend/templates
            template_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'templates')
            self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
            
            # Log template directory for debugging
            self.logger.info(f"Template directory: {os.path.abspath(template_dir)}")
            
            self._initialized = True
            logger.info("Product report service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize product report service: {str(e)}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform product report service health check"""
        try:
            health_info = {
                "status": "healthy",
                "database_available": False,
                "pdf_service_available": False,
                "google_drive_available": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Check database service
            if self.db_service:
                try:
                    db_health = self.db_service.health_check()
                    health_info["database_available"] = db_health.get("status") == "healthy"
                except Exception as e:
                    health_info["database_error"] = str(e)
            
            # Check PDF service
            if self.pdf_service:
                try:
                    pdf_health = self.pdf_service.health_check()
                    health_info["pdf_service_available"] = pdf_health.get("status") == "healthy"
                except Exception as e:
                    health_info["pdf_service_error"] = str(e)
            
            # Check Google Drive service
            if self.google_drive_service:
                try:
                    drive_health = self.google_drive_service.health_check()
                    health_info["google_drive_available"] = drive_health.get("status") == "healthy"
                except Exception as e:
                    health_info["google_drive_error"] = str(e)
            
            # No longer checking results directory - using temporary files
            
            # Determine overall status
            if not health_info["database_available"]:
                health_info["status"] = "unhealthy"
            
            return health_info
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def generate_product_report(self, code: str, product_id: str) -> Dict[str, Any]:
        """Generate combined PDF report for a product
        
        Args:
            code: Test result code from workflow database
            product_id: Product configuration ID
            
        Returns:
            Dict containing success status, file path, filename, or error
        """
        try:
            if not self._initialized:
                return {
                    'success': False,
                    'error': 'Product report service not initialized',
                    'error_type': 'service_not_initialized'
                }
            
            if not self.db_service:
                return {
                    'success': False,
                    'error': 'Database service not available',
                    'error_type': 'service_unavailable'
                }
            
            # Get product configuration
            logger.info(f"Looking for product config: productId='{product_id}', isActive=True")
            product_config = self._get_product_config(product_id)
            if not product_config:
                return {
                    'success': False,
                    'error': f'Product configuration not found: {product_id}',
                    'error_type': 'product_not_found'
                }
            
            # Get test results from workflow database
            test_data = self._get_test_data(code)
            if not test_data:
                return {
                    'success': False,
                    'error': f'Test data not found for code: {code}',
                    'error_type': 'test_data_not_found'
                }
            
            # Validate that all required tests are completed
            validation_result = self._validate_required_tests(test_data, product_config)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'error_type': 'missing_required_tests'
                }
            
            # Generate combined PDF
            result = self._generate_combined_pdf(test_data, product_config)
            
            if result['success']:
                logger.info(f"Product report generated successfully: {result['filename']}")
                return result
            else:
                logger.error(f"Failed to generate product report: {result['error']}")
                return result
                
        except Exception as e:
            logger.error(f"Error in generate_product_report: {str(e)}")
            return {
                'success': False,
                'error': f'Internal server error: {str(e)}',
                'error_type': 'internal_error'
            }
    
    def _get_product_config(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product configuration from database"""
        try:
            # Get from mindframe database product_configs collection
            product_config = self.mindframe_db.product_configs.find_one(
                {"productId": product_id, "isActive": True}
            )
            
            if product_config:
                logger.info(f"Product config found: {product_config.get('productId', 'N/A')}")
                return product_config
            else:
                logger.warning(f"Product config not found for productId: {product_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting product config: {str(e)}")
            return None
    
    def _get_test_data(self, code: str) -> Optional[Dict[str, Any]]:
        """Get test data from workflow database"""
        try:
            # Get from workflow database psikotes_v2 collection
            test_data = self.workflow_db.psikotes_v2.find_one(
                {"code": code}
            )
            
            return test_data
            
        except Exception as e:
            logger.error(f"Error getting test data: {str(e)}")
            return None
    
    def _validate_required_tests(self, test_data: Dict[str, Any], product_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that all required tests are completed"""
        try:
            test_results = test_data.get('testResult', {})
            missing_tests = []
            
            for test_config in product_config.get('tests', []):
                if test_config.get('required', False) and test_config.get('testType') not in test_results:
                    missing_tests.append(test_config.get('testType'))
            
            if missing_tests:
                return {
                    'valid': False,
                    'error': f'Missing required test results: {", ".join(missing_tests)}'
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating required tests: {str(e)}")
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}'
            }
    
    def _generate_combined_pdf(self, test_data: Dict[str, Any], product_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate combined PDF by merging individual PDFs"""
        try:
            # Generate filename for final combined PDF
            user_name = test_data.get('name', 'User')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{product_config['productId']}_{user_name}_{timestamp}.pdf"
            
            # Create temporary file for final PDF
            temp_fd, temp_file_path = tempfile.mkstemp(suffix='.pdf', prefix=f'{product_config["productId"]}_')
            os.close(temp_fd)  # Close file descriptor, we'll use the path
            
            # Sort tests by order
            sorted_tests = sorted(product_config.get('tests', []), key=lambda x: x.get('order', 0))
            
            # Generate individual PDFs and collect their paths
            individual_pdf_paths = []
            test_results = test_data.get('testResult', {})
            
            logger.info(f"Starting PDF merging pipeline for {len(sorted_tests)} tests...")
            
            # Always generate cover page PDF for all products
            logger.info("Generating cover page PDF...")
            cover_pdf_path = self._generate_cover_page_pdf(test_data, product_config, timestamp)
            if cover_pdf_path:
                individual_pdf_paths.append(cover_pdf_path)
                logger.info(f"Cover page PDF generated: {os.path.basename(cover_pdf_path)}")
            else:
                logger.error("Cover page PDF generation failed")
            
            # Generate introduction PDF if configured
            if 'introduction' in product_config.get('staticContent', {}):
                intro_pdf_path = self._generate_introduction_pdf(product_config['staticContent']['introduction'], timestamp)
                if intro_pdf_path:
                    individual_pdf_paths.append(intro_pdf_path)
                    logger.info(f"Introduction PDF generated: {os.path.basename(intro_pdf_path)}")
            
            # Generate individual test PDFs
            for test_config in sorted_tests:
                test_type = test_config.get('testType')
                if test_type in test_results:
                    # Create a mock mongo_data object for the existing template functions
                    mock_mongo_data = {
                        'name': test_data.get('name', 'User'),
                        'email': test_data.get('email', ''),
                        'testResult': {test_type: test_results[test_type]}
                    }
                    
                    # Generate individual PDF using PDF service
                    pdf_path = self._generate_individual_test_pdf(mock_mongo_data, test_type, timestamp)
                    if pdf_path:
                        individual_pdf_paths.append(pdf_path)
                        logger.info(f"Individual PDF generated for {test_type}: {os.path.basename(pdf_path)}")
            
            # Generate closing PDF if configured
            if 'closing' in product_config.get('staticContent', {}):
                closing_pdf_path = self._generate_closing_pdf(product_config['staticContent']['closing'], timestamp)
                if closing_pdf_path:
                    individual_pdf_paths.append(closing_pdf_path)
                    logger.info(f"Closing PDF generated: {os.path.basename(closing_pdf_path)}")
            
            # Merge all PDFs
            if not individual_pdf_paths:
                return {
                    'success': False,
                    'error': 'No individual PDFs were generated to merge'
                }
            
            # Use PDF service to merge PDFs
            merge_result = self._merge_pdfs(individual_pdf_paths, temp_file_path)
            
            if merge_result['success']:
                # Clean up individual PDF files
                self._cleanup_individual_pdfs(individual_pdf_paths)
                
                # Upload to Google Drive if service is available
                google_drive_result = None
                if self.google_drive_service:
                    try:
                        logger.info(f"Uploading combined PDF to Google Drive: {filename}")
                        google_drive_result = self.google_drive_service.upload_file(
                            file_path=temp_file_path,
                            file_name=filename
                        )
                        
                        if google_drive_result.get('success'):
                            logger.info(f"Successfully uploaded to Google Drive: {google_drive_result.get('file_id')}")
                        else:
                            logger.warning(f"Failed to upload to Google Drive: {google_drive_result.get('error')}")
                            
                    except Exception as e:
                        logger.error(f"Error uploading to Google Drive: {str(e)}")
                        google_drive_result = {
                            'success': False,
                            'error': str(e)
                        }
                
                # Clean up temporary file
                try:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                        logger.info(f"Temporary file cleaned up: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {temp_file_path}: {str(e)}")
                
                result = {
                    'success': True,
                    'filename': filename
                }
                
                # Add Google Drive info to result if upload was attempted
                if google_drive_result:
                    result['google_drive'] = google_drive_result
                
                return result
            else:
                return merge_result
                
        except Exception as e:
            logger.error(f"Error generating combined PDF: {str(e)}")
            return {
                'success': False,
                'error': f'PDF generation error: {str(e)}'
            }
    
    def _generate_cover_page_pdf(self, test_data: Dict[str, Any], product_config: Dict[str, Any], timestamp: str) -> Optional[str]:
        """Generate cover page PDF using the standard cover page template"""
        try:
            # Extract data for template rendering
            user_name = test_data.get('name', 'User')
            current_date = datetime.now().strftime('%d %B %Y')
            product_name = product_config.get('productName', 'Laporan Psikotes')
            
            # Load and render cover page template
            template = self.jinja_env.get_template('layout/cover_page_template.html')
            html_content = template.render(
                user_name=user_name,
                current_date=current_date,
                product_name=product_name
            )
            
            # Generate PDF using temporary file
            temp_fd, pdf_path = tempfile.mkstemp(suffix='.pdf', prefix=f"cover_{product_config.get('productId', 'product')}_{timestamp}_")
            os.close(temp_fd)  # Close file descriptor, we'll use the path
            
            html_obj = HTML(string=html_content)
            html_obj.write_pdf(pdf_path)
            
            logger.info(f"Cover page PDF generated: {os.path.basename(pdf_path)}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating cover page PDF: {str(e)}")
            return None
    
    def _generate_personality_pdf(self, mongo_data: Dict[str, Any], timestamp: str) -> Optional[str]:
        """
        Generate personality PDF and return file path
        """
        try:
            # Load interpretation data for 'kepribadian' template from MongoDB
            interpretation_data = self._load_interpretation_data('kepribadian')
            if not interpretation_data:
                logger.error("Failed to load interpretation data for kepribadian template")
                return None
            
            # Prepare template data
            template_data = {
                'client_name': mongo_data.get('name', 'Unknown'),
                'test_date': datetime.now().strftime('%d %B %Y'),
                'report_date': datetime.now().strftime('%d %B %Y'),
                'test_name': interpretation_data.get('testName', 'Personality Test'),
                'test_type': interpretation_data.get('testType', 'Personality Assessment'),
                'overview': interpretation_data.get('overview', 'Analisis kepribadian'),
                'dimensions': interpretation_data.get('results', {}).get('dimensions', [])
            }
            
            # Load and render template
            template = self.jinja_env.get_template('reports/personality_report_template.html')
            html_content = template.render(**template_data)
            
            # Generate PDF using temporary file
            temp_fd, pdf_path = tempfile.mkstemp(suffix='.pdf', prefix=f"personality_{timestamp}_")
            os.close(temp_fd)  # Close file descriptor, we'll use the path
            
            html_obj = HTML(string=html_content)
            html_obj.write_pdf(pdf_path)
            
            logger.info(f"Personality PDF generated: {os.path.basename(pdf_path)}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating personality PDF: {str(e)}")
            return None
    
    def _generate_minat_bakat_pdf(self, mongo_data: Dict[str, Any], timestamp: str) -> Optional[str]:
        """
        Generate minat bakat PDF and return file path
        """
        try:
            # Load interpretation data for 'minatBakat' template from MongoDB
            interpretation_data = self._load_interpretation_data('minatBakat')
            if not interpretation_data:
                logger.error("Failed to load interpretation data for minatBakat template")
                return None
            
            # Prepare template data
            template_data = {
                'client_name': mongo_data.get('name', 'Unknown'),
                'client_age': mongo_data.get('age', '25'),
                'test_date': datetime.now().strftime('%d %B %Y'),
                'report_date': datetime.now().strftime('%d %B %Y'),
                'test_name': interpretation_data.get('testName', 'Minat Bakat'),
                'test_type': interpretation_data.get('testType', 'Career Interest & Talent Assessment'),
                'overview': interpretation_data.get('overview', 'Analisis minat dan bakat karier'),
                'dimensions': interpretation_data.get('results', {}).get('dimensions', [])
            }
            
            # Load and render template
            template = self.jinja_env.get_template('reports/minat_bakat_report_template.html')
            html_content = template.render(**template_data)
            
            # Generate PDF using temporary file
            temp_fd, pdf_path = tempfile.mkstemp(suffix='.pdf', prefix=f"minat_bakat_{timestamp}_")
            os.close(temp_fd)  # Close file descriptor, we'll use the path
            
            html_obj = HTML(string=html_content)
            html_obj.write_pdf(pdf_path)
            
            logger.info(f"Minat Bakat PDF generated: {os.path.basename(pdf_path)}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating minat bakat PDF: {str(e)}")
            return None
    
    def _generate_personal_values_pdf(self, mongo_data: Dict[str, Any], timestamp: str) -> Optional[str]:
        """
        Generate personal values PDF and return file path
        """
        try:
            # Load interpretation data for 'personalValues' template from MongoDB
            interpretation_data = self._load_interpretation_data('personalValues')
            if not interpretation_data:
                logger.error("Failed to load interpretation data for personalValues template")
                return None
            
            # Prepare template data
            template_data = {
                'client_name': mongo_data.get('name', 'Unknown'),
                'test_date': datetime.now().strftime('%d %B %Y'),
                'report_date': datetime.now().strftime('%d %B %Y'),
                'test_name': interpretation_data.get('testName', 'Personal Values'),
                'test_type': interpretation_data.get('testType', 'Values Assessment'),
                'overview': interpretation_data.get('overview', 'Analisis nilai personal'),
                'dimensions': interpretation_data.get('results', {}).get('dimensions', [])
            }
            
            # Load and render template
            template = self.jinja_env.get_template('reports/personal_values_report_template.html')
            html_content = template.render(**template_data)
            
            # Generate PDF using temporary file
            temp_fd, pdf_path = tempfile.mkstemp(suffix='.pdf', prefix=f"personal_values_{timestamp}_")
            os.close(temp_fd)  # Close file descriptor, we'll use the path
            
            html_obj = HTML(string=html_content)
            html_obj.write_pdf(pdf_path)
            
            logger.info(f"Personal Values PDF generated: {os.path.basename(pdf_path)}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating personal values PDF: {str(e)}")
            return None
    
    def _generate_motivation_boost_pdf(self, mongo_data: Dict[str, Any], timestamp: str) -> Optional[str]:
        """
        Generate motivation boost PDF and return file path
        """
        try:
            # Load interpretation data for 'motivationBoost' template from MongoDB
            interpretation_data = self._load_interpretation_data('motivationBoost')
            if not interpretation_data:
                logger.error("Failed to load interpretation data for motivationBoost template")
                return None
            
            # Prepare template data
            template_data = {
                'client_name': mongo_data.get('name', 'Unknown'),
                'test_date': datetime.now().strftime('%d %B %Y'),
                'report_date': datetime.now().strftime('%d %B %Y'),
                'test_name': interpretation_data.get('testName', 'Motivation Boost'),
                'test_type': interpretation_data.get('testType', 'Motivation Assessment'),
                'overview': interpretation_data.get('overview', 'Analisis motivasi'),
                'dimensions': interpretation_data.get('results', {}).get('dimensions', [])
            }
            
            # Load and render template
            template = self.jinja_env.get_template('reports/motivation_boost_report_template.html')
            html_content = template.render(**template_data)
            
            # Generate PDF using temporary file
            temp_fd, pdf_path = tempfile.mkstemp(suffix='.pdf', prefix=f"motivation_boost_{timestamp}_")
            os.close(temp_fd)  # Close file descriptor, we'll use the path
            
            html_obj = HTML(string=html_content)
            html_obj.write_pdf(pdf_path)
            
            logger.info(f"Motivation Boost PDF generated: {os.path.basename(pdf_path)}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating motivation boost PDF: {str(e)}")
            return None
    
    def _generate_peta_perilaku_pdf(self, mongo_data: Dict[str, Any], timestamp: str) -> Optional[str]:
        """
        Generate peta perilaku PDF and return file path
        """
        try:
            # Load interpretation data for 'petaPerilaku' template from MongoDB
            interpretation_data = self._load_interpretation_data('petaPerilaku')
            if not interpretation_data:
                logger.error("Failed to load interpretation data for petaPerilaku template")
                return None
            
            # Prepare template data
            template_data = {
                'client_name': mongo_data.get('name', 'Unknown'),
                'test_date': datetime.now().strftime('%d %B %Y'),
                'report_date': datetime.now().strftime('%d %B %Y'),
                'test_name': interpretation_data.get('testName', 'Peta Perilaku'),
                'test_type': interpretation_data.get('testType', 'Behavior Mapping'),
                'overview': interpretation_data.get('overview', 'Analisis peta perilaku'),
                'dimensions': interpretation_data.get('results', {}).get('dimensions', [])
            }
            
            # Load and render template
            template = self.jinja_env.get_template('reports/peta_perilaku_report_template.html')
            html_content = template.render(**template_data)
            
            # Generate PDF using temporary file
            temp_fd, pdf_path = tempfile.mkstemp(suffix='.pdf', prefix=f"peta_perilaku_{timestamp}_")
            os.close(temp_fd)  # Close file descriptor, we'll use the path
            
            html_obj = HTML(string=html_content)
            html_obj.write_pdf(pdf_path)
            
            logger.info(f"Peta Perilaku PDF generated: {os.path.basename(pdf_path)}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating peta perilaku PDF: {str(e)}")
            return None
    
    def _load_interpretation_data(self, test_name: str) -> Optional[Dict[str, Any]]:
        """
        Load interpretation data from MongoDB for a specific test
        """
        try:
            interpretation_doc = self.mindframe_db.interpretations.find_one({'testName': test_name})
            return interpretation_doc
        except Exception as e:
            logger.error(f"Error loading interpretation data for {test_name}: {str(e)}")
            return None
    
    def _generate_introduction_pdf(self, intro_config: Dict[str, Any], timestamp: str) -> Optional[str]:
        """Generate introduction PDF using the same approach as simple_api_server.py"""
        try:
            # Load and render introduction template (same as simple_api_server.py)
            template = self.jinja_env.get_template('layout/introduction_section_template.html')
            html_content = template.render(intro_config=intro_config)
            
            # Generate PDF using temporary file
            temp_fd, pdf_path = tempfile.mkstemp(suffix='.pdf', prefix=f'introduction_{timestamp}_')
            os.close(temp_fd)  # Close file descriptor, we'll use the path
            
            html_obj = HTML(string=html_content)
            html_obj.write_pdf(pdf_path)
            
            logger.info(f"Introduction PDF generated: {os.path.basename(pdf_path)}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating introduction PDF: {str(e)}")
            return None
    
    def _generate_closing_pdf(self, closing_config: Dict[str, Any], timestamp: str) -> Optional[str]:
        """
        Generate closing PDF using the same approach as simple_api_server.py
        """
        try:
            # Prepare template data with proper structure
            template_data = {
                'closing_message': closing_config.get('content', 'Terima kasih telah mengikuti tes ini.'),
                'next_steps': closing_config.get('nextSteps', 'Silakan hubungi kami untuk konsultasi lebih lanjut.'),
                'contact_info': {
                    'email': closing_config.get('contactInfo', {}).get('email', 'info@satupersen.net'),
                    'website': closing_config.get('contactInfo', {}).get('website', 'www.satupersen.net'),
                    'phone': closing_config.get('contactInfo', {}).get('phone', '+62 21 1234 5678')
                },
                'company_name': closing_config.get('companyName', 'Satu Persen'),
                'report_date': datetime.now().strftime('%d %B %Y')
            }
            
            # Load and render closing template
            template = self.jinja_env.get_template('layout/closing_section_template.html')
            html_content = template.render(**template_data)
            
            # Generate PDF using temporary file
            temp_fd, pdf_path = tempfile.mkstemp(suffix='.pdf', prefix=f'closing_{timestamp}_')
            os.close(temp_fd)  # Close file descriptor, we'll use the path
            
            html_obj = HTML(string=html_content)
            html_obj.write_pdf(pdf_path)
            
            logger.info(f"Closing PDF generated: {os.path.basename(pdf_path)}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating closing PDF: {str(e)}")
            return None
    
    def _generate_individual_test_pdf(self, mongo_data: Dict[str, Any], test_type: str, timestamp: str) -> Optional[str]:
        """Generate individual test PDF"""
        try:
            # Map test types to their corresponding generation functions
            generation_functions = {
                'kepribadian': self._generate_personality_pdf,
                'personalValues': self._generate_personal_values_pdf,
                'motivationBoost': self._generate_motivation_boost_pdf,
                'minatBakat': self._generate_minat_bakat_pdf,
                'petaPerilaku': self._generate_peta_perilaku_pdf
            }
            
            if test_type not in generation_functions:
                logger.error(f"Unknown test type: {test_type}")
                return None
            
            # Call the appropriate generation function (no longer need temp_dir since functions use tempfile.mkstemp)
            generation_function = generation_functions[test_type]
            pdf_path = generation_function(mongo_data, timestamp)
            
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating individual test PDF for {test_type}: {str(e)}")
            return None
    
    def _merge_pdfs(self, pdf_paths: List[str], output_path: str) -> Dict[str, Any]:
        """Merge multiple PDFs into a single file"""
        try:
            import PyPDF2
            
            # Validate that all files exist
            for file_path in pdf_paths:
                if not os.path.exists(file_path):
                    logger.error(f"File not found: {file_path}")
                    return {
                        'success': False,
                        'error': f'File not found: {file_path}'
                    }
            
            # Create PDF merger
            pdf_merger = PyPDF2.PdfMerger()
            
            # Add each PDF file to the merger
            for file_path in pdf_paths:
                logger.info(f"Adding PDF: {os.path.basename(file_path)}")
                with open(file_path, 'rb') as pdf_file:
                    pdf_merger.append(pdf_file)
            
            # Write the merged PDF
            with open(output_path, 'wb') as output_file:
                pdf_merger.write(output_file)
            
            pdf_merger.close()
            
            # Get file size
            file_size = os.path.getsize(output_path)
            logger.info(f"Combined PDF created: {os.path.basename(output_path)} ({file_size} bytes)")
            
            return {'success': True}
            
        except ImportError:
            logger.error("PyPDF2 not available for PDF merging")
            return {
                'success': False,
                'error': 'PyPDF2 not available for PDF merging'
            }
        except Exception as e:
            logger.error(f"Error merging PDFs: {str(e)}")
            return {
                'success': False,
                'error': f'PDF merge error: {str(e)}'
            }
    
    def _cleanup_individual_pdfs(self, pdf_paths: List[str]) -> None:
        """Clean up individual PDF files after merging"""
        try:
            for pdf_path in pdf_paths:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                    logger.debug(f"Cleaned up individual PDF: {pdf_path}")
                    
        except Exception as e:
            logger.warning(f"Error cleaning up individual PDFs: {str(e)}")


# Global service instance
product_report_service = ProductReportService()