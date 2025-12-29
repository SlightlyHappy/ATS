"use client"

import { AdminService } from './admin.service'

// Enhanced Admin Service that adds new v1.3 backend capabilities
// Uses composition instead of inheritance to avoid constructor issues
export class EnhancedAdminService {
  
  // Delegate to existing AdminService instance
  private adminService = AdminService;
  
  // Payment & Credit Management
  async getPaymentAnalytics(days: number = 30): Promise<any> {
    try {
      const response = await fetch(`/api/payment/analytics?days=${days}`, {
        method: 'GET',
        credentials: 'include', // Important for cookie-based auth
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get payment analytics:', error)
      throw error
    }
  }

  async getUserCreditsDetailed(userId: string): Promise<any> {
    try {
      const response = await fetch(`/api/admin/users/${userId}/credits`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get user credits:', error)
      throw error
    }
  }

  async updateUserCredits(userId: string, credits: number, reason: string): Promise<any> {
    try {
      const response = await fetch(`/api/admin/users/${userId}/reset-trial`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          new_limit: credits,
          reset_usage: true,
          reason
        }),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to update user credits:', error)
      throw error
    }
  }

  // Advanced Resume Management
  async getResumeAnalytics(): Promise<any> {
    try {
      const response = await fetch('/api/admin/resumes/analytics', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        // If the endpoint doesn't exist, return fallback data
        if (response.status === 404) {
          console.warn('📊 Resume analytics endpoint not found, using fallback data');
          return {
            success: true,
            data: {
              total_resumes: 0,
              processed_count: 0,
              average_score: 0,
              success_rate: 0,
              processing_time_avg: 0,
              recent_uploads: [],
              score_distribution: []
            }
          };
        }
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get resume analytics:', error)
      // Return fallback data instead of throwing
      return {
        success: false,
        data: {
          total_resumes: 0,
          processed_count: 0,
          average_score: 0,
          success_rate: 0,
          processing_time_avg: 0,
          recent_uploads: [],
          score_distribution: []
        }
      };
    }
  }

  async analyzeResumeAdvanced(resumeId: string, options: {
    jobDescription?: string
    analysisType?: 'comprehensive' | 'quick'
    includeComparisons?: boolean
  }): Promise<any> {
    try {
      const response = await fetch(`/api/admin/analyze/${resumeId}`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_description: options.jobDescription,
          analysis_type: options.analysisType || 'comprehensive',
          include_comparisons: options.includeComparisons || false
        }),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to analyze resume:', error)
      throw error
    }
  }

  async batchAnalyzeResumesAdvanced(resumeIds: string[], analysisType: 'comparative' | 'individual' = 'comparative'): Promise<any> {
    try {
      const response = await fetch('/api/admin/analyze/batch', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resume_ids: resumeIds,
          analysis_type: analysisType
        }),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to batch analyze resumes:', error)
      throw error
    }
  }

  // System Management
  async getSystemHealthDetailed(): Promise<any> {
    try {
      const response = await fetch('/api/admin/system/health', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get system health:', error)
      throw error
    }
  }

  async cleanupSessions(): Promise<any> {
    try {
      const response = await fetch('/api/admin/sessions/cleanup', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to cleanup sessions:', error)
      throw error
    }
  }

  async getActiveSessions(): Promise<any> {
    try {
      const response = await fetch('/api/admin/sessions/active', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get active sessions:', error)
      throw error
    }
  }

  // Legal Query Management
  async createLegalQueryAdvanced(query: string, userId?: string, priority: 'low' | 'medium' | 'high' = 'medium'): Promise<any> {
    try {
      const response = await fetch('/api/admin/hr-legal/query', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          user_id: userId,
          priority
        }),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to create legal query:', error)
      throw error
    }
  }

  // Railway Database & Infrastructure Monitoring
  async getRailwayDatabaseStats(): Promise<any> {
    try {
      const response = await fetch('/api/admin/infrastructure/railway/database', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get Railway database stats:', error)
      throw error
    }
  }

  async getRailwayServiceStatus(): Promise<any> {
    try {
      const response = await fetch('/api/admin/infrastructure/railway/services', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get Railway service status:', error)
      throw error
    }
  }

  async getRailwayDeployments(limit: number = 10): Promise<any> {
    try {
      const response = await fetch(`/api/admin/infrastructure/railway/deployments?limit=${limit}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get Railway deployments:', error)
      throw error
    }
  }

  async triggerRailwayRedeploy(serviceId: string): Promise<any> {
    try {
      const response = await fetch('/api/admin/infrastructure/railway/redeploy', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ service_id: serviceId }),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to trigger Railway redeploy:', error)
      throw error
    }
  }

  // Agentic System Data Dashboard
  async getAgenticSystemOverview(): Promise<any> {
    try {
      const response = await fetch('/api/admin/agentic/overview', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        // Return mock data for development/testing
        if (response.status === 404) {
          console.warn('🤖 Agentic system overview endpoint not found, using mock data');
          return {
            success: true,
            data: {
              total_analyses: 156,
              total_queries: 89,
              ai_interactions: 245,
              success_rate: 94.2,
              avg_response_time: 1240
            }
          };
        }
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get agentic system overview:', error)
      return {
        success: false,
        data: {
          total_analyses: 0,
          total_queries: 0,
          ai_interactions: 0,
          success_rate: 0,
          avg_response_time: 0
        }
      };
    }
  }

  async getAgenticDataWithFilters(params: {
    page?: number
    limit?: number
    dataType?: 'resume_analysis' | 'legal_queries' | 'ai_interactions' | 'system_logs'
    status?: 'active' | 'completed' | 'failed' | 'pending'
    dateFrom?: string
    dateTo?: string
    userId?: string
    severity?: 'low' | 'medium' | 'high' | 'critical'
    search?: string
    sort?: 'created_at' | 'updated_at' | 'priority' | 'user_id'
    order?: 'asc' | 'desc'
  } = {}): Promise<any> {
    try {
      const queryParams = new URLSearchParams()
      
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString())
        }
      })
      
      const response = await fetch(`/api/admin/agentic/data?${queryParams.toString()}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        // Return mock data for development/testing
        if (response.status === 404) {
          console.warn('📋 Agentic data filtering endpoint not found, using mock data');
          return {
            success: true,
            data: {
              items: [
                {
                  id: 'mock-1',
                  type: 'resume_analysis',
                  status: 'completed',
                  created_at: new Date().toISOString(),
                  user_id: 'user-123',
                  metadata: { score: 85 }
                },
                {
                  id: 'mock-2',
                  type: 'legal_queries',
                  status: 'pending',
                  created_at: new Date(Date.now() - 1800000).toISOString(),
                  user_id: 'user-456',
                  metadata: { priority: 'high' }
                }
              ],
              total: 2,
              page: params.page || 1,
              limit: params.limit || 50
            }
          };
        }
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get agentic data:', error)
      return {
        success: false,
        data: {
          items: [],
          total: 0,
          page: params.page || 1,
          limit: params.limit || 50
        }
      };
    }
  }

  async getAgenticSystemMetrics(timeRange: '1h' | '24h' | '7d' | '30d' = '24h'): Promise<any> {
    try {
      const response = await fetch(`/api/admin/agentic/metrics?range=${timeRange}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        // Return mock data for development/testing
        if (response.status === 404) {
          console.warn('📊 Agentic system metrics endpoint not found, using mock data');
          return {
            success: true,
            data: {
              timeline: [
                { timestamp: new Date().toISOString(), analyses: 12, queries: 8 },
                { timestamp: new Date(Date.now() - 3600000).toISOString(), analyses: 15, queries: 6 }
              ],
              by_type: [
                { type: 'resume_analysis', count: 89 },
                { type: 'legal_queries', count: 34 },
                { type: 'ai_interactions', count: 122 }
              ],
              performance: {
                avg_processing_time: 1240,
                queue_size: 3,
                active_workers: 2
              }
            }
          };
        }
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get agentic system metrics:', error)
      return {
        success: false,
        data: {
          timeline: [],
          by_type: [],
          performance: {
            avg_processing_time: 0,
            queue_size: 0,
            active_workers: 0
          }
        }
      };
    }
  }

  // Enhanced Database Operations
  async getDatabaseConnectionPool(): Promise<any> {
    try {
      const response = await fetch('/api/admin/database/connections', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get database connection pool:', error)
      throw error
    }
  }

  async getDatabaseTableStats(): Promise<any> {
    try {
      const response = await fetch('/api/admin/database/tables/stats', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get database table stats:', error)
      throw error
    }
  }

  async performDatabaseMaintenance(operation: 'vacuum' | 'reindex' | 'analyze' | 'cleanup_logs'): Promise<any> {
    try {
      const response = await fetch('/api/admin/database/maintenance', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ operation }),
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to perform database maintenance:', error)
      throw error
    }
  }

  // Enhanced Railway Infrastructure Monitoring
  async getRailwayInfrastructureOverview(): Promise<any> {
    try {
      const response = await fetch('/api/admin/infrastructure/railway/overview', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        // Return mock data for development/testing
        if (response.status === 404) {
          console.warn('🚂 Railway infrastructure endpoint not found, using mock data');
          return {
            success: true,
            data: {
              database: {
                status: 'healthy',
                size: '1.2GB',
                connections: 15,
                cpu_usage: 25,
                memory_usage: 65,
                disk_usage: 40
              },
              services: [
                {
                  id: 'backend-service',
                  name: 'Backend API',
                  status: 'running',
                  cpu: 30,
                  memory: 70,
                  restarts: 0,
                  last_deploy: new Date().toISOString()
                }
              ],
              deployments: []
            }
          };
        }
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get Railway infrastructure overview:', error)
      // Return fallback mock data
      return {
        success: false,
        data: {
          database: {
            status: 'unknown',
            size: 'N/A',
            connections: 0,
            cpu_usage: 0,
            memory_usage: 0,
            disk_usage: 0
          },
          services: [],
          deployments: []
        }
      };
    }
  }

  async getRailwayDatabaseMetrics(): Promise<any> {
    try {
      const response = await fetch('/api/admin/infrastructure/railway/database/metrics', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get Railway database metrics:', error)
      throw error
    }
  }

  async getRailwayServiceLogs(serviceId: string, limit: number = 100): Promise<any> {
    try {
      const response = await fetch(`/api/admin/infrastructure/railway/services/${serviceId}/logs?limit=${limit}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get Railway service logs:', error)
      throw error
    }
  }

  // Real-time System Monitoring
  async getSystemResourceUsage(): Promise<any> {
    try {
      const response = await fetch('/api/admin/system/resources', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get system resource usage:', error)
      throw error
    }
  }

  async getSystemLogs(params: {
    level?: 'debug' | 'info' | 'warning' | 'error' | 'critical'
    service?: string
    limit?: number
    since?: string
  } = {}): Promise<any> {
    try {
      const queryParams = new URLSearchParams()
      
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString())
        }
      })
      
      const response = await fetch(`/api/admin/system/logs?${queryParams.toString()}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get system logs:', error)
      throw error
    }
  }

  // Database Operations
  async getUsersWithAdvancedFilters(params: {
    page?: number
    limit?: number
    search?: string
    accessType?: 'trial' | 'full' | 'admin'
    sort?: 'created_at' | 'last_login' | 'name' | 'email'
    order?: 'asc' | 'desc'
    dateFrom?: string
    dateTo?: string
    minCredits?: number
    maxCredits?: number
    status?: 'active' | 'inactive' | 'suspended'
  } = {}): Promise<any> {
    try {
      const queryParams = new URLSearchParams()
      
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString())
        }
      })
      
      const response = await fetch(`/api/admin/users?${queryParams.toString()}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get users with advanced filters:', error)
      throw error
    }
  }

  async getResumesWithAdvancedFilters(params: {
    page?: number
    limit?: number
    status?: 'pending' | 'processing' | 'completed' | 'failed'
    minScore?: number
    maxScore?: number
    userId?: string
    dateFrom?: string
    dateTo?: string
    sort?: 'upload_date' | 'filename' | 'overall_score' | 'processing_status'
    order?: 'asc' | 'desc'
    search?: string
  } = {}): Promise<any> {
    try {
      const queryParams = new URLSearchParams()
      
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString())
        }
      })
      
      const response = await fetch(`/api/admin/resumes?${queryParams.toString()}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed to get resumes with advanced filters:', error)
      throw error
    }
  }

  // Bulk Operations
  async bulkDeleteUsers(userIds: string[]): Promise<any> {
    try {
      const results = await Promise.allSettled(
        userIds.map(id => this.adminService.deleteUser(id))
      )
      
      const successful = results.filter(r => r.status === 'fulfilled').length
      const failed = results.filter(r => r.status === 'rejected').length
      
      return {
        success: true,
        data: {
          successful,
          failed,
          total: userIds.length
        }
      }
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed bulk delete users:', error)
      throw error
    }
  }

  async bulkDeleteResumes(resumeIds: string[]): Promise<any> {
    try {
      const results = await Promise.allSettled(
        resumeIds.map(id => this.adminService.deleteResume(id))
      )
      
      const successful = results.filter(r => r.status === 'fulfilled').length
      const failed = results.filter(r => r.status === 'rejected').length
      
      return {
        success: true,
        data: {
          successful,
          failed,
          total: resumeIds.length
        }
      }
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed bulk delete resumes:', error)
      throw error
    }
  }

  async bulkUpdateUserCredits(updates: Array<{ userId: string; credits: number; reason: string }>): Promise<any> {
    try {
      const results = await Promise.allSettled(
        updates.map(update => this.updateUserCredits(update.userId, update.credits, update.reason))
      )
      
      const successful = results.filter(r => r.status === 'fulfilled').length
      const failed = results.filter(r => r.status === 'rejected').length
      
      return {
        success: true,
        data: {
          successful,
          failed,
          total: updates.length
        }
      }
    } catch (error) {
      console.error('❌ EnhancedAdminService: Failed bulk update user credits:', error)
      throw error
    }
  }

  // Wrapper methods for common AdminService functionality
  async getDashboardStats() {
    return this.adminService.getDashboardStats()
  }

  async getUsers(params?: any) {
    return this.adminService.getUsers(params || {})
  }

  async createUser(userData: any) {
    return this.adminService.createUser(userData)
  }

  async updateUser(userId: string, userData: any) {
    return this.adminService.updateUser(userId, userData)
  }

  async deleteUser(userId: string) {
    return this.adminService.deleteUser(userId)
  }

  async resetUserTrial(userId: string) {
    return this.adminService.resetUserTrial(userId)
  }

  async getUserCredits(userId: string) {
    return this.adminService.getUserCredits(userId)
  }

  async getResumes(params?: any) {
    return this.adminService.getResumes(params || {})
  }

  async uploadResume(file: File, userId?: string) {
    return this.adminService.uploadResume(file, userId)
  }

  async deleteResume(resumeId: string) {
    return this.adminService.deleteResume(resumeId)
  }

  async analyzeResume(resumeId: string) {
    return this.adminService.analyzeResume(resumeId)
  }

  async batchAnalyzeResumes(resumeIds: string[]) {
    return this.adminService.batchAnalyzeResumes(resumeIds)
  }

  async getLegalQueries(params?: any) {
    return this.adminService.getLegalQueries(params || {})
  }

  async createLegalQuery(query: string) {
    return this.adminService.createLegalQuery(query)
  }

  async deleteLegalQuery(queryId: string) {
    return this.adminService.deleteLegalQuery(queryId)
  }

  async getActivityLog(params?: any) {
    return this.adminService.getActivityLog(params || {})
  }

  async getUsageStats() {
    return this.adminService.getUsageStats()
  }

  async getSystemHealth() {
    return this.adminService.getSystemHealth()
  }

  async getSystemSettings() {
    return this.adminService.getSystemSettings()
  }

  async updateSystemSettings(settings: any) {
    return this.adminService.updateSystemSettings(settings)
  }
}

// Export singleton instance
export const enhancedAdminService = new EnhancedAdminService()
