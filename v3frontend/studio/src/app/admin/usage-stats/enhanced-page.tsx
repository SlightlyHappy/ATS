"use client";

import { useEffect, useState } from "react";
import { AdminService } from "@/services/admin.service";
import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { 
  RefreshCw, 
  Download, 
  TrendingUp, 
  Users, 
  FileText, 
  MessageSquare,
  Clock,
  AlertTriangle,
  Activity,
  BarChart3
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { format, subDays, parseISO } from "date-fns";

interface UsageStats {
  overview: {
    total_users: number;
    active_users_today: number;
    total_resumes_processed: number;
    total_legal_queries: number;
    growth_rate: number;
    conversion_rate: number;
  };
  daily_usage: {
    date: string;
    resume_uploads: number;
    user_logins: number;
    legal_queries: number;
    new_registrations: number;
  }[];
  feature_usage: {
    resume_analysis: number;
    legal_queries: number;
    user_management: number;
    file_uploads: number;
    admin_actions: number;
  };
  trial_usage: {
    users_at_resume_limit: number;
    users_at_legal_limit: number;
    average_usage_percentage: number;
    trial_conversion_rate: number;
  };
  system_performance: {
    avg_response_time: number;
    error_rate: number;
    uptime_percentage: number;
    api_calls_today: number;
  };
  geographic_data: {
    country: string;
    users: number;
    percentage: number;
  }[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

export default function AdminUsageStatsPage() {
  const [data, setData] = useState<UsageStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [dateRange, setDateRange] = useState(7); // days
  const { toast } = useToast();

  const loadUsageStats = async () => {
    try {
      setIsLoading(true);
      const response = await AdminService.getUsageStats();
      
      // Mock data for development - replace with actual API response
      const mockData: UsageStats = {
        overview: {
          total_users: 1247,
          active_users_today: 89,
          total_resumes_processed: 3456,
          total_legal_queries: 892,
          growth_rate: 12.5,
          conversion_rate: 18.3,
        },
        daily_usage: Array.from({ length: 7 }, (_, i) => ({
          date: format(subDays(new Date(), 6 - i), 'yyyy-MM-dd'),
          resume_uploads: Math.floor(Math.random() * 50) + 20,
          user_logins: Math.floor(Math.random() * 100) + 50,
          legal_queries: Math.floor(Math.random() * 30) + 10,
          new_registrations: Math.floor(Math.random() * 15) + 5,
        })),
        feature_usage: {
          resume_analysis: 2845,
          legal_queries: 892,
          user_management: 456,
          file_uploads: 3234,
          admin_actions: 178,
        },
        trial_usage: {
          users_at_resume_limit: 23,
          users_at_legal_limit: 15,
          average_usage_percentage: 67.8,
          trial_conversion_rate: 23.4,
        },
        system_performance: {
          avg_response_time: 245,
          error_rate: 0.8,
          uptime_percentage: 99.7,
          api_calls_today: 15642,
        },
        geographic_data: [
          { country: 'United States', users: 456, percentage: 36.6 },
          { country: 'Canada', users: 234, percentage: 18.8 },
          { country: 'United Kingdom', users: 189, percentage: 15.2 },
          { country: 'Australia', users: 156, percentage: 12.5 },
          { country: 'Germany', users: 134, percentage: 10.8 },
          { country: 'Others', users: 78, percentage: 6.1 },
        ],
      };

      setData(mockData);
    } catch (error) {
      console.error('Failed to load usage stats:', error);
      setData(null);
      toast({
        title: "Failed to Load Usage Stats",
        description: error instanceof Error ? error.message : "Could not connect to the server. Please try refreshing.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setIsRefreshing(true);
      await loadUsageStats();
      toast({
        title: "Success",
        description: "Usage statistics refreshed successfully.",
      });
    } catch (error) {
      toast({
        title: "Error refreshing data",
        description: error instanceof Error ? error.message : "Could not refresh data.",
        variant: "destructive",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleExport = () => {
    if (!data) return;

    const csvData = [
      ['Metric', 'Value'],
      ['Total Users', data.overview.total_users],
      ['Active Users Today', data.overview.active_users_today],
      ['Total Resumes Processed', data.overview.total_resumes_processed],
      ['Total Legal Queries', data.overview.total_legal_queries],
      ['Growth Rate (%)', data.overview.growth_rate],
      ['Conversion Rate (%)', data.overview.conversion_rate],
    ];

    const csvContent = csvData.map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `usage-stats-${format(new Date(), 'yyyy-MM-dd')}.csv`;
    a.click();
    URL.revokeObjectURL(url);

    toast({
      title: "Export Complete",
      description: "Usage statistics have been exported successfully.",
    });
  };

  const getPerformanceStatus = (value: number, type: 'response_time' | 'error_rate' | 'uptime') => {
    switch (type) {
      case 'response_time':
        return value < 300 ? 'excellent' : value < 500 ? 'good' : value < 1000 ? 'fair' : 'poor';
      case 'error_rate':
        return value < 1 ? 'excellent' : value < 2 ? 'good' : value < 5 ? 'fair' : 'poor';
      case 'uptime':
        return value > 99.5 ? 'excellent' : value > 99 ? 'good' : value > 98 ? 'fair' : 'poor';
      default:
        return 'unknown';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'good':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'fair':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'poor':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  useEffect(() => {
    loadUsageStats();
  }, []);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-8">
        <PageHeader
          title="Usage Statistics"
          description="Comprehensive analytics and performance metrics"
        />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-64" />
          ))}
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col gap-8">
        <PageHeader
          title="Usage Statistics"
          description="Comprehensive analytics and performance metrics"
        />
        <Card>
          <CardContent className="flex items-center justify-center py-8">
            <div className="text-center">
              <AlertTriangle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Data Available</h3>
              <p className="text-muted-foreground mb-4">
                Unable to load usage statistics. Please try refreshing the page.
              </p>
              <Button onClick={loadUsageStats}>Try Again</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Usage Statistics"
        description="Comprehensive analytics and performance metrics for your HR platform"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleExport} className="gap-2">
              <Download className="h-4 w-4" />
              Export
            </Button>
            <Button
              variant="outline"
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.overview.total_users.toLocaleString()}</div>
            <div className="flex items-center gap-1 mt-1">
              <TrendingUp className="h-3 w-3 text-green-600" />
              <span className="text-xs text-green-600">+{data.overview.growth_rate}% this month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Today</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.overview.active_users_today}</div>
            <div className="text-xs text-muted-foreground mt-1">
              {((data.overview.active_users_today / data.overview.total_users) * 100).toFixed(1)}% engagement rate
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resumes Processed</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.overview.total_resumes_processed.toLocaleString()}</div>
            <div className="text-xs text-muted-foreground mt-1">
              {(data.overview.total_resumes_processed / data.overview.total_users).toFixed(1)} per user avg
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Legal Queries</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.overview.total_legal_queries.toLocaleString()}</div>
            <div className="text-xs text-muted-foreground mt-1">
              {(data.overview.total_legal_queries / data.overview.total_users).toFixed(1)} per user avg
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Usage Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Daily Usage Trends</CardTitle>
            <CardDescription>User activity over the past 7 days</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.daily_usage}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(value) => format(parseISO(value), 'MMM dd')}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(value) => format(parseISO(value as string), 'MMM dd, yyyy')}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="user_logins" 
                  stroke="#8884d8" 
                  name="User Logins"
                  strokeWidth={2}
                />
                <Line 
                  type="monotone" 
                  dataKey="resume_uploads" 
                  stroke="#82ca9d" 
                  name="Resume Uploads"
                  strokeWidth={2}
                />
                <Line 
                  type="monotone" 
                  dataKey="legal_queries" 
                  stroke="#ffc658" 
                  name="Legal Queries"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Feature Usage */}
        <Card>
          <CardHeader>
            <CardTitle>Feature Usage Distribution</CardTitle>
            <CardDescription>How users interact with different features</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={Object.entries(data.feature_usage).map(([key, value]) => ({
                    name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                    value: value,
                  }))}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {Object.entries(data.feature_usage).map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* System Performance */}
        <Card>
          <CardHeader>
            <CardTitle>System Performance</CardTitle>
            <CardDescription>Real-time performance metrics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Response Time</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm">{data.system_performance.avg_response_time}ms</span>
                  <Badge className={getStatusColor(getPerformanceStatus(data.system_performance.avg_response_time, 'response_time'))}>
                    {getPerformanceStatus(data.system_performance.avg_response_time, 'response_time')}
                  </Badge>
                </div>
              </div>
              <Progress value={Math.max(0, 100 - (data.system_performance.avg_response_time / 10))} />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Error Rate</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm">{data.system_performance.error_rate}%</span>
                  <Badge className={getStatusColor(getPerformanceStatus(data.system_performance.error_rate, 'error_rate'))}>
                    {getPerformanceStatus(data.system_performance.error_rate, 'error_rate')}
                  </Badge>
                </div>
              </div>
              <Progress value={Math.max(0, 100 - data.system_performance.error_rate * 20)} />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Uptime</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm">{data.system_performance.uptime_percentage}%</span>
                  <Badge className={getStatusColor(getPerformanceStatus(data.system_performance.uptime_percentage, 'uptime'))}>
                    {getPerformanceStatus(data.system_performance.uptime_percentage, 'uptime')}
                  </Badge>
                </div>
              </div>
              <Progress value={data.system_performance.uptime_percentage} />
            </div>

            <div className="pt-2 border-t">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">API Calls Today</span>
                <span className="text-sm font-bold">{data.system_performance.api_calls_today.toLocaleString()}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Trial Usage Analytics */}
        <Card>
          <CardHeader>
            <CardTitle>Trial Usage Analytics</CardTitle>
            <CardDescription>User engagement and conversion metrics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{data.trial_usage.users_at_resume_limit}</div>
                <div className="text-xs text-muted-foreground">At Resume Limit</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{data.trial_usage.users_at_legal_limit}</div>
                <div className="text-xs text-muted-foreground">At Legal Limit</div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Average Usage</span>
                <span className="text-sm font-bold">{data.trial_usage.average_usage_percentage}%</span>
              </div>
              <Progress value={data.trial_usage.average_usage_percentage} />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Trial Conversion Rate</span>
                <span className="text-sm font-bold text-green-600">{data.trial_usage.trial_conversion_rate}%</span>
              </div>
              <Progress value={data.trial_usage.trial_conversion_rate} className="bg-green-100" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Geographic Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Geographic Distribution</CardTitle>
          <CardDescription>User distribution by country</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.geographic_data} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="country" type="category" width={100} />
              <Tooltip formatter={(value, name) => [value, 'Users']} />
              <Bar dataKey="users" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
