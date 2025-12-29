'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { 
  Settings, 
  Monitor, 
  Shield, 
  RefreshCw,
  Database,
  Cpu,
  MemoryStick,
  HardDrive,
  Network,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Play,
  Square,
  Trash2,
  Download,
  Upload,
  Key,
  Users,
  Activity,
  FileText,
  Clock,
  Server
} from 'lucide-react';
import { toast } from 'sonner';
import { adminApi } from '@/lib/admin-api';
import { ScrollArea } from '@/components/ui/scroll-area';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://hrtv6backend-production.up.railway.app';

interface SystemConfig {
  feature_flags: {
    [key: string]: boolean;
  };
  rate_limits: {
    [key: string]: number;
  };
  maintenance_mode: boolean;
  debug_logging: boolean;
}

interface JobQueue {
  id: string;
  name: string;
  status: 'active' | 'paused' | 'failed';
  pending_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  avg_processing_time: number;
}

interface SecurityEvent {
  id: string;
  timestamp: string;
  event_type: 'failed_login' | 'suspicious_activity' | 'rate_limit_exceeded';
  ip_address: string;
  user_agent: string;
  details: string;
  severity: 'low' | 'medium' | 'high';
}

interface SystemResource {
  name: string;
  usage: number;
  limit: number;
  status: 'normal' | 'warning' | 'critical';
}

export default function SystemAdmin() {
  const [systemConfig, setSystemConfig] = useState<SystemConfig | null>(null);
  const [jobQueues, setJobQueues] = useState<JobQueue[]>([]);
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [systemResources, setSystemResources] = useState<SystemResource[]>([]);
  const [loading, setLoading] = useState(true);
  const [maintenanceMode, setMaintenanceMode] = useState(false);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('admin_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  useEffect(() => {
    fetchSystemData();
  }, []);

  const fetchSystemData = async () => {
    try {
      setLoading(true);
      
      // Fetch system health for basic system info
      const healthResponse = await adminApi.getSystemHealth() as any;
      
      if (healthResponse?.success) {
        // Mock system configuration data (would come from API)
        const config: SystemConfig = {
          feature_flags: {
            'advanced_analytics': true,
            'batch_processing': true,
            'real_time_notifications': false,
            'enterprise_features': true,
            'beta_ai_models': false
          },
          rate_limits: {
            'api_requests_per_minute': 100,
            'upload_size_mb': 50,
            'concurrent_analyses': 10,
            'daily_quota': 1000
          },
          maintenance_mode: false,
          debug_logging: true
        };
        
        setSystemConfig(config);
        setMaintenanceMode(config.maintenance_mode);
        
        // Mock job queue data
        const queues: JobQueue[] = [
          {
            id: 'analysis_queue',
            name: 'Resume Analysis',
            status: 'active',
            pending_tasks: 23,
            completed_tasks: 1847,
            failed_tasks: 12,
            avg_processing_time: 145
          },
          {
            id: 'upload_queue',
            name: 'File Processing',
            status: 'active',
            pending_tasks: 5,
            completed_tasks: 892,
            failed_tasks: 3,
            avg_processing_time: 32
          },
          {
            id: 'email_queue',
            name: 'Email Notifications',
            status: 'active',
            pending_tasks: 0,
            completed_tasks: 234,
            failed_tasks: 1,
            avg_processing_time: 8
          }
        ];
        
        setJobQueues(queues);
        
        // Mock security events
        const events: SecurityEvent[] = [
          {
            id: '1',
            timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
            event_type: 'failed_login',
            ip_address: '192.168.1.100',
            user_agent: 'Mozilla/5.0...',
            details: 'Multiple failed login attempts',
            severity: 'medium'
          },
          {
            id: '2',
            timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
            event_type: 'rate_limit_exceeded',
            ip_address: '10.0.0.50',
            user_agent: 'Python/3.9',
            details: 'API rate limit exceeded',
            severity: 'low'
          }
        ];
        
        setSecurityEvents(events);
        
        // Mock system resources
        const resources: SystemResource[] = [
          { name: 'CPU Usage', usage: 45, limit: 100, status: 'normal' },
          { name: 'Memory', usage: 72, limit: 100, status: 'warning' },
          { name: 'Disk Space', usage: 38, limit: 100, status: 'normal' },
          { name: 'Network I/O', usage: 28, limit: 100, status: 'normal' },
          { name: 'Database Connections', usage: 15, limit: 50, status: 'normal' }
        ];
        
        setSystemResources(resources);
      }
    } catch (error) {
      console.error('Error loading system data:', error);
      toast.error('Failed to load system administration data');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleFeature = async (feature: string, enabled: boolean) => {
    try {
      // In a real implementation, this would call the API
      toast.info(`${enabled ? 'Enabling' : 'Disabling'} ${feature}...`);
      
      setSystemConfig(prev => prev ? {
        ...prev,
        feature_flags: {
          ...prev.feature_flags,
          [feature]: enabled
        }
      } : null);
      
      toast.success(`Feature ${feature} ${enabled ? 'enabled' : 'disabled'} successfully`);
    } catch (error) {
      toast.error(`Failed to update feature ${feature}`);
    }
  };

  const handleToggleMaintenanceMode = async () => {
    try {
      const newMode = !maintenanceMode;
      toast.info(`${newMode ? 'Enabling' : 'Disabling'} maintenance mode...`);
      
      setMaintenanceMode(newMode);
      setSystemConfig(prev => prev ? { ...prev, maintenance_mode: newMode } : null);
      
      toast.success(`Maintenance mode ${newMode ? 'enabled' : 'disabled'}`);
    } catch (error) {
      toast.error('Failed to toggle maintenance mode');
    }
  };

  const handleRetryFailedJobs = async (queueId: string) => {
    try {
      toast.info(`Retrying failed jobs in ${queueId}...`);
      
      // Update local state optimistically
      setJobQueues(prev => prev.map(queue => 
        queue.id === queueId 
          ? { ...queue, failed_tasks: 0, pending_tasks: queue.pending_tasks + queue.failed_tasks }
          : queue
      ));
      
      toast.success('Failed jobs queued for retry');
    } catch (error) {
      toast.error('Failed to retry jobs');
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'text-red-500';
      case 'medium': return 'text-yellow-500';
      case 'low': return 'text-blue-500';
      default: return 'text-muted-foreground';
    }
  };

  const getResourceStatus = (resource: SystemResource) => {
    const percentage = (resource.usage / resource.limit) * 100;
    if (percentage > 90) return 'critical';
    if (percentage > 70) return 'warning';
    return 'normal';
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="pb-2">
                <div className="h-4 bg-muted rounded w-1/2" />
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-muted rounded w-1/3" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">System Administration</h2>
          <p className="text-muted-foreground">
            System maintenance, configuration, and administrative tools
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center space-x-2">
            <Switch
              id="maintenance-mode"
              checked={maintenanceMode}
              onCheckedChange={handleToggleMaintenanceMode}
            />
            <Label htmlFor="maintenance-mode" className="text-sm">
              Maintenance Mode
            </Label>
          </div>
          <Button onClick={fetchSystemData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {maintenanceMode && (
        <Alert className="border-orange-200 bg-orange-50">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            System is currently in maintenance mode. New user registrations and uploads are temporarily disabled.
          </AlertDescription>
        </Alert>
      )}

      {/* System Resources Overview */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        {systemResources.map((resource) => (
          <Card key={resource.name}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{resource.name}</CardTitle>
              {resource.name === 'CPU Usage' && <Cpu className="h-4 w-4 text-muted-foreground" />}
              {resource.name === 'Memory' && <MemoryStick className="h-4 w-4 text-muted-foreground" />}
              {resource.name === 'Disk Space' && <HardDrive className="h-4 w-4 text-muted-foreground" />}
              {resource.name === 'Network I/O' && <Network className="h-4 w-4 text-muted-foreground" />}
              {resource.name === 'Database Connections' && <Database className="h-4 w-4 text-muted-foreground" />}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{resource.usage}%</div>
              <div className="flex items-center justify-between mt-2">
                <div className={`w-full h-2 bg-muted rounded-full overflow-hidden`}>
                  <div
                    className={`h-full rounded-full ${
                      getResourceStatus(resource) === 'critical' ? 'bg-red-500' :
                      getResourceStatus(resource) === 'warning' ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${(resource.usage / resource.limit) * 100}%` }}
                  />
                </div>
                <Badge
                  variant="outline"
                  className={
                    getResourceStatus(resource) === 'critical' ? 'text-red-600' :
                    getResourceStatus(resource) === 'warning' ? 'text-yellow-600' : 'text-green-600'
                  }
                >
                  {getResourceStatus(resource)}
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="config" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="config">Configuration</TabsTrigger>
          <TabsTrigger value="queues">Job Queues</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
          <TabsTrigger value="backup">Backup</TabsTrigger>
        </TabsList>

        <TabsContent value="config" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Feature Flags</CardTitle>
                <CardDescription>Enable or disable platform features</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {systemConfig && Object.entries(systemConfig.feature_flags).map(([feature, enabled]) => (
                    <div key={feature} className="flex items-center justify-between">
                      <div>
                        <div className="font-medium capitalize">
                          {feature.replace(/_/g, ' ')}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {feature === 'advanced_analytics' && 'Enhanced analytics and reporting'}
                          {feature === 'batch_processing' && 'Process multiple resumes at once'}
                          {feature === 'real_time_notifications' && 'Instant notification system'}
                          {feature === 'enterprise_features' && 'Advanced enterprise capabilities'}
                          {feature === 'beta_ai_models' && 'Experimental AI analysis models'}
                        </div>
                      </div>
                      <Switch
                        checked={enabled}
                        onCheckedChange={(checked) => handleToggleFeature(feature, checked)}
                      />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Rate Limits</CardTitle>
                <CardDescription>Configure system rate limiting</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {systemConfig && Object.entries(systemConfig.rate_limits).map(([limit, value]) => (
                    <div key={limit} className="space-y-2">
                      <Label className="capitalize">
                        {limit.replace(/_/g, ' ')}
                      </Label>
                      <div className="flex items-center gap-2">
                        <Input
                          type="number"
                          value={value}
                          onChange={(e) => {
                            const newValue = parseInt(e.target.value);
                            setSystemConfig(prev => prev ? {
                              ...prev,
                              rate_limits: { ...prev.rate_limits, [limit]: newValue }
                            } : null);
                          }}
                          className="w-32"
                        />
                        <Button variant="outline" size="sm">
                          Update
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="queues" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Job Queue Management</CardTitle>
              <CardDescription>Monitor and manage background processing queues</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Queue Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Pending</TableHead>
                    <TableHead>Completed</TableHead>
                    <TableHead>Failed</TableHead>
                    <TableHead>Avg Time</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobQueues.map((queue) => (
                    <TableRow key={queue.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Activity className="h-4 w-4" />
                          {queue.name}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={
                          queue.status === 'active' ? 'default' :
                          queue.status === 'paused' ? 'secondary' : 'destructive'
                        }>
                          {queue.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{queue.pending_tasks}</TableCell>
                      <TableCell>{queue.completed_tasks}</TableCell>
                      <TableCell>
                        {queue.failed_tasks > 0 ? (
                          <Badge variant="destructive">{queue.failed_tasks}</Badge>
                        ) : (
                          queue.failed_tasks
                        )}
                      </TableCell>
                      <TableCell>{queue.avg_processing_time}s</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button variant="outline" size="sm">
                            <Play className="h-4 w-4" />
                          </Button>
                          <Button variant="outline" size="sm">
                            <Square className="h-4 w-4" />
                          </Button>
                          {queue.failed_tasks > 0 && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleRetryFailedJobs(queue.id)}
                            >
                              <RefreshCw className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Security Events
              </CardTitle>
              <CardDescription>Recent security alerts and suspicious activities</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Event Type</TableHead>
                    <TableHead>IP Address</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Details</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {securityEvents.map((event) => (
                    <TableRow key={event.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          {new Date(event.timestamp).toLocaleString()}
                        </div>
                      </TableCell>
                      <TableCell className="capitalize">
                        {event.event_type.replace(/_/g, ' ')}
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {event.ip_address}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={getSeverityColor(event.severity)}
                        >
                          {event.severity}
                        </Badge>
                      </TableCell>
                      <TableCell>{event.details}</TableCell>
                      <TableCell className="text-right">
                        <Button variant="outline" size="sm">
                          Block IP
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {securityEvents.length === 0 && (
                <div className="text-center py-8">
                  <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No security events detected</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="monitoring" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>System Health</CardTitle>
                <CardDescription>Real-time system status monitoring</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { service: 'API Gateway', status: 'online', response_time: 45 },
                    { service: 'Database', status: 'online', response_time: 12 },
                    { service: 'Redis Cache', status: 'online', response_time: 3 },
                    { service: 'File Storage', status: 'online', response_time: 28 },
                    { service: 'AI Processing', status: 'online', response_time: 145 }
                  ].map((service) => (
                    <div key={service.service} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <CheckCircle className="h-5 w-5 text-green-500" />
                        <div>
                          <div className="font-medium">{service.service}</div>
                          <div className="text-sm text-muted-foreground">
                            {service.response_time}ms response time
                          </div>
                        </div>
                      </div>
                      <Badge variant="outline" className="text-green-600">
                        {service.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
                <CardDescription>Key performance indicators</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-primary">99.8%</div>
                      <div className="text-sm text-muted-foreground">Uptime</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-primary">145ms</div>
                      <div className="text-sm text-muted-foreground">Avg Response</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-primary">0.02%</div>
                      <div className="text-sm text-muted-foreground">Error Rate</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-primary">2.3k</div>
                      <div className="text-sm text-muted-foreground">Req/min</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="backup" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Database Backup</CardTitle>
                <CardDescription>Manage database backups and recovery</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span>Last Backup</span>
                  <Badge variant="outline">2 hours ago</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span>Backup Size</span>
                  <span className="text-sm">2.4 GB</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Retention Period</span>
                  <span className="text-sm">30 days</span>
                </div>
                <div className="flex gap-2 pt-4 border-t">
                  <Button size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Create Backup
                  </Button>
                  <Button variant="outline" size="sm">
                    <Upload className="h-4 w-4 mr-2" />
                    Restore
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>System Export</CardTitle>
                <CardDescription>Export system configuration and data</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <input type="checkbox" id="config" defaultChecked />
                    <Label htmlFor="config">System Configuration</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input type="checkbox" id="users" defaultChecked />
                    <Label htmlFor="users">User Data</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input type="checkbox" id="analytics" />
                    <Label htmlFor="analytics">Analytics Data</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input type="checkbox" id="logs" />
                    <Label htmlFor="logs">System Logs</Label>
                  </div>
                </div>
                <Button size="sm" className="w-full">
                  <Download className="h-4 w-4 mr-2" />
                  Export Selected Data
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
