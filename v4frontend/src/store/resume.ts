import { create } from 'zustand'
import type { Resume, Analysis, QueueItem, BatchUpload } from '../types'
import { resumeService } from '../services/resume'
import { queueService } from '../services/queue'

interface ResumeState {
  resumes: Resume[]
  analyses: Analysis[]
  queueItems: QueueItem[]
  batches: BatchUpload[]
  isLoading: boolean
  error: string | null
  uploadProgress: number

  // Actions
  uploadResume: (file: File, metadata?: any) => Promise<string>
  fetchResumes: (params?: any) => Promise<void>
  fetchAnalyses: (resumeId?: string, params?: any) => Promise<void>
  analyzeResume: (resumeId: string, context?: any) => Promise<string>
  deleteResume: (resumeId: string) => Promise<void>
  fetchQueueItems: (userId: string, status?: string) => Promise<void>
  uploadBatch: (files: File[] | File, batchName?: string) => Promise<string>
  clearError: () => void
  setUploadProgress: (progress: number) => void
}

export const useResumeStore = create<ResumeState>((set, get) => ({
  resumes: [],
  analyses: [],
  queueItems: [],
  batches: [],
  isLoading: false,
  error: null,
  uploadProgress: 0,

  uploadResume: async (file: File, metadata?: any) => {
    set({ isLoading: true, error: null, uploadProgress: 0 })

    try {
      const response = await resumeService.uploadResume(file, metadata)
      
      // Refresh resumes list
      await get().fetchResumes()
      
      set({ isLoading: false, uploadProgress: 100 })
      return response.resume_id
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.error || 'Upload failed',
        uploadProgress: 0
      })
      throw error
    }
  },

  fetchResumes: async (params?: any) => {
    set({ isLoading: true, error: null })

    try {
      const response = await resumeService.getResumes(params)
      set({
        resumes: response.resumes,
        isLoading: false
      })
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.error || 'Failed to fetch resumes'
      })
    }
  },

  fetchAnalyses: async (resumeId?: string, params?: any) => {
    set({ isLoading: true, error: null })

    try {
      let response
      if (resumeId) {
        response = await resumeService.getResumeAnalyses(resumeId, params)
        set({
          analyses: response.analyses,
          isLoading: false
        })
      } else {
        response = await resumeService.getAllAnalyses(params)
        set({
          analyses: response.analyses,
          isLoading: false
        })
      }
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.error || 'Failed to fetch analyses'
      })
    }
  },

  analyzeResume: async (resumeId: string, context?: any) => {
    set({ isLoading: true, error: null })

    try {
      const analysis = await resumeService.analyzeResume(resumeId, context)
      
      // Add the new analysis to the list
      set(state => ({
        analyses: [...state.analyses, analysis],
        isLoading: false
      }))
      
      return analysis.id
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.error || 'Analysis failed'
      })
      throw error
    }
  },

  deleteResume: async (resumeId: string) => {
    set({ isLoading: true, error: null })

    try {
      await resumeService.deleteResume(resumeId)
      
      // Remove the resume from the list
      set(state => ({
        resumes: state.resumes.filter(resume => resume.id !== resumeId),
        analyses: state.analyses.filter(analysis => analysis.resume_id !== resumeId),
        isLoading: false
      }))
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.error || 'Delete failed'
      })
      throw error
    }
  },

  fetchQueueItems: async (userId: string, status?: string) => {
    try {
      const response = await queueService.getUserQueueItems(userId, status)
      set({ queueItems: response.items })
    } catch (error: any) {
      set({ error: error.error || 'Failed to fetch queue items' })
    }
  },

  uploadBatch: async (files: File[] | File, batchName?: string) => {
    set({ isLoading: true, error: null, uploadProgress: 0 })

    try {
      const response = await queueService.uploadBatch(files, batchName)
      
      // Refresh data
      await get().fetchResumes()
      
      set({ isLoading: false, uploadProgress: 100 })
      return response.batch_id
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.error || 'Batch upload failed',
        uploadProgress: 0
      })
      throw error
    }
  },

  clearError: () => {
    set({ error: null })
  },

  setUploadProgress: (progress: number) => {
    set({ uploadProgress: progress })
  }
}))
