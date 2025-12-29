"use client";

import { useEffect, useState } from "react";
import { enhancedAdminService } from "@/services/enhanced-admin.service";
import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  RefreshCw, 
  Server, 
  Database, 
  Users, 
  Activity, 
  CreditCard,
  AlertTriangle,
  CheckCircle,
  Clock,
  Trash2,
  Monitor,
  Cloud,
  Cpu,
  HardDrive,
  Zap,
  FileText,
  Settings,
  Play,
  Eye,
  Filter
} from "lucide-react";

interface SystemHealth {
  status: string;
  database: {
    connected: boolean;
    response_time: number;
    active_connections: number;
  };
  services: {
    payment_service: boolean;
    analytics_service: boolean;
    websocket_service: boolean;
  };
  uptime: string;
  memory_usage: number;
  cpu_usage: number;
}

interface PaymentAnalytics {
  total_revenue: number;
  total_transactions: number;
  success_rate: number;
  recent_payments: Array<{
    id: string;
    amount: number;
    status: string;
    created_at: string;
    user_email: string;
  }>;
}

interface ActiveSessions {
  total_active: number;
  admin_sessions: number;
  user_sessions: number;
  sessions: Array<{
    user_id: string;
    user_email: string;
    last_activity: string;
    ip_address: string;
    user_agent: string;
  }>;
}

interface RailwayStats {
  database: {
    status: string;
    size: string;
    connections: number;
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
  };
  services: Array<{
    id: string;
    name: string;
    status: string;
    cpu: number;
    memory: number;
    restarts: number;
    last_deploy: string;
  }>;
  deployments: Array<{
    id: string;
    status: string;
    created_at: string;
    service_name: string;
    commit_hash: string;
  }>;
}

interface AgenticSystemData {
  overview: {
    total_analyses: number;
    total_queries: number;
    ai_interactions: number;
    success_rate: number;
    avg_response_time: number;
  };
  metrics: {
    timeline: Array<{ timestamp: string; analyses: number; queries: number; }>;
    by_type: Array<{ type: string; count: number; }>;
    performance: {
      avg_processing_time: number;
      queue_size: number;
      active_workers: number;
    };
  };
  recent_data: Array<{
    id: string;
    type: string;
    status: string;
    created_at: string;
    user_id: string;
    metadata: any;
  }>;
}

export default function AdminMonitoringPage() {
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [paymentAnalytics, setPaymentAnalytics] = useState<PaymentAnalytics | null>(null);
  const [activeSessions, setActiveSessions] = useState<ActiveSessions | null>(null);
  const [railwayStats, setRailwayStats] = useState<RailwayStats | null>(null);
  const [agenticData, setAgenticData] = useState<AgenticSystemData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");
  const [agenticFilters, setAgenticFilters] = useState<{
    dataType: 'resume_analysis' | 'legal_queries' | 'ai_interactions' | 'system_logs' | '';
    status: 'active' | 'completed' | 'failed' | 'pending' | '';
    timeRange: '1h' | '24h' | '7d' | '30d';
    page: number;
    limit: number;
  }>({
    dataType: '',
    status: '',
    timeRange: '24h',
    page: 1,
    limit: 50
  });
  const { toast } = useToast();

  const loadMonitoringData = async () => {
    try {
      setIsLoading(true);
      
      // Load all monitoring data in parallel
      const [
        healthResponse, 
        analyticsResponse, 
        sessionsResponse,
        railwayResponse,
        agenticOverviewResponse,
        agenticMetricsResponse
      ] = await Promise.all([
        enhancedAdminService.getSystemHealthDetailed(),
        enhancedAdminService.getPaymentAnalytics(30),
        enhancedAdminService.getActiveSessions(),
        enhancedAdminService.getRailwayInfrastructureOverview(),
        enhancedAdminService.getAgenticSystemOverview(),
        enhancedAdminService.getAgenticSystemMetrics(agenticFilters.timeRange as any)
      ]);

      if (healthResponse.success) {
        setSystemHealth(healthResponse.data);
      }
      
      if (analyticsResponse.success) {
        setPaymentAnalytics(analyticsResponse.data);
      }
      
      if (sessionsResponse.success) {
        setActiveSessions(sessionsResponse.data);
      }

      if (railwayResponse.success) {
        setRailwayStats(railwayResponse.data);
      }

      if (agenticOverviewResponse.success && agenticMetricsResponse.success) {
        setAgenticData({
          overview: agenticOverviewResponse.data,
          metrics: agenticMetricsResponse.data,
          recent_data: [] // Will be loaded separately with filters
        });
      }
      
    } catch (error) {
      console.error('Failed to load monitoring data:', error);
      toast({
        title: "Error",
        description: "Failed to load monitoring data. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadAgenticData = async () => {
    try {
      const response = await enhancedAdminService.getAgenticDataWithFilters({
        ...agenticFilters,
        dataType: agenticFilters.dataType || undefined as any,
        status: agenticFilters.status || undefined as any
      });
      
      if (response.success) {
        setAgenticData(prev => prev ? {
          ...prev,
          recent_data: response.data.items || []
        } : null);
      }
    } catch (error) {
      console.error('Failed to load agentic data:', error);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadMonitoringData();
    setIsRefreshing(false);
    toast({
      title: "Success",
      description: "Monitoring data refreshed successfully.",
    });
  };

  const handleSessionCleanup = async () => {
    try {
      const response = await enhancedAdminService.cleanupSessions();
      if (response.success) {
        toast({
          title: "Success",
          description: "Inactive sessions cleaned up successfully.",
        });
        await loadMonitoringData(); // Refresh data
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to cleanup sessions.",
        variant: "destructive",
      });
    }
  };

  useEffect(() => {
    loadMonitoringData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadMonitoringData, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (agenticData) {
      loadAgenticData();
    }
  }, [agenticFilters]);

  const getStatusBadge = (status: boolean | string) => {
    if (typeof status === 'boolean') {
      return status ? (
        <Badge variant="default" className="gap-1">
          <CheckCircle className="h-3 w-3" />
          Healthy
        </Badge>
      ) : (
        <Badge variant="destructive" className="gap-1">
          <AlertTriangle className="h-3 w-3" />
          Error
        </Badge>
      );
    }
    
    return status === 'healthy' ? (
      <Badge variant="default" className="gap-1">
        <CheckCircle className="h-3 w-3" />
        Healthy
      </Badge>
    ) : (
      <Badge variant="destructive" className="gap-1">
        <AlertTriangle className="h-3 w-3" />
        Issues
      </Badge>
    );
  };

  const formatUptime = (uptime: string) => {
    // Assuming uptime is in seconds or a formatted string
    return uptime;
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(amount);
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="System Monitoring"
        description="Monitor system health, performance, and analytics"
        actions={
          <Button 
            onClick={handleRefresh} 
            disabled={isRefreshing}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        }
      />

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-4 w-48" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="space-y-6">
          {/* System Health Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Server className="h-4 w-4" />
                  System Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                {systemHealth ? getStatusBadge(systemHealth.status) : (
                  <Badge variant="outline">Unknown</Badge>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Database className="h-4 w-4" />
                  Database
                </CardTitle>
              </CardHeader>
              <CardContent>
                {systemHealth ? getStatusBadge(systemHealth.database.connected) : (
                  <Badge variant="outline">Unknown</Badge>
                )}
                {systemHealth && (
                  <p className="text-xs text-muted-foreground mt-1">
                    {systemHealth.database.response_time}ms response
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Active Sessions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {activeSessions?.total_active || 0}
                </div>
                {activeSessions && (
                  <p className="text-xs text-muted-foreground">
                    {activeSessions.admin_sessions} admin, {activeSessions.user_sessions} users
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Uptime
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm font-medium">
                  {systemHealth ? formatUptime(systemHealth.uptime) : 'Unknown'}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Detailed System Health */}
          {systemHealth && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  System Health Details
                </CardTitle>
                <CardDescription>
                  Detailed system performance and service status
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <h4 className="font-medium text-sm">Database Status</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Connected:</span>
                        {getStatusBadge(systemHealth.database.connected)}
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Response Time:</span>
                        <span className="text-sm font-medium">{systemHealth.database.response_time}ms</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Active Connections:</span>
                        <span className="text-sm font-medium">{systemHealth.database.active_connections}</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h4 className="font-medium text-sm">Service Status</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Payment Service:</span>
                        {getStatusBadge(systemHealth.services.payment_service)}
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">Analytics Service:</span>
                        {getStatusBadge(systemHealth.services.analytics_service)}
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground">WebSocket Service:</span>
                        {getStatusBadge(systemHealth.services.websocket_service)}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">Memory Usage:</span>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full" 
                        style={{ width: `${systemHealth.memory_usage}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground">{systemHealth.memory_usage}%</span>
                  </div>
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">CPU Usage:</span>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full" 
                        style={{ width: `${systemHealth.cpu_usage}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground">{systemHealth.cpu_usage}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Payment Analytics */}
          {paymentAnalytics && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CreditCard className="h-5 w-5" />
                  Payment Analytics (Last 30 Days)
                </CardTitle>
                <CardDescription>
                  Revenue and transaction statistics
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">Total Revenue:</span>
                    <div className="text-2xl font-bold text-green-600">
                      {formatCurrency(paymentAnalytics.total_revenue)}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">Total Transactions:</span>
                    <div className="text-2xl font-bold">
                      {paymentAnalytics.total_transactions}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">Success Rate:</span>
                    <div className="text-2xl font-bold text-blue-600">
                      {paymentAnalytics.success_rate}%
                    </div>
                  </div>
                </div>

                {paymentAnalytics.recent_payments && paymentAnalytics.recent_payments.length > 0 && (
                  <div className="pt-4 border-t">
                    <h4 className="font-medium text-sm mb-3">Recent Payments</h4>
                    <div className="space-y-2">
                      {paymentAnalytics.recent_payments.slice(0, 5).map((payment) => (
                        <div key={payment.id} className="flex items-center justify-between p-2 bg-muted rounded">
                          <div className="flex-1">
                            <span className="text-sm font-medium">{payment.user_email}</span>
                            <p className="text-xs text-muted-foreground">
                              {new Date(payment.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-medium">{formatCurrency(payment.amount)}</div>
                            <Badge variant={payment.status === 'success' ? 'default' : 'destructive'} className="text-xs">
                              {payment.status}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Active Sessions Management */}
          {activeSessions && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Users className="h-5 w-5" />
                    Active Sessions
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleSessionCleanup}
                    className="gap-2"
                  >
                    <Trash2 className="h-4 w-4" />
                    Cleanup Inactive
                  </Button>
                </CardTitle>
                <CardDescription>
                  Currently active user sessions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {activeSessions.sessions.slice(0, 10).map((session) => (
                    <div key={session.user_id} className="flex items-center justify-between p-3 bg-muted rounded">
                      <div className="flex-1">
                        <span className="text-sm font-medium">{session.user_email}</span>
                        <p className="text-xs text-muted-foreground">
                          Last active: {new Date(session.last_activity).toLocaleString()}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          IP: {session.ip_address}
                        </p>
                      </div>
                      <div className="text-right">
                        <Badge variant="outline" className="text-xs">
                          Active
                        </Badge>
                      </div>
                    </div>
                  ))}
                  
                  {activeSessions.sessions.length > 10 && (
                    <p className="text-sm text-muted-foreground text-center pt-2">
                      And {activeSessions.sessions.length - 10} more sessions...
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Railway Infrastructure Monitoring */}
          {railwayStats && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cloud className="h-5 w-5" />
                  Railway Infrastructure
                </CardTitle>
                <CardDescription>
                  Database and service status on Railway
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Database Stats */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">Database Status:</span>
                    {getStatusBadge(railwayStats.database.status === 'healthy')}
                    <p className="text-xs text-muted-foreground">
                      Size: {railwayStats.database.size}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">Connections:</span>
                    <div className="text-lg font-semibold">{railwayStats.database.connections}</div>
                  </div>
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">CPU Usage:</span>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full" 
                        style={{ width: `${railwayStats.database.cpu_usage}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground">{railwayStats.database.cpu_usage}%</span>
                  </div>
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">Memory Usage:</span>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full" 
                        style={{ width: `${railwayStats.database.memory_usage}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground">{railwayStats.database.memory_usage}%</span>
                  </div>
                </div>

                {/* Services Status */}
                {railwayStats.services && railwayStats.services.length > 0 && (
                  <div className="pt-4 border-t">
                    <h4 className="font-medium text-sm mb-3">Services Status</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {railwayStats.services.map((service) => (
                        <div key={service.id} className="p-3 bg-muted rounded space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">{service.name}</span>
                            {getStatusBadge(service.status === 'running')}
                          </div>
                          <div className="text-xs text-muted-foreground space-y-1">
                            <div>CPU: {service.cpu}% | Memory: {service.memory}%</div>
                            <div>Restarts: {service.restarts} | Last Deploy: {new Date(service.last_deploy).toLocaleDateString()}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recent Deployments */}
                {railwayStats.deployments && railwayStats.deployments.length > 0 && (
                  <div className="pt-4 border-t">
                    <h4 className="font-medium text-sm mb-3">Recent Deployments</h4>
                    <div className="space-y-2">
                      {railwayStats.deployments.slice(0, 5).map((deployment) => (
                        <div key={deployment.id} className="flex items-center justify-between p-2 bg-muted rounded">
                          <div className="flex-1">
                            <span className="text-sm font-medium">{deployment.service_name}</span>
                            <p className="text-xs text-muted-foreground">
                              {deployment.commit_hash.substring(0, 8)} • {new Date(deployment.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <Badge variant={deployment.status === 'success' ? 'default' : 'destructive'} className="text-xs">
                            {deployment.status}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Agentic System Dashboard */}
          {agenticData && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Monitor className="h-5 w-5" />
                  Agentic System Dashboard
                </CardTitle>
                <CardDescription>
                  AI system performance and data analytics
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Overview Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">Total Analyses:</span>
                    <div className="text-lg font-semibold">{agenticData.overview.total_analyses}</div>
                  </div>
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">Legal Queries:</span>
                    <div className="text-lg font-semibold">{agenticData.overview.total_queries}</div>
                  </div>
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">AI Interactions:</span>
                    <div className="text-lg font-semibold">{agenticData.overview.ai_interactions}</div>
                  </div>
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">Success Rate:</span>
                    <div className="text-lg font-semibold text-green-600">{agenticData.overview.success_rate}%</div>
                  </div>
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">Avg Response:</span>
                    <div className="text-lg font-semibold">{agenticData.overview.avg_response_time}ms</div>
                  </div>
                </div>

                {/* Performance Metrics */}
                {agenticData.metrics?.performance && (
                  <div className="pt-4 border-t">
                    <h4 className="font-medium text-sm mb-3">Performance Metrics</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <span className="text-sm text-muted-foreground">Processing Time:</span>
                        <div className="text-sm font-medium">{agenticData.metrics.performance.avg_processing_time}ms avg</div>
                      </div>
                      <div className="space-y-2">
                        <span className="text-sm text-muted-foreground">Queue Size:</span>
                        <div className="text-sm font-medium">{agenticData.metrics.performance.queue_size} items</div>
                      </div>
                      <div className="space-y-2">
                        <span className="text-sm text-muted-foreground">Active Workers:</span>
                        <div className="text-sm font-medium">{agenticData.metrics.performance.active_workers}</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Data Type Breakdown */}
                {agenticData.metrics?.by_type && (
                  <div className="pt-4 border-t">
                    <h4 className="font-medium text-sm mb-3">Data Type Breakdown</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {agenticData.metrics.by_type.map((item) => (
                        <div key={item.type} className="p-2 bg-muted rounded text-center">
                          <div className="text-sm font-medium">{item.count}</div>
                          <div className="text-xs text-muted-foreground">{item.type.replace('_', ' ')}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recent Data Activity */}
                {agenticData.recent_data && agenticData.recent_data.length > 0 && (
                  <div className="pt-4 border-t">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-sm">Recent Activity</h4>
                      <div className="flex items-center gap-2">
                        <select 
                          className="text-xs border rounded px-2 py-1"
                          value={agenticFilters.dataType}
                          onChange={(e) => setAgenticFilters(prev => ({...prev, dataType: e.target.value as any}))}
                        >
                          <option value="">All Types</option>
                          <option value="resume_analysis">Resume Analysis</option>
                          <option value="legal_queries">Legal Queries</option>
                          <option value="ai_interactions">AI Interactions</option>
                          <option value="system_logs">System Logs</option>
                        </select>
                        <select 
                          className="text-xs border rounded px-2 py-1"
                          value={agenticFilters.status}
                          onChange={(e) => setAgenticFilters(prev => ({...prev, status: e.target.value as any}))}
                        >
                          <option value="">All Status</option>
                          <option value="active">Active</option>
                          <option value="completed">Completed</option>
                          <option value="failed">Failed</option>
                          <option value="pending">Pending</option>
                        </select>
                        <Button 
                          size="sm" 
                          variant="outline" 
                          onClick={loadAgenticData}
                          className="gap-1"
                        >
                          <Filter className="h-3 w-3" />
                          Apply
                        </Button>
                      </div>
                    </div>
                    <ScrollArea className="h-64">
                      <div className="space-y-2">
                        {agenticData.recent_data.map((item) => (
                          <div key={item.id} className="flex items-center justify-between p-2 bg-muted rounded">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-medium">{item.type.replace('_', ' ')}</span>
                                <Badge variant={item.status === 'completed' ? 'default' : 'outline'} className="text-xs">
                                  {item.status}
                                </Badge>
                              </div>
                              <p className="text-xs text-muted-foreground">
                                User: {item.user_id} • {new Date(item.created_at).toLocaleString()}
                              </p>
                            </div>
                            <Button size="sm" variant="ghost" className="gap-1">
                              <Eye className="h-3 w-3" />
                              View
                            </Button>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
