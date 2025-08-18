#!/usr/bin/env python3
"""
Script untuk menghubungkan payload MongoDB dengan sistem interpretasi Personal Values
"""

import json
import os
from typing import Dict, List, Tuple, Any

def load_mongo_payload() -> Dict[str, Any]:
    """Load payload MongoDB example"""
    mongo_path = "/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/ai/interpretation-data/mongoData-example.json"
    
    with open(mongo_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def load_interpretation_data() -> Dict[str, Any]:
    """Load data interpretasi Personal Values"""
    interpretation_path = "/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/ai/interpretation-data/interpretation-personal-values.json"
    
    with open(interpretation_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def map_mongo_keys_to_interpretation_keys() -> Dict[str, str]:
    """Mapping key dari MongoDB ke key interpretasi"""
    return {
        "universalism": "universalism",
        "security": "security", 
        "benevolence": "benevolence",
        "hedonism": "hedonism",
        "achievement": "achievement",
        "power": "power",
        "self_direction": "selfDirection",  # Perhatikan perbedaan naming convention
        "Stimulation": "stimulation",      # Perhatikan kapitalisasi
        "tradition": "tradition",
        "conformity": "conformity"
    }

def extract_personal_values_from_mongo(mongo_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract data personal values dari payload MongoDB"""
    try:
        personal_values = mongo_data["testResult"]["personalValues"]
        
        extracted_data = {
            "formId": personal_values["formId"],
            "formName": personal_values["formName"],
            "topValue": personal_values["result"]["value"],
            "scores": personal_values["result"]["score"]
        }
        
        print("📊 DATA PERSONAL VALUES DARI MONGODB:")
        print(f"  Form ID: {extracted_data['formId']}")
        print(f"  Form Name: {extracted_data['formName']}")
        print(f"  Top Value: {extracted_data['topValue']}")
        print(f"  Scores: {extracted_data['scores']}")
        
        return extracted_data
        
    except KeyError as e:
        print(f"❌ Error extracting personal values: {e}")
        return {}

def get_top_n_values(scores: Dict[str, int], n: int = 3) -> List[Tuple[str, int]]:
    """Mendapatkan top N values berdasarkan score tertinggi"""
    # Sort berdasarkan score (descending)
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_scores[:n]

def map_to_interpretation_format(mongo_personal_values: Dict[str, Any], 
                                interpretation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Map data MongoDB ke format interpretasi"""
    
    scores = mongo_personal_values["scores"]
    key_mapping = map_mongo_keys_to_interpretation_keys()
    
    # Get top 3 values
    top_values = get_top_n_values(scores, 3)
    
    print("\n🏆 TOP 3 VALUES DARI MONGODB:")
    for i, (key, score) in enumerate(top_values, 1):
        print(f"  {i}. {key}: {score}")
    
    # Map ke format interpretasi
    mapped_data = {
        "testName": "personalValues",
        "testType": "top-n-dimension", 
        "results": {
            "topN": 3,
            "dimensions": {}
        },
        "sourceData": {
            "formId": mongo_personal_values["formId"],
            "formName": mongo_personal_values["formName"],
            "originalScores": scores,
            "topValue": mongo_personal_values["topValue"]
        }
    }
    
    # Map top 3 values ke interpretasi
    interpretation_dimensions = interpretation_data["results"]["dimensions"]
    
    print("\n🔄 MAPPING KE FORMAT INTERPRETASI:")
    
    for i, (mongo_key, score) in enumerate(top_values, 1):
        # Map key MongoDB ke key interpretasi
        interpretation_key = key_mapping.get(mongo_key)
        
        if interpretation_key and interpretation_key in interpretation_dimensions:
            mapped_data["results"]["dimensions"][interpretation_key] = {
                **interpretation_dimensions[interpretation_key],
                "score": score,
                "rank": i,
                "originalKey": mongo_key
            }
            print(f"  ✅ {i}. {mongo_key} → {interpretation_key} (score: {score})")
        else:
            print(f"  ❌ {i}. {mongo_key} → NOT FOUND in interpretation data")
    
    return mapped_data

def generate_template_data(mapped_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate data untuk template rendering"""
    
    top_n = mapped_data["results"]["topN"]
    dimensions = mapped_data["results"]["dimensions"]
    
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
    
    template_data = {
        "top_n": top_n,
        "top_values": top_values,
        "source_info": mapped_data["sourceData"]
    }
    
    print("\n📋 TEMPLATE DATA GENERATED:")
    print(f"  Top N: {template_data['top_n']}")
    print(f"  Number of top values: {len(template_data['top_values'])}")
    
    for value in template_data['top_values']:
        print(f"    Rank {value['rank']}: {value['title']} (score: {value['score']})")
    
    return template_data

def save_results(mapped_data: Dict[str, Any], template_data: Dict[str, Any]):
    """Save hasil mapping dan template data"""
    
    # Save mapped interpretation data
    with open("mongo_to_interpretation_mapped.json", 'w', encoding='utf-8') as file:
        json.dump(mapped_data, file, indent=2, ensure_ascii=False)
    
    # Save template data
    with open("mongo_template_data.json", 'w', encoding='utf-8') as file:
        json.dump(template_data, file, indent=2, ensure_ascii=False)
    
    print("\n💾 FILES SAVED:")
    print("  ✅ mongo_to_interpretation_mapped.json")
    print("  ✅ mongo_template_data.json")

def analyze_score_differences(mongo_data: Dict[str, Any], interpretation_data: Dict[str, Any]):
    """Analisis perbedaan score dan ranking"""
    
    mongo_scores = mongo_data["scores"]
    top_values = get_top_n_values(mongo_scores, 3)
    
    print("\n📈 ANALISIS SCORE:")
    print("=" * 50)
    
    print("\nTop 3 dari MongoDB:")
    for i, (key, score) in enumerate(top_values, 1):
        print(f"  {i}. {key}: {score}")
    
    print("\nSemua scores (sorted):")
    all_sorted = sorted(mongo_scores.items(), key=lambda x: x[1], reverse=True)
    for key, score in all_sorted:
        print(f"  {key}: {score}")
    
    # Analisis gap antara top values
    print("\nGap Analysis:")
    for i in range(len(top_values) - 1):
        current_score = top_values[i][1]
        next_score = top_values[i + 1][1]
        gap = current_score - next_score
        print(f"  Gap antara rank {i+1} dan {i+2}: {gap} points")

def main():
    """Main function"""
    print("🔗 CONNECTING MONGODB PAYLOAD TO PERSONAL VALUES INTERPRETATION")
    print("=" * 70)
    
    try:
        # Load data
        mongo_data = load_mongo_payload()
        interpretation_data = load_interpretation_data()
        
        # Extract personal values dari MongoDB
        mongo_personal_values = extract_personal_values_from_mongo(mongo_data)
        
        if not mongo_personal_values:
            print("❌ Failed to extract personal values from MongoDB")
            return
        
        # Analisis score
        analyze_score_differences(mongo_personal_values, interpretation_data)
        
        # Map ke format interpretasi
        mapped_data = map_to_interpretation_format(mongo_personal_values, interpretation_data)
        
        # Generate template data
        template_data = generate_template_data(mapped_data)
        
        # Save results
        save_results(mapped_data, template_data)
        
        print("\n🎉 SUCCESS: MongoDB payload berhasil dihubungkan dengan interpretasi Personal Values!")
        print("\n📋 SUMMARY:")
        print(f"  - Form ID: {mongo_personal_values['formId']}")
        print(f"  - Form Name: {mongo_personal_values['formName']}")
        print(f"  - Top Value: {mongo_personal_values['topValue']}")
        print(f"  - Top 3 mapped dimensions: {len(template_data['top_values'])}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()