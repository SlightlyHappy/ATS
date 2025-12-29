#!/usr/bin/env python3
"""
Advanced Search & Filtering Engine for HR ATS System
Provides semantic search, advanced filtering, and intelligent query processing
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import math

from railway_database import RailwayPostgreSQL
from utils.response_formatter import EnhancedResponseFormatter

logger = logging.getLogger(__name__)

class SearchType(Enum):
    """Search type enumeration"""
    FULLTEXT = "fulltext"
    SEMANTIC = "semantic"
    FUZZY = "fuzzy"
    EXACT = "exact"
    BOOLEAN = "boolean"

class SortDirection(Enum):
    """Sort direction enumeration"""
    ASC = "asc"
    DESC = "desc"

@dataclass
class SearchFilter:
    """Search filter definition"""
    field: str
    operator: str  # eq, ne, gt, gte, lt, lte, in, not_in, like, ilike, between, is_null, is_not_null
    value: Any
    logical_operator: str = "AND"  # AND, OR

@dataclass
class SearchSort:
    """Search sort definition"""
    field: str
    direction: SortDirection
    priority: int = 0  # For multi-field sorting

@dataclass
class SearchQuery:
    """Complete search query definition"""
    query_text: str = ""
    search_type: SearchType = SearchType.FULLTEXT
    filters: List[SearchFilter] = None
    sorts: List[SearchSort] = None
    page: int = 1
    per_page: int = 20
    include_fields: List[str] = None
    exclude_fields: List[str] = None
    facets: List[str] = None
    highlight: bool = False
    boost_fields: Dict[str, float] = None
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = []
        if self.sorts is None:
            self.sorts = []
        if self.boost_fields is None:
            self.boost_fields = {}

@dataclass
class SearchResult:
    """Search result item"""
    id: str
    score: float
    data: Dict[str, Any]
    highlights: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.highlights is None:
            self.highlights = {}

@dataclass
class SearchResponse:
    """Complete search response"""
    results: List[SearchResult]
    total_count: int
    page: int
    per_page: int
    total_pages: int
    execution_time_ms: float
    facets: Dict[str, Any] = None
    suggestions: List[str] = None
    query_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.facets is None:
            self.facets = {}
        if self.suggestions is None:
            self.suggestions = []
        if self.query_info is None:
            self.query_info = {}

class AdvancedSearchEngine:
    """Advanced search and filtering engine"""
    
    def __init__(self, db_manager=None):
        if db_manager and hasattr(db_manager, 'railway_pg'):
            self.db = db_manager.railway_pg
        else:
            self.db = RailwayPostgreSQL()
        
        # Search configurations for different tables
        self.search_configs = {
            'resumes': {
                'searchable_fields': ['filename', 'skills', 'experience_summary', 'education', 'analysis_data'],
                'filterable_fields': ['user_id', 'status', 'experience_years', 'upload_date', 'analysis_date'],
                'sortable_fields': ['upload_date', 'analysis_date', 'experience_years', 'filename'],
                'facet_fields': ['status', 'experience_years', 'skills'],
                'boost_fields': {
                    'skills': 2.0,
                    'experience_summary': 1.5,
                    'filename': 1.0,
                    'education': 1.2
                },
                'default_sort': [{'field': 'upload_date', 'direction': 'desc'}]
            },
            'users': {
                'searchable_fields': ['email', 'first_name', 'last_name', 'profile_data'],
                'filterable_fields': ['role', 'is_active', 'created_at', 'last_login'],
                'sortable_fields': ['created_at', 'last_login', 'email', 'first_name', 'last_name'],
                'facet_fields': ['role', 'is_active'],
                'boost_fields': {
                    'email': 2.0,
                    'first_name': 1.5,
                    'last_name': 1.5
                },
                'default_sort': [{'field': 'created_at', 'direction': 'desc'}]
            },
            'job_postings': {
                'searchable_fields': ['title', 'description', 'requirements', 'skills_required'],
                'filterable_fields': ['company_id', 'status', 'salary_min', 'salary_max', 'location', 'created_at'],
                'sortable_fields': ['created_at', 'title', 'salary_min', 'salary_max'],
                'facet_fields': ['status', 'location', 'skills_required'],
                'boost_fields': {
                    'title': 2.5,
                    'skills_required': 2.0,
                    'description': 1.0
                },
                'default_sort': [{'field': 'created_at', 'direction': 'desc'}]
            }
        }
        
        # Query optimization cache
        self.query_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Search analytics
        self.search_analytics = {
            'total_searches': 0,
            'average_response_time': 0,
            'popular_queries': {},
            'failed_queries': [],
            'search_patterns': {}
        }
    
    def search(self, table_name: str, search_query: SearchQuery, user_context: Dict[str, Any] = None) -> SearchResponse:
        """Execute advanced search query"""
        start_time = time.time()
        
        try:
            # Validate table and configuration
            if table_name not in self.search_configs:
                raise ValueError(f"Search not configured for table: {table_name}")
            
            config = self.search_configs[table_name]
            
            # Apply user context and security
            search_query = self._apply_security_filters(search_query, table_name, user_context)
            
            # Generate cache key
            cache_key = self._generate_cache_key(table_name, search_query)
            
            # Check cache
            if cache_key in self.query_cache:
                cache_entry = self.query_cache[cache_key]
                if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                    logger.debug(f"Cache hit for search query: {cache_key}")
                    return cache_entry['result']
            
            # Build SQL query
            sql_query, params = self._build_sql_query(table_name, search_query, config)
            
            # Execute main query
            results = self.db.execute_read(sql_query, params)
            
            # Get total count
            count_query, count_params = self._build_count_query(table_name, search_query, config)
            total_count = self.db.execute_read(count_query, count_params)[0]['total']
            
            # Process results
            search_results = self._process_results(results, search_query, config)
            
            # Get facets if requested
            facets = {}
            if search_query.facets:
                facets = self._get_facets(table_name, search_query, config)
            
            # Generate suggestions
            suggestions = self._generate_suggestions(search_query.query_text, table_name)
            
            # Calculate pagination
            total_pages = math.ceil(total_count / search_query.per_page)
            
            execution_time = (time.time() - start_time) * 1000
            
            # Create response
            response = SearchResponse(
                results=search_results,
                total_count=total_count,
                page=search_query.page,
                per_page=search_query.per_page,
                total_pages=total_pages,
                execution_time_ms=execution_time,
                facets=facets,
                suggestions=suggestions,
                query_info={
                    'query_text': search_query.query_text,
                    'search_type': search_query.search_type.value,
                    'filters_applied': len(search_query.filters),
                    'sorts_applied': len(search_query.sorts)
                }
            )
            
            # Cache result
            self.query_cache[cache_key] = {
                'result': response,
                'timestamp': time.time()
            }
            
            # Update analytics
            self._update_search_analytics(search_query.query_text, execution_time, True)
            
            logger.info(f"Search executed successfully: {total_count} results in {execution_time:.2f}ms")
            return response
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self._update_search_analytics(search_query.query_text, execution_time, False)
            logger.error(f"Search failed: {e}")
            raise
    
    def _apply_security_filters(self, search_query: SearchQuery, table_name: str, user_context: Dict[str, Any]) -> SearchQuery:
        """Apply security filters based on user context"""
        if not user_context:
            return search_query
        
        user_id = user_context.get('user_id')
        is_admin = user_context.get('is_admin', False)
        
        # Apply table-specific security filters
        if table_name == 'resumes' and not is_admin:
            # Users can only search their own resumes
            user_filter = SearchFilter(
                field='user_id',
                operator='eq',
                value=user_id
            )
            search_query.filters.insert(0, user_filter)
        
        elif table_name == 'users' and not is_admin:
            # Users can only search active users (limited fields)
            active_filter = SearchFilter(
                field='is_active',
                operator='eq',
                value=True
            )
            search_query.filters.append(active_filter)
            
            # Limit fields for non-admin users
            if not search_query.include_fields:
                search_query.include_fields = ['id', 'email', 'first_name', 'last_name']
        
        return search_query
    
    def _build_sql_query(self, table_name: str, search_query: SearchQuery, config: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """Build SQL query from search parameters"""
        params = []
        
        # SELECT clause
        if search_query.include_fields:
            select_fields = ', '.join([f'"{field}"' for field in search_query.include_fields if field in config.get('searchable_fields', []) + config.get('filterable_fields', [])])
        else:
            select_fields = '*'
        
        # FROM clause
        query_parts = [f'SELECT {select_fields}']
        
        # Add search ranking for full-text search
        if search_query.query_text and search_query.search_type == SearchType.FULLTEXT:
            # Use PostgreSQL full-text search with ranking
            search_vector = self._build_search_vector(config['searchable_fields'])
            query_parts[0] = f'SELECT {select_fields}, ts_rank({search_vector}, plainto_tsquery(%s)) as search_score'
            params.append(search_query.query_text)
        
        query_parts.append(f'FROM {table_name}')
        
        # WHERE clause
        where_conditions = []
        
        # Text search condition
        if search_query.query_text:
            if search_query.search_type == SearchType.FULLTEXT:
                search_vector = self._build_search_vector(config['searchable_fields'])
                where_conditions.append(f'{search_vector} @@ plainto_tsquery(%s)')
                params.append(search_query.query_text)
            
            elif search_query.search_type == SearchType.SEMANTIC:
                # Implement semantic search (requires vector embeddings)
                semantic_condition = self._build_semantic_search(search_query.query_text, config['searchable_fields'])
                where_conditions.append(semantic_condition)
            
            elif search_query.search_type == SearchType.FUZZY:
                # Implement fuzzy search using similarity
                fuzzy_conditions = []
                for field in config['searchable_fields']:
                    fuzzy_conditions.append(f'similarity({field}, %s) > 0.3')
                    params.append(search_query.query_text)
                where_conditions.append(f'({" OR ".join(fuzzy_conditions)})')
            
            elif search_query.search_type == SearchType.EXACT:
                # Exact match search
                exact_conditions = []
                for field in config['searchable_fields']:
                    exact_conditions.append(f'{field} ILIKE %s')
                    params.append(f'%{search_query.query_text}%')
                where_conditions.append(f'({" OR ".join(exact_conditions)})')
        
        # Filter conditions
        for filter_item in search_query.filters:
            condition, filter_params = self._build_filter_condition(filter_item)
            where_conditions.append(condition)
            params.extend(filter_params)
        
        if where_conditions:
            query_parts.append(f'WHERE {" AND ".join(where_conditions)}')
        
        # ORDER BY clause
        order_clauses = []
        
        # Add search score ordering for full-text search
        if search_query.query_text and search_query.search_type == SearchType.FULLTEXT:
            order_clauses.append('search_score DESC')
        
        # Add custom sorts
        for sort_item in sorted(search_query.sorts, key=lambda x: x.priority):
            if sort_item.field in config['sortable_fields']:
                order_clauses.append(f'{sort_item.field} {sort_item.direction.value.upper()}')
        
        # Add default sorting if no custom sorts
        if not order_clauses and not (search_query.query_text and search_query.search_type == SearchType.FULLTEXT):
            for default_sort in config['default_sort']:
                order_clauses.append(f'{default_sort["field"]} {default_sort["direction"].upper()}')
        
        if order_clauses:
            query_parts.append(f'ORDER BY {", ".join(order_clauses)}')
        
        # LIMIT and OFFSET
        offset = (search_query.page - 1) * search_query.per_page
        query_parts.append(f'LIMIT {search_query.per_page} OFFSET {offset}')
        
        final_query = ' '.join(query_parts)
        logger.debug(f"Generated SQL: {final_query}")
        logger.debug(f"Parameters: {params}")
        
        return final_query, params
    
    def _build_count_query(self, table_name: str, search_query: SearchQuery, config: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """Build count query for total results"""
        params = []
        
        query_parts = ['SELECT COUNT(*) as total']
        query_parts.append(f'FROM {table_name}')
        
        # WHERE clause (same as main query but without SELECT fields)
        where_conditions = []
        
        # Text search condition
        if search_query.query_text:
            if search_query.search_type == SearchType.FULLTEXT:
                search_vector = self._build_search_vector(config['searchable_fields'])
                where_conditions.append(f'{search_vector} @@ plainto_tsquery(%s)')
                params.append(search_query.query_text)
            
            elif search_query.search_type == SearchType.FUZZY:
                fuzzy_conditions = []
                for field in config['searchable_fields']:
                    fuzzy_conditions.append(f'similarity({field}, %s) > 0.3')
                    params.append(search_query.query_text)
                where_conditions.append(f'({" OR ".join(fuzzy_conditions)})')
            
            elif search_query.search_type == SearchType.EXACT:
                exact_conditions = []
                for field in config['searchable_fields']:
                    exact_conditions.append(f'{field} ILIKE %s')
                    params.append(f'%{search_query.query_text}%')
                where_conditions.append(f'({" OR ".join(exact_conditions)})')
        
        # Filter conditions
        for filter_item in search_query.filters:
            condition, filter_params = self._build_filter_condition(filter_item)
            where_conditions.append(condition)
            params.extend(filter_params)
        
        if where_conditions:
            query_parts.append(f'WHERE {" AND ".join(where_conditions)}')
        
        return ' '.join(query_parts), params
    
    def _build_search_vector(self, searchable_fields: List[str]) -> str:
        """Build PostgreSQL search vector from searchable fields"""
        vector_parts = []
        for field in searchable_fields:
            # Handle JSON fields
            if field in ['skills', 'education', 'analysis_data']:
                vector_parts.append(f"to_tsvector('english', COALESCE({field}::text, ''))")
            else:
                vector_parts.append(f"to_tsvector('english', COALESCE({field}, ''))")
        
        return f"({' || '.join(vector_parts)})"
    
    def _build_semantic_search(self, query_text: str, searchable_fields: List[str]) -> str:
        """Build semantic search condition (placeholder for vector search)"""
        # This would integrate with vector embeddings for semantic search
        # For now, fall back to full-text search with enhanced weighting
        return f"({' OR '.join([f'{field} ILIKE %{query_text}%' for field in searchable_fields])})"
    
    def _build_filter_condition(self, filter_item: SearchFilter) -> Tuple[str, List[Any]]:
        """Build SQL condition for a filter"""
        field = filter_item.field
        operator = filter_item.operator
        value = filter_item.value
        
        if operator == 'eq':
            return f'{field} = %s', [value]
        elif operator == 'ne':
            return f'{field} != %s', [value]
        elif operator == 'gt':
            return f'{field} > %s', [value]
        elif operator == 'gte':
            return f'{field} >= %s', [value]
        elif operator == 'lt':
            return f'{field} < %s', [value]
        elif operator == 'lte':
            return f'{field} <= %s', [value]
        elif operator == 'in':
            placeholders = ', '.join(['%s'] * len(value))
            return f'{field} IN ({placeholders})', value
        elif operator == 'not_in':
            placeholders = ', '.join(['%s'] * len(value))
            return f'{field} NOT IN ({placeholders})', value
        elif operator == 'like':
            return f'{field} LIKE %s', [value]
        elif operator == 'ilike':
            return f'{field} ILIKE %s', [value]
        elif operator == 'between':
            return f'{field} BETWEEN %s AND %s', [value[0], value[1]]
        elif operator == 'is_null':
            return f'{field} IS NULL', []
        elif operator == 'is_not_null':
            return f'{field} IS NOT NULL', []
        else:
            raise ValueError(f"Unsupported filter operator: {operator}")
    
    def _process_results(self, results: List[Dict[str, Any]], search_query: SearchQuery, config: Dict[str, Any]) -> List[SearchResult]:
        """Process raw database results into SearchResult objects"""
        search_results = []
        
        for result in results:
            # Extract search score if available
            score = result.pop('search_score', 0.0) if 'search_score' in result else 0.0
            
            # Apply field exclusions
            if search_query.exclude_fields:
                for field in search_query.exclude_fields:
                    result.pop(field, None)
            
            # Generate highlights if requested
            highlights = {}
            if search_query.highlight and search_query.query_text:
                highlights = self._generate_highlights(result, search_query.query_text, config['searchable_fields'])
            
            search_results.append(SearchResult(
                id=str(result.get('id', '')),
                score=float(score),
                data=result,
                highlights=highlights
            ))
        
        return search_results
    
    def _generate_highlights(self, result: Dict[str, Any], query_text: str, searchable_fields: List[str]) -> Dict[str, List[str]]:
        """Generate search result highlights"""
        highlights = {}
        query_words = query_text.lower().split()
        
        for field in searchable_fields:
            if field in result and result[field]:
                field_value = str(result[field]).lower()
                field_highlights = []
                
                for word in query_words:
                    if word in field_value:
                        # Simple highlighting - can be enhanced with proper snippet extraction
                        start_idx = field_value.find(word)
                        if start_idx != -1:
                            snippet_start = max(0, start_idx - 30)
                            snippet_end = min(len(field_value), start_idx + len(word) + 30)
                            snippet = field_value[snippet_start:snippet_end]
                            highlighted_snippet = snippet.replace(word, f'<mark>{word}</mark>')
                            field_highlights.append(highlighted_snippet)
                
                if field_highlights:
                    highlights[field] = field_highlights
        
        return highlights
    
    def _get_facets(self, table_name: str, search_query: SearchQuery, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get faceted search results"""
        facets = {}
        
        for facet_field in search_query.facets:
            if facet_field in config['facet_fields']:
                # Build facet query
                facet_query = f"""
                SELECT {facet_field}, COUNT(*) as count
                FROM {table_name}
                """
                
                # Apply same WHERE conditions as main query (without pagination)
                params = []
                where_conditions = []
                
                if search_query.query_text and search_query.search_type == SearchType.FULLTEXT:
                    search_vector = self._build_search_vector(config['searchable_fields'])
                    where_conditions.append(f'{search_vector} @@ plainto_tsquery(%s)')
                    params.append(search_query.query_text)
                
                for filter_item in search_query.filters:
                    if filter_item.field != facet_field:  # Exclude current facet field
                        condition, filter_params = self._build_filter_condition(filter_item)
                        where_conditions.append(condition)
                        params.extend(filter_params)
                
                if where_conditions:
                    facet_query += f' WHERE {" AND ".join(where_conditions)}'
                
                facet_query += f' GROUP BY {facet_field} ORDER BY count DESC LIMIT 20'
                
                facet_results = self.db.execute_read(facet_query, params)
                facets[facet_field] = [
                    {'value': row[facet_field], 'count': row['count']}
                    for row in facet_results
                ]
        
        return facets
    
    def _generate_suggestions(self, query_text: str, table_name: str) -> List[str]:
        """Generate search suggestions based on query"""
        if not query_text or len(query_text) < 3:
            return []
        
        # Simple suggestion generation - can be enhanced with ML models
        suggestions = []
        
        # Query popular terms from search analytics
        if query_text.lower() in self.search_analytics['popular_queries']:
            # Add variations of popular queries
            for popular_query in self.search_analytics['popular_queries']:
                if query_text.lower() in popular_query.lower() and popular_query != query_text:
                    suggestions.append(popular_query)
        
        # Add spell corrections (basic implementation)
        if table_name == 'resumes':
            # Common skill suggestions
            common_skills = ['python', 'javascript', 'java', 'react', 'angular', 'nodejs', 'sql', 'aws']
            for skill in common_skills:
                if self._calculate_similarity(query_text.lower(), skill) > 0.6:
                    suggestions.append(skill.title())
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity (simple implementation)"""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _generate_cache_key(self, table_name: str, search_query: SearchQuery) -> str:
        """Generate cache key for search query"""
        import hashlib
        
        query_data = {
            'table': table_name,
            'query_text': search_query.query_text,
            'search_type': search_query.search_type.value,
            'filters': [(f.field, f.operator, str(f.value)) for f in search_query.filters],
            'sorts': [(s.field, s.direction.value) for s in search_query.sorts],
            'page': search_query.page,
            'per_page': search_query.per_page
        }
        
        query_string = json.dumps(query_data, sort_keys=True)
        return hashlib.md5(query_string.encode()).hexdigest()
    
    def _update_search_analytics(self, query_text: str, execution_time: float, success: bool):
        """Update search analytics"""
        self.search_analytics['total_searches'] += 1
        
        # Update average response time
        current_avg = self.search_analytics['average_response_time']
        total_searches = self.search_analytics['total_searches']
        self.search_analytics['average_response_time'] = (
            (current_avg * (total_searches - 1) + execution_time) / total_searches
        )
        
        if success and query_text:
            # Track popular queries
            query_lower = query_text.lower()
            self.search_analytics['popular_queries'][query_lower] = (
                self.search_analytics['popular_queries'].get(query_lower, 0) + 1
            )
        else:
            # Track failed queries
            self.search_analytics['failed_queries'].append({
                'query': query_text,
                'timestamp': datetime.utcnow().isoformat(),
                'execution_time': execution_time
            })
            
            # Keep only last 100 failed queries
            if len(self.search_analytics['failed_queries']) > 100:
                self.search_analytics['failed_queries'] = self.search_analytics['failed_queries'][-100:]
    
    def get_search_analytics(self) -> Dict[str, Any]:
        """Get search analytics data"""
        # Sort popular queries by frequency
        popular_queries = sorted(
            self.search_analytics['popular_queries'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'total_searches': self.search_analytics['total_searches'],
            'average_response_time_ms': round(self.search_analytics['average_response_time'], 2),
            'popular_queries': [{'query': q[0], 'count': q[1]} for q in popular_queries],
            'failed_queries_count': len(self.search_analytics['failed_queries']),
            'cache_size': len(self.query_cache),
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def clear_cache(self):
        """Clear search query cache"""
        cleared_count = len(self.query_cache)
        self.query_cache.clear()
        logger.info(f"Cleared {cleared_count} cached search queries")
        return cleared_count

# Global search engine instance
search_engine = AdvancedSearchEngine()

# Convenience functions for common searches
def search_resumes(query_text: str = "", filters: List[Dict[str, Any]] = None, 
                  page: int = 1, per_page: int = 20, user_context: Dict[str, Any] = None) -> SearchResponse:
    """Search resumes with advanced filtering"""
    search_filters = []
    if filters:
        for filter_data in filters:
            search_filters.append(SearchFilter(
                field=filter_data['field'],
                operator=filter_data['operator'],
                value=filter_data['value']
            ))
    
    search_query = SearchQuery(
        query_text=query_text,
        search_type=SearchType.FULLTEXT,
        filters=search_filters,
        page=page,
        per_page=per_page,
        highlight=True,
        facets=['status', 'experience_years']
    )
    
    return search_engine.search('resumes', search_query, user_context)

def search_users(query_text: str = "", filters: List[Dict[str, Any]] = None,
                page: int = 1, per_page: int = 20, user_context: Dict[str, Any] = None) -> SearchResponse:
    """Search users with advanced filtering"""
    search_filters = []
    if filters:
        for filter_data in filters:
            search_filters.append(SearchFilter(
                field=filter_data['field'],
                operator=filter_data['operator'],
                value=filter_data['value']
            ))
    
    search_query = SearchQuery(
        query_text=query_text,
        search_type=SearchType.FULLTEXT,
        filters=search_filters,
        page=page,
        per_page=per_page,
        facets=['role', 'is_active']
    )
    
    return search_engine.search('users', search_query, user_context)
