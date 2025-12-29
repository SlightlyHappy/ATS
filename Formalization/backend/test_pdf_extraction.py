#!/usr/bin/env python3
"""
Test script to diagnose PDF text extraction issues
"""

import os
import sys

def test_dependencies():
    """Test if all required dependencies are available"""
    print("🔍 Testing PDF extraction dependencies...")
    
    # Test PyMuPDF (fitz)
    try:
        import fitz
        print("✅ PyMuPDF (fitz) is available")
        print(f"   Version: {fitz.version}")
    except ImportError as e:
        print(f"❌ PyMuPDF (fitz) not available: {e}")
        return False
    
    # Test PIL/Pillow
    try:
        from PIL import Image
        print("✅ PIL/Pillow is available")
    except ImportError as e:
        print(f"❌ PIL/Pillow not available: {e}")
        return False
    
    # Test pytesseract
    try:
        import pytesseract
        print("✅ pytesseract is available")
        
        # Test if Tesseract executable is available
        try:
            version = pytesseract.get_tesseract_version()
            print(f"   Tesseract version: {version}")
        except Exception as e:
            print(f"⚠️ pytesseract is installed but Tesseract executable might not be available: {e}")
            print("   This will cause OCR to fail, but regular PDF text extraction should still work")
            
    except ImportError as e:
        print(f"❌ pytesseract not available: {e}")
        print("   OCR won't work, but regular PDF text extraction should still work")
    
    return True

def test_pdf_extraction(pdf_path):
    """Test PDF text extraction on a specific file"""
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print(f"\n🔍 Testing PDF extraction on: {pdf_path}")
    
    try:
        import fitz
        doc = fitz.open(pdf_path)
        print(f"✅ PDF opened successfully")
        print(f"   Pages: {len(doc)}")
        
        total_text = ""
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            total_text += page_text
            print(f"   Page {page_num + 1}: {len(page_text)} characters")
            if len(page_text) > 0:
                print(f"      Sample: {repr(page_text[:100])}")
        
        print(f"\n📊 Total extracted text: {len(total_text)} characters")
        if len(total_text) > 0:
            print(f"📝 Text preview (first 500 chars):")
            print("-" * 50)
            print(total_text[:500])
            print("-" * 50)
        
        doc.close()
        
        if len(total_text.strip()) < 20:
            print("\n⚠️ Extracted text is too short, this would cause the upload to fail")
            print("   Recommendation: The PDF might contain images or non-extractable text")
            print("   Try OCR or convert the PDF to a text-based format")
        else:
            print(f"\n✅ Text extraction successful - {len(total_text.strip())} characters extracted")
            
    except Exception as e:
        print(f"❌ Error during PDF extraction: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    print("🚀 PDF Text Extraction Diagnostic Tool")
    print("=" * 50)
    
    # Test dependencies first
    if not test_dependencies():
        print("\n❌ Some dependencies are missing. Please install them:")
        print("   pip install PyMuPDF pillow pytesseract")
        sys.exit(1)
    
    # Test with a sample PDF if provided
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        test_pdf_extraction(pdf_path)
    else:
        print("\n💡 Usage: python test_pdf_extraction.py <path_to_pdf>")
        print("   Example: python test_pdf_extraction.py sample_resume.pdf")
        
        # Look for any PDF files in common locations
        common_paths = [
            "uploads/",
            "../sample_resumes/",
            "sample_resumes/",
            "./"
        ]
        
        found_pdfs = []
        for path in common_paths:
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.lower().endswith('.pdf'):
                        found_pdfs.append(os.path.join(path, file))
        
        if found_pdfs:
            print(f"\n📁 Found {len(found_pdfs)} PDF files:")
            for pdf in found_pdfs[:5]:  # Show first 5
                print(f"   {pdf}")
            
            if len(found_pdfs) > 5:
                print(f"   ... and {len(found_pdfs) - 5} more")
            
            print(f"\n💡 To test extraction on the first PDF:")
            print(f"   python test_pdf_extraction.py \"{found_pdfs[0]}\"")
