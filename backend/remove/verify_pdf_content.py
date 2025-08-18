#!/usr/bin/env python3
"""Verify PDF content to check if all 3 dimensions are present"""

import PyPDF2
import re

def extract_pdf_text(pdf_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def analyze_pdf_content(pdf_path):
    """Analyze PDF content for Personal Values dimensions"""
    print(f"Analyzing PDF: {pdf_path}")
    print("=" * 50)
    
    text = extract_pdf_text(pdf_path)
    if not text:
        print("❌ Could not extract text from PDF")
        return
    
    # Look for the three expected dimensions
    dimensions = [
        "Kemandirian (Self-Direction)",
        "Keamanan (Security)", 
        "Stimulasi (Stimulation)"
    ]
    
    found_dimensions = []
    
    for dimension in dimensions:
        if dimension in text:
            found_dimensions.append(dimension)
            print(f"✅ Found: {dimension}")
        else:
            print(f"❌ Missing: {dimension}")
    
    print(f"\nTotal dimensions found: {len(found_dimensions)}/3")
    
    # Look for rank badges
    rank_patterns = [r"\b1\b", r"\b2\b", r"\b3\b"]
    ranks_found = []
    
    for i, pattern in enumerate(rank_patterns, 1):
        if re.search(pattern, text):
            ranks_found.append(i)
    
    print(f"Rank badges found: {ranks_found}")
    
    # Look for value cards structure
    manifestation_count = text.count("Bagaimana Ini Termanifestasi")
    strength_count = text.count("Kekuatan & Tantangan")
    
    print(f"Manifestation sections: {manifestation_count}")
    print(f"Strength sections: {strength_count}")
    
    # Summary
    if len(found_dimensions) == 3:
        print("\n🎉 SUCCESS: All 3 dimensions are present in the PDF!")
    else:
        print(f"\n⚠️  ISSUE: Only {len(found_dimensions)} dimensions found")
    
    return len(found_dimensions) == 3

def compare_pdfs():
    """Compare original and fixed PDFs"""
    print("\n" + "=" * 60)
    print("COMPARING ORIGINAL VS FIXED PDF")
    print("=" * 60)
    
    original_pdf = "test_complete_personal_values_report.pdf"
    fixed_pdf = "test_complete_personal_values_report_FIXED.pdf"
    
    print("\n1. ORIGINAL PDF:")
    original_success = analyze_pdf_content(original_pdf)
    
    print("\n2. FIXED PDF:")
    fixed_success = analyze_pdf_content(fixed_pdf)
    
    print("\n" + "=" * 60)
    print("COMPARISON RESULT:")
    print("=" * 60)
    
    if fixed_success and not original_success:
        print("🎉 FIXED! The issue has been resolved.")
    elif fixed_success and original_success:
        print("✅ Both PDFs are working correctly.")
    elif not fixed_success and not original_success:
        print("❌ Issue still persists in both PDFs.")
    else:
        print("🤔 Unexpected result - original works but fixed doesn't.")

if __name__ == '__main__':
    compare_pdfs()