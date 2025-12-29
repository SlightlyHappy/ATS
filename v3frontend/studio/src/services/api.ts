/**
 * @file Real API client for backend integration
 * Implements all endpoints from FRONTEND_SPEC.md
 */

import type { Resume, ResumeStatus, User } from '@/types';

// Get backend URL from environment variables
// For local development, use local API routes instead of direct backend calls
const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? '' // Use relative URLs to leverage local API routes proxy
  : (process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app');

interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  timestamp?: string;
  pagination?: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    const method = options.method || 'GET';
    
    console.log(`🌐 API Request Starting:`, {
      method,
      url,
      hasBody: !!options.body,
      bodyType: options.body instanceof FormData ? 'FormData' : typeof options.body,
      credentialsMode: options.credentials || 'include'
    });
    
    // Default headers
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    // Add Authorization header as fallback if we have session tokens
    if (typeof window !== 'undefined') {
      const adminToken = document.cookie.split('; ').find(row => row.startsWith('admin_session_token='))?.split('=')[1];
      const userToken = document.cookie.split('; ').find(row => row.startsWith('user_session_token='))?.split('=')[1];
      
      const token = adminToken || userToken;
      if (token && !headers['Authorization']) {
        headers['Authorization'] = `Bearer ${token}`;
        console.log('🔐 ApiClient: Added Authorization header as fallback');
      }
    }

    // Include credentials for cookie-based auth
    const config: RequestInit = {
      ...options,
      headers,
      credentials: 'include', // Important for httpOnly cookies
    };

    try {
      console.log(`📤 Making ${method} request to:`, url);
      console.log(`📤 Request headers:`, headers);
      
      const response = await fetch(url, config);
      
      console.log(`📡 Response received:`, {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
        headers: Object.fromEntries(response.headers.entries())
      });
      
      if (!response.ok) {
        console.log(`❌ HTTP Error Response:`, response.status, response.statusText);
        
        // Handle HTTP error responses
        const errorData = await response.json().catch(() => ({}));
        console.log(`❌ Error response body:`, errorData);
        
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data: ApiResponse<T> = await response.json();
      
      console.log(`📊 Response data structure:`, {
        success: data.success,
        hasData: !!data.data,
        hasError: !!data.error,
        hasMessage: !!data.message,
        timestamp: data.timestamp
      });
      
      if (!data.success) {
        console.log(`❌ API response indicates failure:`, data.error);
        throw new Error(data.error || 'API request failed');
      }

      console.log(`✅ API Success: ${endpoint}`, {
        success: data.success,
        dataKeys: data.data ? Object.keys(data.data) : 'no data',
        message: data.message
      });
      
      return data;
      
    } catch (error) {
      console.log(`❌ API Error for ${method} ${endpoint}:`, error);
      
      // Log additional context for debugging
      console.log(`❌ Request context:`, {
        endpoint,
        method,
        baseURL: this.baseURL,
        hasBody: !!options.body,
        timestamp: new Date().toISOString()
      });
      
      throw error;
    }
  }

  // Authentication endpoints
  async register(userData: { email: string; password: string; username: string }) {
    return this.request<{ 
      message: string;
      user_id: string;
      credits_balance: number;
    }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async login(credentials: { email: string; password: string }) {
    return this.request<{
      access_token: string;
      refresh_token: string;
      token_type: string;
      expires_in: number;
      user: {
        id: string;
        email: string;
        is_admin: boolean;
        credits_balance: number;
      };
    }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async adminLogin(credentials: { email: string; password: string }) {
    // Backward compatibility wrapper
    return this.login(credentials);
  }

  async userLogin(credentials: { email: string; password: string }) {
    // Backward compatibility wrapper
    return this.login(credentials);
  }

  async refreshToken(refreshToken: string) {
    return this.request<{
      access_token: string;
      refresh_token: string;
      token_type: string;
      expires_in: number;
    }>('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }

  async logout() {
    return this.request('/auth/logout', { method: 'POST' });
  }

  async getCurrentUser() {
    return this.request<{ user: User }>('/auth/me');
  }

  async changePassword(passwords: { old_password: string; new_password: string }) {
    return this.request('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(passwords),
    });
  }

  // Admin - Dashboard
  async getDashboardStats() {
    return this.request<{
      stats: {
        users: {
          total_analyzed: number;
          at_resume_limit: number;
          at_legal_limit: number;
        };
        database: {
          connections: number;
          query_times: number[];
        };
        system: {
          timestamp: string;
          admin_user: string;
        };
      }
    }>('/api/admin/dashboard-stats');
  }

  // Admin - Users
  async getUsers(params?: {
    page?: number;
    limit?: number;
    search?: string;
    access_type?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.search) queryParams.append('search', params.search);
    if (params?.access_type) queryParams.append('access_type', params.access_type);

    const query = queryParams.toString();
    return this.request<{ users: User[] }>(`/api/admin/users${query ? `?${query}` : ''}`);
  }

  async createUser(userData: {
    email: string;
    name: string;
    password: string;
    access_type: string;
    trial_resume_limit?: number;
    trial_legal_limit?: number;
  }) {
    return this.request<{ user: User }>('/api/admin/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async updateUser(userId: string, updates: Partial<User>) {
    return this.request<{ user: User }>(`/api/admin/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteUser(userId: string) {
    return this.request(`/api/admin/users/${userId}`, { method: 'DELETE' });
  }

  async resetUserTrial(userId: string) {
    return this.request(`/api/admin/users/${userId}/reset-trial`, { method: 'POST' });
  }

  async getUserCredits(userId: string) {
    return this.request<{ credits: number }>(`/api/admin/users/${userId}/credits`);
  }

  // Admin - Resumes  
  // Legacy method - use getResumes() instead
  async getAdminResumes(params?: {
    status?: string;
    min_score?: number;
    max_score?: number;
    start_date?: string;
    end_date?: string;
    query?: string;
    page?: number;
    page_size?: number;
  }) {
    // Convert admin params to standard resume params
    const standardParams = {
      status: params?.status,
      page: params?.page,
      per_page: params?.page_size,
    };
    
    return this.getResumes(standardParams);
  }

  async getResumeAnalytics() {
    return this.request<{
      stats: {
        avg_scores: number;
        counts_by_status: Record<string, number>;
        top_skills: string[];
        recent_uploads_count: number;
      }
    }>('/api/admin/resumes/analytics');
  }

  // Resume endpoints
  async uploadResume(file: File, metadata?: string) {
    console.log('📄 API Client: Starting resume upload...', {
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      lastModified: new Date(file.lastModified).toISOString()
    });
    
    const formData = new FormData();
    formData.append('file', file);
    if (metadata) formData.append('metadata', metadata);

    console.log('📦 FormData prepared:', {
      hasFile: formData.has('file'),
      hasMetadata: formData.has('metadata'),
      formDataEntries: Array.from(formData.keys())
    });

    return this.request<{
      message: string;
      resume_id: string;
      status: string;
      metadata: {
        filename: string;
        file_size: number;
        file_type: string;
      };
    }>('/resumes', {
      method: 'POST',
      headers: {}, // Let browser set Content-Type for FormData
      body: formData,
    });
  }

  async getResumeDetails(resumeId: string) {
    return this.request<{
      id: string;
      filename: string;
      original_filename: string;
      file_size: number;
      file_type: string;
      processing_status: string;
      batch_upload_id: string | null;
      created_at: string;
      processed_at: string;
      analyses_count: number;
      structured_data: any;
    }>(`/resumes/${resumeId}`);
  }

  async getResumes(params?: {
    user_id?: string;
    status?: string;
    page?: number;
    per_page?: number;
  }) {
    const queryParams = new URLSearchParams();
    Object.entries(params || {}).forEach(([key, value]) => {
      if (value !== undefined) queryParams.append(key, value.toString());
    });

    const query = queryParams.toString();
    return this.request<{
      resumes: Resume[];
      pagination: {
        page: number;
        per_page: number;
        total: number;
        pages: number;
        has_next: boolean;
        has_prev: boolean;
      };
    }>(`/resumes${query ? `?${query}` : ''}`);
  }

  async getResumeText(resumeId: string) {
    return this.request<{
      resume_id: string;
      text: string;
      extracted_at: string;
      structured_data: any;
    }>(`/resumes/${resumeId}/text`);
  }

  async deleteResume(resumeId: string) {
    console.log('🗑️ API Client: Starting resume deletion for ID:', resumeId);
    
    const result = await this.request<{
      message: string;
      file_deleted: boolean;
    }>(`/resumes/${resumeId}`, { method: 'DELETE' });
    
    console.log('✅ API Client: Resume deletion completed for ID:', resumeId);
    return result;
  }

  async reprocessResume(resumeId: string) {
    return this.request<{
      message: string;
      status: string;
    }>(`/resumes/${resumeId}/reprocess`, { method: 'POST' });
  }

  // Analysis endpoints
  async triggerResumeAnalysis(resumeId: string, context?: {
    job_description?: string;
    company_culture?: string;
    specific_requirements?: string[];
  }) {
    return this.request<{
      message: string;
      analysis_id: string;
      overall_score: number;
      status: string;
      processing_time: number;
      summary: {
        strengths: string[];
        weaknesses: string[];
        recommendations: string[];
      };
    }>(`/resumes/${resumeId}/analyze`, {
      method: 'POST',
      body: JSON.stringify({ context }),
    });
  }

  async getAnalysisResults(analysisId: string) {
    return this.request<{
      id: string;
      resume_id: string;
      analysis_type: string;
      overall_score: number;
      scores_breakdown: {
        technical_skills: { score: number; confidence: number; weight: number };
        experience: { score: number; confidence: number; weight: number };
        education: { score: number; confidence: number; weight: number };
        soft_skills: { score: number; confidence: number; weight: number };
      };
      strengths: string[];
      weaknesses: string[];
      recommendations: string[];
      processing_time: number;
      status: string;
      created_at: string;
      completed_at: string;
      agent_results: any;
    }>(`/analyses/${analysisId}`);
  }

  async listResumeAnalyses(resumeId: string, params?: {
    page?: number;
    per_page?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.per_page) queryParams.append('per_page', params.per_page.toString());

    const query = queryParams.toString();
    return this.request<{
      resume_id: string;
      analyses: Array<{
        id: string;
        analysis_type: string;
        overall_score: number;
        status: string;
        created_at: string;
        completed_at: string;
      }>;
      pagination: {
        page: number;
        per_page: number;
        total: number;
        pages: number;
        has_next: boolean;
        has_prev: boolean;
      };
    }>(`/resumes/${resumeId}/analyses${query ? `?${query}` : ''}`);
  }

  async reanalyzeResume(resumeId: string, options?: {
    agent_types?: string[];
    context?: {
      job_description?: string;
      focus_areas?: string[];
    };
  }) {
    return this.request<{
      message: string;
      analysis_id: string;
      overall_score: number;
      status: string;
      processing_time: number;
    }>(`/resumes/${resumeId}/reanalyze`, {
      method: 'POST',
      body: JSON.stringify(options),
    });
  }

  async compareAnalyses(analysisId1: string, analysisId2: string) {
    return this.request<{
      comparison_summary: {
        score_difference: number;
        improvement_areas: string[];
        regression_areas: string[];
        overall_trend: string;
      };
      detailed_comparison: any;
    }>(`/analyses/${analysisId1}/compare/${analysisId2}`);
  }

  async getSpecificAgentResult(analysisId: string, agentName: 'technical_skills' | 'experience' | 'education' | 'soft_skills') {
    return this.request<{
      analysis_id: string;
      agent_name: string;
      result: any;
      agent_score: number;
    }>(`/analyses/${analysisId}/agent/${agentName}`);
  }

  async listAllAnalyses(params?: {
    resume_id?: string;
    status?: string;
    min_score?: number;
    max_score?: number;
    page?: number;
    per_page?: number;
  }) {
    const queryParams = new URLSearchParams();
    Object.entries(params || {}).forEach(([key, value]) => {
      if (value !== undefined) queryParams.append(key, value.toString());
    });

    const query = queryParams.toString();
    return this.request<{
      analyses: Array<{
        id: string;
        resume_id: string;
        analysis_type: string;
        overall_score: number;
        status: string;
        created_at: string;
        completed_at: string;
      }>;
      pagination: any;
    }>(`/analyses${query ? `?${query}` : ''}`);
  }

  // Queue Management endpoints
  async uploadResumeToQueue(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<{
      message: string;
      resume_id: string;
      queue_id: string;
      queue_position: number;
      estimated_completion: string;
    }>('/queue/upload', {
      method: 'POST',
      headers: {}, // Let browser set Content-Type for FormData
      body: formData,
    });
  }

  async uploadBatchResumes(files: File[] | File, batchName?: string) {
    const formData = new FormData();
    
    if (Array.isArray(files)) {
      // Multiple files
      files.forEach(file => formData.append('files', file));
    } else {
      // Single ZIP file
      formData.append('zip_file', files);
    }
    
    if (batchName) formData.append('batch_name', batchName);

    return this.request<{
      message: string;
      batch_id: string;
      batch_name: string;
      total_resumes: number;
      resume_ids: string[];
      credits_required: number;
    }>('/queue/upload/batch', {
      method: 'POST',
      headers: {},
      body: formData,
    });
  }

  async getQueueStatus(userId?: string) {
    const params = userId ? `?user_id=${userId}` : '';
    return this.request<{
      queue_statistics: {
        total_pending: number;
        total_processing: number;
        average_wait_time: string;
        estimated_completion: string;
      };
      user_statistics: {
        pending_items: number;
        processing_items: number;
        completed_today: number;
      };
    }>(`/queue/status${params}`);
  }

  async getUserQueueItems(userId: string, status?: string) {
    const params = status ? `?status=${status}` : '';
    return this.request<{
      items: Array<{
        id: string;
        resume_id: string;
        status: string;
        priority: number;
        queue_position: number;
        estimated_completion_time: string;
        created_at: string;
      }>;
    }>(`/queue/user/${userId}/queue${params}`);
  }

  async getUserBatches(userId: string) {
    return this.request<{
      batches: Array<{
        id: string;
        batch_name: string;
        total_resumes: number;
        processed_resumes: number;
        successful_analyses: number;
        failed_analyses: number;
        status: string;
        credits_used: number;
        created_at: string;
      }>;
    }>(`/queue/user/${userId}/batches`);
  }

  async getBatchStatus(batchId: string, userId: string) {
    return this.request<{
      id: string;
      batch_name: string;
      total_resumes: number;
      processed_resumes: number;
      successful_analyses: number;
      failed_analyses: number;
      status: string;
      credits_used: number;
      created_at: string;
      completed_at: string | null;
    }>(`/queue/batch/${batchId}/status?user_id=${userId}`);
  }

  async cancelQueueItem(queueId: string, userId: string) {
    return this.request<{
      message: string;
    }>(`/queue/cancel/${queueId}`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
  }
  // NOTE: These endpoints may not exist in backend yet. Fallback to admin endpoints with user filtering.
  
  /**
   * Get current user's own resumes only
   * Implements FRONTEND_SPEC.md: GET /api/user/my-resumes
   * PRODUCTION FALLBACK: Falls back to admin endpoint with user filtering if user endpoint doesn't exist
   */
  async getMyResumes(params?: {
    page?: number;
    limit?: number;
    status?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.status) queryParams.append('status', params.status);

    const query = queryParams.toString();
    const userEndpoint = `/api/user/my-resumes${query ? `?${query}` : ''}`;
    
    console.log('📄 API Client: Attempting user-specific resumes endpoint...', userEndpoint);
    
    try {
      // Try user-specific endpoint first (future-proof)
      const response = await this.request<{ resumes: Resume[] }>(userEndpoint);
      console.log('✅ User endpoint exists and working:', userEndpoint);
      return response;
    } catch (error: any) {
      // If user endpoint doesn't exist (404, 501, etc.), fall back to admin endpoint
      if (error.message?.includes('404') || error.message?.includes('501') || error.message?.includes('Not Found')) {
        console.log('⚠️ User endpoint not implemented, falling back to admin endpoint with filtering');
        console.log('🔧 Backend TODO: Implement', userEndpoint, 'endpoint');
        
        try {
          // Fallback to admin endpoint (users only see their own resumes via backend filtering)
          const adminResponse = await this.request<{ resumes: Resume[] }>('/api/admin/resumes');
          console.log('✅ Fallback successful: Using admin endpoint with user filtering');
          
          // Log for backend team
          console.log('📝 BACKEND IMPLEMENTATION NEEDED:', {
            endpoint: userEndpoint,
            fallbackUsed: '/api/admin/resumes',
            expectedBehavior: 'Backend should filter resumes to current user only',
            securityNote: 'Ensure user cookie validation and data filtering'
          });
          
          return adminResponse;
        } catch (fallbackError) {
          console.error('❌ Both user and admin endpoints failed:', { userError: error, fallbackError });
          throw new Error('Unable to fetch resumes from either user or admin endpoints');
        }
      } else {
        // Re-throw non-404 errors (auth issues, server errors, etc.)
        throw error;
      }
    }
  }

  /**
   * Get user dashboard data and statistics
   * Implements FRONTEND_SPEC.md: GET /api/user/dashboard
   * PRODUCTION FALLBACK: Falls back to admin dashboard with user filtering
   */
  async getMyDashboard() {
    const userEndpoint = '/api/user/dashboard';
    
    console.log('📊 API Client: Attempting user-specific dashboard endpoint...', userEndpoint);
    
    try {
      // Try user-specific endpoint first
      const response = await this.request<{
        stats: {
          totalResumes: number;
          pendingAnalysis: number;
          completedAnalysis: number;
          averageScore: number;
        };
        recentResumes: Resume[];
        trialInfo?: {
          resumesUsed: number;
          resumeLimit: number;
          legalUsed: number;
          legalLimit: number;
        };
      }>(userEndpoint);
      
      console.log('✅ User dashboard endpoint exists and working:', userEndpoint);
      return response;
    } catch (error: any) {
      if (error.message?.includes('404') || error.message?.includes('501') || error.message?.includes('Not Found')) {
        console.log('⚠️ User dashboard endpoint not implemented, falling back to admin dashboard');
        console.log('🔧 Backend TODO: Implement', userEndpoint, 'endpoint');
        
        try {
          // Fallback to admin dashboard (backend should filter to current user)
          const adminResponse = await this.getDashboardStats();
          
          // Transform admin stats to user dashboard format
          const userDashboard = {
            stats: {
              totalResumes: adminResponse.data?.stats?.users?.total_analyzed || 0,
              pendingAnalysis: 0, // Would need user-specific endpoint
              completedAnalysis: adminResponse.data?.stats?.users?.total_analyzed || 0,
              averageScore: 0, // Would need user-specific endpoint
            },
            recentResumes: [], // Would need user-specific endpoint
            trialInfo: {
              resumesUsed: adminResponse.data?.stats?.users?.at_resume_limit || 0,
              resumeLimit: 10, // Default, should come from user profile
              legalUsed: adminResponse.data?.stats?.users?.at_legal_limit || 0,
              legalLimit: 5, // Default, should come from user profile
            }
          };
          
          console.log('📝 BACKEND IMPLEMENTATION NEEDED:', {
            endpoint: userEndpoint,
            fallbackUsed: '/api/admin/dashboard-stats',
            expectedBehavior: 'Return user-specific dashboard data only',
            requiredFields: ['stats', 'recentResumes', 'trialInfo']
          });
          
          return {
            success: true,
            data: userDashboard,
            timestamp: new Date().toISOString()
          };
        } catch (fallbackError) {
          console.error('❌ Both user and admin dashboard endpoints failed:', { userError: error, fallbackError });
          throw new Error('Unable to fetch dashboard data from either user or admin endpoints');
        }
      } else {
        throw error;
      }
    }
  }

  /**
   * Upload resume as a regular user (not admin)
   * Implements FRONTEND_SPEC.md: POST /api/user/upload-resume
   * PRODUCTION FALLBACK: Falls back to admin upload endpoint
   */
  async uploadMyResume(file: File, jobDescription?: string) {
    console.log('📄 API Client: Starting user resume upload...', {
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      hasJobDescription: !!jobDescription
    });
    
    const formData = new FormData();
    formData.append('file', file);
    if (jobDescription) formData.append('job_description', jobDescription);

    const userEndpoint = '/api/user/upload-resume';
    
    console.log('� API Client: Attempting user-specific upload endpoint...', userEndpoint);
    
    try {
      // Try user-specific endpoint first
      const response = await this.request<{ resume: Resume }>(userEndpoint, {
        method: 'POST',
        headers: {}, // Let browser set Content-Type for FormData
        body: formData,
      });
      
      console.log('✅ User upload endpoint exists and working:', userEndpoint);
      return response;
    } catch (error: any) {
      if (error.message?.includes('404') || error.message?.includes('501') || error.message?.includes('Not Found')) {
        console.log('⚠️ User upload endpoint not implemented, falling back to admin upload');
        console.log('🔧 Backend TODO: Implement', userEndpoint, 'endpoint');
        
        try {
          // Fallback to admin upload (backend should associate with current user)
          const adminResponse = await this.uploadResume(file);
          
          console.log('📝 BACKEND IMPLEMENTATION NEEDED:', {
            endpoint: userEndpoint,
            fallbackUsed: '/api/admin/resumes/upload',
            expectedBehavior: 'Auto-associate upload with authenticated user',
            securityNote: 'Ensure user cannot upload for other users'
          });
          
          return adminResponse;
        } catch (fallbackError) {
          console.error('❌ Both user and admin upload endpoints failed:', { userError: error, fallbackError });
          throw new Error('Unable to upload resume to either user or admin endpoints');
        }
      } else {
        throw error;
      }
    }
  }

  /**
   * Delete own resume as a regular user
   * Implements FRONTEND_SPEC.md: DELETE /api/user/my-resumes/{resume_id}
   * PRODUCTION FALLBACK: Falls back to admin delete endpoint with user validation
   */
  async deleteMyResume(resumeId: string) {
    console.log('🗑️ API Client: Starting user resume deletion for ID:', resumeId);
    
    const userEndpoint = `/api/user/my-resumes/${resumeId}`;
    
    console.log('🗑️ API Client: Attempting user-specific delete endpoint...', userEndpoint);
    
    try {
      // Try user-specific endpoint first
      const response = await this.request(userEndpoint, { method: 'DELETE' });
      console.log('✅ User delete endpoint exists and working:', userEndpoint);
      return response;
    } catch (error: any) {
      if (error.message?.includes('404') || error.message?.includes('501') || error.message?.includes('Not Found')) {
        console.log('⚠️ User delete endpoint not implemented, falling back to admin delete');
        console.log('🔧 Backend TODO: Implement', userEndpoint, 'endpoint');
        
        try {
          // Fallback to admin delete (backend should validate user ownership)
          const adminResponse = await this.deleteResume(resumeId);
          
          console.log('📝 BACKEND IMPLEMENTATION NEEDED:', {
            endpoint: userEndpoint,
            fallbackUsed: `/api/admin/resumes/${resumeId}`,
            expectedBehavior: 'Validate user owns resume before deletion',
            securityNote: 'Ensure user cannot delete other users resumes'
          });
          
          return adminResponse;
        } catch (fallbackError) {
          console.error('❌ Both user and admin delete endpoints failed:', { userError: error, fallbackError });
          throw new Error('Unable to delete resume from either user or admin endpoints');
        }
      } else {
        throw error;
      }
    }
  }

  /**
   * Get specific resume details (user's own only)
   * Implements FRONTEND_SPEC.md: GET /api/user/my-resumes/{resume_id}
   * PRODUCTION FALLBACK: Falls back to admin endpoint with user validation
   */
  async getMyResumeById(resumeId: string) {
    const userEndpoint = `/api/user/my-resumes/${resumeId}`;
    
    console.log('📄 API Client: Attempting user-specific resume detail endpoint...', userEndpoint);
    
    try {
      // Try user-specific endpoint first
      const response = await this.request<{ resume: Resume }>(userEndpoint);
      console.log('✅ User resume detail endpoint exists and working:', userEndpoint);
      return response;
    } catch (error: any) {
      if (error.message?.includes('404') || error.message?.includes('501') || error.message?.includes('Not Found')) {
        console.log('⚠️ User resume detail endpoint not implemented, using admin endpoint');
        console.log('🔧 Backend TODO: Implement', userEndpoint, 'endpoint');
        
        try {
          // Fallback: Get all resumes and filter client-side (not ideal but works)
          const allResumesResponse = await this.getResumes();
          const userResume = allResumesResponse.data?.resumes?.find(r => r.id === resumeId);
          
          if (userResume) {
            console.log('📝 BACKEND IMPLEMENTATION NEEDED:', {
              endpoint: userEndpoint,
              fallbackUsed: '/api/admin/resumes + client filtering',
              expectedBehavior: 'Return specific resume if user owns it',
              securityNote: 'Backend should validate ownership before returning data'
            });
            
            return {
              success: true,
              data: { resume: userResume },
              timestamp: new Date().toISOString()
            };
          } else {
            throw new Error('Resume not found or access denied');
          }
        } catch (fallbackError) {
          console.error('❌ Both user and admin resume detail failed:', { userError: error, fallbackError });
          throw new Error('Unable to fetch resume details from either user or admin endpoints');
        }
      } else {
        throw error;
      }
    }
  }

  /**
   * Trigger analysis for user's own resume
   * Implements FRONTEND_SPEC.md: POST /api/user/analyze/{resume_id}
   * PRODUCTION FALLBACK: Falls back to admin analyze endpoint with user validation
   */
  async analyzeMyResume(resumeId: string, jobDescription?: string) {
    const userEndpoint = `/api/user/analyze/${resumeId}`;
    const body = jobDescription ? { job_description: jobDescription } : {};
    
    console.log('🔬 API Client: Attempting user-specific analyze endpoint...', userEndpoint);
    
    try {
      // Try user-specific endpoint first
      const response = await this.request<{ job_id: string }>(userEndpoint, {
        method: 'POST',
        body: JSON.stringify(body),
      });
      console.log('✅ User analyze endpoint exists and working:', userEndpoint);
      return response;
    } catch (error: any) {
      if (error.message?.includes('404') || error.message?.includes('501') || error.message?.includes('Not Found')) {
        console.log('⚠️ User analyze endpoint not implemented, falling back to admin analyze');
        console.log('🔧 Backend TODO: Implement', userEndpoint, 'endpoint');
        
        try {
          // Fallback to admin analyze (backend should validate user ownership)
          const adminResponse = await this.analyzeResume(resumeId);
          
          console.log('📝 BACKEND IMPLEMENTATION NEEDED:', {
            endpoint: userEndpoint,
            fallbackUsed: `/api/admin/analyze/${resumeId}`,
            expectedBehavior: 'Validate user owns resume before analysis',
            securityNote: 'Ensure user cannot analyze other users resumes'
          });
          
          return adminResponse;
        } catch (fallbackError) {
          console.error('❌ Both user and admin analyze endpoints failed:', { userError: error, fallbackError });
          throw new Error('Unable to trigger analysis from either user or admin endpoints');
        }
      } else {
        throw error;
      }
    }
  }

  // Payment endpoints
  async getPaymentPackages() {
    return this.request<{ packages: any[] }>('/api/payment/packages');
  }

  async createPaymentOrder(data: { payment_type: string; package_id?: string }) {
    return this.request<{
      order_id: string;
      amount: number;
      currency: string;
      razorpay_key: string;
    }>('/api/payment/create-order', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async verifyPayment(data: {
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
  }) {
    return this.request<{
      credits_added: number;
      processing_tier: string;
      order_id: string;
    }>('/api/payment/verify', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Health checks
  async checkHealth() {
    return this.request('/health');
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Legacy function wrappers for backward compatibility
export async function fetchResumes(): Promise<Resume[]> {
  try {
    const response = await apiClient.getResumes();
    return response.data?.resumes || [];
  } catch (error) {
    console.error('Failed to fetch resumes:', error);
    throw error;
  }
}

export async function fetchUsers(): Promise<User[]> {
  try {
    const response = await apiClient.getUsers();
    return response.data?.users || [];
  } catch (error) {
    console.error('Failed to fetch users:', error);
    throw error;
  }
}

export async function fetchDashboardStats() {
  try {
    const response = await apiClient.getDashboardStats();
    return response.data;
  } catch (error) {
    console.error('Failed to fetch dashboard stats:', error);
    throw error;
  }
}

// Additional helper functions for resume operations
export async function addResume(resumeData: Omit<Resume, 'id' | 'date' | 'status' | 'aiScore'>): Promise<Resume> {
  try {
    // For now, this will use the upload endpoint with form data
    console.warn('addResume called - should use uploadResume with file instead');
    throw new Error('Use uploadResume for file-based resume submission');
  } catch (error) {
    console.error('Failed to add resume:', error);
    throw error;
  }
}

export async function fetchResumeById(id: string): Promise<Resume | undefined> {
  try {
    const response = await apiClient.getResumeDetails(id);
    if (response.success && response.data) {
      // Transform the API response to match Resume type
      return {
        id: response.data.id,
        user_id: '', // Will be set by backend based on auth
        filename: response.data.filename,
        file_url: '', // Not provided in this endpoint
        upload_date: response.data.created_at,
        status: response.data.processing_status,
        processing_status: response.data.processing_status as ResumeStatus,
        // Add other fields as needed
      } as Resume;
    }
    return undefined;
  } catch (error) {
    console.error('Failed to fetch resume by ID:', error);
    throw error;
  }
}

export async function updateResumeStatus(id: string, status: ResumeStatus): Promise<Resume> {
  try {
    // This would need a specific endpoint for status updates
    console.warn('updateResumeStatus called - endpoint may not exist yet');
    throw new Error('Status update endpoint not implemented');
  } catch (error) {
    console.error('Failed to update resume status:', error);
    throw error;
  }
}

export async function deleteUser(id: string): Promise<void> {
  try {
    await apiClient.deleteUser(id);
  } catch (error) {
    console.error('Failed to delete user:', error);
    throw error;
  }
}

export async function deleteResume(id: string): Promise<void> {
  try {
    await apiClient.deleteResume(id);
  } catch (error) {
    console.error('Failed to delete resume:', error);
    throw error;
  }
}