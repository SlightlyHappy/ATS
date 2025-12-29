"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Progress } from "@/components/ui/progress";
import { 
  ChevronDown, 
  Play, 
  Trash2, 
  Download, 
  X,
  Check,
  RefreshCw
} from "lucide-react";
import { AdminService } from "@/services/admin.service";
import { useToast } from "@/hooks/use-toast";
import type { Resume } from "@/types";

interface BatchOperationsProps {
  selectedResumes: Resume[];
  onClearSelectionAction: () => void;
  onBatchCompleteAction: () => void;
}

interface BatchProgress {
  total: number;
  completed: number;
  failed: number;
  isRunning: boolean;
  currentOperation: string;
}

export function BatchOperations({
  selectedResumes,
  onClearSelectionAction,
  onBatchCompleteAction,
}: BatchOperationsProps) {
  const [progress, setProgress] = useState<BatchProgress | null>(null);
  const { toast } = useToast();

  if (selectedResumes.length === 0) return null;

  const handleBatchAnalyze = async () => {
    const resumeIds = selectedResumes.map(r => r.id);
    
    setProgress({
      total: resumeIds.length,
      completed: 0,
      failed: 0,
      isRunning: true,
      currentOperation: "Analyzing resumes..."
    });

    try {
      const response = await AdminService.batchAnalyzeResumes(resumeIds);
      
      if (response.success) {
        toast({
          title: "Batch analysis started",
          description: `Analysis queued for ${resumeIds.length} resumes.`,
        });
        
        setProgress({
          total: resumeIds.length,
          completed: resumeIds.length,
          failed: 0,
          isRunning: false,
          currentOperation: "Analysis queued"
        });
        
        setTimeout(() => {
          setProgress(null);
          onBatchCompleteAction();
        }, 2000);
      } else {
        throw new Error(response.error || "Batch analysis failed");
      }
    } catch (error) {
      toast({
        title: "Batch analysis failed",
        description: error instanceof Error ? error.message : "Could not start batch analysis.",
        variant: "destructive",
      });
      
      setProgress({
        total: resumeIds.length,
        completed: 0,
        failed: resumeIds.length,
        isRunning: false,
        currentOperation: "Analysis failed"
      });
      
      setTimeout(() => setProgress(null), 3000);
    }
  };

  const handleBatchDelete = async () => {
    const resumeIds = selectedResumes.map(r => r.id);
    
    setProgress({
      total: resumeIds.length,
      completed: 0,
      failed: 0,
      isRunning: true,
      currentOperation: "Deleting resumes..."
    });

    let completed = 0;
    let failed = 0;

    // Delete resumes one by one to track progress
    for (const resumeId of resumeIds) {
      try {
        await AdminService.deleteResume(resumeId);
        completed++;
      } catch (error) {
        failed++;
        console.error(`Failed to delete resume ${resumeId}:`, error);
      }
      
      setProgress(prev => prev ? {
        ...prev,
        completed,
        failed
      } : null);
    }

    const successCount = completed;
    const failureCount = failed;

    toast({
      title: failureCount > 0 ? "Partial deletion completed" : "Deletion completed",
      description: `${successCount} resumes deleted successfully${failureCount > 0 ? `, ${failureCount} failed` : ''}.`,
      variant: failureCount > 0 ? "destructive" : "default",
    });

    setProgress({
      total: resumeIds.length,
      completed,
      failed,
      isRunning: false,
      currentOperation: "Deletion completed"
    });

    setTimeout(() => {
      setProgress(null);
      onBatchCompleteAction();
    }, 2000);
  };

  const handleBatchDownload = async () => {
    toast({
      title: "Download started",
      description: `Preparing download for ${selectedResumes.length} resumes.`,
    });

    // This would typically trigger a zip file creation on the backend
    // For now, we'll simulate the process
    setProgress({
      total: selectedResumes.length,
      completed: 0,
      failed: 0,
      isRunning: true,
      currentOperation: "Preparing download..."
    });

    // Simulate download preparation
    setTimeout(() => {
      setProgress({
        total: selectedResumes.length,
        completed: selectedResumes.length,
        failed: 0,
        isRunning: false,
        currentOperation: "Download ready"
      });

      toast({
        title: "Download ready",
        description: "Resume archive is ready for download.",
      });

      setTimeout(() => setProgress(null), 2000);
    }, 2000);
  };

  const progressPercentage = progress 
    ? Math.round(((progress.completed + progress.failed) / progress.total) * 100)
    : 0;

  return (
    <Card className="mb-4 border-blue-200 bg-blue-50/50">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Badge variant="secondary" className="bg-blue-100 text-blue-800">
              {selectedResumes.length} selected
            </Badge>
            
            {!progress && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="gap-2">
                    Batch Actions
                    <ChevronDown className="h-3 w-3" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start">
                  <DropdownMenuItem onClick={handleBatchAnalyze} className="gap-2">
                    <Play className="h-4 w-4" />
                    Analyze Selected
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleBatchDownload} className="gap-2">
                    <Download className="h-4 w-4" />
                    Download Selected
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem 
                    onClick={handleBatchDelete} 
                    className="gap-2 text-destructive focus:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete Selected
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}

            {progress && (
              <div className="flex items-center gap-3">
                {progress.isRunning ? (
                  <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                ) : progress.failed > 0 ? (
                  <X className="h-4 w-4 text-red-600" />
                ) : (
                  <Check className="h-4 w-4 text-green-600" />
                )}
                
                <div className="min-w-[200px]">
                  <div className="flex justify-between text-xs text-muted-foreground mb-1">
                    <span>{progress.currentOperation}</span>
                    <span>{progress.completed + progress.failed}/{progress.total}</span>
                  </div>
                  <Progress value={progressPercentage} className="h-2" />
                </div>
              </div>
            )}
          </div>

          {!progress && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={onClearSelectionAction}
              className="gap-2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-3 w-3" />
              Clear Selection
            </Button>
          )}
        </div>

        {/* Selected resumes preview */}
        {selectedResumes.length > 0 && !progress && (
          <div className="mt-3 pt-3 border-t border-blue-200">
            <div className="flex flex-wrap gap-1 max-h-20 overflow-y-auto">
              {selectedResumes.slice(0, 10).map((resume) => (
                <Badge key={resume.id} variant="outline" className="text-xs">
                  {resume.filename.length > 20 
                    ? `${resume.filename.substring(0, 20)}...` 
                    : resume.filename
                  }
                </Badge>
              ))}
              {selectedResumes.length > 10 && (
                <Badge variant="outline" className="text-xs">
                  +{selectedResumes.length - 10} more
                </Badge>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
