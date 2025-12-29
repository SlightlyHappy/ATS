#!/usr/bin/env python3
"""
AI Response Processing Layer
Transforms AI responses to match database schema requirements
Handles Railway PostgreSQL and Supabase compatibility
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class AIResponseProcessor:
    """
    Processing layer that transforms AI responses to match database schema
    Handles both Railway PostgreSQL and Supabase compatibility
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define the expected database schema mapping
        self.railway_schema = {
            'skills': 'jsonb',  # Railway uses jsonb
            'analysis_results': 'jsonb',
            'job_titles': 'jsonb',
            'companies': 'jsonb',
            'programming_languages': 'jsonb',
            'certifications': 'jsonb',
            'tags': 'jsonb'
        }
        
        self.supabase_schema = {
            'skills': 'jsonb',  # Supabase should also use jsonb
            'analysis_results': 'jsonb',  # Missing in Supabase - needs to be added
            'extracted_text': 'text',
            'upload_date': 'timestamp'
        }
    
    def process_ai_response_for_database(self, ai_result: Dict[str, Any], resume_id: str, user_id: str) -> Dict[str, Any]:
        """
        Process AI response and prepare it for database insertion
        Handles both Railway and Supabase compatibility
        """
        try:
            self.logger.info(f"Processing AI response for resume {resume_id}")
            
            # Extract core data from AI response
            processed_data = self._extract_core_fields(ai_result)
            
            # Add metadata
            processed_data.update({
                'id': resume_id,
                'user_id': user_id,
                'processing_status': 'completed',
                'processing_completed_at': datetime.utcnow().isoformat(),
                'ai_model_used': ai_result.get('metadata', {}).get('model_used', 'unknown'),
                'ai_processing_time': ai_result.get('processing_time', 0),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            })
            
            # Process for Railway PostgreSQL format
            railway_data = self._format_for_railway(processed_data)
            
            # Process for Supabase format
            supabase_data = self._format_for_supabase(processed_data)
            
            return {
                'railway_format': railway_data,
                'supabase_format': supabase_data,
                'raw_ai_response': ai_result
            }
            
        except Exception as e:
            self.logger.error(f"Error processing AI response: {e}")
            return self._create_fallback_response(resume_id, user_id, ai_result)
    
    def _extract_core_fields(self, ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and standardize core fields from AI response"""
        
        # Handle both unified format and agentic format
        if 'scores' in ai_result and 'analysis' in ai_result:
            # New agentic format
            return self._extract_from_agentic_format(ai_result)
        else:
            # Legacy unified format
            return self._extract_from_unified_format(ai_result)
    
    def _extract_from_agentic_format(self, ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract from new agentic format"""
        
        candidate_info = ai_result.get('candidate_info', {})
        scores = ai_result.get('scores', {})
        analysis = ai_result.get('analysis', {})
        skills_data = ai_result.get('skills', {})
        experience_data = ai_result.get('experience', {})
        assessment = ai_result.get('assessment', {})
        recommendations = ai_result.get('recommendations', {})
        
        return {
            # Candidate information
            'candidate_name': candidate_info.get('name', ''),
            'candidate_email': candidate_info.get('email', ''),
            'candidate_phone': candidate_info.get('phone', ''),
            
            # Scores (ensure they're integers)
            'overall_score': int(scores.get('overall_score', 0)),
            'technical_score': int(scores.get('technical_score', 0)),
            'experience_score': int(scores.get('experience_score', 0)),
            'education_score': int(scores.get('education_score', 0)),
            'role_fit_score': int(scores.get('role_fit_score', 0)),
            
            # Analysis data
            'experience_years': int(analysis.get('experience_years', 0)),
            'education_level': analysis.get('seniority_level', ''),
            
            # JSONB fields - ensure proper format
            'skills': json.dumps(skills_data.get('key_skills', [])),
            'job_titles': json.dumps(experience_data.get('job_titles', [])),
            'companies': json.dumps(experience_data.get('companies', [])),
            'programming_languages': json.dumps(skills_data.get('technical_skills', [])),
            'certifications': json.dumps(skills_data.get('certifications', [])),
            'tags': json.dumps(self._generate_tags(skills_data, analysis)),
            
            # AI feedback
            'ai_feedback': assessment.get('summary', '') or analysis.get('summary', ''),
            
            # Analysis results (complete AI response)
            'analysis_results': json.dumps(ai_result),
            
            # Additional fields
            'category': analysis.get('industry_fit', 'general'),
            'priority': 1,
            'is_shortlisted': False,
            'is_archived': False,
            'notes': '',
            'similarity_score': 0.0
        }
    
    def _extract_from_unified_format(self, ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract from legacy unified format"""
        
        return {
            # Candidate information
            'candidate_name': ai_result.get('candidate_name', ''),
            'candidate_email': ai_result.get('candidate_email', ''),
            'candidate_phone': ai_result.get('candidate_phone', ''),
            
            # Scores
            'overall_score': int(ai_result.get('overall_score', 0)),
            'technical_score': int(ai_result.get('technical_score', 0)),
            'experience_score': int(ai_result.get('experience_score', 0)),
            'education_score': int(ai_result.get('education_score', 0)),
            'role_fit_score': int(ai_result.get('role_fit_score', 0)),
            
            # Experience and education
            'experience_years': int(ai_result.get('experience_years', 0)),
            'education_level': ai_result.get('education_level', ''),
            
            # JSONB fields
            'skills': json.dumps(ai_result.get('skills', [])),
            'job_titles': json.dumps(ai_result.get('job_titles', [])),
            'companies': json.dumps(ai_result.get('companies', [])),
            'programming_languages': json.dumps(ai_result.get('programming_languages', [])),
            'certifications': json.dumps(ai_result.get('certifications', [])),
            'tags': json.dumps(ai_result.get('tags', [])),
            
            # AI feedback
            'ai_feedback': ai_result.get('ai_feedback', ''),
            
            # Analysis results
            'analysis_results': json.dumps(ai_result),
            
            # Additional fields
            'category': ai_result.get('category', 'general'),
            'priority': ai_result.get('priority', 1),
            'is_shortlisted': ai_result.get('is_shortlisted', False),
            'is_archived': ai_result.get('is_archived', False),
            'notes': ai_result.get('notes', ''),
            'similarity_score': float(ai_result.get('similarity_score', 0.0))
        }
    
    def _format_for_railway(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format data specifically for Railway PostgreSQL"""
        
        railway_data = processed_data.copy()
        
        # Ensure JSONB fields are properly formatted for PostgreSQL
        jsonb_fields = ['skills', 'job_titles', 'companies', 'programming_languages', 'certifications', 'tags', 'analysis_results']
        
        for field in jsonb_fields:
            if field in railway_data:
                value = railway_data[field]
                if isinstance(value, str):
                    # Already JSON string, ensure it's valid
                    try:
                        json.loads(value)
                    except json.JSONDecodeError:
                        railway_data[field] = json.dumps([])
                else:
                    # Convert to JSON string
                    railway_data[field] = json.dumps(value)
        
        # Ensure proper data types
        railway_data['overall_score'] = int(railway_data.get('overall_score', 0))
        railway_data['technical_score'] = int(railway_data.get('technical_score', 0))
        railway_data['experience_score'] = int(railway_data.get('experience_score', 0))
        railway_data['education_score'] = int(railway_data.get('education_score', 0))
        railway_data['role_fit_score'] = int(railway_data.get('role_fit_score', 0))
        railway_data['experience_years'] = int(railway_data.get('experience_years', 0))
        railway_data['similarity_score'] = float(railway_data.get('similarity_score', 0.0))
        
        return railway_data
    
    def _format_for_supabase(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format data specifically for Supabase"""
        
        supabase_data = processed_data.copy()
        
        # Supabase format - convert JSONB to proper JSON objects
        jsonb_fields = ['skills', 'job_titles', 'companies', 'programming_languages', 'certifications', 'tags']
        
        for field in jsonb_fields:
            if field in supabase_data and isinstance(supabase_data[field], str):
                try:
                    supabase_data[field] = json.loads(supabase_data[field])
                except json.JSONDecodeError:
                    supabase_data[field] = []
        
        # Handle analysis_results for Supabase (if column exists)
        if 'analysis_results' in supabase_data:
            try:
                if isinstance(supabase_data['analysis_results'], str):
                    supabase_data['analysis_results'] = json.loads(supabase_data['analysis_results'])
            except json.JSONDecodeError:
                supabase_data['analysis_results'] = {}
        
        return supabase_data
    
    def _generate_tags(self, skills_data: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Generate relevant tags from skills and analysis data"""
        
        tags = []
        
        # Add seniority level
        seniority = analysis.get('seniority_level', '')
        if seniority:
            tags.append(seniority)
        
        # Add industry fit
        industry = analysis.get('industry_fit', '')
        if industry:
            tags.append(industry.lower())
        
        # Add top skills as tags
        key_skills = skills_data.get('key_skills', [])
        if key_skills:
            tags.extend(key_skills[:3])  # Top 3 skills
        
        # Add technical skills
        tech_skills = skills_data.get('technical_skills', [])
        if tech_skills:
            tags.extend(tech_skills[:2])  # Top 2 technical skills
        
        return list(set(tags))  # Remove duplicates
    
    def _create_fallback_response(self, resume_id: str, user_id: str, ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback response when processing fails"""
        
        fallback_data = {
            'id': resume_id,
            'user_id': user_id,
            'candidate_name': '',
            'candidate_email': '',
            'candidate_phone': '',
            'overall_score': 60,
            'technical_score': 60,
            'experience_score': 60,
            'education_score': 60,
            'role_fit_score': 60,
            'experience_years': 0,
            'education_level': '',
            'skills': json.dumps([]),
            'job_titles': json.dumps([]),
            'companies': json.dumps([]),
            'programming_languages': json.dumps([]),
            'certifications': json.dumps([]),
            'tags': json.dumps(['processed']),
            'ai_feedback': 'Processing completed with limited parsing',
            'analysis_results': json.dumps(ai_result),
            'category': 'general',
            'priority': 1,
            'is_shortlisted': False,
            'is_archived': False,
            'notes': 'Processed with fallback method',
            'similarity_score': 0.0,
            'processing_status': 'completed_with_errors',
            'processing_completed_at': datetime.utcnow().isoformat(),
            'ai_model_used': 'unknown',
            'ai_processing_time': 0,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        return {
            'railway_format': fallback_data,
            'supabase_format': fallback_data,
            'raw_ai_response': ai_result
        }
    
    def validate_processed_data(self, processed_data: Dict[str, Any]) -> bool:
        """Validate that processed data meets requirements"""
        
        required_fields = [
            'id', 'user_id', 'overall_score', 'skills', 'analysis_results'
        ]
        
        for field in required_fields:
            if field not in processed_data:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        # Validate score ranges
        score_fields = ['overall_score', 'technical_score', 'experience_score', 'education_score', 'role_fit_score']
        for field in score_fields:
            if field in processed_data:
                score = processed_data[field]
                if not isinstance(score, int) or score < 0 or score > 100:
                    self.logger.error(f"Invalid score for {field}: {score}")
                    return False
        
        # Validate JSON fields
        json_fields = ['skills', 'analysis_results']
        for field in json_fields:
            if field in processed_data and isinstance(processed_data[field], str):
                try:
                    json.loads(processed_data[field])
                except json.JSONDecodeError:
                    self.logger.error(f"Invalid JSON for {field}")
                    return False
        
        return True

# Global processor instance
response_processor = AIResponseProcessor()

def process_ai_response(ai_result: Dict[str, Any], resume_id: str, user_id: str) -> Dict[str, Any]:
    """
    Global function to process AI responses
    """
    return response_processor.process_ai_response_for_database(ai_result, resume_id, user_id)
