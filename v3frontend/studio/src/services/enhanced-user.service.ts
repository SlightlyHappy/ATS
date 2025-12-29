/**
 * @file Enhanced User service with backend v1.3 user endpoints
 * Replaces admin fallbacks with direct user endpoints
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app'

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
  timestamp: string
}

export interface UserDashboardData {
  stats: {
    totalResumes: number;
    pendingAnalysis: number;
    completedAnalysis: number;
    averageScore: number;
  };
  recentResumes: {
    id: string;
    filename: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    score?: number;
    uploadDate: string;
  }[];
  trialInfo?: {
    resumesUsed: number;
    resumeLimit: number;
    legalUsed: number;
    legalLimit: number;
  };
  credits?: {
    balance: number;
    lastUpdated: string;
  };
}

export interface Resume {
  id: string;
  filename: string;
  upload_date: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  overall_score?: number;
  analysis_result?: any;
  file_url: string;
}

export interface EnhancedUserProfile {
  user_id: string;
  email: string;
  name: string;
  access_type: 'admin' | 'user';
  is_trial: boolean;
  trial_info?: {
    resume_limit: number;
    legal_limit: number;
    used_resumes: number;
    used_legal: number;
  };
  created_at: string;
  last_login?: string;
}

class EnhancedUserServiceClass {

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Default headers
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    // Remove Content-Type for FormData
    if (options.body instanceof FormData) {
      delete headers['Content-Type'];
    }

    const config: RequestInit = {
      ...options,
      headers,
      credentials: 'include', // Important for httpOnly cookies
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data: ApiResponse<T> = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'API request failed');
      }
      
      return data;
    } catch (error) {
      throw error;
    }
  }
  
  /**
   * Get user dashboard data - BACKEND v1.3 ENDPOINT
   * Uses: GET /api/user/dashboard
   */
  async getDashboardData(): Promise<ApiResponse<UserDashboardData>> {
    console.log('📊 Enhanced UserService: Fetching dashboard via v1.3 endpoint...')
    
    try {
      const response = await this.request<UserDashboardData>('/api/user/dashboard');
      
      console.log('📡 v1.3 User dashboard response:', {
        success: response.success,
        hasStats: !!response.data?.stats,
        recentCount: response.data?.recentResumes?.length || 0,
        hasCredits: !!response.data?.credits
      });
      
      return {
        success: true,
        data: response.data!,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('❌ Enhanced UserService.getDashboardData error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to load dashboard data',
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Get user's own resumes - BACKEND v1.3 ENDPOINT
   * Uses: GET /api/user/my-resumes
   */
  async getMyResumes(params?: {
    page?: number;
    limit?: number;
    status?: string;
  }): Promise<ApiResponse<{ resumes: Resume[] }>> {
    try {
      console.log('📄 Enhanced UserService: Fetching resumes via v1.3 endpoint...', params);
      
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      if (params?.status) queryParams.append('status', params.status);
      
      const endpoint = `/api/user/my-resumes${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const response = await this.request<{ resumes: Resume[] }>(endpoint);
      
      console.log('📡 v1.3 User resumes response:', {
        success: response.success,
        count: response.data?.resumes?.length || 0,
        endpoint
      });
      
      return {
        success: true,
        data: { resumes: response.data!.resumes },
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('❌ Enhanced UserService.getMyResumes error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to load resumes',
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Get specific resume details - BACKEND v1.3 ENDPOINT
   * Uses: GET /api/user/my-resumes/{resume_id}
   */
  async getMyResumeById(resumeId: string): Promise<ApiResponse<Resume>> {
    try {
      console.log('📄 Enhanced UserService: Fetching resume details via v1.3 endpoint...', resumeId);
      
      const response = await this.request<Resume>(`/api/user/my-resumes/${resumeId}`);
      
      console.log('✅ v1.3 Resume details loaded:', response.data?.filename);
      return {
        success: true,
        data: response.data!,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('❌ Enhanced UserService.getMyResumeById error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to load resume details',
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Submit a new resume - BACKEND v1.3 ENDPOINT
   * Uses: POST /api/user/upload-resume
   */
  async submitResume(file: File, jobDescription?: string): Promise<ApiResponse<Resume>> {
    console.log('📄 Enhanced UserService: Uploading resume via v1.3 endpoint...', {
      fileName: file.name,
      fileSize: file.size,
      hasJobDescription: !!jobDescription
    });
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (jobDescription) {
        formData.append('job_description', jobDescription);
      }
      
      const response = await this.request<{ resume: Resume }>('/api/user/upload-resume', {
        method: 'POST',
        body: formData
      });
      
      console.log('📡 v1.3 Resume upload response:', {
        success: response.success,
        resumeId: response.data?.resume?.id,
        filename: response.data?.resume?.filename
      });
      
      return {
        success: true,
        data: response.data!.resume,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('❌ Enhanced UserService.submitResume error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to upload resume',
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Delete own resume - BACKEND v1.3 ENDPOINT
   * Uses: DELETE /api/user/my-resumes/{resume_id}
   */
  async deleteMyResume(resumeId: string): Promise<ApiResponse> {
    try {
      console.log('🗑️ Enhanced UserService: Deleting resume via v1.3 endpoint...', resumeId);
      
      const response = await this.request(`/api/user/my-resumes/${resumeId}`, {
        method: 'DELETE'
      });
      
      console.log('📡 v1.3 Resume deletion response success');
      
      return {
        success: true,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('❌ Enhanced UserService.deleteMyResume error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to delete resume',
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Get user profile - BACKEND v1.3 ENDPOINT
   * Uses: GET /api/user/profile
   */
  async getProfile(): Promise<ApiResponse<EnhancedUserProfile>> {
    try {
      console.log('👤 Enhanced UserService: Fetching profile via v1.3 endpoint...');
      
      const response = await this.request<EnhancedUserProfile>('/api/user/profile');
      
      console.log('✅ v1.3 User profile loaded:', response.data?.email);
      return {
        success: true,
        data: response.data!,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('❌ Enhanced UserService.getProfile error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to load profile',
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Update user profile - BACKEND v1.3 ENDPOINT
   * Uses: PUT /api/user/profile
   */
  async updateProfile(updates: Partial<EnhancedUserProfile>): Promise<ApiResponse<EnhancedUserProfile>> {
    try {
      console.log('👤 Enhanced UserService: Updating profile via v1.3 endpoint...', updates);
      
      const response = await this.request<EnhancedUserProfile>('/api/user/profile', {
        method: 'PUT',
        body: JSON.stringify(updates)
      });
      
      console.log('✅ v1.3 Profile updated successfully');
      return {
        success: true,
        data: response.data!,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('❌ Enhanced UserService.updateProfile error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update profile',
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Get user credits balance - BACKEND v1.3 ENDPOINT
   * Uses: GET /api/user/credits
   */
  async getCredits(): Promise<ApiResponse<{ balance: number; history: any[] }>> {
    try {
      console.log('💰 Enhanced UserService: Fetching credits via v1.3 endpoint...');
      
      const response = await this.request<{ balance: number; history: any[] }>('/api/user/credits');
      
      console.log('✅ v1.3 Credits loaded:', response.data?.balance);
      return {
        success: true,
        data: response.data!,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('❌ Enhanced UserService.getCredits error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to load credits',
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Get legal queries history - BACKEND v1.3 ENDPOINT
   * Uses: GET /api/user/legal-queries
   */
  async getLegalQueries(params?: {
    page?: number;
    limit?: number;
  }): Promise<ApiResponse<{ queries: any[] }>> {
    try {
      console.log('⚖️ Enhanced UserService: Fetching legal queries via v1.3 endpoint...', params);
      
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      
      const endpoint = `/api/user/legal-queries${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const response = await this.request<{ queries: any[] }>(endpoint);
      
      console.log('✅ v1.3 Legal queries loaded:', response.data?.queries.length);
      return {
        success: true,
        data: response.data!,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('❌ Enhanced UserService.getLegalQueries error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to load legal queries',
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Submit legal query - BACKEND v1.3 ENDPOINT
   * Uses: POST /api/user/legal-query
   */
  async submitLegalQuery(query: string): Promise<ApiResponse<any>> {
    try {
      console.log('⚖️ Enhanced UserService: Submitting legal query via v1.3 endpoint...');
      
      const response = await this.request('/api/user/legal-query', {
        method: 'POST',
        body: JSON.stringify({ query })
      });
      
      console.log('✅ v1.3 Legal query submitted successfully');
      return {
        success: true,
        data: response.data,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('❌ Enhanced UserService.submitLegalQuery error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to submit legal query',
        timestamp: new Date().toISOString()
      };
    }
  }
}

// Export singleton instance
export const EnhancedUserService = new EnhancedUserServiceClass();
