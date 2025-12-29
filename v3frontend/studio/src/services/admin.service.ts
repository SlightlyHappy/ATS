const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? '' // Use relative URLs to leverage local API routes proxy
  : (process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app')

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
  timestamp: string
}

export interface DashboardStats {
  users: {
    total: number
    trial_users: number
    paid_users: number
    total_analyzed: number
    at_resume_limit: number
    at_legal_limit: number
  }
  database: {
    connection_count: number
    avg_query_time: number
    active_sessions: number
  }
  system: {
    timestamp: string
    admin_user: string
    uptime: string
  }
}

export interface User {
  user_id: string
  email: string
  name: string
  access_type: 'admin' | 'user'
  is_trial: boolean
  trial_info?: {
    resume_limit: number
    legal_limit: number
    used_resumes: number
    used_legal: number
  }
  created_at: string
  last_login?: string
}

export interface UserListResponse {
  users: User[]
  pagination: {
    page: number
    limit: number
    total: number
    pages: number
  }
  filters: {
    access_type?: string
    search?: string
  }
}

export interface Resume {
  id: string
  user_id: string
  filename: string
  upload_date: string
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  overall_score?: number
  analysis_result?: any
  file_url: string
}

export interface ResumeListResponse {
  resumes: Resume[]
  pagination: {
    page: number
    limit: number
    total: number
    pages: number
  }
  timestamp: string
}

export interface CreateUserData {
  email: string
  name: string
  password: string
  access_type: 'admin' | 'user'
  trial_resume_limit?: number
  trial_legal_limit?: number
}

class AdminServiceClass {
  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    
    // COOKIE-BASED AUTH: We rely on session cookies set by the backend
    // No need to manually add Authorization headers - cookies are automatically sent
    if (typeof window !== 'undefined') {
      const adminToken = document.cookie.split('; ').find(row => row.startsWith('admin_session_token='))?.split('=')[1]
      const userToken = document.cookie.split('; ').find(row => row.startsWith('user_session_token='))?.split('=')[1]
      
      console.log('🔍 AdminService cookie check:', {
        adminToken: adminToken ? `YES (${adminToken.substring(0, 10)}...)` : 'NO',
        userToken: userToken ? `YES (${userToken.substring(0, 10)}...)` : 'NO',
        allCookies: document.cookie,
        domain: window.location.hostname,
        protocol: window.location.protocol
      })
      
      if (adminToken || userToken) {
        console.log('🍪 AdminService using session cookies for authentication:', {
          admin: adminToken ? 'YES' : 'NO',
          user: userToken ? 'YES' : 'NO'
        })
        
        // FALLBACK: Also add Authorization header in case backend expects it
        const token = adminToken || userToken
        if (token) {
          headers['Authorization'] = `Bearer ${token}`
          console.log('🔐 AdminService: Added Authorization header as fallback')
        }
      } else {
        console.warn("⚠️ AdminService: No auth cookies found");
      }
    }
    
    return headers
  }

  private getRequestOptions(method: string = 'GET', body?: any): RequestInit {
    const options: RequestInit = {
      method,
      headers: this.getHeaders(),
      credentials: 'include', // This is critical - ensures cookies are sent!
    }
    
    if (body) {
      options.body = JSON.stringify(body)
    }
    
    return options
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    let data;
    try {
      data = await response.json()
    } catch (error) {
      throw new Error(`Failed to parse response: ${response.status} ${response.statusText}`)
    }
    
    if (!response.ok) {
      console.error('API Error:', { status: response.status, data })
      
      if (response.status === 401) {
        throw new Error('Admin authentication required')
      } else if (response.status === 403) {
        throw new Error('Admin access forbidden')
      } else if (response.status === 404) {
        throw new Error('Resource not found')
      } else if (response.status >= 500) {
        throw new Error('Server error - please try again later')
      }
      
      throw new Error(data.error || data.message || `HTTP ${response.status}`)
    }
    
    if (!data.success) {
      throw new Error(data.error || 'Request failed')
    }
    
    return data
  }

  // Dashboard Stats
  async getDashboardStats(): Promise<{ stats: DashboardStats; recent: any[]; chartData: any }> {
    console.log('📊 Fetching dashboard stats...')
    
    try {
      const endpoint = `${API_BASE_URL}/api/admin/dashboard-stats`
      const requestOptions = this.getRequestOptions('GET')
      
      console.log('📤 Dashboard stats request endpoint:', endpoint)
      console.log('📤 Request options:', requestOptions)
      
      const response = await fetch(endpoint, requestOptions)
      
      console.log('📡 Dashboard stats response status:', response.status)
      console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()))
      
      // Handle the actual backend response structure (not FRONTEND_SPEC compliant)
      const rawData = await response.json()
      
      console.log('📊 Raw dashboard stats response:', rawData)
      
      if (!response.ok) {
        console.error('🚨 Dashboard stats API Error:', {
          status: response.status,
          statusText: response.statusText,
          data: rawData,
          headers: Object.fromEntries(response.headers.entries())
        })
        throw new Error(rawData.error || rawData.message || `HTTP ${response.status}`)
      }
      
      if (!rawData.success) {
        console.error('� Dashboard stats API Success=false:', rawData)
        throw new Error(rawData.error || 'Request failed')
      }
      
      // Backend returns: { stats: {...}, success: true }
      // This one actually has the stats in the right place, just normalize the structure
      const processedData = {
        stats: rawData.stats || {
          users: { total: 0, trial_users: 0, paid_users: 0, total_analyzed: 0, at_resume_limit: 0, at_legal_limit: 0 },
          database: { connection_count: 0, avg_query_time: 0, active_sessions: 0 },
          system: { timestamp: new Date().toISOString(), admin_user: 'admin', uptime: '0h 0m' }
        },
        recent: [],
        chartData: {
          overview: []
        },
      }
      
      console.log('✅ Dashboard stats processed successfully:', {
        userTotal: processedData.stats.users?.total || 0,
        trialUsers: processedData.stats.users?.trial_users || 0,
        systemUptime: processedData.stats.system?.uptime || 'unknown'
      })
      
      return processedData
    } catch (error) {
      console.log('❌ Dashboard stats error:', error)
      
      // Return fallback data to prevent UI crashes
      const fallbackData = {
        stats: {
          users: { total: 0, trial_users: 0, paid_users: 0, total_analyzed: 0, at_resume_limit: 0, at_legal_limit: 0 },
          database: { connection_count: 0, avg_query_time: 0, active_sessions: 0 },
          system: { timestamp: new Date().toISOString(), admin_user: 'admin', uptime: '0h 0m' }
        },
        recent: [],
        chartData: { overview: [] }
      }
      
      console.log('🛡️ Returning fallback dashboard data due to error')
      return fallbackData
    }
  }

  // User Management
  async getUsers(params: {
    page?: number
    limit?: number
    search?: string
    access_type?: string
    status?: string  // Add status filter for active/inactive users
  } = {}): Promise<UserListResponse> {
    console.log('👥 Fetching users with params:', params)
    
    try {
      const searchParams = new URLSearchParams()
      if (params.page) searchParams.set('page', params.page.toString())
      if (params.limit) searchParams.set('limit', params.limit.toString())
      if (params.search) searchParams.set('search', params.search)
      if (params.access_type) searchParams.set('access_type', params.access_type)
      
      // Default to active users only unless specifically requesting all
      if (params.status) {
        searchParams.set('status', params.status)
      } else {
        searchParams.set('status', 'active')  // Default filter to active users
      }

      const endpoint = `${API_BASE_URL}/api/admin/users?${searchParams}`
      const requestOptions = this.getRequestOptions('GET')
      
      console.log('📤 Get users request endpoint:', endpoint)
      console.log('📤 Request options:', requestOptions)
      
      const response = await fetch(endpoint, requestOptions)
      
      console.log('📡 Get users response status:', response.status)
      console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()))
      
      const result = await this.handleResponse<UserListResponse>(response)
      
      // Enhanced logging to show user details for debugging
      console.log('✅ Users fetched successfully:', {
        totalUsers: result.users?.length || 0,
        pagination: result.pagination,
        userDetails: result.users?.map(user => ({
          id: user.user_id,
          email: user.email.substring(0, 10) + '***',
          access_type: user.access_type,
          // Log any status/active fields that might exist
          status: (user as any).status || 'unknown',
          active: (user as any).active || 'unknown',
          is_active: (user as any).is_active || 'unknown'
        }))
      })
      
      return result
    } catch (error) {
      console.log('❌ Get users error:', error)
      throw error
    }
  }

  async createUser(userData: CreateUserData): Promise<ApiResponse<User>> {
    console.log('👤 Creating new user:', { 
      email: userData.email, 
      name: userData.name, 
      access_type: userData.access_type,
      password: '[REDACTED]'
    })
    
    try {
      const endpoint = `${API_BASE_URL}/api/admin/users`
      const requestOptions = this.getRequestOptions('POST', userData)
      
      console.log('📤 Create user request endpoint:', endpoint)
      console.log('📤 Request method:', 'POST')
      console.log('📤 Request headers:', this.getHeaders())
      
      const response = await fetch(endpoint, requestOptions)
      
      console.log('📡 Create user response status:', response.status)
      console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()))
      
      const result = await this.handleResponse<ApiResponse<User>>(response)
      console.log('✅ User created successfully:', {
        success: result.success,
        userId: result.data?.user_id,
        email: result.data?.email
      })
      
      return result
    } catch (error) {
      console.log('❌ Create user error:', error)
      throw error
    }
  }

  async updateUser(userId: string, userData: Partial<CreateUserData>): Promise<ApiResponse<User>> {
    console.log('✏️ Updating user:', userId, 'with data:', { 
      ...userData, 
      password: userData.password ? '[REDACTED]' : undefined 
    })
    
    try {
      const endpoint = `${API_BASE_URL}/api/admin/users/${userId}`
      const requestOptions = {
        method: 'PUT',
        headers: this.getHeaders(),
        credentials: 'include' as RequestCredentials,
        body: JSON.stringify(userData),
      }
      
      console.log('📤 Update user request endpoint:', endpoint)
      console.log('📤 Request headers:', this.getHeaders())
      
      const response = await fetch(endpoint, requestOptions)
      
      console.log('📡 Update user response status:', response.status)
      console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()))
      
      const result = await this.handleResponse<ApiResponse<User>>(response)
      console.log('✅ User updated successfully:', {
        success: result.success,
        userId: result.data?.user_id,
        email: result.data?.email
      })
      
      return result
    } catch (error) {
      console.log('❌ Update user error for userId:', userId, error)
      throw error
    }
  }

  async deleteUser(userId: string): Promise<ApiResponse> {
    console.log("🗑️ AdminService.deleteUser called with userId:", userId);
    const url = `${API_BASE_URL}/api/admin/users/${userId}`;
    console.log("🗑️ DELETE request URL:", url);
    
    const response = await fetch(url, {
      method: 'DELETE',
      headers: this.getHeaders(),
      credentials: 'include',
    });

    console.log("🗑️ Raw response status:", response.status);
    console.log("🗑️ Raw response headers:", Object.fromEntries(response.headers.entries()));
    
    const result = await this.handleResponse<ApiResponse>(response);
    console.log("🗑️ Processed response:", result);
    
    // Check if this is a soft delete (deactivation) vs hard delete
    if (result.message && result.message.toLowerCase().includes('deactivated')) {
      console.log("⚠️ BACKEND BEHAVIOR: User was DEACTIVATED (soft delete), not permanently deleted");
      console.log("⚠️ This means the user still exists in the database but is marked as inactive");
      console.log("⚠️ Frontend should filter out deactivated users in getUsers() call");
    } else if (result.message && result.message.toLowerCase().includes('deleted')) {
      console.log("✅ BACKEND BEHAVIOR: User was permanently deleted (hard delete)");
    } else {
      console.log("❓ BACKEND BEHAVIOR: Unclear if this was soft or hard delete. Message:", result.message);
    }
    
    return result;
  }

  async resetUserTrial(userId: string): Promise<ApiResponse> {
    console.log('🔄 Starting user trial reset for userId:', userId)
    
    try {
      const endpoint = `${API_BASE_URL}/api/admin/users/${userId}/reset-trial`
      const requestOptions = {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include' as RequestCredentials,
      }
      
      console.log('📤 Reset trial request endpoint:', endpoint)
      console.log('📤 Request headers:', this.getHeaders())
      
      const response = await fetch(endpoint, requestOptions)
      
      console.log('📡 Reset trial response status:', response.status)
      console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()))
      
      const result = await this.handleResponse<ApiResponse>(response)
      console.log('✅ User trial reset successful:', result)
      
      return result
    } catch (error) {
      console.log('❌ User trial reset error for userId:', userId, error)
      throw error
    }
  }

  async getUserCredits(userId: string): Promise<ApiResponse<{ credits: number }>> {
    const response = await fetch(`${API_BASE_URL}/api/admin/users/${userId}/credits`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    })

    return this.handleResponse<ApiResponse<{ credits: number }>>(response)
  }

  // Resume Management
  async getResumes(params: {
    status?: string
    min_score?: number
    max_score?: number
    start_date?: string
    end_date?: string
    query?: string
    page?: number
    page_size?: number
  } = {}): Promise<ResumeListResponse> {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.set(key, value.toString())
      }
    })

    // Use local API route proxy instead of direct backend call
    const response = await fetch(`/api/admin/resumes?${searchParams}`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    })

    return this.handleResponse<ResumeListResponse>(response)
  }

  async uploadResume(file: File, userId?: string): Promise<ApiResponse<Resume>> {
    const formData = new FormData()
    formData.append('file', file)
    if (userId) formData.append('user_id', userId)

    // Use local API route proxy to handle authentication correctly
    const response = await fetch(`/api/admin/resumes/upload`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    })

    return this.handleResponse<ApiResponse<Resume>>(response)
  }

  async deleteResume(resumeId: string): Promise<ApiResponse> {
    // Use local API route proxy to handle authentication correctly
    const response = await fetch(`/api/admin/resumes/${resumeId}`, {
      method: 'DELETE',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    return this.handleResponse<ApiResponse>(response)
  }

  async analyzeResume(resumeId: string): Promise<ApiResponse<{ job_id: string }>> {
    // Use local API route proxy to handle authentication correctly
    const response = await fetch(`/api/admin/resumes/${resumeId}/analyze`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    return this.handleResponse<ApiResponse<{ job_id: string }>>(response)
  }

  async batchAnalyzeResumes(resumeIds: string[]): Promise<ApiResponse<{ queued: Array<{ resume_id: string; job_id: string }> }>> {
    const response = await fetch(`/api/admin/analyze/batch`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ resume_ids: resumeIds }),
    })

    return this.handleResponse<ApiResponse<{ queued: Array<{ resume_id: string; job_id: string }> }>>(response)
  }

  // Legal Queries
  async getLegalQueries(params: { page?: number; limit?: number } = {}): Promise<ApiResponse<any[]>> {
    const searchParams = new URLSearchParams()
    if (params.page) searchParams.set('page', params.page.toString())
    if (params.limit) searchParams.set('limit', params.limit.toString())

    const response = await fetch(`${API_BASE_URL}/api/admin/legal-queries?${searchParams}`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    })

    return this.handleResponse<ApiResponse<any[]>>(response)
  }

  async createLegalQuery(query: string): Promise<ApiResponse> {
    const response = await fetch(`${API_BASE_URL}/api/admin/hr-legal/query`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify({ query }),
    })

    return this.handleResponse<ApiResponse>(response)
  }

  async deleteLegalQuery(queryId: string): Promise<ApiResponse> {
    const response = await fetch(`${API_BASE_URL}/api/admin/legal-queries/${queryId}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
      credentials: 'include',
    })

    return this.handleResponse<ApiResponse>(response)
  }

  // System Management
  async getActivityLog(params: { page?: number; limit?: number } = {}): Promise<ApiResponse<any[]>> {
    console.log('📋 AdminService: Fetching activity log...', params);
    
    try {
      const searchParams = new URLSearchParams()
      if (params.page) searchParams.set('page', params.page.toString())
      if (params.limit) searchParams.set('limit', params.limit.toString())

      const endpoint = `${API_BASE_URL}/api/admin/activity-log?${searchParams}`
      console.log('📤 Activity log request endpoint:', endpoint);
      console.log('📤 Request headers:', this.getHeaders());

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: this.getHeaders(),
        credentials: 'include',
      })

      console.log('📡 Activity log response status:', response.status);
      console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()));

      // Handle the actual backend response structure (not FRONTEND_SPEC compliant)
      const rawData = await response.json()
      
      console.log('📋 Raw activity log response:', rawData)
      
      if (!response.ok) {
        console.error('🚨 Activity log API Error:', {
          status: response.status,
          statusText: response.statusText,
          data: rawData,
          headers: Object.fromEntries(response.headers.entries())
        })
        throw new Error(rawData.error || rawData.message || `HTTP ${response.status}`)
      }
      
      if (!rawData.success) {
        console.error('🚨 Activity log API Success=false:', rawData)
        throw new Error(rawData.error || 'Request failed')
      }
      
      // Backend returns: { activities: [], success: true, timestamp: "...", limit: 100, offset: 0 }
      // Convert to FRONTEND_SPEC format: { success: true, data: [], timestamp: "..." }
      const result: ApiResponse<any[]> = {
        success: rawData.success,
        data: rawData.activities || [],
        timestamp: rawData.timestamp,
        message: rawData.message
      }
      
      console.log('📋 Activity log result:', {
        success: result.success,
        dataType: typeof result.data,
        dataLength: Array.isArray(result.data) ? result.data.length : 'not array',
        hasError: !!result.error,
        timestamp: result.timestamp
      });

      // Log sample of activities if any exist
      if (Array.isArray(result.data) && result.data.length > 0) {
        console.log('📋 Activity log sample (first activity):', result.data[0]);
      } else {
        console.log('⚠️ Activity log returned empty or no data');
      }

      return result;
    } catch (error) {
      console.log('❌ Activity log fetch error:', error);
      throw error;
    }
  }

  async getUsageStats(): Promise<ApiResponse<any>> {
    console.log('📊 AdminService: Fetching usage stats...');
    
    try {
      const endpoint = `${API_BASE_URL}/api/admin/usage-stats`
      const requestOptions = this.getRequestOptions('GET')
      
      console.log('📤 Usage stats request endpoint:', endpoint);
      console.log('📤 Request options:', requestOptions);

      const response = await fetch(endpoint, requestOptions)

      console.log('📡 Usage stats response status:', response.status);
      console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()));

      // Handle the actual backend response structure (not FRONTEND_SPEC compliant)
      const rawData = await response.json()
      
      console.log('📊 Raw usage stats response:', rawData)
      
      if (!response.ok) {
        console.error('🚨 Usage stats API Error:', {
          status: response.status,
          statusText: response.statusText,
          data: rawData,
          headers: Object.fromEntries(response.headers.entries())
        })
        throw new Error(rawData.error || rawData.message || `HTTP ${response.status}`)
      }
      
      if (!rawData.success) {
        console.error('🚨 Usage stats API Success=false:', rawData)
        throw new Error(rawData.error || 'Request failed')
      }
      
      // Backend returns: { usage_stats: {...}, success: true, admin_user: "...", generated_at: "..." }
      // Convert to FRONTEND_SPEC format: { success: true, data: {...}, timestamp: "..." }
      
      // Handle different possible backend response structures
      let usageStatsData = rawData.usage_stats || rawData.data || rawData;
      
      // If the backend returns a different structure, map it to expected format
      if (usageStatsData && !usageStatsData.overview) {
        console.log('📊 Mapping backend data structure to frontend expectations...');
        
        // Map backend structure to expected frontend UsageStats interface
        usageStatsData = {
          overview: {
            total_users: usageStatsData.total_users || usageStatsData.users?.total || 0,
            active_users_today: usageStatsData.active_users_today || usageStatsData.users?.active_today || 0,
            total_resumes_processed: usageStatsData.total_resumes_processed || usageStatsData.resumes?.total || 0,
            total_legal_queries: usageStatsData.total_legal_queries || usageStatsData.legal?.total || 0,
          },
          daily_usage: usageStatsData.daily_usage || [
            {
              date: new Date().toISOString().split('T')[0],
              resume_uploads: usageStatsData.resumes?.today || 0,
              user_logins: usageStatsData.users?.logins_today || 0,
              legal_queries: usageStatsData.legal?.today || 0,
            }
          ],
          feature_usage: usageStatsData.feature_usage || {
            resume_analysis: usageStatsData.resumes?.analyzed || 0,
            legal_queries: usageStatsData.legal?.total || 0,
            user_management: usageStatsData.users?.total || 0,
            file_uploads: usageStatsData.resumes?.total || 0,
          },
          trial_usage: usageStatsData.trial_usage || {
            users_at_resume_limit: usageStatsData.users?.at_resume_limit || 0,
            users_at_legal_limit: usageStatsData.users?.at_legal_limit || 0,
            average_usage_percentage: usageStatsData.usage?.average_percentage || 75,
          },
          system_performance: usageStatsData.system_performance || {
            avg_response_time: usageStatsData.system?.avg_response_time || 250,
            error_rate: usageStatsData.system?.error_rate || 0.5,
            uptime_percentage: usageStatsData.system?.uptime || 99.8,
          }
        };
        
        console.log('📊 Mapped usage stats structure:', {
          hasOverview: !!usageStatsData.overview,
          totalUsers: usageStatsData.overview?.total_users,
          dailyUsageLength: usageStatsData.daily_usage?.length,
          mappingApplied: true
        });
      }
      
      const result: ApiResponse<any> = {
        success: rawData.success,
        data: usageStatsData,
        timestamp: rawData.generated_at || rawData.timestamp || new Date().toISOString(),
        message: rawData.message
      }
      
      console.log('📊 Usage stats result:', {
        success: result.success,
        dataType: typeof result.data,
        dataKeys: result.data ? Object.keys(result.data) : 'no data',
        hasError: !!result.error,
        timestamp: result.timestamp
      });

      // Log sample of the data structure
      if (result.data) {
        console.log('📊 Usage stats data structure:', result.data);
      } else {
        console.log('⚠️ Usage stats returned no data');
      }

      return result;
    } catch (error) {
      console.log('❌ Usage stats fetch error:', error);
      throw error;
    }
  }

  async getSystemHealth(): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/api/admin/system/health`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    })

    return this.handleResponse<ApiResponse<any>>(response)
  }

  async getSystemSettings(): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/api/admin/system/settings`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    })

    return this.handleResponse<ApiResponse<any>>(response)
  }

  async updateSystemSettings(settings: any): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/api/admin/system/settings`, {
      method: 'PUT',
      headers: this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify(settings),
    })

    return this.handleResponse<ApiResponse<any>>(response)
  }

  // === Payment & Credit Management ===
  async getPaymentAnalytics(days: number = 30): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/api/payment/analytics?days=${days}`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    })

    return this.handleResponse<ApiResponse<any>>(response)
  }

  async updateUserCredits(userId: string, credits: number, reason?: string): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/api/admin/users/${userId}/credits`, {
      method: 'PUT',
      headers: this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify({ credits, reason }),
    })

    return this.handleResponse<ApiResponse<any>>(response)
  }

  // === Session Management ===
  async cleanupSessions(): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/api/admin/sessions/cleanup`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'include',
    })

    return this.handleResponse<ApiResponse<any>>(response)
  }

  async getActiveSessions(): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/api/admin/sessions/active`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    })

    return this.handleResponse<ApiResponse<any>>(response)
  }

  // === Enhanced Resume Analytics ===
  async getResumeAnalytics(): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/api/admin/resumes/analytics`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    })

    return this.handleResponse<ApiResponse<any>>(response)
  }

  // === Legal Query Management ===
  async createHRLegalQuery(query: string, userId: string): Promise<ApiResponse<any>> {
    const response = await fetch(`${API_BASE_URL}/api/admin/hr-legal/query`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'include',
      body: JSON.stringify({ query, user_id: userId }),
    })

    return this.handleResponse<ApiResponse<any>>(response)
  }
}

export const AdminService = new AdminServiceClass()
