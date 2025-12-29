"use client";

import { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  Users,
  FileText,
  Briefcase,
  Clock,
  ArrowUpRight,
  RefreshCw,
  Database,
  Activity,
} from "lucide-react";
import PageHeader from "@/components/page-header";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { AdminService } from "@/services/admin.service";
import { DashboardCharts } from "@/app/dashboard/dashboard-charts";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { StatsCard } from "@/components/ui/stats-card";
import { PageTransition, StaggerItem, AnimatedCard } from "@/components/animations/page-transition";

interface AdminDashboardData {
  stats: {
    users: {
      total: number;
      trial_users: number;
      paid_users: number;
      total_analyzed: number;
      at_resume_limit: number;
      at_legal_limit: number;
    };
    database: {
      connection_count: number;
      avg_query_time: number;
      active_sessions: number;
    };
    system: {
      timestamp: string;
      admin_user: string;
      uptime: string;
    };
  };
  recent: {
    id: string;
    name: string;
    status: string;
    aiScore: number;
    date: string;
  }[];
  chartData: any;
}

export default function AdminDashboardPage() {
  const [data, setData] = useState<AdminDashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const { toast } = useToast();

  const loadData = async () => {
    try {
      setIsLoading(true);
      const dashboardData = await AdminService.getDashboardStats();
      
      // AdminService returns direct data, not ApiResponse wrapper
      if (dashboardData && dashboardData.stats) {
        setData(dashboardData);
      } else {
        // Handle case where service returns empty/invalid data
        console.warn("Admin dashboard service returned invalid data:", dashboardData);
        
        const emptyData: AdminDashboardData = {
          stats: {
            users: {
              total: 0,
              trial_users: 0,
              paid_users: 0,
              total_analyzed: 0,
              at_resume_limit: 0,
              at_legal_limit: 0,
            },
            database: {
              connection_count: 0,
              avg_query_time: 0,
              active_sessions: 0,
            },
            system: {
              timestamp: new Date().toISOString(),
              admin_user: "Admin",
              uptime: "Unknown",
            },
          },
          recent: [],
          chartData: {
            averageScores: [],
            resumesByStatus: [],
          },
        };
        
        setData(emptyData);
        
        toast({
          title: "No Data Available",
          description: "Could not load dashboard data. Please try refreshing.",
          variant: "default",
        });
      }
    } catch (error) {
      console.error('Dashboard data loading failed:', error);
      
      // Set empty data on catch error
      const emptyData: AdminDashboardData = {
        stats: {
          users: {
            total: 0,
            trial_users: 0,
            paid_users: 0,
            total_analyzed: 0,
            at_resume_limit: 0,
            at_legal_limit: 0,
          },
          database: {
            connection_count: 0,
            avg_query_time: 0,
            active_sessions: 0,
          },
          system: {
            timestamp: new Date().toISOString(),
            admin_user: "Admin",
            uptime: "Unknown",
          },
        },
        recent: [],
        chartData: {
          averageScores: [],
          resumesByStatus: [],
        },
      };
      
      setData(emptyData);
      
      toast({
        title: "Connection Error",
        description: error instanceof Error ? error.message : "Could not connect to the server. Please try refreshing.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const dashboardData = await AdminService.getDashboardStats();
      setData(dashboardData);
      toast({
        title: "Success",
        description: "Dashboard data refreshed successfully.",
      });
    } catch (error) {
      console.error("Failed to refresh dashboard stats", error);
      toast({
        title: "Refresh Failed",
        description: "Could not refresh data. Keeping current demo data.",
        variant: "default",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (isLoading || !data) {
    return (
      <div className="flex flex-col gap-8">
        <PageHeader 
          title="Admin Dashboard" 
          description="Monitor system performance, user activity, and business metrics."
        />
        
        {/* Enhanced Stats Cards Skeleton */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="stat-card skeleton-enhanced">
              <div className="flex items-center justify-between">
                <div className="space-y-3">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-8 w-16" />
                  <Skeleton className="h-3 w-32" />
                </div>
                <Skeleton className="h-12 w-12 rounded-full" />
              </div>
            </div>
          ))}
        </div>
        
        {/* Enhanced System Health Skeleton */}
        <div className="grid gap-4 md:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="stat-card skeleton-enhanced">
              <div className="flex items-center justify-between">
                <div className="space-y-3">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-8 w-12" />
                  <Skeleton className="h-3 w-28" />
                </div>
                <Skeleton className="h-12 w-12 rounded-full" />
              </div>
            </div>
          ))}
        </div>
        
        {/* Enhanced Charts and Table Skeleton */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          <div className="lg:col-span-4 chart-container skeleton-enhanced">
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <Skeleton className="h-5 w-40" />
                  <Skeleton className="h-4 w-60" />
                </div>
                <Skeleton className="h-8 w-20" />
              </div>
              
              {/* Enhanced Table Skeleton */}
              <div className="space-y-3">
                <div className="flex space-x-4 pb-2 border-b">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-16" />
                </div>
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="flex items-center space-x-4 py-2">
                    <div className="flex items-center space-x-3">
                      <Skeleton className="h-9 w-9 rounded-full" />
                      <Skeleton className="h-4 w-32" />
                    </div>
                    <Skeleton className="h-6 w-16 rounded-full" />
                    <Skeleton className="h-4 w-12" />
                    <Skeleton className="h-4 w-20" />
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          <div className="lg:col-span-3 chart-container skeleton-enhanced">
            <div className="p-6 space-y-6">
              <div className="space-y-2">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-4 w-48" />
              </div>
              
              {/* Chart Skeletons */}
              <div className="space-y-6">
                <div className="space-y-3">
                  <Skeleton className="h-4 w-40 mx-auto" />
                  <Skeleton className="h-32 w-full" />
                </div>
                <div className="space-y-3">
                  <Skeleton className="h-4 w-36 mx-auto" />
                  <Skeleton className="h-32 w-32 rounded-full mx-auto" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const { stats, recent, chartData } = data;

  return (
    <PageTransition stagger>
      <div className="flex flex-col gap-8">
        <StaggerItem>
          <PageHeader 
            title="Admin Dashboard" 
            description="Monitor system performance, user activity, and business metrics."
            actions={
              <Button 
                onClick={handleRefresh} 
                disabled={isRefreshing}
                variant="outline"
                size="sm"
                className="gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                Refresh Stats
              </Button>
            }
          />
        </StaggerItem>

        {/* User Statistics */}
        <StaggerItem>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <AnimatedCard>
              <StatsCard
                title="Total Users"
                value={stats.users.total}
                change={{
                  value: 12,
                  trend: 'up'
                }}
                icon={<Users className="h-6 w-6 text-primary" />}
                description={`${stats.users.trial_users} trial, ${stats.users.paid_users} paid`}
              />
            </AnimatedCard>
            <AnimatedCard>
              <StatsCard
                title="Resumes Analyzed"
                value={stats.users.total_analyzed}
                change={{
                  value: 8,
                  trend: 'up'
                }}
                icon={<FileText className="h-6 w-6 text-primary" />}
                description="Total processed this month"
              />
            </AnimatedCard>
            <AnimatedCard>
              <StatsCard
                title="At Resume Limit"
                value={stats.users.at_resume_limit}
                change={{
                  value: -5,
                  trend: 'down'
                }}
                icon={<Clock className="h-6 w-6 text-primary" />}
                description="Users needing upgrade"
              />
            </AnimatedCard>
            <AnimatedCard>
              <StatsCard
                title="At Legal Limit"
                value={stats.users.at_legal_limit}
                change={{
                  value: 2,
                  trend: 'up'
                }}
                icon={<Briefcase className="h-6 w-6 text-primary" />}
                description="Legal query limits reached"
              />
            </AnimatedCard>
          </div>
        </StaggerItem>

        {/* System Health */}
        <StaggerItem>
          <div className="grid gap-4 md:grid-cols-3">
            <AnimatedCard>
              <StatsCard
                title="Database"
                value={stats.database.connection_count}
                icon={<Database className="h-6 w-6 text-primary" />}
                description={`Avg query: ${stats.database.avg_query_time}ms`}
              />
            </AnimatedCard>
            <AnimatedCard>
              <StatsCard
                title="Active Sessions"
                value={stats.database.active_sessions}
                icon={<Activity className="h-6 w-6 text-primary" />}
                description="Current user sessions"
              />
            </AnimatedCard>
            <AnimatedCard>
              <StatsCard
                title="System Health"
                value="Healthy"
                icon={<Activity className="h-6 w-6 text-green-500" />}
                description={`Uptime: ${stats.system.uptime}`}
              />
            </AnimatedCard>
          </div>
        </StaggerItem>

        {/* Recent Activity & Charts */}
        <StaggerItem>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <AnimatedCard className="col-span-12 lg:col-span-4">
              <Card>
                <CardHeader className="flex flex-row items-center">
                  <div className="grid gap-2">
                    <CardTitle>Recent Submissions</CardTitle>
                    <CardDescription>
                      Latest resumes submitted for analysis.
                    </CardDescription>
                  </div>
                  <Button asChild size="sm" className="ml-auto gap-1">
                    <Link href="/admin/resumes">
                      View All
                      <ArrowUpRight className="h-4 w-4" />
                    </Link>
                  </Button>
                </CardHeader>
                <CardContent>
                  <Table className="data-table-enhanced">
                    <TableHeader>
                      <TableRow className="table-header-enhanced">
                        <TableHead className="h-12 px-4 text-left font-medium">Candidate</TableHead>
                        <TableHead className="hidden sm:table-cell h-12 px-4 text-left font-medium">Status</TableHead>
                        <TableHead className="hidden md:table-cell h-12 px-4 text-left font-medium">AI Score</TableHead>
                        <TableHead className="text-right h-12 px-4 font-medium">Date</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {recent.map((submission) => (
                        <TableRow key={submission.id} className="table-row-enhanced">
                          <TableCell className="px-4 py-3">
                            <div className="flex items-center gap-4">
                              <Avatar className="hidden h-9 w-9 sm:flex">
                                <AvatarFallback>{submission.name.charAt(0)}</AvatarFallback>
                              </Avatar>
                              <div className="font-medium">{submission.name}</div>
                            </div>
                          </TableCell>
                          <TableCell className="hidden sm:table-cell px-4 py-3">
                            <Badge
                              variant={
                                submission.status === "Pending"
                                  ? "secondary"
                                  : submission.status === "Approved"
                                  ? "default"
                                  : "destructive"
                              }
                              className="capitalize hover-lift"
                            >
                              {submission.status.toLowerCase()}
                            </Badge>
                          </TableCell>
                          <TableCell className="hidden md:table-cell px-4 py-3">
                            <span className="font-medium">{submission.aiScore}%</span>
                          </TableCell>
                          <TableCell className="text-right px-4 py-3">
                            <span className="text-sm text-muted-foreground">{submission.date}</span>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </AnimatedCard>
            <AnimatedCard className="lg:col-span-3">
              <DashboardCharts chartData={chartData} />
            </AnimatedCard>
          </div>
        </StaggerItem>
      </div>
    </PageTransition>
  );
}
