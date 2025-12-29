"""
File Processing System
Handles PDF, DOCX, and Image file processing with OCR support
"""

import os
import io
import logging
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path

# File processing imports
import fitz  # PyMuPDF
from docx import Document
from PIL import Image
import pytesseract

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tesseract configuration
TESSERACT_CONFIG = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?;:()[]{}"\'-/@#$%^&*+=_|\\<>~ '

class FileProcessor:
    """Handles file processing for resume analysis"""
    
    def __init__(self):
        """Initialize file processor"""
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE', 10485760))  # 10MB
        self.allowed_extensions = {'.pdf', '.docx', '.png', '.jpg', '.jpeg'}
        
        # Ensure temp directories exist
        self.upload_folder = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
        self.processed_folder = os.getenv('PROCESSED_FOLDER', '/tmp/processed')
        
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.processed_folder, exist_ok=True)
        
        logger.info("File processor initialized")
    
    def validate_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Validate uploaded file"""
        try:
            file_ext = Path(filename).suffix.lower()
            file_size = len(file_content)
            
            # Check file extension
            if file_ext not in self.allowed_extensions:
                return {
                    'valid': False,
                    'error': f'Unsupported file type: {file_ext}. Allowed: {", ".join(self.allowed_extensions)}'
                }
            
            # Check file size
            if file_size > self.max_file_size:
                return {
                    'valid': False,
                    'error': f'File size ({file_size} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)'
                }
            
            # Basic malware check (simple magic number validation)
            if not self._validate_file_header(file_content, file_ext):
                return {
                    'valid': False,
                    'error': 'File appears to be corrupted or invalid'
                }
            
            return {
                'valid': True,
                'file_type': file_ext,
                'file_size': file_size
            }
            
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return {'valid': False, 'error': f'Validation error: {str(e)}'}
    
    def _validate_file_header(self, file_content: bytes, file_ext: str) -> bool:
        """Validate file header/magic numbers"""
        try:
            if file_ext == '.pdf':
                return file_content.startswith(b'%PDF-')
            elif file_ext == '.docx':
                return file_content.startswith(b'PK')  # ZIP-based format
            elif file_ext in ['.jpg', '.jpeg']:
                return file_content.startswith(b'\xff\xd8\xff')
            elif file_ext == '.png':
                return file_content.startswith(b'\x89PNG\r\n\x1a\n')
            
            return True  # Default to valid if we can't check
            
        except Exception as e:
            logger.error(f"Header validation error: {str(e)}")
            return False
    
    def process_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process file and extract text content"""
        try:
            # Validate file first
            validation = self.validate_file(file_content, filename)
            if not validation['valid']:
                return validation
            
            file_ext = validation['file_type']
            
            # Extract text based on file type
            if file_ext == '.pdf':
                text_content = self._process_pdf(file_content)
            elif file_ext == '.docx':
                text_content = self._process_docx(file_content)
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                text_content = self._process_image(file_content)
            else:
                return {'valid': False, 'error': f'Unsupported file type: {file_ext}'}
            
            if not text_content or len(text_content.strip()) < 50:
                return {
                    'valid': False,
                    'error': 'Insufficient text content extracted from file'
                }
            
            # Clean and normalize text
            cleaned_content = self._clean_text(text_content)
            
            return {
                'valid': True,
                'filename': filename,
                'file_type': file_ext,
                'file_size': validation['file_size'],
                'content': cleaned_content,
                'raw_content': text_content,
                'word_count': len(cleaned_content.split())
            }
            
        except Exception as e:
            logger.error(f"File processing error: {str(e)}")
            return {'valid': False, 'error': f'Processing error: {str(e)}'}
    
    def _process_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Open PDF with PyMuPDF
                doc = fitz.open(temp_file_path)
                text_content = ""
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text_content += page.get_text()
                    text_content += "\n\n"  # Add page separator
                
                doc.close()
                return text_content.strip()
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except Exception as e:
            logger.error(f"PDF processing error: {str(e)}")
            raise Exception(f"Failed to process PDF: {str(e)}")
    
    def _process_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Open DOCX with python-docx
                doc = Document(temp_file_path)
                text_content = ""
                
                # Extract text from paragraphs
                for paragraph in doc.paragraphs:
                    text_content += paragraph.text + "\n"
                
                # Extract text from tables
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            text_content += cell.text + " "
                        text_content += "\n"
                
                return text_content.strip()
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except Exception as e:
            logger.error(f"DOCX processing error: {str(e)}")
            raise Exception(f"Failed to process DOCX: {str(e)}")
    
    def _process_image(self, file_content: bytes) -> str:
        """Extract text from image using OCR"""
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(file_content))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Perform OCR with Tesseract
            text_content = pytesseract.image_to_string(image, config=TESSERACT_CONFIG)
            
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"Image OCR error: {str(e)}")
            raise Exception(f"Failed to process image: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        try:
            # Remove excessive whitespace
            lines = [line.strip() for line in text.split('\n')]
            lines = [line for line in lines if line]  # Remove empty lines
            
            # Join lines and normalize spacing
            cleaned = ' '.join(lines)
            
            # Remove excessive spaces
            import re
            cleaned = re.sub(r'\s+', ' ', cleaned)
            
            return cleaned.strip()
            
        except Exception as e:
            logger.error(f"Text cleaning error: {str(e)}")
            return text  # Return original text if cleaning fails
    
    def get_file_info(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Get basic file information without processing"""
        try:
            validation = self.validate_file(file_content, filename)
            
            if validation['valid']:
                return {
                    'filename': filename,
                    'file_type': validation['file_type'],
                    'file_size': validation['file_size'],
                    'size_mb': round(validation['file_size'] / 1024 / 1024, 2)
                }
            else:
                return validation
                
        except Exception as e:
            logger.error(f"File info error: {str(e)}")
            return {'valid': False, 'error': str(e)}

# Singleton instance
file_processor = FileProcessor()
