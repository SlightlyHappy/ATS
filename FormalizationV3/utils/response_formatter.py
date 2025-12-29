#!/usr/bin/env python3
"""
Enhanced Response Formatter for Frontend Data Structures
Provides standardized response formats with performance metadata and UI helpers
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from flask import g
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetadata:
    """Performance metadata for API responses"""
    response_time_ms: float
    cache_hit: bool
    cache_key: Optional[str] = None
    database_queries: int = 0
    database_time_ms: float = 0.0
    total_records: int = 0
    memory_usage_mb: Optional[float] = None

@dataclass
class PaginationMetadata:
    """Pagination metadata"""
    current_page: int
    total_pages: int
    total_records: int
    per_page: int
    has_next: bool
    has_previous: bool
    next_page: Optional[int] = None
    previous_page: Optional[int] = None

@dataclass
class FilterMetadata:
    """Applied filters metadata"""
    filters_applied: Dict[str, Any]
    available_filters: Dict[str, List[str]]
    suggested_filters: List[Dict[str, str]]
    filter_counts: Dict[str, int]

@dataclass
class UIHelpers:
    """UI helper data for frontend"""
    quick_actions: List[Dict[str, str]]
    status_counts: Dict[str, int]
    suggested_next_actions: List[str]
    keyboard_shortcuts: Dict[str, str]
    bulk_actions: List[Dict[str, str]]

class EnhancedResponseFormatter:
    """Enhanced response formatter with performance metadata and UI helpers"""
    
    def __init__(self):
        self.start_time = time.time()
        self._db_queries = 0
        self._db_time = 0.0
        
    def track_db_query(self, execution_time_ms: float):
        """Track database query performance"""
        self._db_queries += 1
        self._db_time += execution_time_ms
        
    def create_response(
        self,
        success: bool = True,
        data: Any = None,
        message: str = "",
        error: Optional[str] = None,
        error_code: Optional[str] = None,
        pagination: Optional[PaginationMetadata] = None,
        filters: Optional[FilterMetadata] = None,
        ui_helpers: Optional[UIHelpers] = None,
        cache_hit: bool = False,
        cache_key: Optional[str] = None,
        total_records: int = 0
    ) -> Dict[str, Any]:
        """Create standardized enhanced response"""
        
        # Calculate performance metrics
        response_time = (time.time() - self.start_time) * 1000
        
        performance = PerformanceMetadata(
            response_time_ms=round(response_time, 2),
            cache_hit=cache_hit,
            cache_key=cache_key,
            database_queries=self._db_queries,
            database_time_ms=round(self._db_time, 2),
            total_records=total_records,
            memory_usage_mb=self._get_memory_usage()
        )
        
        response = {
            "success": success,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": getattr(g, 'request_id', None),
            "performance": asdict(performance)
        }
        
        if success:
            response["data"] = data
            if message:
                response["message"] = message
        else:
            response["error"] = error or "An error occurred"
            if error_code:
                response["error_code"] = error_code
                
        if pagination:
            response["pagination"] = asdict(pagination)
            
        if filters:
            response["filters"] = asdict(filters)
            
        if ui_helpers:
            response["ui_helpers"] = asdict(ui_helpers)
            
        return response
    
    def create_list_response(
        self,
        items: List[Any],
        total_count: int,
        page: int,
        per_page: int,
        filters_applied: Dict[str, Any] = None,
        available_statuses: List[str] = None,
        cache_hit: bool = False,
        endpoint_type: str = "generic"
    ) -> Dict[str, Any]:
        """Create enhanced list response with pagination and UI helpers"""
        
        # Calculate pagination
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_previous = page > 1
        
        pagination = PaginationMetadata(
            current_page=page,
            total_pages=total_pages,
            total_records=total_count,
            per_page=per_page,
            has_next=has_next,
            has_previous=has_previous,
            next_page=page + 1 if has_next else None,
            previous_page=page - 1 if has_previous else None
        )
        
        # Create filter metadata
        filters = None
        if filters_applied:
            filters = FilterMetadata(
                filters_applied=filters_applied,
                available_filters=self._get_available_filters(endpoint_type),
                suggested_filters=self._get_suggested_filters(filters_applied, items),
                filter_counts=self._calculate_filter_counts(items, endpoint_type)
            )
        
        # Create UI helpers
        ui_helpers = self._create_ui_helpers(items, endpoint_type, filters_applied)
        
        return self.create_response(
            success=True,
            data={
                "items": items,
                "summary": self._create_summary(items, total_count, endpoint_type)
            },
            pagination=pagination,
            filters=filters,
            ui_helpers=ui_helpers,
            cache_hit=cache_hit,
            total_records=total_count
        )
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return round(process.memory_info().rss / 1024 / 1024, 2)
        except:
            return None
    
    def _get_available_filters(self, endpoint_type: str) -> Dict[str, List[str]]:
        """Get available filters for endpoint type"""
        filter_map = {
            "resumes": {
                "status": ["pending", "processing", "completed", "failed"],
                "score_range": ["0-25", "26-50", "51-75", "76-100"],
                "date_range": ["today", "week", "month", "quarter", "year"],
                "sort_by": ["upload_date", "score", "filename", "status"]
            },
            "users": {
                "access_type": ["trial", "premium", "enterprise"],
                "status": ["active", "inactive", "suspended"],
                "registration": ["today", "week", "month"],
                "sort_by": ["created_at", "last_active", "name"]
            },
            "activities": {
                "type": ["upload", "analysis", "login", "export"],
                "date_range": ["today", "week", "month"],
                "sort_by": ["timestamp", "type", "user"]
            }
        }
        return filter_map.get(endpoint_type, {})
    
    def _get_suggested_filters(self, current_filters: Dict[str, Any], items: List[Any]) -> List[Dict[str, str]]:
        """Generate suggested filters based on current data"""
        suggestions = []
        
        if not current_filters.get('status') and len(items) > 5:
            suggestions.append({
                "label": "Filter by completed only",
                "filter": "status",
                "value": "completed",
                "description": "Show only completed items"
            })
        
        if not current_filters.get('date_range'):
            suggestions.append({
                "label": "Show recent items",
                "filter": "date_range", 
                "value": "week",
                "description": "Items from last 7 days"
            })
            
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _calculate_filter_counts(self, items: List[Any], endpoint_type: str) -> Dict[str, int]:
        """Calculate counts for different filter values"""
        counts = {}
        
        if endpoint_type == "resumes":
            status_counts = {}
            for item in items:
                status = item.get('processing_status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            counts['status'] = status_counts
        
        return counts
    
    def _create_ui_helpers(self, items: List[Any], endpoint_type: str, filters: Dict[str, Any] = None) -> UIHelpers:
        """Create UI helpers based on endpoint type and data"""
        
        quick_actions = []
        status_counts = {}
        suggested_actions = []
        keyboard_shortcuts = {}
        bulk_actions = []
        
        if endpoint_type == "resumes":
            quick_actions = [
                {"label": "Upload Resume", "action": "upload", "icon": "upload"},
                {"label": "Bulk Analyze", "action": "bulk_analyze", "icon": "cpu"},
                {"label": "Export Results", "action": "export", "icon": "download"}
            ]
            
            # Count statuses
            for item in items:
                status = item.get('processing_status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            if status_counts.get('pending', 0) > 0:
                suggested_actions.append("Process pending resumes")
            if status_counts.get('failed', 0) > 0:
                suggested_actions.append("Review failed analyses")
                
            keyboard_shortcuts = {
                "u": "Upload new resume",
                "r": "Refresh list", 
                "f": "Focus search",
                "e": "Export selected"
            }
            
            bulk_actions = [
                {"label": "Analyze Selected", "action": "bulk_analyze", "requires_selection": True},
                {"label": "Delete Selected", "action": "bulk_delete", "requires_selection": True, "destructive": True},
                {"label": "Export Selected", "action": "bulk_export", "requires_selection": True}
            ]
            
        elif endpoint_type == "users":
            quick_actions = [
                {"label": "Add User", "action": "add_user", "icon": "user-plus"},
                {"label": "Export Users", "action": "export", "icon": "download"},
                {"label": "Send Notification", "action": "notify", "icon": "mail"}
            ]
            
            for item in items:
                access_type = item.get('access_type', 'unknown')
                status_counts[access_type] = status_counts.get(access_type, 0) + 1
                
            keyboard_shortcuts = {
                "n": "New user",
                "r": "Refresh list",
                "f": "Focus search"
            }
            
        return UIHelpers(
            quick_actions=quick_actions,
            status_counts=status_counts,
            suggested_next_actions=suggested_actions,
            keyboard_shortcuts=keyboard_shortcuts,
            bulk_actions=bulk_actions
        )
    
    def _create_summary(self, items: List[Any], total_count: int, endpoint_type: str) -> Dict[str, Any]:
        """Create summary statistics for the response"""
        summary = {
            "total_items": total_count,
            "items_in_page": len(items),
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        if endpoint_type == "resumes" and items:
            scores = [item.get('overall_score') for item in items if item.get('overall_score') is not None]
            if scores:
                summary.update({
                    "average_score": round(sum(scores) / len(scores), 1),
                    "highest_score": max(scores),
                    "lowest_score": min(scores)
                })
                
        elif endpoint_type == "users" and items:
            trial_users = len([item for item in items if item.get('access_type') == 'trial'])
            premium_users = len([item for item in items if item.get('access_type') in ['premium', 'enterprise']])
            
            summary.update({
                "trial_users": trial_users,
                "premium_users": premium_users,
                "conversion_rate": round((premium_users / len(items)) * 100, 1) if items else 0
            })
            
        return summary
    
    def success(self, data: Any = None, message: str = "", **kwargs) -> Dict[str, Any]:
        """Create success response - convenience method"""
        return self.create_response(
            success=True,
            data=data,
            message=message,
            **kwargs
        )
    
    def error(self, error: str, error_code: str = None, **kwargs) -> Dict[str, Any]:
        """Create error response - convenience method"""
        return self.create_response(
            success=False,
            error=error,
            error_code=error_code,
            **kwargs
        )
    
    def paginated_success(self, items: List[Any], total_count: int, page: int, per_page: int, **kwargs) -> Dict[str, Any]:
        """Create paginated success response - convenience method"""
        return self.create_list_response(
            items=items,
            total_count=total_count,
            page=page,
            per_page=per_page,
            **kwargs
        )

def create_enhanced_response_formatter() -> EnhancedResponseFormatter:
    """Factory function to create enhanced response formatter"""
    return EnhancedResponseFormatter()

# Convenience functions for common response types
def success_response(data: Any = None, message: str = "", **kwargs) -> Dict[str, Any]:
    """Create successful response"""
    formatter = create_enhanced_response_formatter()
    return formatter.create_response(success=True, data=data, message=message, **kwargs)

def error_response(error: str, error_code: str = None, **kwargs) -> Dict[str, Any]:
    """Create error response"""
    formatter = create_enhanced_response_formatter()
    return formatter.create_response(success=False, error=error, error_code=error_code, **kwargs)

def list_response(items: List[Any], total_count: int, page: int, per_page: int, **kwargs) -> Dict[str, Any]:
    """Create enhanced list response"""
    formatter = create_enhanced_response_formatter()
    return formatter.create_list_response(items, total_count, page, per_page, **kwargs)
