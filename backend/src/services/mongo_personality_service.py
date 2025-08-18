import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from jinja2 import Environment, FileSystemLoader
import weasyprint

class MongoPersonalityService:
    """
    Service untuk mengkonversi payload MongoDB kepribadian menjadi PDF report
    """
    
    def __init__(self, template_dir: str = None):
        """
        Initialize service dengan template directory
        
        Args:
            template_dir: Path ke directory template. Default: templates/
        """
        if template_dir is None:
            # Get current script directory and go up to find templates
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'templates')
        
        self.template_dir = template_dir
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
        # Load interpretation data
        interpretation_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 
            'ai', 'interpretation-data', 'interpretation.json'
        )
        
        with open(interpretation_path, 'r', encoding='utf-8') as f:
            self.interpretation_data = json.load(f)
    
    def validate_mongo_payload(self, mongo_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validasi payload MongoDB untuk kepribadian
        
        Args:
            mongo_payload: Data dari MongoDB
            
        Returns:
            Dict dengan status validasi dan informasi tambahan
        """
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check testResult
        if 'testResult' not in mongo_payload:
            validation['errors'].append('testResult not found in payload')
            validation['valid'] = False
            return {'validation': validation}
        
        # Check kepribadian
        if 'kepribadian' not in mongo_payload['testResult']:
            validation['errors'].append('kepribadian not found in testResult')
            validation['valid'] = False
            return {'validation': validation}
        
        kepribadian_data = mongo_payload['testResult']['kepribadian']
        
        # Check score
        if 'score' not in kepribadian_data:
            validation['errors'].append('score not found in kepribadian')
            validation['valid'] = False
            return {'validation': validation}
        
        # Check rank
        if 'rank' not in kepribadian_data:
            validation['warnings'].append('rank not found in kepribadian')
        
        # Validate required fields
        if 'name' not in mongo_payload:
            validation['errors'].append('name not found in payload')
            validation['valid'] = False
        
        # Get additional info
        additional_info = {
            'clientInfo': {
                'name': mongo_payload.get('name', 'Unknown'),
                'email': mongo_payload.get('email', '')
            },
            'formInfo': {
                'formId': kepribadian_data.get('formId', ''),
                'formName': kepribadian_data.get('formName', 'Tes Kepribadian')
            },
            'scores': kepribadian_data.get('score', {}),
            'ranks': kepribadian_data.get('rank', {})
        }
        
        return {
            'validation': validation,
            'additionalInfo': additional_info
        }
    
    def extract_personality_data(self, mongo_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ekstrak data kepribadian dari payload MongoDB
        
        Args:
            mongo_payload: Data dari MongoDB
            
        Returns:
            Dict dengan data kepribadian yang sudah diekstrak
        """
        kepribadian_data = mongo_payload['testResult']['kepribadian']
        
        return {
            'client_name': mongo_payload.get('name', 'Unknown'),
            'client_email': mongo_payload.get('email', ''),
            'phone_number': mongo_payload.get('phoneNumber', ''),
            'order_number': mongo_payload.get('orderNumber', ''),
            'created_date': mongo_payload.get('createdDate', ''),
            'form_id': kepribadian_data.get('formId', ''),
            'form_name': kepribadian_data.get('formName', 'Tes Kepribadian'),
            'scores': kepribadian_data.get('score', {}),
            'ranks': kepribadian_data.get('rank', {})
        }
    
    def determine_level(self, score: int, dimension: str) -> str:
        """
        Tentukan level (tinggi/sedang/rendah) berdasarkan skor
        
        Args:
            score: Skor dimensi
            dimension: Nama dimensi
            
        Returns:
            Level sebagai string
        """
        # Threshold dapat disesuaikan berdasarkan standar psikologi
        if score >= 70:
            return 'tinggi'
        elif score >= 40:
            return 'sedang'
        else:
            return 'rendah'
    
    def map_to_interpretation_format(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map data yang sudah diekstrak ke format interpretasi

        Args:
            extracted_data: Data yang sudah diekstrak

        Returns:
            Dict dengan format yang sesuai untuk interpretasi
        """
        dimensions = []
        dimension_names = {
            'openness': 'Keterbukaan (Openness)',
            'conscientiousness': 'Kehati-hatian (Conscientiousness)', 
            'extraversion': 'Ekstraversi (Extraversion)',
            'agreeableness': 'Keramahan (Agreeableness)',
            'neuroticism': 'Neurotisisme (Neuroticism)'
        }
        
        # Map MongoDB keys to interpretation keys
        mongo_to_interpretation = {
            'open': 'openness',
            'conscientious': 'conscientiousness',
            'extraversion': 'extraversion',
            'agreeable': 'agreeableness',
            'neurotic': 'neuroticism'
        }
        
        scores = extracted_data['scores']
        ranks = extracted_data.get('ranks', {})
        
        for mongo_key, interpretation_key in mongo_to_interpretation.items():
            if mongo_key in scores:
                score = scores[mongo_key]
                level = self.determine_level(score, interpretation_key)
                rank = ranks.get(mongo_key, '')
                
                # Get interpretation data
                interpretation_info = self.interpretation_data['results']['dimensions'][interpretation_key][level]
                
                dimension_data = {
                    'key': interpretation_key,
                    'title': dimension_names[interpretation_key],
                    'score': score,
                    'rank': rank,
                    'level': level,
                    'level_label': level.title(),
                    'interpretation': interpretation_info['interpretation'],
                    'aspects': interpretation_info['aspekKehidupan'],
                    'recommendations': interpretation_info['rekomendasi']
                }
                
                dimensions.append(dimension_data)
        
        return {
            'client_name': extracted_data['client_name'],
            'client_email': extracted_data['client_email'],
            'phone_number': extracted_data['phone_number'],
            'order_number': extracted_data['order_number'],
            'test_date': self._format_date(extracted_data['created_date']),
            'form_name': extracted_data['form_name'],
            'form_id': extracted_data['form_id'],
            'dimensions': dimensions,
            'overview': self._generate_overview(dimensions),
            'current_year': datetime.now().year
        }
    
    def _format_date(self, date_str: str) -> str:
        """
        Format tanggal ke format yang lebih readable
        
        Args:
            date_str: String tanggal
            
        Returns:
            Formatted date string
        """
        if not date_str:
            return datetime.now().strftime('%d %B %Y')
        
        try:
            # Parse ISO format
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%d %B %Y')
        except:
            return date_str
    
    def _generate_overview(self, dimensions: List[Dict[str, Any]]) -> str:
        """
        Generate overview berdasarkan dimensi kepribadian
        
        Args:
            dimensions: List dimensi kepribadian
            
        Returns:
            Overview text
        """
        if not dimensions:
            return "Analisis kepribadian berdasarkan model Big Five Personality."
        
        # Find dominant traits
        high_traits = [d for d in dimensions if d['level'] == 'tinggi']
        
        if len(high_traits) >= 2:
            trait_names = [d['title'].split('(')[0].strip() for d in high_traits[:2]]
            return f"Kepribadian Anda didominasi oleh {' dan '.join(trait_names)}, yang menunjukkan karakteristik unik dalam cara Anda berinteraksi dengan dunia dan menghadapi berbagai situasi."
        elif len(high_traits) == 1:
            trait_name = high_traits[0]['title'].split('(')[0].strip()
            return f"Kepribadian Anda menonjol dalam aspek {trait_name}, yang menjadi ciri khas utama dalam cara Anda berperilaku dan mengambil keputusan."
        else:
            return "Kepribadian Anda menunjukkan keseimbangan yang baik di berbagai aspek, dengan karakteristik yang beragam dan adaptif."
    
    def render_html_template(self, template_data: Dict[str, Any]) -> str:
        """
        Render template HTML dengan data
        
        Args:
            template_data: Data untuk template
            
        Returns:
            HTML string yang sudah dirender
        """
        template = self.jinja_env.get_template('reports/personality_report_template.html')
        return template.render(**template_data)
    
    def generate_pdf(self, html_content: str, output_path: str) -> bool:
        """
        Generate PDF dari HTML content
        
        Args:
            html_content: HTML content
            output_path: Path output PDF
            
        Returns:
            True jika berhasil, False jika gagal
        """
        try:
            # Create WeasyPrint HTML document
            html_doc = weasyprint.HTML(string=html_content)
            
            # Generate PDF
            html_doc.write_pdf(output_path)
            
            return True
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False
    
    def generate_pdf_report(self, mongo_payload: dict) -> bytes:
        """
        Generate PDF report from MongoDB personality data
        
        Args:
            mongo_payload: MongoDB personality test data
            
        Returns:
            bytes: PDF content
            
        Raises:
            ValueError: If payload is invalid
            Exception: If PDF generation fails
        """
        try:
            # Validate payload
            validation_result = self.validate_mongo_payload(mongo_payload)
            if not validation_result['validation']['valid']:
                raise ValueError(f"Invalid MongoDB payload: {validation_result['validation']['errors']}")
            
            # Extract and map data
            extracted_data = self.extract_personality_data(mongo_payload)
            interpreted_data = self.map_to_interpretation_format(extracted_data)
            
            # Render HTML
            html_content = self.render_html_template(interpreted_data)
            
            # Convert to PDF using weasyprint
            try:
                from weasyprint import HTML, CSS
                from weasyprint.text.fonts import FontConfiguration
                
                font_config = FontConfiguration()
                html_doc = HTML(string=html_content)
                pdf_bytes = html_doc.write_pdf(font_config=font_config)
                
                return pdf_bytes
                
            except ImportError:
                raise Exception("WeasyPrint not installed. Install with: pip install weasyprint")
            
        except Exception as e:
            raise Exception(f"PDF generation failed: {str(e)}")
    
    def process_mongo_payload_to_pdf(
        self, 
        mongo_payload: Dict[str, Any], 
        output_path: str,
        save_intermediate_files: bool = False
    ) -> Dict[str, Any]:
        """
        Process complete pipeline dari MongoDB payload ke PDF
        
        Args:
            mongo_payload: Data dari MongoDB
            output_path: Path output PDF
            save_intermediate_files: Apakah menyimpan file intermediate
            
        Returns:
            Dict dengan hasil processing
        """
        try:
            # Validate payload
            validation_result = self.validate_mongo_payload(mongo_payload)
            if not validation_result['validation']['valid']:
                return {
                    'success': False,
                    'error': 'Validation failed',
                    'validation': validation_result['validation']
                }
            
            # Extract data
            extracted_data = self.extract_personality_data(mongo_payload)
            
            # Map to interpretation format
            template_data = self.map_to_interpretation_format(extracted_data)
            
            # Save intermediate files if requested
            if save_intermediate_files:
                base_name = os.path.splitext(output_path)[0]
                
                # Save mapped data
                with open(f"{base_name}_template_data.json", 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=2, ensure_ascii=False)
            
            # Render HTML
            html_content = self.render_html_template(template_data)
            
            # Save HTML if requested
            if save_intermediate_files:
                base_name = os.path.splitext(output_path)[0]
                with open(f"{base_name}.html", 'w', encoding='utf-8') as f:
                    f.write(html_content)
            
            # Generate PDF using weasyprint directly
            try:
                from weasyprint import HTML, CSS
                from weasyprint.text.fonts import FontConfiguration
                
                font_config = FontConfiguration()
                html_doc = HTML(string=html_content)
                html_doc.write_pdf(output_path, font_config=font_config)
                
            except ImportError:
                raise Exception("WeasyPrint not installed. Install with: pip install weasyprint")
            
            return {
                'success': True,
                'output_path': output_path,
                'client_name': template_data['client_name'],
                'dimensions_count': len(template_data['dimensions']),
                'form_name': template_data['form_name']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Processing failed: {str(e)}'
            }

# Example usage
if __name__ == "__main__":
    # Load example MongoDB data
    with open('../../ai/interpretation-data/mongoData-example.json', 'r', encoding='utf-8') as f:
        mongo_data = json.load(f)
    
    # Initialize service
    service = MongoPersonalityService()
    
    # Validate payload
    validation = service.validate_mongo_payload(mongo_data)
    print("Validation:", validation)
    
    if validation['validation']['valid']:
        # Process to PDF
        result = service.process_mongo_payload_to_pdf(
            mongo_data,
            'personality_report.pdf',
            save_intermediate_files=True
        )
        
        print("Result:", result)
    else:
        print("Validation failed:", validation['validation']['errors'])