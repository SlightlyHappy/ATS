import api, { apiCall } from './api'
import type { QueueItem, QueueStats, BatchUpload } from '../types'

export const queueService = {
  // Queue Upload
  async uploadToQueue(file: File): Promise<{ message: string; resume_id: string; queue_id: string; queue_position: number; estimated_completion: string }> {
    const formData = new FormData()
    formData.append('file', file)

    return apiCall(() => api.post('/queue/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }))
  },

  async uploadBatch(files: File[] | File, batchName?: string): Promise<{ message: string; batch_id: string; batch_name: string; total_resumes: number; resume_ids: string[]; credits_required: number }> {
    const formData = new FormData()
    
    if (Array.isArray(files)) {
      files.forEach(file => formData.append('files', file))
    } else {
      formData.append('zip_file', files)
    }
    
    if (batchName) {
      formData.append('batch_name', batchName)
    }

    return apiCall(() => api.post('/queue/upload/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }))
  },

  // Queue Status
  async getQueueStatus(userId?: string): Promise<{ queue_statistics: QueueStats; user_statistics: any }> {
    const params = userId ? { user_id: userId } : {}
    return apiCall(() => api.get('/queue/status', { params }))
  },

  async getUserQueueItems(userId: string, status?: string): Promise<{ items: QueueItem[] }> {
    const params = status ? { status } : {}
    return apiCall(() => api.get(`/queue/user/${userId}/queue`, { params }))
  },

  async getUserBatches(userId: string): Promise<{ batches: BatchUpload[] }> {
    return apiCall(() => api.get(`/queue/user/${userId}/batches`))
  },

  async getBatchStatus(batchId: string, userId: string): Promise<BatchUpload> {
    return apiCall(() => api.get(`/queue/batch/${batchId}/status`, {
      params: { user_id: userId }
    }))
  },

  async cancelQueueItem(queueId: string, userId: string): Promise<{ message: string }> {
    return apiCall(() => api.post(`/queue/cancel/${queueId}`, { user_id: userId }))
  }
}
