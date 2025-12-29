"use client";

import { useEffect, useState } from "react";
import { enhancedAdminService } from "@/services/enhanced-admin.service";
import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Upload, RefreshCw } from "lucide-react";
import type { Resume } from "@/types";
import { AlertDialogProvider } from "@/components/alert-dialog-provider";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import { UploadResumeModal } from "./upload-resume-modal";
import { EnhancedResumeDashboard } from "@/components/resume/enhanced-resume-dashboard";
import { ResumeDetailView } from "@/components/resume/resume-detail-view";

export default function AdminResumesPage() {
  const [data, setData] = useState<Resume[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  const [showDetailView, setShowDetailView] = useState(false);
  const { toast } = useToast();

  const loadResumes = async () => {
    try {
      setIsLoading(true);
      console.log('📊 Admin Resumes: Fetching resumes...');
      const response = await enhancedAdminService.getResumes();
      
      if (response && Array.isArray(response)) {
        console.log('✅ Admin Resumes: Data loaded successfully', response.length);
        setData(response);
      } else {
        console.error('❌ Admin Resumes: Invalid response format');
        toast({
          title: "Error loading resumes",
          description: "Invalid response format from server",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('❌ Admin Resumes: Exception:', error);
      const errorMsg = error instanceof Error ? error.message : 'Failed to load resumes';
      toast({
        title: "Error loading resumes",
        description: errorMsg,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
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
    // Implement bulk actions like delete, archive, etc.
    console.log('Bulk action:', action, resumes.length, 'resumes');
    toast({
      title: "Bulk action",
      description: `${action} applied to ${resumes.length} resumes`,
    });
  };

  useEffect(() => {
    loadResumes();
  }, []);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-8">
        <PageHeader
          title="Resume Management"
          description="Enhanced dashboard for managing and analyzing candidate resumes."
          actions={
            <div className="flex gap-2">
              <Button disabled>
                <Upload className="mr-2 h-4 w-4" />
                Upload Resumes
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
          title="Resume Management"
          description="Enhanced dashboard for managing and analyzing candidate resumes with detailed analytics."
          actions={
            <div className="flex gap-2">
              <Button onClick={() => setShowUploadModal(true)}>
                <Upload className="mr-2 h-4 w-4" />
                Upload Resumes
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
          isAdmin={true}
          onResumeSelect={handleResumeSelect}
          onBulkAction={handleBulkAction}
        />

        {/* Upload Modal */}
        {showUploadModal && (
          <UploadResumeModal
            open={showUploadModal}
            onOpenChangeAction={(open) => setShowUploadModal(open)}
            onSuccessAction={() => {
              loadResumes();
              setShowUploadModal(false);
            }}
          />
        )}

        {/* Resume Detail View */}
        {selectedResume && (
          <ResumeDetailView
            resume={selectedResume}
            isOpen={showDetailView}
            onCloseAction={() => {
              setShowDetailView(false);
              setSelectedResume(null);
            }}
            isAdmin={true}
          />
        )}
      </div>
    </AlertDialogProvider>
  );
}
