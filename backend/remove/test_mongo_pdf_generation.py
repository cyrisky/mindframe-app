#!/usr/bin/env python3
"""
Test PDF generation menggunakan data dari MongoDB payload
"""

import json
import os
from jinja2 import Environment, FileSystemLoader
import weasyprint
import PyPDF2
import re

def load_mongo_template_data():
    """Load template data yang sudah dimapping dari MongoDB"""
    with open("mongo_template_data.json", 'r', encoding='utf-8') as file:
        return json.load(file)

def render_template_with_mongo_data(template_data):
    """Render template menggunakan data dari MongoDB"""
    
    # Setup Jinja2 environment
    template_dir = "templates"
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("personal_values_report_template.html")
    
    # Prepare data untuk template (sama seperti yang digunakan di test sebelumnya)
    client_info = {
        "name": "Jhon Doe",
        "email": "example@mail.com", 
        "phone": "628112345678",
        "test_date": "30 Juli 2025",
        "order_number": "2025730144807"
    }
    
    # Combine dengan template data dari MongoDB
    full_template_data = {
        **template_data,
        "client_info": client_info
    }
    
    print("🎨 RENDERING TEMPLATE WITH MONGO DATA:")
    print(f"  Client: {client_info['name']}")
    print(f"  Top N: {template_data['top_n']}")
    print(f"  Number of values: {len(template_data['top_values'])}")
    
    for i, value in enumerate(template_data['top_values'], 1):
        print(f"    {i}. {value['title']} (score: {value['score']})")
    
    # Render template
    rendered_html = template.render(**full_template_data)
    
    return rendered_html

def generate_pdf_from_mongo_data(html_content, output_filename):
    """Generate PDF dari HTML content"""
    
    print(f"\n📄 GENERATING PDF: {output_filename}")
    
    try:
        # Generate PDF menggunakan WeasyPrint
        pdf_document = weasyprint.HTML(string=html_content)
        pdf_document.write_pdf(output_filename)
        
        print(f"  ✅ PDF berhasil dibuat: {output_filename}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error generating PDF: {e}")
        return False

def analyze_generated_pdf(pdf_filename):
    """Analisis PDF yang dihasilkan untuk memastikan semua konten ada"""
    
    print(f"\n🔍 ANALYZING GENERATED PDF: {pdf_filename}")
    
    if not os.path.exists(pdf_filename):
        print(f"  ❌ File not found: {pdf_filename}")
        return False
    
    try:
        with open(pdf_filename, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            print(f"  📊 Total pages: {len(pdf_reader.pages)}")
            
            # Extract all text
            full_text = ""
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                full_text += page_text
                print(f"  Page {page_num}: {len(page_text)} characters")
            
            # Check for expected dimensions
            expected_dimensions = [
                "Universalisme (Universalism)",
                "Keamanan (Security)", 
                "Kemandirian (Self-Direction)"
            ]
            
            print("\n  📋 CONTENT VERIFICATION:")
            
            found_dimensions = []
            for dim in expected_dimensions:
                if dim in full_text:
                    found_dimensions.append(dim)
                    print(f"    ✅ Found: {dim}")
                else:
                    print(f"    ❌ Missing: {dim}")
            
            # Count sections
            manifestation_count = len(re.findall(r'Bagaimana Ini Termanifestasi dalam Hidup Anda', full_text))
            strength_count = len(re.findall(r'Kekuatan & Tantangan Potensial', full_text))
            
            print(f"\n  📊 SECTION COUNTS:")
            print(f"    Manifestation sections: {manifestation_count}/3")
            print(f"    Strength sections: {strength_count}/3")
            
            # Check for rank badges
            rank_1 = len(re.findall(r'1\s*Universalisme', full_text))
            rank_2 = len(re.findall(r'2\s*Keamanan', full_text))
            rank_3 = len(re.findall(r'3\s*Kemandirian', full_text))
            
            print(f"\n  🏆 RANK BADGES:")
            print(f"    Rank 1 (Universalisme): {rank_1}")
            print(f"    Rank 2 (Keamanan): {rank_2}")
            print(f"    Rank 3 (Kemandirian): {rank_3}")
            
            # Overall assessment
            success = (
                len(found_dimensions) == 3 and
                manifestation_count == 3 and
                strength_count == 3 and
                rank_1 > 0 and rank_2 > 0 and rank_3 > 0
            )
            
            print(f"\n  🎯 OVERALL RESULT: {'✅ SUCCESS' if success else '❌ ISSUES FOUND'}")
            
            return success
            
    except Exception as e:
        print(f"  ❌ Error analyzing PDF: {e}")
        return False

def compare_with_original_test_data():
    """Bandingkan dengan data test original untuk melihat perbedaan"""
    
    print("\n🔄 COMPARISON WITH ORIGINAL TEST DATA:")
    print("=" * 50)
    
    # Load original interpretation data
    interpretation_path = "/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/ai/interpretation-data/interpretation-personal-values.json"
    
    with open(interpretation_path, 'r', encoding='utf-8') as file:
        original_data = json.load(file)
    
    # Load mongo template data
    mongo_data = load_mongo_template_data()
    
    print("\nOriginal test data (top 3):")
    original_dimensions = original_data["results"]["dimensions"]
    original_keys = list(original_dimensions.keys())[:3]  # Ambil 3 pertama
    
    for i, key in enumerate(original_keys, 1):
        title = original_dimensions[key]["title"]
        print(f"  {i}. {title} (key: {key})")
    
    print("\nMongoDB data (top 3):")
    for value in mongo_data["top_values"]:
        print(f"  {value['rank']}. {value['title']} (score: {value['score']}, key: {value['key']})")
    
    print("\nKey differences:")
    print("  - Original menggunakan data dummy/contoh")
    print("  - MongoDB menggunakan data real dari user 'Jhon Doe'")
    print("  - Ranking berbeda berdasarkan score aktual dari test")
    print("  - MongoDB: Universalisme (28) > Keamanan (27) > Kemandirian (23)")
    print("  - Original: Kemandirian > Keamanan > Stimulasi")

def save_html_for_debugging(html_content, filename="mongo_debug_template.html"):
    """Save HTML untuk debugging"""
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)
    print(f"  💾 HTML saved for debugging: {filename}")

def main():
    """Main function"""
    print("🧪 TESTING PDF GENERATION WITH MONGODB DATA")
    print("=" * 60)
    
    try:
        # Load template data dari MongoDB
        template_data = load_mongo_template_data()
        
        # Render template
        html_content = render_template_with_mongo_data(template_data)
        
        # Save HTML untuk debugging
        save_html_for_debugging(html_content)
        
        # Generate PDF
        pdf_filename = "mongo_personal_values_report.pdf"
        pdf_success = generate_pdf_from_mongo_data(html_content, pdf_filename)
        
        if pdf_success:
            # Analyze PDF
            analysis_success = analyze_generated_pdf(pdf_filename)
            
            # Compare with original
            compare_with_original_test_data()
            
            print("\n" + "=" * 60)
            print("📋 FINAL SUMMARY:")
            print("=" * 60)
            
            if analysis_success:
                print("🎉 SUCCESS: PDF generation dengan MongoDB data berhasil!")
                print("✅ Semua 3 dimensi ditampilkan dengan lengkap")
                print("✅ Template system bekerja dengan data real dari MongoDB")
                print("✅ Mapping dari payload MongoDB ke interpretasi berhasil")
                
                print("\n📊 Generated content:")
                for value in template_data['top_values']:
                    print(f"  Rank {value['rank']}: {value['title']} (score: {value['score']})")
                    
            else:
                print("❌ ISSUES: Ada masalah dengan PDF generation")
                print("🔧 Perlu debugging lebih lanjut")
                
        else:
            print("❌ FAILED: PDF generation gagal")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()