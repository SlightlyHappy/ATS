"""
HR Pipeline API endpoints for candidate management and analytics.
Provides comprehensive candidate pipeline management functionality.
"""
from flask import Blueprint, request, jsonify, current_app
from app.services.auth_manager import auth_manager, require_auth, require_admin
from app.services.hr_pipeline_service import HRPipelineService
from app.services.candidate_scoring_service import CandidateScoringService
from app.services.hiring_analytics_service import HiringAnalyticsService
from app.services.high_priority_alert_service import HighPriorityAlertService
from app.models.candidate import Candidate, CandidateStatus, PipelineStage, Priority
from app.models.user import User
from app.services.error_handler import ApplicationError, ValidationError
import logging

logger = logging.getLogger(__name__)

# Create API blueprint
pipeline_bp = Blueprint('pipeline', __name__)

# Initialize services
hr_pipeline_service = HRPipelineService()
scoring_service = CandidateScoringService()
analytics_service = HiringAnalyticsService()
alert_service = HighPriorityAlertService()

@pipeline_bp.route('/candidates', methods=['GET'])
@require_auth
def get_candidates():
    """Get candidates with filtering and pagination."""
    try:
        user_id = request.current_user.id
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        stage = request.args.get('stage')
        status = request.args.get('status', CandidateStatus.ACTIVE.value)
        priority = request.args.get('priority')
        department = request.args.get('department')
        search = request.args.get('search')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query
        query = Candidate.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if stage:
            query = query.filter_by(current_stage=stage)
        
        if priority:
            query = query.filter_by(priority=priority)
        
        if department:
            query = query.filter_by(department=department)
        
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Candidate.first_name.ilike(search_filter)) |
                (Candidate.last_name.ilike(search_filter)) |
                (Candidate.email.ilike(search_filter)) |
                (Candidate.position_title.ilike(search_filter))
            )
        
        # Apply sorting
        if sort_by == 'score':
            sort_column = Candidate.overall_score.desc() if sort_order == 'desc' else Candidate.overall_score.asc()
        elif sort_by == 'name':
            sort_column = Candidate.first_name.desc() if sort_order == 'desc' else Candidate.first_name.asc()
        elif sort_by == 'applied_at':
            sort_column = Candidate.applied_at.desc() if sort_order == 'desc' else Candidate.applied_at.asc()
        else:  # created_at
            sort_column = Candidate.created_at.desc() if sort_order == 'desc' else Candidate.created_at.asc()
        
        query = query.order_by(sort_column)
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        candidates = [candidate.to_dict() for candidate in pagination.items]
        
        return jsonify({
            'candidates': candidates,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'filters_applied': {
                'stage': stage,
                'status': status,
                'priority': priority,
                'department': department,
                'search': search
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting candidates: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/candidates', methods=['POST'])
@require_auth
def create_candidate():
    """Create a new candidate."""
    try:
        user_id = request.current_user.id
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Add created_by information
        data['created_by'] = request.current_user.email
        
        result = hr_pipeline_service.create_candidate(user_id, data, data.get('resume_id'))
        
        if result.get('error'):
            return jsonify(result), 400
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Error creating candidate: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/candidates/<candidate_id>', methods=['GET'])
@require_auth
def get_candidate(candidate_id):
    """Get detailed candidate information."""
    try:
        user_id = request.current_user.id
        
        candidate = Candidate.query.filter_by(id=candidate_id, user_id=user_id).first()
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        # Get candidate timeline
        timeline_result = hr_pipeline_service.get_candidate_timeline(candidate_id)
        
        if timeline_result.get('error'):
            return jsonify({'candidate': candidate.to_dict(include_sensitive=True)}), 200
        
        return jsonify(timeline_result), 200
        
    except Exception as e:
        logger.error(f"Error getting candidate: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/candidates/<candidate_id>', methods=['PUT'])
@require_auth
def update_candidate(candidate_id):
    """Update candidate information."""
    try:
        user_id = request.current_user.id
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Check candidate belongs to user
        candidate = Candidate.query.filter_by(id=candidate_id, user_id=user_id).first()
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        # Add updated_by information
        data['updated_by'] = request.current_user.email
        
        result = hr_pipeline_service.update_candidate(candidate_id, data, request.current_user.email)
        
        if result.get('error'):
            return jsonify(result), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error updating candidate: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/candidates/<candidate_id>/stage', methods=['PUT'])
@require_auth
def move_candidate_stage(candidate_id):
    """Move candidate to a new pipeline stage."""
    try:
        user_id = request.current_user.id
        data = request.get_json()
        
        if not data or 'stage' not in data:
            return jsonify({'error': 'Stage is required'}), 400
        
        # Check candidate belongs to user
        candidate = Candidate.query.filter_by(id=candidate_id, user_id=user_id).first()
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        result = hr_pipeline_service.move_candidate_stage(
            candidate_id,
            data['stage'],
            data.get('notes'),
            request.current_user.email
        )
        
        if result.get('error'):
            return jsonify(result), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error moving candidate stage: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/candidates/<candidate_id>/score', methods=['POST'])
@require_auth
def score_candidate(candidate_id):
    """Score or re-score a candidate."""
    try:
        user_id = request.current_user.id
        data = request.get_json() or {}
        
        # Check candidate belongs to user
        candidate = Candidate.query.filter_by(id=candidate_id, user_id=user_id).first()
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        recalculate = data.get('recalculate', False)
        
        result = scoring_service.score_candidate(candidate, recalculate=recalculate)
        
        if result.get('error'):
            return jsonify(result), 400
        
        # Commit changes to database
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'scoring_result': result,
            'candidate': candidate.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error scoring candidate: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/candidates/<candidate_id>/interviews', methods=['POST'])
@require_auth
def schedule_interview(candidate_id):
    """Schedule an interview for a candidate."""
    try:
        user_id = request.current_user.id
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Interview data is required'}), 400
        
        # Check candidate belongs to user
        candidate = Candidate.query.filter_by(id=candidate_id, user_id=user_id).first()
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        # Add scheduled_by information
        data['scheduled_by'] = request.current_user.email
        
        result = hr_pipeline_service.schedule_interview(candidate_id, data)
        
        if result.get('error'):
            return jsonify(result), 400
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Error scheduling interview: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/candidates/<candidate_id>/notes', methods=['POST'])
@require_auth
def add_candidate_note(candidate_id):
    """Add a note/activity to a candidate."""
    try:
        user_id = request.current_user.id
        data = request.get_json()
        
        if not data or 'description' not in data:
            return jsonify({'error': 'Description is required'}), 400
        
        # Check candidate belongs to user
        candidate = Candidate.query.filter_by(id=candidate_id, user_id=user_id).first()
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        # Add created_by information
        data['created_by'] = request.current_user.email
        
        result = hr_pipeline_service.add_candidate_note(candidate_id, data)
        
        if result.get('error'):
            return jsonify(result), 400
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Error adding candidate note: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/pipeline/overview', methods=['GET'])
@require_auth
def get_pipeline_overview():
    """Get comprehensive pipeline overview."""
    try:
        user_id = request.current_user.id
        department = request.args.get('department')
        
        result = hr_pipeline_service.get_pipeline_overview(user_id, department)
        
        if result.get('error'):
            return jsonify(result), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting pipeline overview: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/scoring/batch', methods=['POST'])
@require_auth
def batch_score_candidates():
    """Score all candidates for the user."""
    try:
        user_id = request.current_user.id
        data = request.get_json() or {}
        
        force_recalculate = data.get('force_recalculate', False)
        
        result = scoring_service.score_all_candidates(user_id, force_recalculate)
        
        # Commit changes
        from app import db
        db.session.commit()
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in batch scoring: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/scoring/top-candidates', methods=['GET'])
@require_auth
def get_top_candidates():
    """Get top-scoring candidates."""
    try:
        user_id = request.current_user.id
        limit = int(request.args.get('limit', 10))
        stage = request.args.get('stage')
        
        result = scoring_service.get_top_candidates(user_id, limit, stage)
        
        return jsonify({'top_candidates': result}), 200
        
    except Exception as e:
        logger.error(f"Error getting top candidates: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/scoring/analytics', methods=['GET'])
@require_auth
def get_scoring_analytics():
    """Get candidate scoring analytics."""
    try:
        user_id = request.current_user.id
        days = int(request.args.get('days', 30))
        
        result = scoring_service.get_scoring_analytics(user_id, days)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting scoring analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/analytics/hiring', methods=['GET'])
@require_auth
def get_hiring_analytics():
    """Get comprehensive hiring analytics."""
    try:
        user_id = request.current_user.id
        period_days = int(request.args.get('period_days', 30))
        
        result = analytics_service.generate_hiring_analytics(user_id, period_days)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting hiring analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/analytics/historical', methods=['GET'])
@require_auth
def get_historical_analytics():
    """Get historical analytics trends."""
    try:
        user_id = request.current_user.id
        months = int(request.args.get('months', 6))
        
        result = analytics_service.get_historical_analytics(user_id, months)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting historical analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/alerts', methods=['GET'])
@require_auth
def get_alerts():
    """Get active alerts for candidates."""
    try:
        user_id = request.current_user.id
        priority = request.args.get('priority')
        
        result = alert_service.get_active_alerts(user_id, priority)
        
        return jsonify({'alerts': result}), 200
        
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/alerts/summary', methods=['GET'])
@require_auth
def get_alert_summary():
    """Get alert summary by type and priority."""
    try:
        user_id = request.current_user.id
        
        result = alert_service.get_alert_summary(user_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting alert summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/alerts/<alert_id>/read', methods=['PUT'])
@require_auth
def mark_alert_read(alert_id):
    """Mark an alert as read."""
    try:
        user_id = request.current_user.id
        
        result = alert_service.mark_alert_read(alert_id, user_id)
        
        if result.get('error'):
            return jsonify(result), 404
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error marking alert as read: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/alerts/<alert_id>/dismiss', methods=['PUT'])
@require_auth
def dismiss_alert(alert_id):
    """Dismiss an alert."""
    try:
        user_id = request.current_user.id
        
        result = alert_service.dismiss_alert(alert_id, user_id)
        
        if result.get('error'):
            return jsonify(result), 404
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error dismissing alert: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/alerts/bulk-read', methods=['PUT'])
@require_auth
def bulk_mark_alerts_read():
    """Mark multiple alerts as read."""
    try:
        user_id = request.current_user.id
        data = request.get_json()
        
        if not data or 'alert_ids' not in data:
            return jsonify({'error': 'Alert IDs are required'}), 400
        
        result = alert_service.bulk_mark_read(data['alert_ids'], user_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error bulk marking alerts as read: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/alerts/generate', methods=['POST'])
@require_auth
def generate_alerts():
    """Manually trigger alert generation."""
    try:
        user_id = request.current_user.id
        
        result = alert_service.check_and_generate_alerts(user_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error generating alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/candidates/<candidate_id>/alerts', methods=['POST'])
@require_auth
def create_manual_alert(candidate_id):
    """Create a manual alert for a candidate."""
    try:
        user_id = request.current_user.id
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Alert data is required'}), 400
        
        # Check candidate belongs to user
        candidate = Candidate.query.filter_by(id=candidate_id, user_id=user_id).first()
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        result = alert_service.create_manual_alert(candidate_id, data, request.current_user.email)
        
        if result.get('error'):
            return jsonify(result), 400
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Error creating manual alert: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/candidates/bulk-update', methods=['PUT'])
@require_auth
def bulk_update_candidates():
    """Bulk update multiple candidates."""
    try:
        user_id = request.current_user.id
        data = request.get_json()
        
        if not data or 'candidate_ids' not in data or 'updates' not in data:
            return jsonify({'error': 'Candidate IDs and updates are required'}), 400
        
        # Verify all candidates belong to user
        candidates = Candidate.query.filter(
            Candidate.id.in_(data['candidate_ids']),
            Candidate.user_id == user_id
        ).all()
        
        if len(candidates) != len(data['candidate_ids']):
            return jsonify({'error': 'Some candidates not found or not authorized'}), 404
        
        result = hr_pipeline_service.bulk_update_candidates(
            data['candidate_ids'],
            data['updates'],
            request.current_user.email
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in bulk candidate update: {str(e)}")
        return jsonify({'error': str(e)}), 500

@pipeline_bp.route('/enums', methods=['GET'])
@require_auth
def get_pipeline_enums():
    """Get pipeline enumeration values for frontend."""
    try:
        return jsonify({
            'pipeline_stages': [stage.value for stage in PipelineStage],
            'candidate_statuses': [status.value for status in CandidateStatus],
            'priorities': [priority.value for priority in Priority],
            'activity_types': [
                'created', 'updated', 'stage_change', 'interview_scheduled',
                'interview_completed', 'note', 'email', 'call', 'scoring',
                'technical_assessment', 'cultural_assessment', 'offer_made',
                'offer_accepted', 'offer_declined', 'reference_check',
                'background_check', 'alert_generated', 'manual_alert'
            ],
            'interview_types': [
                'phone', 'video', 'on_site', 'technical', 'cultural_fit',
                'behavioral', 'panel', 'final'
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting pipeline enums: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@pipeline_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({'error': str(e)}), 400

@pipeline_bp.errorhandler(ApplicationError)
def handle_application_error(e):
    return jsonify({'error': str(e)}), 500
