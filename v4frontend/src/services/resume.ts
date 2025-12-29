import api, { apiCall } from './api'
import type { Resume, Analysis, QueueItem, BatchUpload } from '../types'

export const resumeService = {
  // Resume Management
  async uploadResume(file: File, metadata?: any): Promise<{ message: string; resume_id: string; status: string; metadata: any }> {
    const formData = new FormData()
    formData.append('file', file)
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata))
    }

    return apiCall(() => api.post('/resumes', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }))
  },

  async getResumes(params?: { page?: number; per_page?: number; status?: string }): Promise<{ resumes: Resume[]; pagination: any }> {
    return apiCall(() => api.get('/resumes', { params }))
  },

  async getResume(resumeId: string): Promise<Resume> {
    return apiCall(() => api.get(`/resumes/${resumeId}`))
  },

  async getResumeText(resumeId: string): Promise<{ resume_id: string; text: string; extracted_at: string; structured_data: any }> {
    return apiCall(() => api.get(`/resumes/${resumeId}/text`))
  },

  async deleteResume(resumeId: string): Promise<{ message: string; file_deleted: boolean }> {
    return apiCall(() => api.delete(`/resumes/${resumeId}`))
  },

  async reprocessResume(resumeId: string): Promise<{ message: string; status: string }> {
    return apiCall(() => api.post(`/resumes/${resumeId}/reprocess`))
  },

  // Analysis Management
  async analyzeResume(resumeId: string, context?: any): Promise<Analysis> {
    return apiCall(() => api.post(`/resumes/${resumeId}/analyze`, context ? { context } : {}))
  },

  async getAnalysis(analysisId: string): Promise<Analysis> {
    return apiCall(() => api.get(`/analyses/${analysisId}`))
  },

  async getResumeAnalyses(resumeId: string, params?: { page?: number; per_page?: number }): Promise<{ resume_id: string; analyses: Analysis[]; pagination: any }> {
    return apiCall(() => api.get(`/resumes/${resumeId}/analyses`, { params }))
  },

  async reanalyzeResume(resumeId: string, options?: { agent_types?: string[]; context?: any }): Promise<Analysis> {
    return apiCall(() => api.post(`/resumes/${resumeId}/reanalyze`, options || {}))
  },

  async compareAnalyses(analysisId1: string, analysisId2: string): Promise<any> {
    return apiCall(() => api.get(`/analyses/${analysisId1}/compare/${analysisId2}`))
  },

  async getAgentResult(analysisId: string, agentName: string): Promise<any> {
    return apiCall(() => api.get(`/analyses/${analysisId}/agent/${agentName}`))
  },

  async getAllAnalyses(params?: { resume_id?: string; status?: string; min_score?: number; max_score?: number; page?: number; per_page?: number }): Promise<{ analyses: Analysis[]; pagination: any }> {
    return apiCall(() => api.get('/analyses', { params }))
  }
}
