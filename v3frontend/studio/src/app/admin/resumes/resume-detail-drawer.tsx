"use client";

import { useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Download, 
  RefreshCw, 
  User, 
  Calendar, 
  FileText, 
  Star,
  Eye,
  Play
} from "lucide-react";
import { format } from "date-fns";
import { AdminService } from "@/services/admin.service";
import { useToast } from "@/hooks/use-toast";
import type { Resume } from "@/types";

interface ResumeDetailDrawerProps {
  resume: Resume | null;
  open: boolean;
  onOpenChangeAction: (open: boolean) => void;
  onRerunAnalysisAction?: (resumeId: string) => void;
}

export function ResumeDetailDrawer({
  resume,
  open,
  onOpenChangeAction,
  onRerunAnalysisAction,
}: ResumeDetailDrawerProps) {
  const [isRerunning, setIsRerunning] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const { toast } = useToast();

  if (!resume) return null;

  const handleDownload = async () => {
    if (!resume.file_url) {
      toast({
        title: "Download unavailable",
        description: "File URL not available for this resume.",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsDownloading(true);
      // In a real implementation, this would trigger a download
      // For now, we'll simulate the download process
      const link = document.createElement('a');
      link.href = resume.file_url;
      link.download = resume.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast({
        title: "Download started",
        description: `Downloading ${resume.filename}`,
      });
    } catch (error) {
      toast({
        title: "Download failed",
        description: "Could not download the file. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsDownloading(false);
    }
  };

  const handleRerunAnalysis = async () => {
    try {
      setIsRerunning(true);
      await AdminService.analyzeResume(resume.id);
      
      toast({
        title: "Analysis queued",
        description: "Resume analysis has been queued for reprocessing.",
      });
      
      onRerunAnalysisAction?.(resume.id);
    } catch (error) {
      toast({
        title: "Failed to rerun analysis",
        description: error instanceof Error ? error.message : "Could not queue analysis.",
        variant: "destructive",
      });
    } finally {
      setIsRerunning(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'default';
      case 'processing':
        return 'secondary';
      case 'pending':
        return 'secondary';
      case 'failed':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  const formatScore = (score: number | null | undefined) => {
    if (score === null || score === undefined) return 'N/A';
    return `${score}%`;
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChangeAction}>
      <SheetContent className="w-full sm:max-w-2xl">
        <SheetHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              <SheetTitle className="text-lg">{resume.filename}</SheetTitle>
            </div>
            <Badge variant={getStatusColor(resume.processing_status)}>
              {resume.processing_status}
            </Badge>
          </div>
          <SheetDescription>
            Resume analysis details and metadata
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-120px)] mt-6">
          <div className="space-y-6">
            {/* Basic Information */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Resume Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Filename:</span>
                    <p className="font-medium">{resume.filename}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">User ID:</span>
                    <p className="font-medium">{resume.user_id}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Upload Date:</span>
                    <p className="font-medium">
                      {format(new Date(resume.upload_date), "MMM dd, yyyy 'at' HH:mm")}
                    </p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Overall Score:</span>
                    <div className="flex items-center gap-2">
                      <Star className="h-4 w-4 text-yellow-500" />
                      <span className="font-bold text-lg">
                        {formatScore(resume.overall_score)}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button
                onClick={handleDownload}
                disabled={isDownloading || !resume.file_url}
                className="flex-1 gap-2"
                variant="outline"
              >
                <Download className="h-4 w-4" />
                {isDownloading ? "Downloading..." : "Download"}
              </Button>
              
              <Button
                onClick={handleRerunAnalysis}
                disabled={isRerunning}
                className="flex-1 gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${isRerunning ? 'animate-spin' : ''}`} />
                {isRerunning ? "Queuing..." : "Rerun Analysis"}
              </Button>
            </div>

            {/* Analysis Results */}
            {resume.analysis_result && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Eye className="h-4 w-4" />
                    Analysis Results
                  </CardTitle>
                  <CardDescription>
                    AI-powered analysis of the resume content
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {resume.analysis_result.overall_assessment && (
                    <div>
                      <h4 className="font-medium text-sm mb-2">Overall Assessment</h4>
                      <p className="text-sm text-muted-foreground bg-muted p-3 rounded-lg">
                        {resume.analysis_result.overall_assessment}
                      </p>
                    </div>
                  )}

                  {resume.analysis_result.agent_insights && (
                    <div>
                      <h4 className="font-medium text-sm mb-2">Agent Insights</h4>
                      <div className="space-y-2">
                        {Object.entries(resume.analysis_result.agent_insights).map(([key, value]) => (
                          <div key={key} className="bg-muted p-3 rounded-lg">
                            <span className="font-medium text-sm capitalize">{key}:</span>
                            <p className="text-sm text-muted-foreground mt-1">{String(value)}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <Separator />

                  {/* JSON Viewer - Collapsible */}
                  <details className="group">
                    <summary className="cursor-pointer font-medium text-sm mb-2 list-none flex items-center gap-2">
                      <Play className="h-3 w-3 transition-transform group-open:rotate-90" />
                      Full Analysis JSON
                    </summary>
                    <div className="mt-2 p-3 bg-slate-950 text-slate-50 rounded-lg overflow-auto text-xs">
                      <pre className="whitespace-pre-wrap">
                        {JSON.stringify(resume.analysis_result, null, 2)}
                      </pre>
                    </div>
                  </details>
                </CardContent>
              </Card>
            )}

            {/* No Analysis Available */}
            {!resume.analysis_result && resume.processing_status === 'completed' && (
              <Card>
                <CardContent className="p-6 text-center text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No analysis results available for this resume.</p>
                  <Button
                    onClick={handleRerunAnalysis}
                    disabled={isRerunning}
                    className="mt-3 gap-2"
                    variant="outline"
                  >
                    <RefreshCw className={`h-4 w-4 ${isRerunning ? 'animate-spin' : ''}`} />
                    Run Analysis
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Processing Status */}
            {resume.processing_status === 'processing' && (
              <Card>
                <CardContent className="p-6 text-center text-muted-foreground">
                  <RefreshCw className="h-12 w-12 mx-auto mb-2 opacity-50 animate-spin" />
                  <p>Analysis is currently in progress...</p>
                  <p className="text-xs mt-1">This may take a few minutes to complete.</p>
                </CardContent>
              </Card>
            )}

            {/* Failed Status */}
            {resume.processing_status === 'failed' && (
              <Card className="border-destructive">
                <CardContent className="p-6 text-center">
                  <div className="text-destructive">
                    <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p className="font-medium">Analysis Failed</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      The analysis could not be completed. Please try running it again.
                    </p>
                    <Button
                      onClick={handleRerunAnalysis}
                      disabled={isRerunning}
                      className="mt-3 gap-2"
                      variant="outline"
                    >
                      <RefreshCw className={`h-4 w-4 ${isRerunning ? 'animate-spin' : ''}`} />
                      Retry Analysis
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
