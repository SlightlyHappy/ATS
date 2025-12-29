# Import all models here for easy access
from .user import User, CreditTransaction
from .resume import Resume
from .analysis import Analysis
from .queue import AnalysisQueue, BatchUpload
from .admin import AdminUser, AdminAction, SystemConfiguration, AdminNotification
from .sales import Lead, LeadScoreHistory, LeadActivity, SalesMetrics, ROICalculation
from .analytics import PerformanceMetric, UsageInsight, ErrorTracking, SystemAlert, AnalyticsSnapshot
from .candidate import (Candidate, CandidateActivity, PipelineStageHistory, Interview, 
                       CandidateAlert, HiringAnalytics, PipelineStage, CandidateStatus, Priority)
from .communication import (HRTemplate, TemplateGeneration, ComplianceRule, 
                           TemplateCategory, TemplateType, ComplianceLevel, TemplateStatus)
from .legal import (LegalDocument, DocumentChunk, LegalQuery, KnowledgeBaseUpdate,
                   DocumentType, ProcessingStatus)
from .api_management import ApiKey, RateLimitRule, Webhook, AccessLog

__all__ = ['User', 'CreditTransaction', 'Resume', 'Analysis', 'AnalysisQueue', 'BatchUpload', 
           'AdminUser', 'AdminAction', 'SystemConfiguration', 'AdminNotification',
           'Lead', 'LeadScoreHistory', 'LeadActivity', 'SalesMetrics', 'ROICalculation',
           'PerformanceMetric', 'UsageInsight', 'ErrorTracking', 'SystemAlert', 'AnalyticsSnapshot',
           'Candidate', 'CandidateActivity', 'PipelineStageHistory', 'Interview', 
           'CandidateAlert', 'HiringAnalytics', 'PipelineStage', 'CandidateStatus', 'Priority',
           'HRTemplate', 'TemplateGeneration', 'ComplianceRule', 
           'TemplateCategory', 'TemplateType', 'ComplianceLevel', 'TemplateStatus',
           'LegalDocument', 'DocumentChunk', 'LegalQuery', 'KnowledgeBaseUpdate',
           'DocumentType', 'ProcessingStatus',
           'ApiKey', 'RateLimitRule', 'Webhook', 'AccessLog']
