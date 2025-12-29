/**
 * @file Monitoring service for system health and performance
 * Implements backend v1.3 monitoring endpoints
 */

interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  components: {
    database: {
      status: 'healthy' | 'degraded' | 'unhealthy';
      connection_count: number;
      avg_query_time: number;
      last_backup: string;
    };
    redis: {
      status: 'healthy' | 'degraded' | 'unhealthy';
      memory_usage: number;
      connected_clients: number;
    };
    storage: {
      status: 'healthy' | 'degraded' | 'unhealthy';
      disk_usage: number;
      available_space: number;
    };
    ai_service: {
      status: 'healthy' | 'degraded' | 'unhealthy';
      response_time: number;
      queue_length: number;
    };
  };
}

interface PerformanceMetrics {
  timestamp: string;
  api_response_times: {
    avg: number;
    p95: number;
    p99: number;
  };
  throughput: {
    requests_per_minute: number;
    resumes_processed_per_hour: number;
  };
  resource_usage: {
    cpu_percent: number;
    memory_percent: number;
    disk_io: number;
  };
  error_rates: {
    total_errors: number;
    error_rate_percent: number;
    top_errors: Array<{
      error: string;
      count: number;
    }>;
  };
}

interface BackupSyncStatus {
  last_sync: string;
  status: 'success' | 'failed' | 'in_progress';
  next_scheduled: string;
  backup_size: number;
  error_message?: string;
}

class MonitoringServiceClass {

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://hrtoolsbackend-production.up.railway.app';
    const url = `${API_BASE_URL}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    const config: RequestInit = {
      ...options,
      headers,
      credentials: 'include',
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'API request failed');
      }
      
      return data.data;
    } catch (error) {
      console.error('❌ MonitoringService request failed:', endpoint, error);
      throw error;
    }
  }

  /**
   * Get overall system health status
   * Uses: GET /api/monitoring/health
   */
  async getSystemHealth(): Promise<SystemHealth> {
    try {
      console.log('🏥 MonitoringService: Fetching system health...');
      
      const data = await this.request<SystemHealth>('/api/monitoring/health');
      
      console.log('✅ System health loaded:', data.status);
      return data;
    } catch (error) {
      console.error('❌ MonitoringService.getSystemHealth error:', error);
      
      // Return fallback data for UI consistency
      return {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        components: {
          database: { status: 'unhealthy', connection_count: 0, avg_query_time: 0, last_backup: '' },
          redis: { status: 'unhealthy', memory_usage: 0, connected_clients: 0 },
          storage: { status: 'unhealthy', disk_usage: 0, available_space: 0 },
          ai_service: { status: 'unhealthy', response_time: 0, queue_length: 0 }
        }
      };
    }
  }

  /**
   * Get performance metrics
   * Uses: GET /api/monitoring/performance
   */
  async getPerformanceMetrics(): Promise<PerformanceMetrics> {
    try {
      console.log('📈 MonitoringService: Fetching performance metrics...');
      
      const data = await this.request<PerformanceMetrics>('/api/monitoring/performance');
      
      console.log('✅ Performance metrics loaded');
      return data;
    } catch (error) {
      console.error('❌ MonitoringService.getPerformanceMetrics error:', error);
      
      // Return fallback data
      return {
        timestamp: new Date().toISOString(),
        api_response_times: { avg: 0, p95: 0, p99: 0 },
        throughput: { requests_per_minute: 0, resumes_processed_per_hour: 0 },
        resource_usage: { cpu_percent: 0, memory_percent: 0, disk_io: 0 },
        error_rates: { total_errors: 0, error_rate_percent: 0, top_errors: [] }
      };
    }
  }

  /**
   * Get backup sync status
   * Uses: GET /api/monitoring/backup-sync/status
   */
  async getBackupSyncStatus(): Promise<BackupSyncStatus> {
    try {
      console.log('💾 MonitoringService: Fetching backup sync status...');
      
      const data = await this.request<BackupSyncStatus>('/api/monitoring/backup-sync/status');
      
      console.log('✅ Backup sync status loaded:', data.status);
      return data;
    } catch (error) {
      console.error('❌ MonitoringService.getBackupSyncStatus error:', error);
      
      return {
        last_sync: '',
        status: 'failed',
        next_scheduled: '',
        backup_size: 0,
        error_message: 'Failed to fetch status'
      };
    }
  }

  /**
   * Trigger manual backup sync
   * Uses: POST /api/monitoring/backup-sync/manual
   */
  async triggerManualBackup(): Promise<{ success: boolean; message: string }> {
    try {
      console.log('🔄 MonitoringService: Triggering manual backup...');
      
      const response = await this.request<{ message: string }>('/api/monitoring/backup-sync/manual', {
        method: 'POST'
      });
      
      console.log('✅ Manual backup triggered successfully');
      return {
        success: true,
        message: response.message || 'Backup initiated successfully'
      };
    } catch (error) {
      console.error('❌ MonitoringService.triggerManualBackup error:', error);
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to trigger backup'
      };
    }
  }

  /**
   * Get system configuration
   * Uses: GET /api/monitoring/configuration
   */
  async getConfiguration(): Promise<any> {
    try {
      console.log('⚙️ MonitoringService: Fetching system configuration...');
      
      const data = await this.request<any>('/api/monitoring/configuration');
      
      console.log('✅ System configuration loaded');
      return data;
    } catch (error) {
      console.error('❌ MonitoringService.getConfiguration error:', error);
      return {};
    }
  }

  /**
   * Get system uptime and basic info
   */
  async getSystemInfo(): Promise<{
    uptime: string;
    version: string;
    environment: string;
    last_restart: string;
  }> {
    try {
      console.log('ℹ️ MonitoringService: Fetching system info...');
      
      const data = await this.request<{
        uptime: string;
        version: string;
        environment: string;
        last_restart: string;
      }>('/api/monitoring/info');
      
      console.log('✅ System info loaded');
      return data;
    } catch (error) {
      console.error('❌ MonitoringService.getSystemInfo error:', error);
      return {
        uptime: 'Unknown',
        version: 'Unknown',
        environment: 'Unknown',
        last_restart: 'Unknown'
      };
    }
  }

  /**
   * Get real-time metrics for dashboard
   */
  async getRealTimeMetrics(): Promise<{
    active_users: number;
    processing_queue: number;
    api_calls_last_hour: number;
    error_rate_last_hour: number;
    avg_response_time: number;
  }> {
    try {
      console.log('⏱️ MonitoringService: Fetching real-time metrics...');
      
      const data = await this.request<{
        active_users: number;
        processing_queue: number;
        api_calls_last_hour: number;
        error_rate_last_hour: number;
        avg_response_time: number;
      }>('/api/monitoring/realtime');
      
      console.log('✅ Real-time metrics loaded');
      return data;
    } catch (error) {
      console.error('❌ MonitoringService.getRealTimeMetrics error:', error);
      return {
        active_users: 0,
        processing_queue: 0,
        api_calls_last_hour: 0,
        error_rate_last_hour: 0,
        avg_response_time: 0
      };
    }
  }
}

// React hook for monitoring data
export function useSystemHealth() {
  const [health, setHealth] = React.useState<SystemHealth | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  
  const fetchHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await MonitoringService.getSystemHealth();
      setHealth(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health data');
    } finally {
      setLoading(false);
    }
  };
  
  React.useEffect(() => {
    fetchHealth();
    
    // Set up polling every 30 seconds
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);
  
  return { health, loading, error, refetch: fetchHealth };
}

// React hook for performance metrics
export function usePerformanceMetrics() {
  const [metrics, setMetrics] = React.useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = React.useState(true);
  
  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const data = await MonitoringService.getPerformanceMetrics();
      setMetrics(data);
    } catch (error) {
      console.error('Failed to fetch performance metrics:', error);
    } finally {
      setLoading(false);
    }
  };
  
  React.useEffect(() => {
    fetchMetrics();
    
    // Update every 60 seconds
    const interval = setInterval(fetchMetrics, 60000);
    return () => clearInterval(interval);
  }, []);
  
  return { metrics, loading, refetch: fetchMetrics };
}

import React from 'react';

export const MonitoringService = new MonitoringServiceClass();
export type { SystemHealth, PerformanceMetrics, BackupSyncStatus };
