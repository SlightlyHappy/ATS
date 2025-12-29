"use client";

import { useEffect, useState } from "react";
import { fetchResumes } from "@/services/api";
import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { PlusCircle, RefreshCw } from "lucide-react";
import type { Resume } from "@/types";
import { AlertDialogProvider } from "@/components/alert-dialog-provider";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import { useLoading } from "@/components/loading/loading-provider";
import { EnhancedResumeDashboard } from "@/components/resume/enhanced-resume-dashboard";
import { ResumeDetailView } from "@/components/resume/resume-detail-view";

export default function ResumesPage() {
  const [data, setData] = useState<Resume[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  const [showDetailView, setShowDetailView] = useState(false);
  const { toast } = useToast();
  const { setLoading } = useLoading();

  const loadResumes = async () => {
    setIsLoading(true);
    setLoading('resumes', true);
    try {
      console.log('📊 User Resumes: Fetching resumes...');
      const resumes = await fetchResumes();
      console.log('✅ User Resumes: Data loaded successfully', resumes.length);
      setData(resumes);
    } catch (error) {
      console.error('❌ User Resumes: Error:', error);
      toast({
        title: "Error fetching resumes",
        description: error instanceof Error ? error.message : "Could not connect to the server.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
      setLoading('resumes', false);
    }
  };

  const refreshData = async () => {
    setIsRefreshing(true);
    await loadResumes();
    setIsRefreshing(false);
    toast({
      title: "Data refreshed",
      description: "Resume data has been updated successfully.",
    });
  };

  const handleResumeSelect = (resume: Resume) => {
    setSelectedResume(resume);
    setShowDetailView(true);
  };

  const handleBulkAction = async (action: string, resumes: Resume[]) => {
    // User-specific bulk actions (more limited than admin)
    console.log('User bulk action:', action, resumes.length, 'resumes');
    toast({
      title: "Action completed",
      description: `${action} applied to ${resumes.length} resumes`,
    });
  };

  useEffect(() => {
    loadResumes();
  }, [setLoading, toast]);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-8">
        <PageHeader
          title="My Resumes"
          description="View and manage your uploaded resumes and analysis results."
          actions={
            <div className="flex gap-2">
              <Button asChild disabled>
                <Link href="/submit-resume">
                  <PlusCircle className="mr-2 h-4 w-4" />
                  Upload Resume
                </Link>
              </Button>
              <Button variant="outline" disabled>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh
              </Button>
            </div>
          }
        />
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    );
  }

  return (
    <AlertDialogProvider>
      <div className="flex flex-col gap-8">
        <PageHeader
          title="My Resumes"
          description="Comprehensive view of your uploaded resumes with detailed analysis results and scores."
          actions={
            <div className="flex gap-2">
              <Button asChild>
                <Link href="/submit-resume">
                  <PlusCircle className="mr-2 h-4 w-4" />
                  Upload Resume
                </Link>
              </Button>
              <Button 
                variant="outline" 
                onClick={refreshData}
                disabled={isRefreshing}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          }
        />

        <EnhancedResumeDashboard
          resumes={data}
          isAdmin={false}
          onResumeSelect={handleResumeSelect}
          onBulkAction={handleBulkAction}
        />

        {/* Resume Detail View */}
        {selectedResume && (
          <ResumeDetailView
            resume={selectedResume}
            isOpen={showDetailView}
            onCloseAction={() => {
              setShowDetailView(false);
              setSelectedResume(null);
            }}
            isAdmin={false}
          />
        )}
      </div>
    </AlertDialogProvider>
  );
}
