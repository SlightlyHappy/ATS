'use client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { UploadCloud, FileText, Gavel, ArrowRight, AlertTriangle } from 'lucide-react';
import Link from "next/link";
import React, { useState, useEffect } from 'react';
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

const quickLinks = [
    { title: "Analyze a New Resume", description: "Upload a resume to get instant AI-powered insights.", href: "/resume-analysis", icon: UploadCloud },
    { title: "View Resume Database", description: "Access and manage all previously analyzed resumes.", href: "/resume-database", icon: FileText },
    { title: "Consult HR Legal AI", description: "Get answers to your Indian labor law questions.", href: "/hr-legal", icon: Gavel },
];

// As per API docs (GET /api/resumes)
type RecentActivity = {
  id: string; // uuid
  filename: string;
  overall_score: number | null;
  upload_date: string; // This is 'created_at' in the resumes table
};

export default function DashboardPage() {
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchRecentActivity() {
      setIsLoading(true);
      setError(null);
      try {
        const token = localStorage.getItem('auth_token');
        if (!token) {
            throw new Error('Authentication token not found. Please log in.');
        }

        const response = await fetch('/api/resumes', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || 'Failed to fetch recent activity.');
        }
        const data = await response.json();
        setRecentActivity((data.resumes || []).slice(0, 3));
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    }
    fetchRecentActivity();
  }, []);

  const renderRecentActivity = () => {
    if (isLoading) {
      return Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="flex items-center justify-between p-3">
          <div>
            <Skeleton className="h-5 w-32 mb-1" />
            <Skeleton className="h-4 w-48" />
          </div>
          <div className="text-right">
            <Skeleton className="h-6 w-12 ml-auto" />
            <Skeleton className="h-4 w-16 mt-1 ml-auto" />
          </div>
        </div>
      ));
    }

    if (error) {
      return (
        <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Error loading activity</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
        </Alert>
      );
    }
    
    if (recentActivity.length === 0) {
      return (
        <div className="text-center text-muted-foreground p-8">
          No recent activity to display. Get started by analyzing a resume.
        </div>
      )
    }

    return recentActivity.map(activity => (
      <div key={activity.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
        <div>
          <p className="font-semibold">{activity.filename}</p>
          <p className="text-sm text-muted-foreground">{new Date(activity.upload_date).toLocaleDateString()}</p>
        </div>
        <div className="text-right">
          {activity.overall_score !== null ? <p className="font-bold text-lg text-primary">{activity.overall_score}</p> : <p className="text-sm text-muted-foreground">Processing...</p>}
          <p className="text-xs text-muted-foreground">AI Score</p>
        </div>
      </div>
    ));
  }

  return (
    <div className="flex flex-col gap-6">
        <div>
            <h1 className="text-3xl font-bold tracking-tight">Welcome back!</h1>
            <p className="text-muted-foreground">Here's a quick overview of your workspace.</p>
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {quickLinks.map((link) => (
                <Card key={link.title} className="shadow-lg hover:shadow-xl transition-shadow duration-300 flex flex-col">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-3">
                            <link.icon className="h-6 w-6 text-primary" />
                            {link.title}
                        </CardTitle>
                        <CardDescription>{link.description}</CardDescription>
                    </CardHeader>
                    <CardContent className="flex-grow flex items-end">
                        <Link href={link.href} className="w-full">
                            <Button className="w-full">
                                Go to {link.title.split(' ')[0]}
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </Link>
                    </CardContent>
                </Card>
            ))}
        </div>

        <Card className="shadow-lg">
            <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>A log of your recent actions within the system.</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                  {renderRecentActivity()}
                </div>
            </CardContent>
        </Card>
    </div>
  );
}
