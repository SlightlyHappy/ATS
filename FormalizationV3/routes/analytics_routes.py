"""
Analytics and reporting routes - extracted from monolithic app.py
Handles: analytics data, search functionality, reporting, performance metrics
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

# Create blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

# Global dependencies (will be injected during initialization)
db_manager = None
auth_middleware = None
analytics_processor = None
railway_db = None
cache_manager = None

def init_analytics_routes(database_manager, auth_mid, analytics_proc=None, 
                         railway_database=None, cache_mgr=None):
    """Initialize analytics routes with dependencies"""
    global db_manager, auth_middleware, analytics_processor, railway_db, cache_manager
    
    db_manager = database_manager
    auth_middleware = auth_mid
    analytics_processor = analytics_proc
    railway_db = railway_database
    cache_manager = cache_mgr
    
    logger.info("✅ Analytics routes initialized with all dependencies")

@analytics_bp.route('/dashboard', methods=['GET'])
def get_user_dashboard():
    """Get user dashboard analytics"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
        
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = user['user_id']
        
        # Check cache first
        cache_key = f"dashboard:{user_id}"
        if cache_manager:
            cached_data = cache_manager.get(cache_key)
            if cached_data:
                return jsonify({
                    "success": True,
                    "data": cached_data,
                    "cached": True
                })
        
        if not railway_db:
            return jsonify({"error": "Database not available"}), 500
        
        # Get time range
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Resume statistics
        resume_stats = railway_db.execute_read("""
            SELECT 
                COUNT(*) as total_resumes,
                COUNT(CASE WHEN upload_date > %s THEN 1 END) as recent_uploads,
                COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as processed,
                COUNT(CASE WHEN processing_status = 'failed' THEN 1 END) as failed,
                AVG(CASE WHEN overall_score > 0 THEN overall_score END) as avg_score,
                MAX(overall_score) as best_score,
                MIN(CASE WHEN overall_score > 0 THEN overall_score END) as lowest_score
            FROM resumes 
            WHERE user_id = %s
        """, (start_date, user_id))
        
        # Score distribution
        score_distribution = railway_db.execute_read("""
            SELECT 
                CASE 
                    WHEN overall_score >= 90 THEN 'Excellent (90-100)'
                    WHEN overall_score >= 80 THEN 'Very Good (80-89)'
                    WHEN overall_score >= 70 THEN 'Good (70-79)'
                    WHEN overall_score >= 60 THEN 'Average (60-69)'
                    ELSE 'Needs Improvement (<60)'
                END as score_range,
                COUNT(*) as count
            FROM resumes 
            WHERE user_id = %s AND overall_score > 0
            GROUP BY score_range
            ORDER BY MIN(overall_score) DESC
        """, (user_id,))
        
        # Recent activity
        recent_activity = railway_db.execute_read("""
            SELECT 
                r.filename, r.upload_date, r.processing_status, r.overall_score,
                r.candidate_name, r.id as resume_id
            FROM resumes r
            WHERE r.user_id = %s
            ORDER BY r.upload_date DESC
            LIMIT 10
        """, (user_id,))
        
        # Monthly trends
        monthly_trends = railway_db.execute_read("""
            SELECT 
                DATE_TRUNC('month', upload_date) as month,
                COUNT(*) as uploads,
                AVG(overall_score) as avg_score
            FROM resumes 
            WHERE user_id = %s AND upload_date > %s
            GROUP BY DATE_TRUNC('month', upload_date)
            ORDER BY month DESC
            LIMIT 6
        """, (user_id, start_date))
        
        # AI provider usage
        ai_usage = railway_db.execute_read("""
            SELECT 
                COALESCE(ai_provider_used, 'unknown') as provider,
                COUNT(*) as usage_count,
                AVG(ai_processing_time) as avg_processing_time
            FROM resumes 
            WHERE user_id = %s AND processing_status = 'completed'
            GROUP BY ai_provider_used
            ORDER BY usage_count DESC
        """, (user_id,))
        
        dashboard_data = {
            "overview": resume_stats[0] if resume_stats else {},
            "score_distribution": score_distribution or [],
            "recent_activity": recent_activity or [],
            "monthly_trends": monthly_trends or [],
            "ai_usage": ai_usage or [],
            "period_days": days,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Cache the data for 5 minutes
        if cache_manager:
            cache_manager.set(cache_key, dashboard_data, ttl=300)
        
        return jsonify({
            "success": True,
            "data": dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Dashboard analytics error: {e}")
        return jsonify({"error": "Failed to get dashboard data"}), 500

@analytics_bp.route('/search', methods=['GET'])
def search_resumes():
    """Search and filter resumes with advanced options"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
        
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = user['user_id']
        
        # Search parameters
        query = request.args.get('q', '').strip()
        skill_filter = request.args.get('skills', '')
        score_min = request.args.get('score_min', 0, type=int)
        score_max = request.args.get('score_max', 100, type=int)
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        sort_by = request.args.get('sort', 'upload_date')
        sort_order = request.args.get('order', 'desc')
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        offset = (page - 1) * per_page
        
        if not railway_db:
            return jsonify({"error": "Database not available"}), 500
        
        # Build search query
        where_conditions = ["user_id = %s"]
        params = [user_id]
        
        # Text search
        if query:
            where_conditions.append("""(
                LOWER(raw_text) LIKE LOWER(%s) OR 
                LOWER(candidate_name) LIKE LOWER(%s) OR 
                LOWER(filename) LIKE LOWER(%s)
            )""")
            search_term = f"%{query}%"
            params.extend([search_term, search_term, search_term])
        
        # Skills filter
        if skill_filter:
            skills = [skill.strip() for skill in skill_filter.split(',')]
            skill_conditions = []
            for skill in skills:
                skill_conditions.append("LOWER(raw_text) LIKE LOWER(%s)")
                params.append(f"%{skill}%")
            where_conditions.append(f"({' OR '.join(skill_conditions)})")
        
        # Score range
        if score_min > 0:
            where_conditions.append("overall_score >= %s")
            params.append(score_min)
        
        if score_max < 100:
            where_conditions.append("overall_score <= %s")
            params.append(score_max)
        
        # Date range
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                where_conditions.append("upload_date >= %s")
                params.append(date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                where_conditions.append("upload_date <= %s")
                params.append(date_to_obj)
            except ValueError:
                pass
        
        where_clause = " AND ".join(where_conditions)
        
        # Validate sort column
        valid_sort_columns = ['upload_date', 'overall_score', 'candidate_name', 'filename']
        if sort_by not in valid_sort_columns:
            sort_by = 'upload_date'
        
        sort_order = 'ASC' if sort_order.lower() == 'asc' else 'DESC'
        
        # Count total results
        count_query = f"SELECT COUNT(*) as total FROM resumes WHERE {where_clause}"
        total_result = railway_db.execute_read(count_query, params)
        total_count = total_result[0]['total'] if total_result else 0
        
        # Get search results
        search_query = f"""
            SELECT 
                id, filename, candidate_name, candidate_email, overall_score,
                experience_score, skills_score, education_score, upload_date,
                processing_status, ai_provider_used
            FROM resumes 
            WHERE {where_clause}
            ORDER BY {sort_by} {sort_order}
            LIMIT %s OFFSET %s
        """
        
        params.extend([per_page, offset])
        results = railway_db.execute_read(search_query, params)
        
        # Get search facets
        facets = get_search_facets(user_id, where_conditions[1:], params[1:-2])
        
        return jsonify({
            "success": True,
            "results": results or [],
            "facets": facets,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "pages": (total_count + per_page - 1) // per_page
            },
            "search_params": {
                "query": query,
                "skills": skill_filter,
                "score_range": [score_min, score_max],
                "date_from": date_from,
                "date_to": date_to,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({"error": "Search failed"}), 500

@analytics_bp.route('/export', methods=['POST'])
def export_analytics():
    """Export analytics data in various formats"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
        
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json() or {}
        export_type = data.get('type', 'resumes')  # 'resumes', 'analytics', 'reports'
        format_type = data.get('format', 'json')  # 'json', 'csv', 'pdf'
        filters = data.get('filters', {})
        
        user_id = user['user_id']
        
        if not railway_db:
            return jsonify({"error": "Database not available"}), 500
        
        # Generate export data based on type
        if export_type == 'resumes':
            export_data = export_resumes_data(user_id, filters)
        elif export_type == 'analytics':
            export_data = export_analytics_data(user_id, filters)
        elif export_type == 'reports':
            export_data = export_reports_data(user_id, filters)
        else:
            return jsonify({"error": "Invalid export type"}), 400
        
        if format_type == 'csv':
            return export_as_csv(export_data, export_type)
        elif format_type == 'pdf':
            return export_as_pdf(export_data, export_type)
        else:
            return jsonify({
                "success": True,
                "export_type": export_type,
                "format": format_type,
                "data": export_data,
                "exported_at": datetime.utcnow().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({"error": "Export failed"}), 500

@analytics_bp.route('/reports/generate', methods=['POST'])
def generate_report():
    """Generate comprehensive analytics report"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
        
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        data = request.get_json() or {}
        report_type = data.get('type', 'summary')  # 'summary', 'detailed', 'comparison'
        date_range = data.get('date_range', 30)  # days
        include_charts = data.get('include_charts', True)
        
        user_id = user['user_id']
        
        if not railway_db:
            return jsonify({"error": "Database not available"}), 500
        
        start_date = datetime.utcnow() - timedelta(days=date_range)
        
        # Generate report data
        report_data = {
            "report_info": {
                "type": report_type,
                "generated_at": datetime.utcnow().isoformat(),
                "date_range": date_range,
                "user_id": user_id
            }
        }
        
        if report_type == 'summary':
            report_data.update(generate_summary_report(user_id, start_date))
        elif report_type == 'detailed':
            report_data.update(generate_detailed_report(user_id, start_date))
        elif report_type == 'comparison':
            report_data.update(generate_comparison_report(user_id, start_date))
        
        # Add charts data if requested
        if include_charts:
            report_data["charts"] = generate_chart_data(user_id, start_date)
        
        return jsonify({
            "success": True,
            "report": report_data
        })
        
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        return jsonify({"error": "Report generation failed"}), 500

@analytics_bp.route('/metrics/performance', methods=['GET'])
def get_performance_metrics():
    """Get system performance metrics for user"""
    try:
        if not auth_middleware:
            return jsonify({"error": "Authentication not available"}), 500
        
        user = auth_middleware.get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        user_id = user['user_id']
        
        if not railway_db:
            return jsonify({"error": "Database not available"}), 500
        
        # AI processing performance
        ai_metrics = railway_db.execute_read("""
            SELECT 
                ai_provider_used,
                COUNT(*) as requests,
                AVG(ai_processing_time) as avg_time,
                MIN(ai_processing_time) as min_time,
                MAX(ai_processing_time) as max_time,
                COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as successful,
                COUNT(CASE WHEN processing_status = 'failed' THEN 1 END) as failed
            FROM resumes 
            WHERE user_id = %s AND ai_processing_time IS NOT NULL
            GROUP BY ai_provider_used
        """, (user_id,))
        
        # Upload performance
        upload_metrics = railway_db.execute_read("""
            SELECT 
                DATE(upload_date) as date,
                COUNT(*) as uploads,
                AVG(EXTRACT(EPOCH FROM (processing_completed_at - upload_date)) * 1000) as avg_processing_time
            FROM resumes 
            WHERE user_id = %s AND processing_completed_at IS NOT NULL
            AND upload_date > NOW() - INTERVAL '30 days'
            GROUP BY DATE(upload_date)
            ORDER BY date DESC
            LIMIT 30
        """, (user_id,))
        
        # Score accuracy metrics (if available)
        score_metrics = railway_db.execute_read("""
            SELECT 
                AVG(overall_score) as avg_overall,
                STDDEV(overall_score) as score_variance,
                AVG(experience_score) as avg_experience,
                AVG(skills_score) as avg_skills,
                AVG(education_score) as avg_education,
                AVG(technical_score) as avg_technical
            FROM resumes 
            WHERE user_id = %s AND overall_score > 0
        """, (user_id,))
        
        metrics_data = {
            "ai_performance": ai_metrics or [],
            "upload_performance": upload_metrics or [],
            "score_metrics": score_metrics[0] if score_metrics else {},
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return jsonify({
            "success": True,
            "metrics": metrics_data
        })
        
    except Exception as e:
        logger.error(f"Performance metrics error: {e}")
        return jsonify({"error": "Failed to get performance metrics"}), 500

# Helper functions

def get_search_facets(user_id, additional_conditions, additional_params):
    """Get search facets for filtering"""
    try:
        base_where = f"user_id = %s"
        base_params = [user_id]
        
        if additional_conditions:
            base_where += " AND " + " AND ".join(additional_conditions)
            base_params.extend(additional_params)
        
        # Score ranges
        score_facets = railway_db.execute_read(f"""
            SELECT 
                CASE 
                    WHEN overall_score >= 90 THEN '90-100'
                    WHEN overall_score >= 80 THEN '80-89'
                    WHEN overall_score >= 70 THEN '70-79'
                    WHEN overall_score >= 60 THEN '60-69'
                    ELSE 'Under 60'
                END as score_range,
                COUNT(*) as count
            FROM resumes 
            WHERE {base_where} AND overall_score > 0
            GROUP BY score_range
        """, base_params)
        
        # Processing status
        status_facets = railway_db.execute_read(f"""
            SELECT processing_status, COUNT(*) as count
            FROM resumes 
            WHERE {base_where}
            GROUP BY processing_status
        """, base_params)
        
        # AI providers
        provider_facets = railway_db.execute_read(f"""
            SELECT 
                COALESCE(ai_provider_used, 'unknown') as provider, 
                COUNT(*) as count
            FROM resumes 
            WHERE {base_where}
            GROUP BY ai_provider_used
        """, base_params)
        
        return {
            "score_ranges": score_facets or [],
            "processing_status": status_facets or [],
            "ai_providers": provider_facets or []
        }
        
    except Exception as e:
        logger.error(f"Facets error: {e}")
        return {}

def export_resumes_data(user_id, filters):
    """Export resumes data"""
    try:
        query = """
            SELECT 
                filename, candidate_name, candidate_email, overall_score,
                experience_score, skills_score, education_score, technical_score,
                upload_date, processing_status, ai_provider_used
            FROM resumes 
            WHERE user_id = %s
            ORDER BY upload_date DESC
        """
        
        return railway_db.execute_read(query, (user_id,)) or []
        
    except Exception as e:
        logger.error(f"Export resumes error: {e}")
        return []

def export_analytics_data(user_id, filters):
    """Export analytics data"""
    try:
        # This would generate comprehensive analytics export
        return {
            "summary": "Analytics export data would go here",
            "user_id": user_id,
            "filters": filters
        }
    except Exception as e:
        logger.error(f"Export analytics error: {e}")
        return {}

def export_reports_data(user_id, filters):
    """Export reports data"""
    try:
        # This would generate report export data
        return {
            "summary": "Reports export data would go here",
            "user_id": user_id,
            "filters": filters
        }
    except Exception as e:
        logger.error(f"Export reports error: {e}")
        return {}

def export_as_csv(data, export_type):
    """Export data as CSV"""
    try:
        import csv
        import io
        from flask import Response
        
        output = io.StringIO()
        
        if data and isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], dict):
                fieldnames = data[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
        
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={export_type}_export.csv'
            }
        )
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        return jsonify({"error": "CSV export failed"}), 500

def export_as_pdf(data, export_type):
    """Export data as PDF"""
    try:
        # This would generate PDF export
        # For now, return a placeholder
        return jsonify({
            "message": "PDF export not yet implemented",
            "data": data
        })
    except Exception as e:
        logger.error(f"PDF export error: {e}")
        return jsonify({"error": "PDF export failed"}), 500

def generate_summary_report(user_id, start_date):
    """Generate summary report"""
    try:
        summary = railway_db.execute_read("""
            SELECT 
                COUNT(*) as total_resumes,
                AVG(overall_score) as avg_score,
                COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as processed,
                COUNT(CASE WHEN overall_score >= 80 THEN 1 END) as high_quality
            FROM resumes 
            WHERE user_id = %s AND upload_date > %s
        """, (user_id, start_date))
        
        return {
            "summary": summary[0] if summary else {},
            "report_type": "summary"
        }
    except Exception as e:
        logger.error(f"Summary report error: {e}")
        return {}

def generate_detailed_report(user_id, start_date):
    """Generate detailed report"""
    try:
        # This would generate comprehensive detailed analytics
        return {
            "detailed_analytics": "Detailed report data would go here",
            "report_type": "detailed"
        }
    except Exception as e:
        logger.error(f"Detailed report error: {e}")
        return {}

def generate_comparison_report(user_id, start_date):
    """Generate comparison report"""
    try:
        # This would generate comparative analytics
        return {
            "comparison_data": "Comparison report data would go here",
            "report_type": "comparison"
        }
    except Exception as e:
        logger.error(f"Comparison report error: {e}")
        return {}

def generate_chart_data(user_id, start_date):
    """Generate chart data for reports"""
    try:
        # Score distribution chart
        score_chart = railway_db.execute_read("""
            SELECT 
                CASE 
                    WHEN overall_score >= 90 THEN 'Excellent'
                    WHEN overall_score >= 80 THEN 'Very Good'
                    WHEN overall_score >= 70 THEN 'Good'
                    WHEN overall_score >= 60 THEN 'Average'
                    ELSE 'Needs Improvement'
                END as category,
                COUNT(*) as count
            FROM resumes 
            WHERE user_id = %s AND upload_date > %s AND overall_score > 0
            GROUP BY category
        """, (user_id, start_date))
        
        # Timeline chart
        timeline_chart = railway_db.execute_read("""
            SELECT 
                DATE(upload_date) as date,
                COUNT(*) as uploads,
                AVG(overall_score) as avg_score
            FROM resumes 
            WHERE user_id = %s AND upload_date > %s
            GROUP BY DATE(upload_date)
            ORDER BY date
        """, (user_id, start_date))
        
        return {
            "score_distribution": score_chart or [],
            "upload_timeline": timeline_chart or []
        }
    except Exception as e:
        logger.error(f"Chart data error: {e}")
        return {}
