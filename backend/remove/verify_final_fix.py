#!/usr/bin/env python3
"""Verify that the final fix works correctly"""

import PyPDF2
import re
import os

def analyze_final_pdf():
    """Analyze the final fixed PDF"""
    pdf_path = "test_complete_personal_values_report_FIXED.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return False
    
    print(f"🔍 ANALYZING FINAL FIXED PDF: {pdf_path}")
    print("=" * 60)
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            print(f"Total pages: {len(pdf_reader.pages)}")
            
            full_text = ""
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                full_text += page_text
                print(f"Page {page_num}: {len(page_text)} characters")
                
                # Check what's on each page
                if "Kemandirian" in page_text:
                    print(f"  ✅ Page {page_num}: Contains Kemandirian")
                if "Keamanan" in page_text:
                    print(f"  ✅ Page {page_num}: Contains Keamanan")
                if "Stimulasi" in page_text:
                    print(f"  ✅ Page {page_num}: Contains Stimulasi")
            
            print("\n📊 CONTENT ANALYSIS:")
            print("-" * 40)
            
            # Check dimensions
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
            
            # Count detailed sections
            manifestation_count = len(re.findall(r'Bagaimana Ini Termanifestasi dalam Hidup Anda', full_text))
            strength_count = len(re.findall(r'Kekuatan & Tantangan Potensial', full_text))
            
            print(f"\n📋 SECTION COUNTS:")
            print(f"  Manifestation sections: {manifestation_count}/3")
            print(f"  Strength sections: {strength_count}/3")
            
            # Check for rank badges
            rank_1 = len(re.findall(r'1\s*Kemandirian', full_text))
            rank_2 = len(re.findall(r'2\s*Keamanan', full_text))
            rank_3 = len(re.findall(r'3\s*Stimulasi', full_text))
            
            print(f"\n🏆 RANK BADGES:")
            print(f"  Rank 1 (Kemandirian): {rank_1}")
            print(f"  Rank 2 (Keamanan): {rank_2}")
            print(f"  Rank 3 (Stimulasi): {rank_3}")
            
            # Overall assessment
            print("\n🎯 FINAL ASSESSMENT:")
            print("=" * 40)
            
            success = True
            issues = []
            
            if len(found_dimensions) != 3:
                success = False
                issues.append(f"Only {len(found_dimensions)}/3 dimensions found")
            
            if manifestation_count != 3:
                success = False
                issues.append(f"Only {manifestation_count}/3 manifestation sections")
            
            if strength_count != 3:
                success = False
                issues.append(f"Only {strength_count}/3 strength sections")
            
            if rank_3 == 0:
                success = False
                issues.append("Rank 3 badge missing")
            
            if success:
                print("🎉 SUCCESS: All 3 dimensions are properly displayed!")
                print("✅ The fix is working correctly.")
                print("✅ All manifestation sections present.")
                print("✅ All strength sections present.")
                print("✅ All rank badges present.")
                return True
            else:
                print("❌ ISSUES FOUND:")
                for issue in issues:
                    print(f"  - {issue}")
                return False
                
    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        return False

def compare_with_original():
    """Compare with the original broken PDF"""
    print("\n" + "=" * 60)
    print("COMPARING WITH ORIGINAL PDF")
    print("=" * 60)
    
    original_pdf = "test_complete_personal_values_report.pdf"
    
    if os.path.exists(original_pdf):
        print(f"\n📄 Original PDF: {original_pdf}")
        
        with open(original_pdf, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            full_text = ""
            for page in pdf_reader.pages:
                full_text += page.extract_text()
            
            manifestation_count = len(re.findall(r'Bagaimana Ini Termanifestasi dalam Hidup Anda', full_text))
            strength_count = len(re.findall(r'Kekuatan & Tantangan Potensial', full_text))
            rank_3 = len(re.findall(r'3\s*Stimulasi', full_text))
            
            print(f"  Manifestations: {manifestation_count}/3")
            print(f"  Strengths: {strength_count}/3")
            print(f"  Rank 3 badges: {rank_3}")
            
            if manifestation_count < 3 or strength_count < 3 or rank_3 == 0:
                print("  ❌ Original PDF was indeed broken")
            else:
                print("  ✅ Original PDF was actually working")
    else:
        print(f"❌ Original PDF not found: {original_pdf}")

def main():
    """Main verification function"""
    success = analyze_final_pdf()
    compare_with_original()
    
    print("\n" + "=" * 60)
    print("FINAL VERDICT:")
    print("=" * 60)
    
    if success:
        print("🎉 THE FIX IS SUCCESSFUL!")
        print("✅ All 3 dimensions are now properly displayed in the PDF.")
        print("✅ The CSS changes resolved the page break issues.")
        print("\n📋 Changes made:")
        print("  - Changed .top-values from 'display: grid' to 'display: block'")
        print("  - Added 'page-break-after: auto' to .value-card")
        print("  - Added 'margin-bottom: 25px' to .value-card")
        print("  - Added '.value-card:last-child { page-break-after: avoid; }'")
    else:
        print("❌ THE FIX NEEDS MORE WORK")
        print("🔧 Additional debugging may be required.")

if __name__ == '__main__':
    main()