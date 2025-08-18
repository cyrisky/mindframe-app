#!/usr/bin/env python3
"""
Direct test untuk Personal Values service tanpa import issues
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

def test_service():
    """
    Test service functionality
    """
    print("Personal Values Service Direct Test")
    print("===================================")
    
    try:
        # Initialize service
        service = MongoPersonalValuesService(
            template_dir="/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/backend/templates"
        )
        
        print("✓ Service initialized successfully")
        
        # Load MongoDB example data
        mongo_data_path = "/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/ai/interpretation-data/mongoData-example.json"
        
        with open(mongo_data_path, 'r', encoding='utf-8') as file:
            mongo_data = json.load(file)
        
        print(f"✓ MongoDB data loaded: {mongo_data.get('name', 'Unknown')}")
        
        # Test validation
        print("\n=== Validation Test ===")
        validation = service.validate_mongo_payload(mongo_data)
        print(f"Valid: {validation['valid']}")
        print(f"Errors: {validation['errors']}")
        print(f"Warnings: {validation['warnings']}")
        
        if not validation['valid']:
            print("✗ Validation failed")
            return False
        
        # Test extraction
        print("\n=== Data Extraction Test ===")
        extracted_data = service.extract_personal_values_from_mongo(mongo_data)
        
        print(f"Form ID: {extracted_data['formId']}")
        print(f"Form Name: {extracted_data['formName']}")
        print(f"Client Name: {extracted_data['clientInfo']['name']}")
        print(f"Scores count: {len(extracted_data['scores'])}")
        
        # Show top 3 scores
        top_values = service.get_top_n_values(extracted_data['scores'], 3)
        print("\nTop 3 values:")
        for i, (key, score) in enumerate(top_values, 1):
            print(f"  {i}. {key}: {score}")
        
        # Test key mapping
        print("\n=== Key Mapping Test ===")
        scores = extracted_data['scores']
        interpretation_dimensions = service.interpretation_data['results']['dimensions']
        
        print(f"MongoDB keys: {list(scores.keys())}")
        print(f"Interpretation keys: {list(interpretation_dimensions.keys())}")
        
        print("\nMapping check:")
        mapping_success = True
        for mongo_key in scores.keys():
            interpretation_key = service.key_mapping.get(mongo_key)
            if interpretation_key:
                if interpretation_key in interpretation_dimensions:
                    print(f"✓ {mongo_key} → {interpretation_key}")
                else:
                    print(f"✗ {mongo_key} → {interpretation_key} (not found)")
                    mapping_success = False
            else:
                print(f"✗ {mongo_key} → No mapping")
                mapping_success = False
        
        if mapping_success:
            print("✓ All key mappings successful")
        else:
            print("✗ Some key mappings failed")
            return False
        
        print("\n🎉 All tests passed!")
        print("\nService is ready for integration with:")
        print(f"- MongoDB payload: {mongo_data.get('name')}")
        print(f"- Top 3 values: {[key for key, _ in top_values]}")
        print(f"- Form: {extracted_data['formName']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == '__main__':
    test_service()