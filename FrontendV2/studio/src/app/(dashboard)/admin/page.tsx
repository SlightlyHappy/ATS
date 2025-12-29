
'use client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Users, FileText, Activity, AlertTriangle, List, CheckCircle, Clock } from 'lucide-react';
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, Legend, Pie, PieChart, Cell, CartesianGrid } from "recharts"
import React, { useState, useEffect } from 'react';
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { authenticatedApiCall } from '@/lib/auth-utils';


type AdminStats = {
  total_users: number;
  active_users_today: number;
  total_resumes_processed: number;
  revenue_this_month: number;
  system_health: 'healthy' | 'degraded' | 'down';
  recent_signups?: number;
  users_by_type?: { trial: number; premium: number; enterprise: number; };
  pending_queue?: number;
};

const recentActivities = [
    { id: 1, description: "New user 'XYZ Corp' was created.", timestamp: "2 mins ago" },
    { id: 2, description: "User 'jane.doe@example.com' purchased 100 credits.", timestamp: "15 mins ago" },
    { id: 3, description: "System health check passed successfully.", timestamp: "30 mins ago" },
    { id: 4, description: "Admin 'admin@hrintel.pro' logged in.", timestamp: "1 hour ago" },
];

const activityData = [
    { date: "Jul 1", signups: 10, analyses: 25 },
    { date: "Jul 5", signups: 12, analyses: 30 },
    { date: "Jul 10", signups: 15, analyses: 40 },
    { date: "Jul 15", signups: 18, analyses: 55 },
    { date: "Jul 20", signups: 20, analyses: 60 },
    { date: "Jul 25", signups: 25, analyses: 75 },
    { date: "Jul 30", signups: 30, analyses: 90 },
];


export default function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await authenticatedApiCall('/api/admin/stats', { useAdminToken: true });
        console.log('Received admin stats data:', JSON.stringify(data, null, 2)); // Better debug log
        
        // The frontend guide has a more detailed stats object, so we'll prefer that structure if available
        const statsData = data.stats || data.admin_stats || data;
        console.log('Processed stats data:', JSON.stringify(statsData, null, 2)); // Better debug log
        setStats(statsData);
      } catch (err: any) {
        setError(err.message);
         // Fallback to mock data on error for UI resilience
         setStats({
          total_users: 1250,
          active_users_today: 89,
          total_resumes_processed: 5420,
          revenue_this_month: 125000,
          system_health: 'healthy' as const, // Ensure type safety
          users_by_type: { trial: 1100, premium: 120, enterprise: 30 },
          pending_queue: 12,
        });
      } finally {
        setIsLoading(false);
      }
    }
    fetchStats();
  }, []);
  
  const userPlanData = [
    { name: 'Trial', value: stats?.users_by_type?.trial ?? 0, fill: 'hsl(var(--chart-1))' },
    { name: 'Premium', value: stats?.users_by_type?.premium ?? 0, fill: 'hsl(var(--chart-2))' },
    { name: 'Enterprise', value: stats?.users_by_type?.enterprise ?? 0, fill: 'hsl(var(--chart-3))' },
  ]


  const kpiData = [
    {
      title: "Total Active Users",
      getValue: (stats: AdminStats | null) => stats?.total_users ? stats.total_users.toLocaleString() : 'N/A',
      icon: Users,
    },
    {
      title: "Active Users (24h)",
      getValue: (stats: AdminStats | null) => stats?.active_users_today ? stats.active_users_today.toLocaleString() : 'N/A',
      icon: Activity,
    },
    {
      title: "Resumes Processed",
      getValue: (stats: AdminStats | null) => stats?.total_resumes_processed ? stats.total_resumes_processed.toLocaleString() : 'N/A',
      icon: FileText,
    },
    {
      title: "System Health",
      getValue: (stats: AdminStats | null) => stats?.system_health || 'N/A',
      icon: stats?.system_health === 'healthy' ? CheckCircle : AlertTriangle,
      color: stats?.system_health === 'healthy' ? 'text-green-500' : 'text-red-500',
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Failed to load dashboard stats</AlertTitle>
          <AlertDescription>{error} Using mock data instead.</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {kpiData.map((kpi) => (
          <Card key={kpi.title} className="shadow-lg hover:shadow-xl transition-shadow duration-300">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{kpi.title}</CardTitle>
              <kpi.icon className={`h-5 w-5 text-muted-foreground ${kpi.color ?? ''}`} />
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-8 w-3/4" />
              ) : (
                <div className="text-2xl font-bold">{kpi.getValue(stats)}</div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-5">
        <Card className="shadow-lg md:col-span-3">
            <CardHeader>
                <CardTitle>User Sign-ups vs. Resume Analyses</CardTitle>
                <CardDescription>Activity over the last 30 days.</CardDescription>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={activityData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))' }}/>
                        <Legend />
                        <Bar dataKey="signups" fill="hsl(var(--primary))" name="New Users" />
                        <Bar dataKey="analyses" fill="hsl(var(--secondary))" name="Resumes Analyzed" />
                    </BarChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
        <Card className="shadow-lg md:col-span-2">
             <CardHeader>
                <CardTitle>Users by Plan</CardTitle>
                <CardDescription>Distribution of users by subscription.</CardDescription>
            </CardHeader>
            <CardContent>
                {isLoading ? <Skeleton className="h-[300px] w-full" /> : (
                 <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                        <Pie data={userPlanData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                             {userPlanData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.fill} />
                            ))}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))' }}/>
                        <Legend />
                    </PieChart>
                </ResponsiveContainer>
                )}
            </CardContent>
        </Card>
      </div>

       <div className="grid gap-6 md:grid-cols-5">
        <Card className="shadow-lg md:col-span-3">
            <CardHeader>
                <CardTitle className="flex items-center gap-2"><List /> Recent Activity Feed</CardTitle>
                 <CardDescription>A real-time log of important system events.</CardDescription>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableBody>
                        {recentActivities.map(activity => (
                             <TableRow key={activity.id}>
                                <TableCell>
                                    <div className="font-medium">{activity.description}</div>
                                </TableCell>
                                <TableCell className="text-right text-muted-foreground text-sm">
                                    {activity.timestamp}
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
        <Card className="shadow-lg md:col-span-2">
             <CardHeader>
                <CardTitle className="flex items-center gap-2"><Clock /> AI System Load</CardTitle>
                 <CardDescription>Current analysis queue status.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col items-center justify-center h-full">
                {isLoading ? <Skeleton className="h-12 w-20" /> : <div className="text-6xl font-bold text-primary">{stats?.pending_queue ?? 0}</div> }
                <p className="text-muted-foreground">items in queue</p>
            </CardContent>
        </Card>
      </div>
    </div>
  );
}
