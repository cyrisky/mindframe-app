#!/usr/bin/env python3
"""
Script untuk mengecek apakah template variables sudah ter-replace dengan benar di PDF
"""

import PyPDF2
import sys

def extract_pdf_text(pdf_path):
    """
    Extract text from PDF file
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
            
            return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def check_template_variables(text):
    """
    Check if template variables are properly replaced
    """
    print("🔍 Checking Template Variables")
    print("=" * 50)
    
    # Variables that should NOT be present (unreplaced template variables)
    template_vars_to_check = [
        "{{ client_name }}",
        "{{ client_email }}", 
        "{{ test_date }}",
        "{{ form_name }}",
        "{{ dimension.title }}",
        "{{ dimension.score }}",
        "{{ dimension.level_label }}",
        "{{ dimension.interpretation }}",
        "{{ rec.title }}",
        "{{ rec.description }}",
        "{% for",
        "{% if",
        "{% endfor %}",
        "{% endif %}"
    ]
    
    # Values that SHOULD be present (properly replaced)
    expected_values = [
        "Cris Bawana",
        "cris.bawana@example.com",
        "Tes Kepribadian Big Five"
    ]
    
    print("❌ Checking for unreplaced template variables:")
    unreplaced_found = False
    for var in template_vars_to_check:
        if var in text:
            print(f"   FOUND: {var}")
            unreplaced_found = True
    
    if not unreplaced_found:
        print("   ✅ No unreplaced template variables found!")
    
    print("\n✅ Checking for expected values:")
    values_found = 0
    for value in expected_values:
        if value in text:
            print(f"   FOUND: {value}")
            values_found += 1
        else:
            print(f"   MISSING: {value}")
    
    print(f"\n📊 Summary:")
    print(f"   Expected values found: {values_found}/{len(expected_values)}")
    print(f"   Unreplaced variables: {'Yes' if unreplaced_found else 'No'}")
    
    # Show first 500 characters of extracted text
    print(f"\n📄 First 500 characters of PDF text:")
    print("-" * 50)
    print(text[:500])
    print("-" * 50)
    
    return not unreplaced_found and values_found == len(expected_values)

def main():
    pdf_path = "test_template_fix.pdf"
    
    print("🔍 PDF Template Variable Checker")
    print("=" * 50)
    print(f"📄 Checking PDF: {pdf_path}")
    
    text = extract_pdf_text(pdf_path)
    
    if text is None:
        print("❌ Failed to extract text from PDF")
        sys.exit(1)
    
    print(f"📏 Extracted text length: {len(text)} characters")
    
    success = check_template_variables(text)
    
    if success:
        print("\n🎉 SUCCESS: Template variables are properly replaced!")
    else:
        print("\n❌ ISSUE: Some template variables are not properly replaced")
    
    return success

if __name__ == "__main__":
    main()