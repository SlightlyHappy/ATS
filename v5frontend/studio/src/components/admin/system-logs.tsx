'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  FileText, 
  Search, 
  RefreshCw, 
  Download, 
  Filter,
  AlertTriangle,
  Info,
  AlertCircle,
  CheckCircle,
  XCircle,
  Eye,
  Calendar,
  Clock
} from 'lucide-react';
import { toast } from 'sonner';
import { ScrollArea } from '@/components/ui/scroll-area';
import { adminApi } from '@/lib/admin-api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://hrtv6backend-production.up.railway.app';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  logger: string;
  message: string;
  module: string;
  user_id?: string;
  ip_address?: string;
  details?: any;
}

interface LogFilters {
  level?: string;
  logger?: string;
  module?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
}

export default function SystemLogs() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<LogFilters>({});
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [totalLogs, setTotalLogs] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(50);

  useEffect(() => {
    fetchLogs();
  }, [page, filters]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('admin_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const data = await adminApi.getSystemLogs({
        page,
        limit,
        level: filters.level as any,
        start_date: filters.start_date,
        end_date: filters.end_date
      }) as any;

      setLogs(data.logs || []);
      setTotalLogs(data.total || 0);
    } catch (error) {
      console.error('Error fetching logs:', error);
      toast.error('Error fetching logs');
    } finally {
      setLoading(false);
    }
  };

  const downloadLogs = async () => {
    try {
      const queryParams = new URLSearchParams({
        format: 'csv',
        ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v))
      });

      const response = await fetch(`${API_BASE_URL}/api/admin/logs/export?${queryParams}`, {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `system_logs_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        toast.success('Logs downloaded successfully');
      } else {
        toast.error('Failed to download logs');
      }
    } catch (error) {
      console.error('Error downloading logs:', error);
      toast.error('Error downloading logs');
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'CRITICAL':
      case 'ERROR':
        return <XCircle className="h-4 w-4" />;
      case 'WARNING':
        return <AlertTriangle className="h-4 w-4" />;
      case 'INFO':
        return <Info className="h-4 w-4" />;
      case 'DEBUG':
        return <CheckCircle className="h-4 w-4" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'CRITICAL':
      case 'ERROR':
        return 'destructive';
      case 'WARNING':
        return 'warning';
      case 'INFO':
        return 'default';
      case 'DEBUG':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({
      ...prev,
      [key]: value || undefined
    }));
    setPage(1); // Reset to first page when filters change
  };

  const clearFilters = () => {
    setFilters({});
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">System Logs</h2>
        <p className="text-muted-foreground">
          Monitor system activity and troubleshoot issues
        </p>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
          <CardDescription>Filter logs by level, module, date range, and search terms</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2">
              <Label htmlFor="level-filter">Log Level</Label>
              <Select value={filters.level || ''} onValueChange={(value) => handleFilterChange('level', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="All levels" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All levels</SelectItem>
                  <SelectItem value="DEBUG">Debug</SelectItem>
                  <SelectItem value="INFO">Info</SelectItem>
                  <SelectItem value="WARNING">Warning</SelectItem>
                  <SelectItem value="ERROR">Error</SelectItem>
                  <SelectItem value="CRITICAL">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="module-filter">Module</Label>
              <Select value={filters.module || ''} onValueChange={(value) => handleFilterChange('module', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="All modules" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All modules</SelectItem>
                  <SelectItem value="auth">Authentication</SelectItem>
                  <SelectItem value="api">API</SelectItem>
                  <SelectItem value="database">Database</SelectItem>
                  <SelectItem value="analysis">Analysis</SelectItem>
                  <SelectItem value="upload">Upload</SelectItem>
                  <SelectItem value="system">System</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="search-filter">Search</Label>
              <Input
                id="search-filter"
                placeholder="Search in messages..."
                value={filters.search || ''}
                onChange={(e) => handleFilterChange('search', e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Actions</Label>
              <div className="flex gap-2">
                <Button onClick={fetchLogs} disabled={loading} size="sm">
                  <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
                <Button onClick={clearFilters} variant="outline" size="sm">
                  Clear
                </Button>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4 mt-4">
            <Button onClick={downloadLogs} variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export Logs
            </Button>
            <div className="text-sm text-muted-foreground">
              Showing {logs.length} of {totalLogs} logs
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardHeader>
          <CardTitle>Log Entries</CardTitle>
          <CardDescription>Recent system log entries</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Level</TableHead>
                <TableHead>Module</TableHead>
                <TableHead>Logger</TableHead>
                <TableHead>Message</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="font-mono text-xs">
                    {new Date(log.timestamp).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <Badge variant={getLevelColor(log.level) as any} className="flex items-center gap-1 w-fit">
                      {getLevelIcon(log.level)}
                      {log.level}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">{log.module}</TableCell>
                  <TableCell className="text-sm font-mono">{log.logger}</TableCell>
                  <TableCell className="max-w-md truncate text-sm">
                    {log.message}
                  </TableCell>
                  <TableCell>
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="ghost" size="sm" onClick={() => setSelectedLog(log)}>
                          <Eye className="h-4 w-4" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-4xl">
                        <DialogHeader>
                          <DialogTitle className="flex items-center gap-2">
                            {getLevelIcon(log.level)}
                            Log Entry Details
                          </DialogTitle>
                          <DialogDescription>
                            {new Date(log.timestamp).toLocaleString()}
                          </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                          <div className="grid gap-4 md:grid-cols-2">
                            <div>
                              <Label>Level</Label>
                              <div className="mt-1">
                                <Badge variant={getLevelColor(log.level) as any}>
                                  {log.level}
                                </Badge>
                              </div>
                            </div>
                            <div>
                              <Label>Module</Label>
                              <p className="text-sm mt-1">{log.module}</p>
                            </div>
                            <div>
                              <Label>Logger</Label>
                              <p className="text-sm font-mono mt-1">{log.logger}</p>
                            </div>
                            {log.user_id && (
                              <div>
                                <Label>User ID</Label>
                                <p className="text-sm font-mono mt-1">{log.user_id}</p>
                              </div>
                            )}
                            {log.ip_address && (
                              <div>
                                <Label>IP Address</Label>
                                <p className="text-sm font-mono mt-1">{log.ip_address}</p>
                              </div>
                            )}
                          </div>
                          
                          <div>
                            <Label>Message</Label>
                            <ScrollArea className="h-32 w-full rounded-md border p-3 mt-1">
                              <p className="text-sm whitespace-pre-wrap">{log.message}</p>
                            </ScrollArea>
                          </div>

                          {log.details && (
                            <div>
                              <Label>Additional Details</Label>
                              <ScrollArea className="h-48 w-full rounded-md border p-3 mt-1">
                                <pre className="text-xs">
                                  {JSON.stringify(log.details, null, 2)}
                                </pre>
                              </ScrollArea>
                            </div>
                          )}
                        </div>
                      </DialogContent>
                    </Dialog>
                  </TableCell>
                </TableRow>
              ))}
              {logs.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground">
                    {loading ? 'Loading logs...' : 'No logs found'}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>

          {/* Pagination */}
          {totalLogs > limit && (
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                Page {page} of {Math.ceil(totalLogs / limit)}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1 || loading}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(Math.min(Math.ceil(totalLogs / limit), page + 1))}
                  disabled={page === Math.ceil(totalLogs / limit) || loading}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
