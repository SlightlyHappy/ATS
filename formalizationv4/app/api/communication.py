"""
HR Communication Templates API endpoints.
Provides AI-powered template generation and management for HR communications.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from flask import Blueprint, request, jsonify, g
from sqlalchemy import desc

from app import db
from app.models.communication import (HRTemplate, TemplateGeneration, ComplianceRule,
                                    TemplateCategory, TemplateType, ComplianceLevel, TemplateStatus)
from app.models.candidate import Candidate
from app.services.hr_template_service import HRTemplateService, TemplateLibraryService
from app.services.auth_manager import require_auth, require_admin
from app.services.error_handler import handle_error

logger = logging.getLogger(__name__)

# Create blueprint
communication_bp = Blueprint('communication', __name__, url_prefix='/api/v1/communication')

# Initialize services
template_service = HRTemplateService()
library_service = TemplateLibraryService()


@communication_bp.route('/templates', methods=['GET'])
@require_auth
def get_templates():
    """
    Get HR communication templates for the authenticated user.
    
    Query Parameters:
    - category: Filter by template category (optional)
    - status: Filter by template status (optional)
    - include_system: Include system templates (default: true)
    """
    try:
        # Parse query parameters
        category_str = request.args.get('category')
        status_str = request.args.get('status')
        include_system = request.args.get('include_system', 'true').lower() == 'true'
        
        # Convert string parameters to enums
        category = None
        if category_str:
            try:
                category = TemplateCategory(category_str)
            except ValueError:
                return jsonify({
                    'error': f'Invalid category: {category_str}',
                    'valid_categories': [cat.value for cat in TemplateCategory]
                }), 400
        
        status = None
        if status_str:
            try:
                status = TemplateStatus(status_str)
            except ValueError:
                return jsonify({
                    'error': f'Invalid status: {status_str}',
                    'valid_statuses': [stat.value for stat in TemplateStatus]
                }), 400
        
        # Get templates
        templates = asyncio.run(template_service.get_templates(
            user_id=str(g.current_user.id),
            category=category,
            status=status,
            include_system=include_system
        ))
        
        return jsonify({
            'templates': [template.to_dict(include_content=False) for template in templates],
            'total': len(templates),
            'filters': {
                'category': category.value if category else None,
                'status': status.value if status else None,
                'include_system': include_system
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get templates: {str(e)}")
        return handle_error(e)


@communication_bp.route('/templates/<template_id>', methods=['GET'])
@require_auth
def get_template(template_id):
    """Get detailed information about a specific template."""
    try:
        template = HRTemplate.query.filter(
            HRTemplate.id == template_id,
            db.or_(
                HRTemplate.user_id == str(g.current_user.id),
                HRTemplate.is_system_template == True
            )
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        return jsonify({
            'template': template.to_dict(include_content=True)
        })
        
    except Exception as e:
        logger.error(f"Failed to get template {template_id}: {str(e)}")
        return handle_error(e)


@communication_bp.route('/templates/generate', methods=['POST'])
@require_auth
def generate_template():
    """
    Generate a new AI-powered HR communication template.
    
    Request Body:
    {
        "category": "screening|phone_interview|offer|rejection|...",
        "template_type": "email|sms|letter",
        "compliance_level": "basic|standard|strict",
        "personalization_data": {...},
        "custom_requirements": "Optional custom requirements"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'category' not in data:
            return jsonify({'error': 'Category is required'}), 400
        
        # Parse and validate category
        try:
            category = TemplateCategory(data['category'])
        except ValueError:
            return jsonify({
                'error': f'Invalid category: {data["category"]}',
                'valid_categories': [cat.value for cat in TemplateCategory]
            }), 400
        
        # Parse optional fields
        template_type = TemplateType.EMAIL
        if 'template_type' in data:
            try:
                template_type = TemplateType(data['template_type'])
            except ValueError:
                return jsonify({
                    'error': f'Invalid template_type: {data["template_type"]}',
                    'valid_types': [tt.value for tt in TemplateType]
                }), 400
        
        compliance_level = ComplianceLevel.STANDARD
        if 'compliance_level' in data:
            try:
                compliance_level = ComplianceLevel(data['compliance_level'])
            except ValueError:
                return jsonify({
                    'error': f'Invalid compliance_level: {data["compliance_level"]}',
                    'valid_levels': [cl.value for cl in ComplianceLevel]
                }), 400
        
        # Generate template
        template = asyncio.run(template_service.generate_template(
            user_id=str(g.current_user.id),
            category=category,
            template_type=template_type,
            compliance_level=compliance_level,
            personalization_data=data.get('personalization_data'),
            custom_requirements=data.get('custom_requirements')
        ))
        
        return jsonify({
            'template': template.to_dict(include_content=True),
            'message': 'Template generated successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to generate template: {str(e)}")
        return handle_error(e)


@communication_bp.route('/templates/<template_id>/personalize', methods=['POST'])
@require_auth
def personalize_template(template_id):
    """
    Generate personalized content from a template.
    
    Request Body:
    {
        "candidate_id": "optional_candidate_id",
        "personalization_data": {
            "candidate_name": "John Doe",
            "position_title": "Software Engineer",
            ...
        }
    }
    """
    try:
        data = request.get_json() or {}
        
        # Generate personalized content
        generation = asyncio.run(template_service.personalize_template(
            template_id=template_id,
            user_id=str(g.current_user.id),
            candidate_id=data.get('candidate_id'),
            personalization_data=data.get('personalization_data')
        ))
        
        return jsonify({
            'generation': generation.to_dict(),
            'message': 'Template personalized successfully'
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Failed to personalize template {template_id}: {str(e)}")
        return handle_error(e)


@communication_bp.route('/templates/<template_id>', methods=['PUT'])
@require_auth
def update_template(template_id):
    """
    Update a template (user templates only).
    
    Request Body:
    {
        "name": "Updated name",
        "description": "Updated description",
        "subject_template": "Updated subject",
        "content_template": "Updated content",
        "status": "draft|active|archived"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        # Get template (user templates only)
        template = HRTemplate.query.filter_by(
            id=template_id,
            user_id=str(g.current_user.id)
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found or not editable'}), 404
        
        # Update fields
        if 'name' in data:
            template.name = data['name']
        if 'description' in data:
            template.description = data['description']
        if 'subject_template' in data:
            template.subject_template = data['subject_template']
        if 'content_template' in data:
            template.content_template = data['content_template']
        if 'status' in data:
            try:
                template.status = TemplateStatus(data['status'])
            except ValueError:
                return jsonify({
                    'error': f'Invalid status: {data["status"]}',
                    'valid_statuses': [stat.value for stat in TemplateStatus]
                }), 400
        
        template.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'template': template.to_dict(include_content=True),
            'message': 'Template updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to update template {template_id}: {str(e)}")
        db.session.rollback()
        return handle_error(e)


@communication_bp.route('/templates/<template_id>', methods=['DELETE'])
@require_auth
def delete_template(template_id):
    """Delete a template (user templates only)."""
    try:
        template = HRTemplate.query.filter_by(
            id=template_id,
            user_id=str(g.current_user.id)
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found or not deletable'}), 404
        
        db.session.delete(template)
        db.session.commit()
        
        return jsonify({'message': 'Template deleted successfully'})
        
    except Exception as e:
        logger.error(f"Failed to delete template {template_id}: {str(e)}")
        db.session.rollback()
        return handle_error(e)


@communication_bp.route('/templates/<template_id>/validate', methods=['POST'])
@require_auth
def validate_template_compliance(template_id):
    """Validate template compliance with legal requirements."""
    try:
        template = HRTemplate.query.filter(
            HRTemplate.id == template_id,
            db.or_(
                HRTemplate.user_id == str(g.current_user.id),
                HRTemplate.is_system_template == True
            )
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        # Validate compliance
        is_compliant, issues = asyncio.run(
            template_service.validate_compliance(template)
        )
        
        return jsonify({
            'is_compliant': is_compliant,
            'issues': issues,
            'compliance_level': template.compliance_level.value,
            'validation_timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to validate template {template_id}: {str(e)}")
        return handle_error(e)


@communication_bp.route('/generations', methods=['GET'])
@require_auth
def get_template_generations():
    """
    Get template generation history for the user.
    
    Query Parameters:
    - template_id: Filter by template ID (optional)
    - candidate_id: Filter by candidate ID (optional)
    - limit: Number of results (default: 50)
    - offset: Pagination offset (default: 0)
    """
    try:
        template_id = request.args.get('template_id')
        candidate_id = request.args.get('candidate_id')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = TemplateGeneration.query.filter_by(user_id=str(g.current_user.id))
        
        if template_id:
            query = query.filter_by(template_id=template_id)
        
        if candidate_id:
            query = query.filter_by(candidate_id=candidate_id)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        generations = query.order_by(desc(TemplateGeneration.created_at)).limit(limit).offset(offset).all()
        
        return jsonify({
            'generations': [gen.to_dict() for gen in generations],
            'total': total,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Failed to get template generations: {str(e)}")
        return handle_error(e)


@communication_bp.route('/categories', methods=['GET'])
def get_template_categories():
    """Get available template categories and their descriptions."""
    categories = []
    
    for category in TemplateCategory:
        categories.append({
            'value': category.value,
            'name': category.value.replace('_', ' ').title(),
            'description': f'Templates for {category.value.replace("_", " ")} communications'
        })
    
    return jsonify({
        'categories': categories,
        'template_types': [{'value': tt.value, 'name': tt.value.title()} for tt in TemplateType],
        'compliance_levels': [{'value': cl.value, 'name': cl.value.title()} for cl in ComplianceLevel]
    })


@communication_bp.route('/compliance/rules', methods=['GET'])
@require_admin
def get_compliance_rules():
    """Get compliance rules (admin only)."""
    try:
        rules = ComplianceRule.query.filter_by(is_active=True).order_by(
            ComplianceRule.jurisdiction, ComplianceRule.compliance_level
        ).all()
        
        return jsonify({
            'rules': [rule.to_dict() for rule in rules],
            'total': len(rules)
        })
        
    except Exception as e:
        logger.error(f"Failed to get compliance rules: {str(e)}")
        return handle_error(e)


@communication_bp.route('/compliance/rules', methods=['POST'])
@require_admin
def create_compliance_rule():
    """
    Create a new compliance rule (admin only).
    
    Request Body:
    {
        "name": "Rule name",
        "description": "Rule description",
        "jurisdiction": "India",
        "rule_text": "Detailed rule text",
        "required_clauses": ["clause1", "clause2"],
        "prohibited_content": ["prohibited1"],
        "applicable_categories": ["screening", "offer"],
        "compliance_level": "standard",
        "source": "Legal source"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        # Validate required fields
        required_fields = ['name', 'rule_text', 'compliance_level']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate compliance level
        try:
            compliance_level = ComplianceLevel(data['compliance_level'])
        except ValueError:
            return jsonify({
                'error': f'Invalid compliance_level: {data["compliance_level"]}',
                'valid_levels': [cl.value for cl in ComplianceLevel]
            }), 400
        
        # Create rule
        rule = ComplianceRule(
            name=data['name'],
            description=data.get('description'),
            jurisdiction=data.get('jurisdiction', 'Global'),
            rule_text=data['rule_text'],
            required_clauses=data.get('required_clauses', []),
            prohibited_content=data.get('prohibited_content', []),
            applicable_categories=data.get('applicable_categories', []),
            compliance_level=compliance_level,
            source=data.get('source')
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify({
            'rule': rule.to_dict(),
            'message': 'Compliance rule created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create compliance rule: {str(e)}")
        db.session.rollback()
        return handle_error(e)


@communication_bp.route('/system/initialize', methods=['POST'])
@require_admin
def initialize_system_templates():
    """Initialize system templates (admin only)."""
    try:
        templates = asyncio.run(library_service.initialize_system_templates())
        
        return jsonify({
            'templates_created': len(templates),
            'templates': [template.to_dict(include_content=False) for template in templates],
            'message': f'Initialized {len(templates)} system templates'
        })
        
    except Exception as e:
        logger.error(f"Failed to initialize system templates: {str(e)}")
        return handle_error(e)


@communication_bp.route('/analytics', methods=['GET'])
@require_auth
def get_template_analytics():
    """Get template usage analytics for the user."""
    try:
        user_id = str(g.current_user.id)
        
        # Get template usage statistics
        templates = HRTemplate.query.filter_by(user_id=user_id).all()
        
        # Calculate analytics
        total_templates = len(templates)
        total_usage = sum(template.usage_count or 0 for template in templates)
        
        # Category breakdown
        category_stats = {}
        for template in templates:
            category = template.category.value
            if category not in category_stats:
                category_stats[category] = {'count': 0, 'usage': 0}
            category_stats[category]['count'] += 1
            category_stats[category]['usage'] += template.usage_count or 0
        
        # Recent generations
        recent_generations = TemplateGeneration.query.filter_by(
            user_id=user_id
        ).order_by(desc(TemplateGeneration.created_at)).limit(10).all()
        
        return jsonify({
            'analytics': {
                'total_templates': total_templates,
                'total_usage': total_usage,
                'category_breakdown': category_stats,
                'average_usage': total_usage / total_templates if total_templates > 0 else 0
            },
            'recent_generations': [gen.to_dict() for gen in recent_generations]
        })
        
    except Exception as e:
        logger.error(f"Failed to get template analytics: {str(e)}")
        return handle_error(e)


# Error handlers for the blueprint
@communication_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400


@communication_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404


@communication_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
