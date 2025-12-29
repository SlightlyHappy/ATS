"""
Business logic services for HR ATS System
Extracted from the monolithic app.py
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

# File processing imports
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from docx import Document
import pandas as pd

from ai_processor import AgenticResumeProcessor, analyze_resume, process_legal_query

logger = logging.getLogger(__name__)

class ResumeProcessingService:
    """Service for handling resume processing operations"""
    
    def __init__(self, db_manager, storage_manager, ai_processor):
        self.db_manager = db_manager
        self.storage_manager = storage_manager
        self.ai_processor = ai_processor
    
    async def process_resume_upload(self, file, user_id: str) -> Dict[str, Any]:
        """Process uploaded resume file"""
        try:
            # Save file
            file_info = await self.storage_manager.save_file(file, user_id)
            
            # Extract text
            text_content = await self._extract_text_from_file(file_info['path'])
            
            # Store in database
            resume_data = {
                'user_id': user_id,
                'filename': file_info['filename'],
                'file_path': file_info['path'],
                'text_content': text_content,
                'upload_timestamp': datetime.utcnow(),
                'status': 'uploaded'
            }
            
            resume_id = await self.db_manager.store_resume(resume_data)
            
            return {
                'success': True,
                'resume_id': resume_id,
                'filename': file_info['filename'],
                'message': 'Resume uploaded successfully'
            }
            
        except Exception as e:
            logger.error(f"Resume upload failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def analyze_resume(self, resume_id: str, job_requirements: str) -> Dict[str, Any]:
        """Analyze resume against job requirements"""
        try:
            # Get resume data
            resume_data = await self.db_manager.get_resume(resume_id)
            if not resume_data:
                return {'success': False, 'error': 'Resume not found'}
            
            # Process with AI
            analysis_result = await self.ai_processor.analyze_resume(
                resume_data['text_content'],
                job_requirements
            )
            
            # Store analysis result
            analysis_data = {
                'resume_id': resume_id,
                'job_requirements': job_requirements,
                'analysis_result': analysis_result,
                'analysis_timestamp': datetime.utcnow(),
                'status': 'completed'
            }
            
            analysis_id = await self.db_manager.store_analysis(analysis_data)
            
            return {
                'success': True,
                'analysis_id': analysis_id,
                'result': analysis_result
            }
            
        except Exception as e:
            logger.error(f"Resume analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def batch_analyze_resumes(self, resume_ids: List[str], job_requirements: str, user_id: str) -> Dict[str, Any]:
        """Batch analyze multiple resumes"""
        try:
            results = []
            
            # Process each resume
            for resume_id in resume_ids:
                result = await self.analyze_resume(resume_id, job_requirements)
                results.append({
                    'resume_id': resume_id,
                    'result': result
                })
            
            # Store batch job info
            batch_data = {
                'user_id': user_id,
                'resume_ids': resume_ids,
                'job_requirements': job_requirements,
                'results': results,
                'batch_timestamp': datetime.utcnow(),
                'status': 'completed'
            }
            
            batch_id = await self.db_manager.store_batch_analysis(batch_data)
            
            return {
                'success': True,
                'batch_id': batch_id,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file formats"""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                return self._extract_text_from_pdf(file_path)
            elif file_extension in ['.doc', '.docx']:
                return self._extract_text_from_docx(file_path)
            elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
                return self._extract_text_from_image(file_path)
            elif file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {e}")
            raise
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using PyMuPDF"""
        text = ""
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX files"""
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\\n"
        return text
    
    def _extract_text_from_image(self, file_path: str) -> str:
        """Extract text from images using OCR"""
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text

class LegalQueryService:
    """Service for handling HR legal queries"""
    
    def __init__(self, ai_processor):
        self.ai_processor = ai_processor
    
    async def process_legal_query(self, query: str, user_id: str) -> Dict[str, Any]:
        """Process HR legal query"""
        try:
            # Process query with AI
            response = await self.ai_processor.process_legal_query(query)
            
            return {
                'success': True,
                'query': query,
                'response': response,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Legal query processing failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

class AdminService:
    """Service for admin operations"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            stats = await self.db_manager.get_system_stats()
            return {
                'success': True,
                'stats': stats,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_user_list(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """Get paginated user list"""
        try:
            users = await self.db_manager.get_users_paginated(page, limit)
            return {
                'success': True,
                'users': users,
                'page': page,
                'limit': limit,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get user list: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def delete_user_data(self, user_id: str) -> Dict[str, Any]:
        """Delete all user data (GDPR compliance)"""
        try:
            await self.db_manager.delete_user_data(user_id)
            return {
                'success': True,
                'message': f'User {user_id} data deleted successfully',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to delete user data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
