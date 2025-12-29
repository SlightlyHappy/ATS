'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Database, 
  Play, 
  Download, 
  Upload, 
  RefreshCw,
  FileText,
  Archive,
  Terminal,
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3
} from 'lucide-react';
import { toast } from 'sonner';
import { Progress } from '@/components/ui/progress';
import { adminApi } from '@/lib/admin-api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://hrtv6backend-production.up.railway.app';

interface DatabaseStats {
  total_tables: number;
  total_records: number;
  database_size: string;
  last_backup: string;
  connection_count: number;
}

interface Migration {
  id: string;
  name: string;
  applied_at: string;
  status: 'completed' | 'pending' | 'failed';
}

interface Backup {
  id: string;
  filename: string;
  size: string;
  created_at: string;
  type: 'manual' | 'automatic';
  status: 'completed' | 'in_progress' | 'failed';
}

interface QueryResult {
  columns: string[];
  rows: any[][];
  execution_time: number;
  affected_rows?: number;
}

export default function DatabaseView() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<DatabaseStats | null>(null);
  const [migrations, setMigrations] = useState<Migration[]>([]);
  const [backups, setBackups] = useState<Backup[]>([]);
  const [sqlQuery, setSqlQuery] = useState('');
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [queryError, setQueryError] = useState('');

  useEffect(() => {
    if (activeTab === 'overview') {
      fetchDatabaseStats();
    } else if (activeTab === 'migrations') {
      fetchMigrations();
    } else if (activeTab === 'backups') {
      fetchBackups();
    }
  }, [activeTab]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('admin_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };

  const fetchDatabaseStats = async () => {
    try {
      setLoading(true);
      const data = await adminApi.getDatabaseStats() as any;
      setStats(data);
    } catch (error) {
      console.error('Error fetching database stats:', error);
      toast.error('Error fetching database statistics');
    } finally {
      setLoading(false);
    }
  };

  const fetchMigrations = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/admin/database/migrations`, {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setMigrations(data.migrations);
      } else {
        toast.error('Failed to fetch migrations');
      }
    } catch (error) {
      console.error('Error fetching migrations:', error);
      toast.error('Error fetching migrations');
    } finally {
      setLoading(false);
    }
  };

  const fetchBackups = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/admin/database/backups`, {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setBackups(data.backups);
      } else {
        toast.error('Failed to fetch backups');
      }
    } catch (error) {
      console.error('Error fetching backups:', error);
      toast.error('Error fetching backups');
    } finally {
      setLoading(false);
    }
  };

  const executeSqlQuery = async () => {
    if (!sqlQuery.trim()) {
      toast.error('Please enter a SQL query');
      return;
    }

    try {
      setLoading(true);
      setQueryError('');
      const response = await fetch(`${API_BASE_URL}/api/admin/database/query`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ query: sqlQuery })
      });

      const data = await response.json();

      if (response.ok) {
        setQueryResult(data);
        toast.success('Query executed successfully');
      } else {
        setQueryError(data.message || 'Query execution failed');
        toast.error('Query execution failed');
      }
    } catch (error) {
      console.error('Error executing query:', error);
      setQueryError('Error executing query');
      toast.error('Error executing query');
    } finally {
      setLoading(false);
    }
  };

  const createBackup = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/admin/database/backup`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ type: 'manual' })
      });

      if (response.ok) {
        toast.success('Backup creation started');
        fetchBackups();
      } else {
        toast.error('Failed to create backup');
      }
    } catch (error) {
      console.error('Error creating backup:', error);
      toast.error('Error creating backup');
    } finally {
      setLoading(false);
    }
  };

  const runMigrations = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/admin/database/migrate`, {
        method: 'POST',
        headers: getAuthHeaders()
      });

      if (response.ok) {
        toast.success('Migrations started');
        fetchMigrations();
      } else {
        toast.error('Failed to run migrations');
      }
    } catch (error) {
      console.error('Error running migrations:', error);
      toast.error('Error running migrations');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Database Management</h2>
        <p className="text-muted-foreground">
          Manage database operations, migrations, backups, and execute queries
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="migrations">Migrations</TabsTrigger>
          <TabsTrigger value="backups">Backups</TabsTrigger>
          <TabsTrigger value="sql">SQL Console</TabsTrigger>
        </TabsList>

        {/* Database Overview */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Tables</CardTitle>
                <Database className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_tables || 0}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Records</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.total_records?.toLocaleString() || 0}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Database Size</CardTitle>
                <Archive className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.database_size || '0 MB'}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Connections</CardTitle>
                <RefreshCw className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.connection_count || 0}</div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Database Information</CardTitle>
              <CardDescription>Current database status and configuration</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Last Backup:</span>
                  <span className="text-sm text-muted-foreground">
                    {stats?.last_backup ? new Date(stats.last_backup).toLocaleString() : 'Never'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Environment:</span>
                  <Badge variant="outline">Production</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Database Type:</span>
                  <span className="text-sm text-muted-foreground">PostgreSQL</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Migrations */}
        <TabsContent value="migrations" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Database Migrations</CardTitle>
                  <CardDescription>Manage database schema changes</CardDescription>
                </div>
                <Button onClick={runMigrations} disabled={loading}>
                  <Play className="h-4 w-4 mr-2" />
                  Run Migrations
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Migration Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Applied At</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {migrations.map((migration) => (
                    <TableRow key={migration.id}>
                      <TableCell className="font-medium">{migration.name}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            migration.status === 'completed' ? 'default' :
                            migration.status === 'failed' ? 'destructive' :
                            'secondary'
                          }
                        >
                          {migration.status === 'completed' && <CheckCircle className="h-3 w-3 mr-1" />}
                          {migration.status === 'failed' && <AlertTriangle className="h-3 w-3 mr-1" />}
                          {migration.status === 'pending' && <Clock className="h-3 w-3 mr-1" />}
                          {migration.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {migration.applied_at ? new Date(migration.applied_at).toLocaleString() : 'Not applied'}
                      </TableCell>
                    </TableRow>
                  ))}
                  {migrations.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center text-muted-foreground">
                        No migrations found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Backups */}
        <TabsContent value="backups" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Database Backups</CardTitle>
                  <CardDescription>Manage database backups and restores</CardDescription>
                </div>
                <Button onClick={createBackup} disabled={loading}>
                  <Archive className="h-4 w-4 mr-2" />
                  Create Backup
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Filename</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created At</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {backups.map((backup) => (
                    <TableRow key={backup.id}>
                      <TableCell className="font-medium">{backup.filename}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {backup.type}
                        </Badge>
                      </TableCell>
                      <TableCell>{backup.size}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            backup.status === 'completed' ? 'default' :
                            backup.status === 'failed' ? 'destructive' :
                            'secondary'
                          }
                        >
                          {backup.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{new Date(backup.created_at).toLocaleString()}</TableCell>
                      <TableCell>
                        <Button variant="outline" size="sm">
                          <Download className="h-4 w-4 mr-2" />
                          Download
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {backups.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-muted-foreground">
                        No backups found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* SQL Console */}
        <TabsContent value="sql" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>SQL Console</CardTitle>
              <CardDescription>Execute raw SQL queries against the database</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Warning:</strong> Be careful when executing SQL queries in production. 
                  Always backup your data before running destructive operations.
                </AlertDescription>
              </Alert>

              <div className="space-y-2">
                <Label htmlFor="sql-query">SQL Query</Label>
                <Textarea
                  id="sql-query"
                  placeholder="SELECT * FROM users LIMIT 10;"
                  value={sqlQuery}
                  onChange={(e) => setSqlQuery(e.target.value)}
                  className="min-h-[120px] font-mono"
                />
              </div>

              <Button onClick={executeSqlQuery} disabled={loading || !sqlQuery.trim()}>
                <Play className="h-4 w-4 mr-2" />
                Execute Query
              </Button>

              {queryError && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>{queryError}</AlertDescription>
                </Alert>
              )}

              {queryResult && (
                <Card>
                  <CardHeader>
                    <CardTitle>Query Results</CardTitle>
                    <CardDescription>
                      Execution time: {queryResult.execution_time}ms
                      {queryResult.affected_rows !== undefined && 
                        ` • Affected rows: ${queryResult.affected_rows}`
                      }
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-auto max-h-96">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            {queryResult.columns.map((column, index) => (
                              <TableHead key={index}>{column}</TableHead>
                            ))}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {queryResult.rows.map((row, rowIndex) => (
                            <TableRow key={rowIndex}>
                              {row.map((cell, cellIndex) => (
                                <TableCell key={cellIndex} className="font-mono text-xs">
                                  {cell !== null ? String(cell) : <span className="text-muted-foreground">NULL</span>}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                          {queryResult.rows.length === 0 && (
                            <TableRow>
                              <TableCell colSpan={queryResult.columns.length} className="text-center text-muted-foreground">
                                No results returned
                              </TableCell>
                            </TableRow>
                          )}
                        </TableBody>
                      </Table>
                    </div>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
