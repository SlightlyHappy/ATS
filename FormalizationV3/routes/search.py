#!/usr/bin/env python3
"""
Advanced Search Routes for HR ATS System
Provides API endpoints for advanced search and filtering capabilities
"""

from flask import Blueprint, request, jsonify
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from utils.advanced_search import (
    search_engine, SearchQuery, SearchFilter, SearchSort, SearchType, SortDirection,
    search_resumes, search_users
)
from utils.response_formatter import EnhancedResponseFormatter
from auth_middleware import require_auth, get_current_user, require_admin

logger = logging.getLogger(__name__)

# Create blueprint
search_bp = Blueprint('search', __name__, url_prefix='/api/v1/search')

# Initialize response formatter
response_formatter = EnhancedResponseFormatter()

@search_bp.route('/resumes', methods=['POST'])
@require_auth
def advanced_resume_search():
    """Advanced resume search with filtering and facets"""
    try:
        user = get_current_user()
        data = request.get_json() or {}
        
        # Extract search parameters
        query_text = data.get('query', '')
        search_type = data.get('search_type', 'fulltext')
        page = max(1, data.get('page', 1))
        per_page = min(data.get('per_page', 20), 100)
        
        # Parse filters
        filters = []
        for filter_data in data.get('filters', []):
            try:
                filters.append(SearchFilter(
                    field=filter_data['field'],
                    operator=filter_data['operator'],
                    value=filter_data['value']
                ))
            except KeyError as e:
                return response_formatter.error(
                    message=f"Invalid filter format: missing {e}",
                    error_code="INVALID_FILTER_FORMAT"
                ), 400
        
        # Parse sorts
        sorts = []
        for sort_data in data.get('sorts', []):
            try:
                sorts.append(SearchSort(
                    field=sort_data['field'],
                    direction=SortDirection(sort_data.get('direction', 'desc')),
                    priority=sort_data.get('priority', 0)
                ))
            except (KeyError, ValueError) as e:
                return response_formatter.error(
                    message=f"Invalid sort format: {e}",
                    error_code="INVALID_SORT_FORMAT"
                ), 400
        
        # Build search query
        try:
            search_query = SearchQuery(
                query_text=query_text,
                search_type=SearchType(search_type),
                filters=filters,
                sorts=sorts,
                page=page,
                per_page=per_page,
                include_fields=data.get('include_fields'),
                exclude_fields=data.get('exclude_fields'),
                facets=data.get('facets', ['status', 'experience_years']),
                highlight=data.get('highlight', True),
                boost_fields=data.get('boost_fields', {})
            )
        except ValueError as e:
            return response_formatter.error(
                message=f"Invalid search type: {e}",
                error_code="INVALID_SEARCH_TYPE"
            ), 400
        
        # Execute search
        user_context = {
            'user_id': user['id'],
            'is_admin': user.get('is_admin', False)
        }
        
        search_result = search_engine.search('resumes', search_query, user_context)
        
        return response_formatter.success(
            data={
                'results': [
                    {
                        'id': result.id,
                        'score': result.score,
                        'data': result.data,
                        'highlights': result.highlights
                    }
                    for result in search_result.results
                ],
                'pagination': {
                    'page': search_result.page,
                    'per_page': search_result.per_page,
                    'total_count': search_result.total_count,
                    'total_pages': search_result.total_pages,
                    'has_next': search_result.page < search_result.total_pages,
                    'has_prev': search_result.page > 1
                },
                'facets': search_result.facets,
                'suggestions': search_result.suggestions,
                'query_info': search_result.query_info,
                'execution_time_ms': search_result.execution_time_ms
            },
            message=f"Found {search_result.total_count} resumes",
            performance_data={
                'execution_time_ms': search_result.execution_time_ms,
                'results_count': len(search_result.results),
                'total_count': search_result.total_count
            }
        )
        
    except Exception as e:
        logger.error(f"Error in advanced resume search: {e}")
        return response_formatter.error(
            message="Failed to execute resume search",
            error_code="RESUME_SEARCH_ERROR",
            details={'error': str(e)}
        ), 500

@search_bp.route('/users', methods=['POST'])
@require_auth
def advanced_user_search():
    """Advanced user search with filtering and facets"""
    try:
        user = get_current_user()
        data = request.get_json() or {}
        
        # Extract search parameters
        query_text = data.get('query', '')
        search_type = data.get('search_type', 'fulltext')
        page = max(1, data.get('page', 1))
        per_page = min(data.get('per_page', 20), 100)
        
        # Parse filters
        filters = []
        for filter_data in data.get('filters', []):
            try:
                filters.append(SearchFilter(
                    field=filter_data['field'],
                    operator=filter_data['operator'],
                    value=filter_data['value']
                ))
            except KeyError as e:
                return response_formatter.error(
                    message=f"Invalid filter format: missing {e}",
                    error_code="INVALID_FILTER_FORMAT"
                ), 400
        
        # Parse sorts
        sorts = []
        for sort_data in data.get('sorts', []):
            try:
                sorts.append(SearchSort(
                    field=sort_data['field'],
                    direction=SortDirection(sort_data.get('direction', 'desc')),
                    priority=sort_data.get('priority', 0)
                ))
            except (KeyError, ValueError) as e:
                return response_formatter.error(
                    message=f"Invalid sort format: {e}",
                    error_code="INVALID_SORT_FORMAT"
                ), 400
        
        # Build search query
        try:
            search_query = SearchQuery(
                query_text=query_text,
                search_type=SearchType(search_type),
                filters=filters,
                sorts=sorts,
                page=page,
                per_page=per_page,
                include_fields=data.get('include_fields'),
                exclude_fields=data.get('exclude_fields', ['password']),  # Always exclude password
                facets=data.get('facets', ['role', 'is_active']),
                highlight=data.get('highlight', True)
            )
        except ValueError as e:
            return response_formatter.error(
                message=f"Invalid search type: {e}",
                error_code="INVALID_SEARCH_TYPE"
            ), 400
        
        # Execute search
        user_context = {
            'user_id': user['id'],
            'is_admin': user.get('is_admin', False)
        }
        
        search_result = search_engine.search('users', search_query, user_context)
        
        return response_formatter.success(
            data={
                'results': [
                    {
                        'id': result.id,
                        'score': result.score,
                        'data': result.data,
                        'highlights': result.highlights
                    }
                    for result in search_result.results
                ],
                'pagination': {
                    'page': search_result.page,
                    'per_page': search_result.per_page,
                    'total_count': search_result.total_count,
                    'total_pages': search_result.total_pages,
                    'has_next': search_result.page < search_result.total_pages,
                    'has_prev': search_result.page > 1
                },
                'facets': search_result.facets,
                'suggestions': search_result.suggestions,
                'query_info': search_result.query_info,
                'execution_time_ms': search_result.execution_time_ms
            },
            message=f"Found {search_result.total_count} users",
            performance_data={
                'execution_time_ms': search_result.execution_time_ms,
                'results_count': len(search_result.results),
                'total_count': search_result.total_count
            }
        )
        
    except Exception as e:
        logger.error(f"Error in advanced user search: {e}")
        return response_formatter.error(
            message="Failed to execute user search",
            error_code="USER_SEARCH_ERROR",
            details={'error': str(e)}
        ), 500

@search_bp.route('/suggestions', methods=['GET'])
@require_auth
def get_search_suggestions():
    """Get search suggestions based on query"""
    try:
        query = request.args.get('q', '')
        table = request.args.get('table', 'resumes')
        limit = min(int(request.args.get('limit', 5)), 20)
        
        if len(query) < 2:
            return response_formatter.success(
                data={'suggestions': []},
                message="Query too short for suggestions"
            )
        
        # Get suggestions from search engine
        suggestions = search_engine._generate_suggestions(query, table)
        
        # Limit results
        suggestions = suggestions[:limit]
        
        return response_formatter.success(
            data={
                'suggestions': suggestions,
                'query': query,
                'table': table
            },
            message=f"Generated {len(suggestions)} suggestions"
        )
        
    except Exception as e:
        logger.error(f"Error getting search suggestions: {e}")
        return response_formatter.error(
            message="Failed to get search suggestions",
            error_code="SUGGESTIONS_ERROR",
            details={'error': str(e)}
        ), 500

@search_bp.route('/filters', methods=['GET'])
@require_auth
def get_available_filters():
    """Get available filters for search tables"""
    try:
        table = request.args.get('table', 'resumes')
        
        if table not in search_engine.search_configs:
            return response_formatter.error(
                message=f"Search not configured for table: {table}",
                error_code="TABLE_NOT_CONFIGURED"
            ), 400
        
        config = search_engine.search_configs[table]
        
        # Define filter operators for different field types
        filter_definitions = {}
        
        for field in config['filterable_fields']:
            # Determine field type based on field name (simplified)
            if field in ['id', 'user_id', 'experience_years']:
                field_type = 'number'
                operators = ['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'not_in']
            elif field in ['created_at', 'updated_at', 'upload_date', 'analysis_date', 'last_login']:
                field_type = 'date'
                operators = ['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'between']
            elif field in ['is_active', 'is_admin']:
                field_type = 'boolean'
                operators = ['eq', 'ne']
            else:
                field_type = 'string'
                operators = ['eq', 'ne', 'like', 'ilike', 'in', 'not_in', 'is_null', 'is_not_null']
            
            filter_definitions[field] = {
                'type': field_type,
                'operators': operators
            }
        
        return response_formatter.success(
            data={
                'table': table,
                'searchable_fields': config['searchable_fields'],
                'filterable_fields': config['filterable_fields'],
                'sortable_fields': config['sortable_fields'],
                'facet_fields': config['facet_fields'],
                'filter_definitions': filter_definitions,
                'search_types': ['fulltext', 'semantic', 'fuzzy', 'exact', 'boolean'],
                'sort_directions': ['asc', 'desc']
            },
            message="Filter definitions retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting available filters: {e}")
        return response_formatter.error(
            message="Failed to get filter definitions",
            error_code="FILTERS_ERROR",
            details={'error': str(e)}
        ), 500

@search_bp.route('/analytics', methods=['GET'])
@require_admin
def get_search_analytics():
    """Get search analytics (admin only)"""
    try:
        analytics = search_engine.get_search_analytics()
        
        return response_formatter.success(
            data=analytics,
            message="Search analytics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting search analytics: {e}")
        return response_formatter.error(
            message="Failed to get search analytics",
            error_code="ANALYTICS_ERROR",
            details={'error': str(e)}
        ), 500

@search_bp.route('/cache', methods=['DELETE'])
@require_admin
def clear_search_cache():
    """Clear search query cache (admin only)"""
    try:
        cleared_count = search_engine.clear_cache()
        
        return response_formatter.success(
            data={'cleared_queries': cleared_count},
            message=f"Cleared {cleared_count} cached queries"
        )
        
    except Exception as e:
        logger.error(f"Error clearing search cache: {e}")
        return response_formatter.error(
            message="Failed to clear search cache",
            error_code="CACHE_CLEAR_ERROR",
            details={'error': str(e)}
        ), 500

@search_bp.route('/export', methods=['POST'])
@require_auth
def export_search_results():
    """Export search results to file"""
    try:
        user = get_current_user()
        data = request.get_json() or {}
        
        # Extract search parameters (similar to search endpoints)
        query_text = data.get('query', '')
        search_type = data.get('search_type', 'fulltext')
        table = data.get('table', 'resumes')
        export_format = data.get('format', 'csv')
        
        if export_format not in ['csv', 'json', 'xlsx']:
            return response_formatter.error(
                message="Invalid export format. Use 'csv', 'json', or 'xlsx'",
                error_code="INVALID_EXPORT_FORMAT"
            ), 400
        
        # Parse filters
        filters = []
        for filter_data in data.get('filters', []):
            filters.append(SearchFilter(
                field=filter_data['field'],
                operator=filter_data['operator'],
                value=filter_data['value']
            ))
        
        # Parse sorts
        sorts = []
        for sort_data in data.get('sorts', []):
            sorts.append(SearchSort(
                field=sort_data['field'],
                direction=SortDirection(sort_data.get('direction', 'desc')),
                priority=sort_data.get('priority', 0)
            ))
        
        # Build search query with high limit for export
        search_query = SearchQuery(
            query_text=query_text,
            search_type=SearchType(search_type),
            filters=filters,
            sorts=sorts,
            page=1,
            per_page=10000,  # High limit for export
            include_fields=data.get('include_fields'),
            exclude_fields=data.get('exclude_fields')
        )
        
        # Execute search
        user_context = {
            'user_id': user['id'],
            'is_admin': user.get('is_admin', False)
        }
        
        search_result = search_engine.search(table, search_query, user_context)
        
        # Prepare export data
        export_data = [result.data for result in search_result.results]
        
        # Use bulk operations for actual file generation
        from utils.bulk_operations import bulk_manager
        
        export_operation_id = bulk_manager.submit_operation(
            'bulk_data_export',
            user['id'],
            [{'data': export_data}],
            {
                'export_type': export_format,
                'filename_prefix': f'search_results_{table}',
                'search_query': query_text
            }
        )
        
        return response_formatter.success(
            data={
                'operation_id': export_operation_id,
                'export_format': export_format,
                'results_count': len(export_data),
                'status': 'submitted'
            },
            message="Search results export submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error exporting search results: {e}")
        return response_formatter.error(
            message="Failed to export search results",
            error_code="EXPORT_ERROR",
            details={'error': str(e)}
        ), 500

@search_bp.route('/saved-searches', methods=['GET'])
@require_auth
def get_saved_searches():
    """Get user's saved searches"""
    try:
        user = get_current_user()
        
        # This would typically query a saved_searches table
        # For now, return empty list as placeholder
        saved_searches = []
        
        return response_formatter.success(
            data={'saved_searches': saved_searches},
            message="Saved searches retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting saved searches: {e}")
        return response_formatter.error(
            message="Failed to get saved searches",
            error_code="SAVED_SEARCHES_ERROR",
            details={'error': str(e)}
        ), 500

@search_bp.route('/saved-searches', methods=['POST'])
@require_auth
def save_search():
    """Save a search query for future use"""
    try:
        user = get_current_user()
        data = request.get_json() or {}
        
        name = data.get('name')
        query_data = data.get('query_data')
        
        if not name or not query_data:
            return response_formatter.error(
                message="Name and query_data are required",
                error_code="MISSING_REQUIRED_FIELDS"
            ), 400
        
        # This would typically save to a saved_searches table
        # For now, just return success
        saved_search_id = f"search_{user['id']}_{int(datetime.utcnow().timestamp())}"
        
        return response_formatter.success(
            data={'saved_search_id': saved_search_id},
            message="Search saved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error saving search: {e}")
        return response_formatter.error(
            message="Failed to save search",
            error_code="SAVE_SEARCH_ERROR",
            details={'error': str(e)}
        ), 500

@search_bp.route('/quick-search', methods=['GET'])
@require_auth
def quick_search():
    """Quick search across multiple tables"""
    try:
        user = get_current_user()
        query = request.args.get('q', '')
        limit = min(int(request.args.get('limit', 10)), 50)
        
        if len(query) < 2:
            return response_formatter.error(
                message="Query must be at least 2 characters",
                error_code="QUERY_TOO_SHORT"
            ), 400
        
        results = {}
        user_context = {
            'user_id': user['id'],
            'is_admin': user.get('is_admin', False)
        }
        
        # Search resumes
        try:
            resume_search = SearchQuery(
                query_text=query,
                search_type=SearchType.FULLTEXT,
                page=1,
                per_page=limit
            )
            resume_results = search_engine.search('resumes', resume_search, user_context)
            results['resumes'] = {
                'count': resume_results.total_count,
                'results': [{'id': r.id, 'data': r.data, 'score': r.score} for r in resume_results.results[:5]]
            }
        except Exception as e:
            logger.warning(f"Resume search failed in quick search: {e}")
            results['resumes'] = {'count': 0, 'results': []}
        
        # Search users (if admin)
        if user.get('is_admin'):
            try:
                user_search = SearchQuery(
                    query_text=query,
                    search_type=SearchType.FULLTEXT,
                    page=1,
                    per_page=limit
                )
                user_results = search_engine.search('users', user_search, user_context)
                results['users'] = {
                    'count': user_results.total_count,
                    'results': [{'id': r.id, 'data': r.data, 'score': r.score} for r in user_results.results[:5]]
                }
            except Exception as e:
                logger.warning(f"User search failed in quick search: {e}")
                results['users'] = {'count': 0, 'results': []}
        
        total_results = sum(results[table]['count'] for table in results)
        
        return response_formatter.success(
            data={
                'query': query,
                'total_results': total_results,
                'results_by_table': results
            },
            message=f"Quick search found {total_results} results"
        )
        
    except Exception as e:
        logger.error(f"Error in quick search: {e}")
        return response_formatter.error(
            message="Failed to execute quick search",
            error_code="QUICK_SEARCH_ERROR",
            details={'error': str(e)}
        ), 500


def init_search_routes(search_engine_param=None, db_manager=None, auth_middleware=None):
    """Initialize search routes with dependencies"""
    global search_engine
    
    if search_engine_param:
        search_engine = search_engine_param
        logger.info("Search routes initialized with custom search engine")
    else:
        logger.info("Search routes initialized with default search engine")
    
    if db_manager:
        logger.info("Search routes initialized with database manager")
    
    if auth_middleware:
        logger.info("Search routes initialized with auth middleware")
    
    return search_bp
