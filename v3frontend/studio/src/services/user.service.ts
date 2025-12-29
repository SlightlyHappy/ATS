/**
 * @file User-specific API service for user dashboard and operations
 * Updated to use real API client from FRONTEND_SPEC.md
 */

import { apiClient } from './api';

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

class UserServiceClass {
  /**
   * Get user dashboard data including stats and recent resumes
   * FIXED: Now uses user-specific dashboard endpoint per FRONTEND_SPEC.md
   */
  async getDashboardData(): Promise<ApiResponse<UserDashboardData>> {
    console.log('📊 UserService: Fetching user dashboard data via /api/user/dashboard...')
    
    try {
      console.log('📤 Making API call to user dashboard endpoint...')
      
      // FIXED: Use user-specific dashboard endpoint instead of admin endpoint
      const response = await apiClient.getMyDashboard();
      
      console.log('📡 User dashboard response:', {
        success: response.success,
        hasData: !!response.data,
        error: response.error,
        endpoint: '/api/user/dashboard'
      })
      
      if (response.success && response.data) {
        console.log('✅ User dashboard data loaded successfully:', {
          totalResumes: response.data.stats.totalResumes,
          recentCount: response.data.recentResumes?.length || 0,
          hasTrialInfo: !!response.data.trialInfo,
          endpoint: '/api/user/dashboard'
        });

        // Transform the API response to match UserDashboardData interface
        const transformedData: UserDashboardData = {
          stats: response.data.stats,
          recentResumes: response.data.recentResumes.map(resume => ({
            id: resume.id,
            filename: resume.filename,
            status: resume.processing_status,
            score: resume.overall_score,
            uploadDate: resume.upload_date,
          })),
          trialInfo: response.data.trialInfo,
        };

        return {
          success: true,
          data: transformedData,
          timestamp: new Date().toISOString()
        };
      }
      
      console.log('❌ Dashboard stats response indicates failure')
      throw new Error(response.error || 'Failed to load dashboard data');
    } catch (error) {
      console.log('❌ UserService.getDashboardData error:', error);
      
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to load dashboard data',
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Get current user's own resumes only
   * FIXED: Now uses user-specific endpoint per FRONTEND_SPEC.md
   */
  async getMyResumes(): Promise<ApiResponse<{ resumes: Resume[] }>> {
    try {
      console.log('📄 UserService: Fetching user resumes via /api/user/my-resumes...');
      
      // FIXED: Use user-specific endpoint instead of admin endpoint
      const response = await apiClient.getMyResumes();
      
      if (response.success && response.data?.resumes) {
        console.log('✅ UserService: User resumes loaded successfully:', {
          count: response.data.resumes.length,
          endpoint: '/api/user/my-resumes'
        });
        
        return {
          success: true,
          data: {
            resumes: response.data.resumes
          },
          timestamp: new Date().toISOString()
        };
      }
      
      throw new Error(response.error || 'Failed to load resumes');
    } catch (error) {
      console.error('❌ UserService.getMyResumes error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to load resumes',
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Submit a new resume for analysis
   * FIXED: Now uses user-specific upload endpoint
   */
  async submitResume(file: File, jobDescription?: string): Promise<ApiResponse<Resume>> {
    console.log('📄 UserService: Starting resume submission...', {
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      hasJobDescription: !!jobDescription,
      endpoint: '/api/user/upload-resume'
    })
    
    try {
      console.log('📤 Uploading resume via user-specific endpoint...')
      
      // FIXED: Use user-specific upload endpoint instead of admin endpoint
      const response = await apiClient.uploadMyResume(file, jobDescription);
      
      console.log('📡 User resume upload response:', {
        success: response.success,
        hasData: !!response.data,
        hasResume: !!response.data?.resume,
        error: response.error,
        endpoint: '/api/user/upload-resume'
      })
      
      if (response.success && response.data?.resume) {
        console.log('✅ Resume submitted successfully via user endpoint:', {
          resumeId: response.data.resume.id,
          filename: response.data.resume.filename,
          status: response.data.resume.processing_status
        })
        
        return {
          success: true,
          data: response.data.resume,
          timestamp: new Date().toISOString()
        };
      }
      
      console.log('❌ Resume submission failed - no resume data in response')
      throw new Error(response.error || 'Failed to submit resume');
    } catch (error) {
      console.log('❌ UserService.submitResume error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to submit resume',
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Delete own resume
   * FIXED: Now uses user-specific delete endpoint
   */
  async deleteMyResume(resumeId: string): Promise<ApiResponse> {
    console.log('🗑️ UserService: Starting resume deletion for ID:', resumeId, 'via /api/user/my-resumes/{id}')
    
    try {
      // FIXED: Use user-specific delete endpoint instead of admin endpoint
      const response = await apiClient.deleteMyResume(resumeId);
      
      console.log('📡 User resume deletion response:', {
        success: response.success,
        error: response.error,
        endpoint: `/api/user/my-resumes/${resumeId}`
      })
      
      if (response.success) {
        console.log('✅ Resume deleted successfully via user endpoint:', resumeId)
        return {
          success: true,
          timestamp: new Date().toISOString()
        };
      }
      
      throw new Error(response.error || 'Failed to delete resume');
    } catch (error) {
      console.log('❌ UserService.deleteMyResume error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to delete resume',
        timestamp: new Date().toISOString()
      };
    }
  }
}

// Export singleton instance
export const UserService = new UserServiceClass();
