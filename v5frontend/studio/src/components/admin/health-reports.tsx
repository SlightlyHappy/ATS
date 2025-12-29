'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Label } from '@/components/ui/label';
import { 
  Activity, 
  RefreshCw, 
  Server, 
  Database, 
  Cpu, 
  MemoryStick, 
  HardDrive,
  Network,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  Zap,
  Users,
  FileText,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react';
import { toast } from 'sonner';
import { adminApi } from '@/lib/admin-api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://hrtv6backend-production.up.railway.app';

interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical';
  uptime: number;
  version: string;
  environment: string;
  last_check: string;
}

interface ServiceHealth {
  name: string;
  status: 'online' | 'offline' | 'degraded';
  response_time?: number;
  last_check: string;
  error?: string;
}

interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_io: {
    bytes_sent: number;
    bytes_received: number;
  };
  active_connections: number;
  queue_size: number;
}

interface PerformanceMetrics {
  api_response_time: {
    average: number;
    p95: number;
    p99: number;
  };
  database_query_time: {
    average: number;
    slow_queries: number;
  };
  error_rate: number;
  throughput: number;
}

export default function HealthReports() {
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [performance, setPerformance] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    fetchHealthData();
    
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(fetchHealthData, 30000); // Refresh every 30 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('admin_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      
      // Fetch health report using the admin API
      const healthData = await adminApi.getHealthReport() as any;
      setSystemHealth(healthData.system || {});
      setServices(healthData.services || []);
      
      // Also fetch metrics if available
      try {
        const metricsData = await adminApi.getSystemMetrics() as any;
        setMetrics(metricsData);
        setPerformance(metricsData.performance || {});
      } catch (metricsError) {
        console.log('Metrics not available:', metricsError);
      }

    } catch (error) {
      console.error('Error fetching health data:', error);
      toast.error('Error fetching health data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning':
      case 'degraded':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'critical':
      case 'offline':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return 'default';
      case 'warning':
      case 'degraded':
        return 'warning';
      case 'critical':
      case 'offline':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">System Health Reports</h2>
          <p className="text-muted-foreground">
            Monitor system performance, service status, and health metrics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={autoRefresh ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto Refresh
          </Button>
          <Button onClick={fetchHealthData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* System Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {systemHealth && getStatusIcon(systemHealth.status)}
              <div className="text-2xl font-bold">
                {systemHealth?.status || 'Unknown'}
              </div>
            </div>
            {systemHealth && (
              <div className="text-xs text-muted-foreground mt-1">
                Uptime: {formatUptime(systemHealth.uptime)}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.cpu_usage.toFixed(1)}%</div>
            <Progress value={metrics?.cpu_usage || 0} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
            <MemoryStick className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.memory_usage.toFixed(1)}%</div>
            <Progress value={metrics?.memory_usage || 0} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Connections</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.active_connections || 0}</div>
            <div className="text-xs text-muted-foreground mt-1">
              Queue: {metrics?.queue_size || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="services" className="space-y-4">
        <TabsList>
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="system">System Metrics</TabsTrigger>
        </TabsList>

        {/* Services Status */}
        <TabsContent value="services" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Service Health</CardTitle>
              <CardDescription>Status of all system services and dependencies</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                {services.map((service, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(service.status)}
                      <div>
                        <div className="font-medium">{service.name}</div>
                        {service.response_time && (
                          <div className="text-xs text-muted-foreground">
                            Response: {service.response_time}ms
                          </div>
                        )}
                      </div>
                    </div>
                    <Badge variant={getStatusColor(service.status) as any}>
                      {service.status}
                    </Badge>
                  </div>
                ))}
                {services.length === 0 && (
                  <div className="text-center text-muted-foreground py-8">
                    No service data available
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Performance Metrics */}
        <TabsContent value="performance" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>API Performance</CardTitle>
                <CardDescription>API response time metrics</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm">Average:</span>
                  <span className="font-mono">{performance?.api_response_time.average.toFixed(2)}ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">95th Percentile:</span>
                  <span className="font-mono">{performance?.api_response_time.p95.toFixed(2)}ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">99th Percentile:</span>
                  <span className="font-mono">{performance?.api_response_time.p99.toFixed(2)}ms</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Database Performance</CardTitle>
                <CardDescription>Database query performance</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm">Average Query Time:</span>
                  <span className="font-mono">{performance?.database_query_time.average.toFixed(2)}ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Slow Queries:</span>
                  <span className="font-mono">{performance?.database_query_time.slow_queries || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Error Rate:</span>
                  <span className="font-mono">{performance?.error_rate.toFixed(2)}%</span>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Throughput</CardTitle>
              <CardDescription>System throughput and error rate</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">
                    {performance?.throughput.toLocaleString() || 0}
                  </div>
                  <div className="text-sm text-muted-foreground">Requests/hour</div>
                </div>
                <div className="text-center">
                  <div className={`text-3xl font-bold ${(performance?.error_rate || 0) > 5 ? 'text-red-600' : 'text-green-600'}`}>
                    {performance?.error_rate.toFixed(2)}%
                  </div>
                  <div className="text-sm text-muted-foreground">Error Rate</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Metrics */}
        <TabsContent value="system" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Resource Usage</CardTitle>
                <CardDescription>Current system resource utilization</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm">CPU Usage</span>
                    <span className="text-sm font-mono">{metrics?.cpu_usage.toFixed(1)}%</span>
                  </div>
                  <Progress value={metrics?.cpu_usage || 0} />
                </div>
                
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm">Memory Usage</span>
                    <span className="text-sm font-mono">{metrics?.memory_usage.toFixed(1)}%</span>
                  </div>
                  <Progress value={metrics?.memory_usage || 0} />
                </div>
                
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm">Disk Usage</span>
                    <span className="text-sm font-mono">{metrics?.disk_usage.toFixed(1)}%</span>
                  </div>
                  <Progress value={metrics?.disk_usage || 0} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Network I/O</CardTitle>
                <CardDescription>Network traffic statistics</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm">Bytes Sent:</span>
                  <span className="font-mono">
                    {formatBytes(metrics?.network_io.bytes_sent || 0)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Bytes Received:</span>
                  <span className="font-mono">
                    {formatBytes(metrics?.network_io.bytes_received || 0)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Active Connections:</span>
                  <span className="font-mono">{metrics?.active_connections || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Queue Size:</span>
                  <span className="font-mono">{metrics?.queue_size || 0}</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {systemHealth && (
            <Card>
              <CardHeader>
                <CardTitle>System Information</CardTitle>
                <CardDescription>Current system configuration and environment</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <Label className="text-sm font-medium">Version</Label>
                    <div className="text-sm text-muted-foreground mt-1">{systemHealth.version}</div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Environment</Label>
                    <div className="text-sm text-muted-foreground mt-1">{systemHealth.environment}</div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Last Check</Label>
                    <div className="text-sm text-muted-foreground mt-1">
                      {new Date(systemHealth.last_check).toLocaleString()}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
