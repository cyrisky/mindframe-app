#!/usr/bin/env python3
"""Debug script to analyze dimension ordering in JSON file"""

import json

def analyze_dimensions():
    """Analyze the dimensions in the JSON file"""
    json_path = '/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/ai/interpretation-data/interpretation-personal-values.json'
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    dimensions = data['results']['dimensions']
    top_n = data['results']['topN']
    
    print(f"Top N: {top_n}")
    print(f"Total dimensions: {len(dimensions)}")
    print("\nAll dimension keys in order:")
    for i, key in enumerate(dimensions.keys(), 1):
        print(f"{i}. {key}: {dimensions[key]['title']}")
    
    print("\nFirst 3 dimensions that would be selected by current logic:")
    first_three = list(dimensions.keys())[:top_n]
    for i, key in enumerate(first_three, 1):
        print(f"{i}. {key}: {dimensions[key]['title']}")
    
    # Check if there are any issues with the dimensions
    print("\nChecking for potential issues:")
    
    # Check if any dimension has missing fields
    for key, dimension in dimensions.items():
        missing_fields = []
        required_fields = ['title', 'description', 'manifestation', 'strengthChallenges']
        
        for field in required_fields:
            if field not in dimension or not dimension[field]:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"⚠ {key} missing fields: {missing_fields}")
        else:
            print(f"✓ {key} has all required fields")
    
    # Simulate the template data preparation
    print("\n" + "="*50)
    print("SIMULATING TEMPLATE DATA PREPARATION")
    print("="*50)
    
    top_values = []
    dimension_keys = list(dimensions.keys())[:top_n]
    
    print(f"Selected dimension keys: {dimension_keys}")
    
    for key in dimension_keys:
        dimension = dimensions[key]
        top_values.append({
            'key': key,
            'title': dimension['title'],
            'description': dimension['description'],
            'manifestation': dimension['manifestation'],
            'strengthChallenges': dimension['strengthChallenges']
        })
    
    print(f"\nPrepared top_values count: {len(top_values)}")
    for i, value in enumerate(top_values, 1):
        print(f"{i}. {value['title']}")
        print(f"   Key: {value['key']}")
        print(f"   Description length: {len(value['description'])} chars")
        print(f"   Manifestation length: {len(value['manifestation'])} chars")
        print(f"   StrengthChallenges length: {len(value['strengthChallenges'])} chars")
        print()

if __name__ == '__main__':
    analyze_dimensions()