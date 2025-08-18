#!/usr/bin/env python3
"""Detailed analysis of PDF content structure"""

import PyPDF2
import re

def detailed_pdf_analysis(pdf_path):
    """Perform detailed analysis of PDF content"""
    print(f"\n📄 DETAILED ANALYSIS: {pdf_path}")
    print("=" * 60)
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            print(f"Total pages: {len(pdf_reader.pages)}")
            
            full_text = ""
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                full_text += page_text
                print(f"\nPage {page_num} content length: {len(page_text)} characters")
                
                # Look for value cards on this page
                if "Kemandirian" in page_text:
                    print(f"  ✅ Page {page_num}: Contains Kemandirian")
                if "Keamanan" in page_text:
                    print(f"  ✅ Page {page_num}: Contains Keamanan")
                if "Stimulasi" in page_text:
                    print(f"  ✅ Page {page_num}: Contains Stimulasi")
            
            # Analyze the structure
            print("\n🔍 CONTENT STRUCTURE ANALYSIS:")
            print("-" * 40)
            
            # Count value cards by looking for rank patterns
            rank_1_matches = len(re.findall(r'1\s*Kemandirian', full_text))
            rank_2_matches = len(re.findall(r'2\s*Keamanan', full_text))
            rank_3_matches = len(re.findall(r'3\s*Stimulasi', full_text))
            
            print(f"Rank 1 (Kemandirian) cards: {rank_1_matches}")
            print(f"Rank 2 (Keamanan) cards: {rank_2_matches}")
            print(f"Rank 3 (Stimulasi) cards: {rank_3_matches}")
            
            # Look for manifestation sections
            manifestation_pattern = r'Bagaimana Ini Termanifestasi dalam Hidup Anda'
            manifestations = re.findall(manifestation_pattern, full_text)
            print(f"Manifestation sections: {len(manifestations)}")
            
            # Look for strength sections
            strength_pattern = r'Kekuatan & Tantangan Potensial'
            strengths = re.findall(strength_pattern, full_text)
            print(f"Strength sections: {len(strengths)}")
            
            # Extract content around each dimension
            print("\n📋 DIMENSION CONTENT PREVIEW:")
            print("-" * 40)
            
            dimensions = [
                ("Kemandirian (Self-Direction)", "Kemandirian"),
                ("Keamanan (Security)", "Keamanan"),
                ("Stimulasi (Stimulation)", "Stimulasi")
            ]
            
            for full_name, short_name in dimensions:
                if full_name in full_text:
                    # Find the position and extract surrounding context
                    pos = full_text.find(full_name)
                    context_start = max(0, pos - 50)
                    context_end = min(len(full_text), pos + 200)
                    context = full_text[context_start:context_end].replace('\n', ' ').strip()
                    print(f"\n{short_name}: ...{context}...")
                else:
                    print(f"\n{short_name}: ❌ NOT FOUND")
            
            # Check if there are any truncation issues
            print("\n⚠️  POTENTIAL ISSUES:")
            print("-" * 40)
            
            if len(manifestations) < 3:
                print(f"❌ Only {len(manifestations)} manifestation sections found (expected 3)")
            else:
                print("✅ All manifestation sections present")
                
            if len(strengths) < 3:
                print(f"❌ Only {len(strengths)} strength sections found (expected 3)")
            else:
                print("✅ All strength sections present")
                
            if rank_3_matches == 0:
                print("❌ Rank 3 (Stimulasi) card might not be properly rendered")
            else:
                print("✅ All rank cards appear to be present")
                
    except Exception as e:
        print(f"Error analyzing PDF: {e}")

def compare_both_pdfs():
    """Compare both PDFs in detail"""
    pdfs = [
        "test_complete_personal_values_report.pdf",
        "test_complete_personal_values_report_FIXED.pdf"
    ]
    
    for pdf in pdfs:
        try:
            detailed_pdf_analysis(pdf)
        except FileNotFoundError:
            print(f"\n❌ File not found: {pdf}")
        except Exception as e:
            print(f"\n❌ Error analyzing {pdf}: {e}")

if __name__ == '__main__':
    compare_both_pdfs()