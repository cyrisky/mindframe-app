#!/usr/bin/env python3
"""Analyze the debug PDFs to find which one works correctly"""

import PyPDF2
import re
import os

def analyze_pdf(pdf_path):
    """Analyze a single PDF file"""
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    print(f"\n📄 ANALYZING: {pdf_path}")
    print("=" * 50)
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            print(f"Total pages: {len(pdf_reader.pages)}")
            
            full_text = ""
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                full_text += page_text
                print(f"Page {page_num}: {len(page_text)} chars")
            
            # Count dimensions
            dimensions = [
                "Kemandirian (Self-Direction)",
                "Keamanan (Security)", 
                "Stimulasi (Stimulation)"
            ]
            
            found_dimensions = []
            for dim in dimensions:
                if dim in full_text:
                    found_dimensions.append(dim)
                    print(f"  ✅ Found: {dim}")
                else:
                    print(f"  ❌ Missing: {dim}")
            
            # Count manifestation and strength sections
            manifestation_count = len(re.findall(r'Bagaimana Ini Termanifestasi dalam Hidup Anda', full_text))
            strength_count = len(re.findall(r'Kekuatan & Tantangan Potensial', full_text))
            
            print(f"\nManifestations: {manifestation_count}/3")
            print(f"Strengths: {strength_count}/3")
            
            # Check for rank badges
            rank_1 = len(re.findall(r'1\s*Kemandirian', full_text))
            rank_2 = len(re.findall(r'2\s*Keamanan', full_text))
            rank_3 = len(re.findall(r'3\s*Stimulasi', full_text))
            
            print(f"Rank badges: 1={rank_1}, 2={rank_2}, 3={rank_3}")
            
            # Overall assessment
            if len(found_dimensions) == 3 and manifestation_count == 3 and strength_count == 3:
                print("🎉 STATUS: PERFECT - All 3 dimensions with complete content")
                return "perfect"
            elif len(found_dimensions) == 3:
                print("⚠️  STATUS: PARTIAL - All 3 dimensions found but incomplete content")
                return "partial"
            else:
                print(f"❌ STATUS: BROKEN - Only {len(found_dimensions)}/3 dimensions found")
                return "broken"
                
    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        return "error"

def main():
    """Analyze all debug PDFs"""
    print("🔍 ANALYZING DEBUG PDFs")
    print("=" * 60)
    
    pdfs = [
        "debug_original_template.pdf",
        "debug_modified_template.pdf", 
        "debug_forced_breaks.pdf"
    ]
    
    results = {}
    
    for pdf in pdfs:
        result = analyze_pdf(pdf)
        results[pdf] = result
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    
    perfect_pdfs = [pdf for pdf, result in results.items() if result == "perfect"]
    partial_pdfs = [pdf for pdf, result in results.items() if result == "partial"]
    broken_pdfs = [pdf for pdf, result in results.items() if result == "broken"]
    
    if perfect_pdfs:
        print(f"🎉 PERFECT PDFs: {', '.join(perfect_pdfs)}")
        print("   → Use this configuration for the fix!")
    elif partial_pdfs:
        print(f"⚠️  PARTIAL PDFs: {', '.join(partial_pdfs)}")
        print("   → These show all dimensions but may have content issues")
    
    if broken_pdfs:
        print(f"❌ BROKEN PDFs: {', '.join(broken_pdfs)}")
    
    # Recommend next steps
    print("\n📋 RECOMMENDATIONS:")
    if perfect_pdfs:
        print(f"1. Apply the configuration from {perfect_pdfs[0]} to fix the issue")
        print("2. Update the main template with the working CSS/structure")
    elif partial_pdfs:
        print(f"1. Investigate why {partial_pdfs[0]} has incomplete content")
        print("2. Check for CSS or page break issues")
    else:
        print("1. All configurations failed - investigate fundamental template issues")
        print("2. Check Jinja2 loop logic and data preparation")

if __name__ == '__main__':
    main()