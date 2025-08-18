#!/usr/bin/env python3
"""
Service untuk mengkonversi payload MongoDB Personal Values ke PDF report
"""

import json
import os
from typing import Dict, List, Tuple, Any, Optional
from jinja2 import Environment, FileSystemLoader
import weasyprint
from datetime import datetime

class MongoPersonalValuesService:
    """Service untuk menangani konversi MongoDB payload ke Personal Values PDF"""
    
    def __init__(self, interpretation_data_path: str = None, template_dir: str = "templates"):
        """
        Initialize service
        
        Args:
            interpretation_data_path: Path ke file interpretation-personal-values.json
            template_dir: Directory template HTML
        """
        self.template_dir = template_dir
        
        # Default path untuk interpretation data
        if interpretation_data_path is None:
            self.interpretation_data_path = "/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/ai/interpretation-data/interpretation-personal-values.json"
        else:
            self.interpretation_data_path = interpretation_data_path
            
        # Load interpretation data
        self.interpretation_data = self._load_interpretation_data()
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
        # Key mapping dari MongoDB ke interpretasi
        self.key_mapping = {
            "universalism": "universalism",
            "security": "security", 
            "benevolence": "benevolence",
            "hedonism": "hedonism",
            "achievement": "achievement",
            "power": "power",
            "self_direction": "selfDirection",
            "Stimulation": "stimulation",
            "tradition": "tradition",
            "conformity": "conformity"
        }
    
    def _load_interpretation_data(self) -> Dict[str, Any]:
        """Load data interpretasi Personal Values"""
        try:
            with open(self.interpretation_data_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Interpretation data not found: {self.interpretation_data_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in interpretation data: {self.interpretation_data_path}")
    
    def extract_personal_values_from_mongo(self, mongo_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data personal values dari MongoDB payload
        
        Args:
            mongo_payload: Full MongoDB document
            
        Returns:
            Dict dengan data personal values yang sudah diekstrak
        """
        try:
            test_result = mongo_payload.get("testResult", {})
            personal_values = test_result.get("personalValues", {})
            
            if not personal_values:
                raise ValueError("personalValues not found in testResult")
            
            result = personal_values.get("result", {})
            scores = result.get("score", {})
            
            if not scores:
                raise ValueError("scores not found in personalValues.result")
            
            extracted_data = {
                "formId": personal_values.get("formId"),
                "formName": personal_values.get("formName"),
                "topValue": result.get("value"),
                "scores": scores,
                "clientInfo": {
                    "name": mongo_payload.get("name"),
                    "email": mongo_payload.get("email"),
                    "phone": mongo_payload.get("phoneNumber"),
                    "orderNumber": mongo_payload.get("orderNumber"),
                    "createdDate": mongo_payload.get("createdDate")
                }
            }
            
            return extracted_data
            
        except KeyError as e:
            raise ValueError(f"Missing required field in MongoDB payload: {e}")
    
    def get_top_n_values(self, scores: Dict[str, int], n: int = 3) -> List[Tuple[str, int]]:
        """Mendapatkan top N values berdasarkan score tertinggi"""
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:n]
    
    def map_to_interpretation_format(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map data yang sudah diekstrak ke format interpretasi
        
        Args:
            extracted_data: Data yang sudah diekstrak dari MongoDB
            
        Returns:
            Dict dengan format interpretasi yang siap untuk template
        """
        scores = extracted_data["scores"]
        top_values = self.get_top_n_values(scores, 3)
        
        # Map ke format interpretasi
        mapped_data = {
            "testName": "personalValues",
            "testType": "top-n-dimension", 
            "results": {
                "topN": 3,
                "dimensions": {}
            },
            "sourceData": {
                "formId": extracted_data["formId"],
                "formName": extracted_data["formName"],
                "originalScores": scores,
                "topValue": extracted_data["topValue"],
                "clientInfo": extracted_data["clientInfo"]
            }
        }
        
        # Map top 3 values ke interpretasi
        interpretation_dimensions = self.interpretation_data["results"]["dimensions"]
        
        for i, (mongo_key, score) in enumerate(top_values, 1):
            # Map key MongoDB ke key interpretasi
            interpretation_key = self.key_mapping.get(mongo_key)
            
            if interpretation_key and interpretation_key in interpretation_dimensions:
                mapped_data["results"]["dimensions"][interpretation_key] = {
                    **interpretation_dimensions[interpretation_key],
                    "score": score,
                    "rank": i,
                    "originalKey": mongo_key
                }
            else:
                raise ValueError(f"Key '{mongo_key}' not found in interpretation data")
        
        return mapped_data
    
    def generate_template_data(self, mapped_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate data untuk template rendering
        
        Args:
            mapped_data: Data yang sudah dimapping
            
        Returns:
            Dict dengan data siap untuk template
        """
        top_n = mapped_data["results"]["topN"]
        dimensions = mapped_data["results"]["dimensions"]
        source_data = mapped_data["sourceData"]
        
        # Prepare top_values untuk template
        top_values = []
        
        # Sort berdasarkan rank
        sorted_dimensions = sorted(dimensions.items(), key=lambda x: x[1]["rank"])
        
        for key, dimension in sorted_dimensions:
            top_values.append({
                "title": dimension["title"],
                "description": dimension["description"],
                "manifestation": dimension["manifestation"],
                "strengthChallenges": dimension["strengthChallenges"],
                "score": dimension["score"],
                "rank": dimension["rank"],
                "key": key
            })
        
        # Format client info
        client_info = source_data["clientInfo"]
        
        # Format tanggal
        test_date = "N/A"
        if client_info.get("createdDate"):
            try:
                # Parse ISO date
                date_obj = datetime.fromisoformat(client_info["createdDate"].replace('Z', '+00:00'))
                test_date = date_obj.strftime("%d %B %Y")
            except:
                test_date = client_info["createdDate"]
        
        template_data = {
            "top_n": top_n,
            "top_values": top_values,
            "client_info": {
                "name": client_info.get("name", "N/A"),
                "email": client_info.get("email", "N/A"),
                "phone": client_info.get("phone", "N/A"),
                "test_date": test_date,
                "order_number": client_info.get("orderNumber", "N/A")
            },
            "source_info": {
                "formId": source_data["formId"],
                "formName": source_data["formName"],
                "originalScores": source_data["originalScores"],
                "topValue": source_data["topValue"]
            }
        }
        
        return template_data
    
    def render_html_template(self, template_data: Dict[str, Any], template_name: str = "personal_values_report_template.html") -> str:
        """
        Render HTML template dengan data
        
        Args:
            template_data: Data untuk template
            template_name: Nama file template
            
        Returns:
            HTML string yang sudah dirender
        """
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**template_data)
        except Exception as e:
            raise ValueError(f"Error rendering template: {e}")
    
    def generate_pdf(self, html_content: str, output_path: str) -> bool:
        """
        Generate PDF dari HTML content
        
        Args:
            html_content: HTML string
            output_path: Path output PDF
            
        Returns:
            True jika berhasil, False jika gagal
        """
        try:
            pdf_document = weasyprint.HTML(string=html_content)
            pdf_document.write_pdf(output_path)
            return True
        except Exception as e:
            raise RuntimeError(f"Error generating PDF: {e}")
    
    def process_mongo_payload_to_pdf(self, mongo_payload: Dict[str, Any], output_path: str, 
                                   save_intermediate_files: bool = False) -> Dict[str, Any]:
        """
        Full pipeline: MongoDB payload → PDF
        
        Args:
            mongo_payload: Full MongoDB document
            output_path: Path output PDF
            save_intermediate_files: Apakah menyimpan file intermediate untuk debugging
            
        Returns:
            Dict dengan informasi hasil processing
        """
        try:
            # Step 1: Extract personal values data
            extracted_data = self.extract_personal_values_from_mongo(mongo_payload)
            
            # Step 2: Map ke format interpretasi
            mapped_data = self.map_to_interpretation_format(extracted_data)
            
            # Step 3: Generate template data
            template_data = self.generate_template_data(mapped_data)
            
            # Step 4: Render HTML
            html_content = self.render_html_template(template_data)
            
            # Step 5: Generate PDF
            self.generate_pdf(html_content, output_path)
            
            # Save intermediate files jika diminta
            if save_intermediate_files:
                base_name = os.path.splitext(output_path)[0]
                
                # Save mapped data
                with open(f"{base_name}_mapped_data.json", 'w', encoding='utf-8') as f:
                    json.dump(mapped_data, f, indent=2, ensure_ascii=False)
                
                # Save template data
                with open(f"{base_name}_template_data.json", 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=2, ensure_ascii=False)
                
                # Save HTML
                with open(f"{base_name}.html", 'w', encoding='utf-8') as f:
                    f.write(html_content)
            
            # Return hasil processing
            result = {
                "success": True,
                "output_path": output_path,
                "client_name": template_data["client_info"]["name"],
                "top_values": [
                    {
                        "rank": value["rank"],
                        "title": value["title"],
                        "score": value["score"]
                    }
                    for value in template_data["top_values"]
                ],
                "form_info": {
                    "formId": template_data["source_info"]["formId"],
                    "formName": template_data["source_info"]["formName"]
                }
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output_path": output_path
            }
    
    def validate_mongo_payload(self, mongo_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validasi MongoDB payload sebelum processing
        
        Args:
            mongo_payload: MongoDB document
            
        Returns:
            Dict dengan hasil validasi
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required fields
        required_fields = ["testResult", "name", "email"]
        for field in required_fields:
            if field not in mongo_payload:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["valid"] = False
        
        # Check personalValues in testResult
        test_result = mongo_payload.get("testResult", {})
        if "personalValues" not in test_result:
            validation_result["errors"].append("Missing personalValues in testResult")
            validation_result["valid"] = False
        else:
            personal_values = test_result["personalValues"]
            
            # Check required personalValues fields
            if "result" not in personal_values:
                validation_result["errors"].append("Missing result in personalValues")
                validation_result["valid"] = False
            else:
                result = personal_values["result"]
                if "score" not in result:
                    validation_result["errors"].append("Missing score in personalValues.result")
                    validation_result["valid"] = False
                else:
                    scores = result["score"]
                    
                    # Check if we have enough scores
                    if len(scores) < 3:
                        validation_result["warnings"].append(f"Only {len(scores)} scores available, need at least 3 for top 3")
                    
                    # Check if all scores are valid numbers
                    for key, score in scores.items():
                        if not isinstance(score, (int, float)):
                            validation_result["errors"].append(f"Invalid score for {key}: {score}")
                            validation_result["valid"] = False
        
        return validation_result

# Example usage function
def example_usage():
    """Contoh penggunaan service"""
    
    # Initialize service
    service = MongoPersonalValuesService()
    
    # Load example MongoDB payload
    mongo_path = "/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/ai/interpretation-data/mongoData-example.json"
    
    with open(mongo_path, 'r', encoding='utf-8') as file:
        mongo_payload = json.load(file)
    
    # Validate payload
    validation = service.validate_mongo_payload(mongo_payload)
    print(f"Validation: {validation}")
    
    if validation["valid"]:
        # Process ke PDF
        result = service.process_mongo_payload_to_pdf(
            mongo_payload, 
            "service_generated_report.pdf",
            save_intermediate_files=True
        )
        
        print(f"Processing result: {result}")
    else:
        print(f"Validation failed: {validation['errors']}")

if __name__ == '__main__':
    example_usage()