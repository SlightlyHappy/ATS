"""
Sales Intelligence API endpoints for lead scoring, ROI calculations,
and sales analytics.
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from app import db
from app.models.user import User
from app.models.sales import Lead, LeadStatus, LeadSource, ROICalculation, SalesMetrics
from app.services.lead_scoring_service import LeadScoringService
from app.services.roi_calculator_service import ROICalculatorService, ROIInput
from app.services.auth_manager import require_admin, get_current_user
from sqlalchemy import desc, and_, func

logger = logging.getLogger(__name__)

sales_bp = Blueprint('sales', __name__, url_prefix='/api/v1/sales')

# Initialize services
lead_scorer = LeadScoringService()
roi_calculator = ROICalculatorService()

@sales_bp.route('/leads', methods=['GET'])
@require_admin
def get_leads():
    """Get all leads with optional filtering and pagination."""
    try:
        # Query parameters
        status = request.args.get('status')
        min_score = request.args.get('min_score', type=int)
        max_score = request.args.get('max_score', type=int)
        source = request.args.get('source')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Build query
        query = Lead.query.join(User)
        
        if status:
            query = query.filter(Lead.status == status)
        if min_score is not None:
            query = query.filter(Lead.overall_score >= min_score)
        if max_score is not None:
            query = query.filter(Lead.overall_score <= max_score)
        if source:
            query = query.filter(Lead.source == source)
        
        # Order by score (highest first)
        query = query.order_by(desc(Lead.overall_score))
        
        # Paginate
        leads = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'leads': [lead.to_dict() for lead in leads.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': leads.total,
                'pages': leads.pages,
                'has_next': leads.has_next,
                'has_prev': leads.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting leads: {str(e)}")
        return jsonify({'error': 'Failed to retrieve leads'}), 500

@sales_bp.route('/leads/<lead_id>', methods=['GET'])
@require_admin
def get_lead(lead_id):
    """Get detailed information about a specific lead."""
    try:
        lead = Lead.query.get_or_404(lead_id)
        
        # Include recent activities
        recent_activities = lead.activities.order_by(
            desc('created_at')
        ).limit(10).all()
        
        # Include score history
        score_history = lead.score_history.order_by(
            desc('created_at')
        ).limit(5).all()
        
        lead_data = lead.to_dict()
        lead_data['recent_activities'] = [
            {
                'activity_type': activity.activity_type,
                'description': activity.description,
                'created_at': activity.created_at.isoformat(),
                'metadata': activity.metadata
            }
            for activity in recent_activities
        ]
        lead_data['score_history'] = [
            {
                'old_score': history.old_score,
                'new_score': history.new_score,
                'change_reason': history.change_reason,
                'created_at': history.created_at.isoformat()
            }
            for history in score_history
        ]
        
        return jsonify(lead_data)
        
    except Exception as e:
        logger.error(f"Error getting lead {lead_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve lead'}), 500

@sales_bp.route('/leads/<lead_id>/score/update', methods=['POST'])
@require_admin
def update_lead_score(lead_id):
    """Force update lead score calculation."""
    try:
        lead = Lead.query.get_or_404(lead_id)
        
        # Force score recalculation
        new_score = lead.update_score(force_recalculate=True)
        
        # Log the manual update
        lead.log_activity(
            'score_update',
            f'Manual score update by admin: {new_score}',
            {'updated_by': get_current_user().id if get_current_user() else 'admin'}
        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Lead score updated successfully',
            'new_score': new_score,
            'lead': lead.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating lead score {lead_id}: {str(e)}")
        return jsonify({'error': 'Failed to update lead score'}), 500

@sales_bp.route('/leads/<lead_id>/qualify', methods=['POST'])
@require_admin
def qualify_lead(lead_id):
    """Mark lead as qualified and add qualification notes."""
    try:
        lead = Lead.query.get_or_404(lead_id)
        data = request.get_json()
        
        # Update lead status
        lead.status = LeadStatus.QUALIFIED.value
        lead.qualification_notes = data.get('notes', '')
        lead.qualification_metadata = data.get('metadata', {})
        
        # Log qualification
        lead.log_activity(
            'qualified',
            f'Lead qualified by admin: {data.get("notes", "No notes provided")}',
            data.get('metadata', {})
        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Lead qualified successfully',
            'lead': lead.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error qualifying lead {lead_id}: {str(e)}")
        return jsonify({'error': 'Failed to qualify lead'}), 500

@sales_bp.route('/leads/hot', methods=['GET'])
@require_admin
def get_hot_leads():
    """Get all hot leads (score >= 70) for immediate attention."""
    try:
        threshold = request.args.get('threshold', 70, type=int)
        hot_leads = lead_scorer.get_hot_leads(threshold)
        
        return jsonify({
            'hot_leads': hot_leads,
            'threshold': threshold,
            'count': len(hot_leads),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting hot leads: {str(e)}")
        return jsonify({'error': 'Failed to retrieve hot leads'}), 500

@sales_bp.route('/leads/score/batch-update', methods=['POST'])
@require_admin
def batch_update_scores():
    """Batch update scores for all or specified leads."""
    try:
        data = request.get_json() or {}
        user_ids = data.get('user_ids')  # Optional list of specific users
        
        # Perform batch update
        results = lead_scorer.batch_update_scores(user_ids)
        
        return jsonify({
            'message': 'Batch score update completed',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in batch score update: {str(e)}")
        return jsonify({'error': 'Failed to update scores'}), 500

@sales_bp.route('/roi/calculate', methods=['POST'])
def calculate_roi():
    """Calculate ROI for a given scenario. Public endpoint for prospects."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['monthly_analyses', 'hourly_rate']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create ROI input
        roi_input = ROIInput(
            monthly_analyses=data['monthly_analyses'],
            hourly_rate=data['hourly_rate'],
            time_saved_per_analysis=data.get('time_saved_per_analysis', 2.0),
            current_process_cost=data.get('current_process_cost'),
            platform_cost_per_analysis=data.get('platform_cost_per_analysis', 2.0)
        )
        
        # Get lead ID if user is authenticated
        lead_id = None
        current_user = get_current_user()
        if current_user:
            lead = Lead.query.filter_by(user_id=current_user.id).first()
            if lead:
                lead_id = str(lead.id)
                # Log ROI calculation activity
                lead.log_activity(
                    'roi_calculation',
                    f'ROI calculated: {data["monthly_analyses"]} analyses/month',
                    data
                )
        
        # Generate comprehensive ROI report
        roi_report = roi_calculator.generate_roi_report(roi_input, lead_id)
        
        return jsonify(roi_report)
        
    except Exception as e:
        logger.error(f"Error calculating ROI: {str(e)}")
        return jsonify({'error': 'Failed to calculate ROI'}), 500

@sales_bp.route('/roi/benchmarks', methods=['GET'])
def get_roi_benchmarks():
    """Get industry benchmarks for ROI calculations."""
    try:
        industry = request.args.get('industry')
        benchmarks = roi_calculator.get_industry_benchmarks(industry)
        
        return jsonify({
            'industry': industry or 'general',
            'benchmarks': benchmarks
        })
        
    except Exception as e:
        logger.error(f"Error getting ROI benchmarks: {str(e)}")
        return jsonify({'error': 'Failed to retrieve benchmarks'}), 500

@sales_bp.route('/analytics/dashboard', methods=['GET'])
@require_admin
def get_sales_dashboard():
    """Get comprehensive sales analytics for admin dashboard."""
    try:
        # Time range parameters
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Lead statistics
        total_leads = Lead.query.count()
        new_leads = Lead.query.filter(Lead.created_at >= start_date).count()
        hot_leads = Lead.query.filter(Lead.overall_score >= 70).count()
        qualified_leads = Lead.query.filter(Lead.status == LeadStatus.QUALIFIED.value).count()
        converted_leads = Lead.query.filter(Lead.status == LeadStatus.CONVERTED.value).count()
        
        # Score distribution
        score_distribution = lead_scorer.get_score_distribution()
        
        # Recent activities
        from app.models.sales import LeadActivity
        recent_activities = LeadActivity.query.order_by(
            desc(LeadActivity.created_at)
        ).limit(20).all()
        
        # Conversion metrics
        if total_leads > 0:
            conversion_rate = (converted_leads / total_leads) * 100
        else:
            conversion_rate = 0
        
        # ROI calculations performed
        roi_calculations = ROICalculation.query.filter(
            ROICalculation.created_at >= start_date
        ).count()
        
        # Top leads by score
        top_leads = Lead.query.order_by(desc(Lead.overall_score)).limit(10).all()
        
        return jsonify({
            'summary': {
                'total_leads': total_leads,
                'new_leads': new_leads,
                'hot_leads': hot_leads,
                'qualified_leads': qualified_leads,
                'converted_leads': converted_leads,
                'conversion_rate': round(conversion_rate, 2),
                'roi_calculations': roi_calculations
            },
            'score_distribution': score_distribution,
            'top_leads': [
                {
                    'id': str(lead.id),
                    'user_email': lead.user.email,
                    'score': lead.overall_score,
                    'status': lead.status,
                    'last_activity': lead.last_activity.isoformat()
                }
                for lead in top_leads
            ],
            'recent_activities': [
                {
                    'activity_type': activity.activity_type,
                    'description': activity.description,
                    'created_at': activity.created_at.isoformat(),
                    'lead_email': activity.lead.user.email if activity.lead.user else 'Unknown'
                }
                for activity in recent_activities
            ],
            'period_days': days,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting sales dashboard: {str(e)}")
        return jsonify({'error': 'Failed to retrieve sales dashboard'}), 500

@sales_bp.route('/analytics/trends', methods=['GET'])
@require_admin
def get_sales_trends():
    """Get sales trends and time-series data."""
    try:
        # Time range parameters
        days = request.args.get('days', 30, type=int)
        
        # Generate daily metrics for the period
        trends_data = []
        
        for i in range(days):
            date = datetime.utcnow().date() - timedelta(days=i)
            start_datetime = datetime.combine(date, datetime.min.time())
            end_datetime = start_datetime + timedelta(days=1)
            
            # Count metrics for this day
            new_leads_count = Lead.query.filter(
                and_(
                    Lead.created_at >= start_datetime,
                    Lead.created_at < end_datetime
                )
            ).count()
            
            roi_calcs_count = ROICalculation.query.filter(
                and_(
                    ROICalculation.created_at >= start_datetime,
                    ROICalculation.created_at < end_datetime
                )
            ).count()
            
            trends_data.append({
                'date': date.isoformat(),
                'new_leads': new_leads_count,
                'roi_calculations': roi_calcs_count
            })
        
        # Reverse to show oldest to newest
        trends_data.reverse()
        
        return jsonify({
            'trends': trends_data,
            'period_days': days,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting sales trends: {str(e)}")
        return jsonify({'error': 'Failed to retrieve sales trends'}), 500

@sales_bp.route('/leads/convert/<lead_id>', methods=['POST'])
@require_admin
def convert_lead(lead_id):
    """Mark a lead as converted with conversion details."""
    try:
        lead = Lead.query.get_or_404(lead_id)
        data = request.get_json()
        
        # Update lead status
        lead.status = LeadStatus.CONVERTED.value
        lead.converted_at = datetime.utcnow()
        lead.conversion_value = data.get('conversion_value', 0)
        lead.conversion_source = data.get('conversion_source', 'direct')
        
        # Log conversion
        lead.log_activity(
            'converted',
            f'Lead converted: ${lead.conversion_value} value',
            {
                'conversion_value': lead.conversion_value,
                'conversion_source': lead.conversion_source,
                'notes': data.get('notes', '')
            }
        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Lead converted successfully',
            'lead': lead.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error converting lead {lead_id}: {str(e)}")
        return jsonify({'error': 'Failed to convert lead'}), 500

# Error handlers
@sales_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@sales_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400
