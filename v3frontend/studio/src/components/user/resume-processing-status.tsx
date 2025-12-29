"use client";

import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  RefreshCw, 
  FileText, 
  Zap, 
  Eye,
  Download
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { UserService } from '@/services/user.service';

interface ResumeProcessingStatusProps {
  resumeId: string;
  filename: string;
  onStatusChange?: (status: string) => void;
  showActions?: boolean;
}

interface ProcessingStatus {
  id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  currentStep?: string;
  error?: string;
  analysis_result?: any;
  overall_score?: number;
  estimated_time?: number;
}

export function ResumeProcessingStatus({ 
  resumeId, 
  filename, 
  onStatusChange,
  showActions = true 
}: ResumeProcessingStatusProps) {
  const [status, setStatus] = useState<ProcessingStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPolling, setIsPolling] = useState(false);
  const { toast } = useToast();

  const checkStatus = async () => {
    try {
      // Simulating API call to check resume processing status
      // In real implementation, this would call something like:
      // const response = await UserService.getResumeStatus(resumeId);
      
      // For now, we'll simulate the status progression
      const mockStatuses: ProcessingStatus['status'][] = ['pending', 'processing', 'completed'];
      const currentIndex = Math.floor(Date.now() / 10000) % mockStatuses.length;
      
      const mockStatus: ProcessingStatus = {
        id: resumeId,
        filename,
        status: mockStatuses[currentIndex],
        progress: currentIndex === 1 ? Math.min(90, Math.floor(Date.now() / 1000) % 100) : undefined,
        currentStep: currentIndex === 1 ? 'Analyzing resume structure...' : undefined,
        overall_score: currentIndex === 2 ? 85 : undefined,
        estimated_time: currentIndex === 1 ? 30 : undefined,
      };

      setStatus(mockStatus);
      onStatusChange?.(mockStatus.status);

      // If processing is complete or failed, stop polling
      if (mockStatus.status === 'completed' || mockStatus.status === 'failed') {
        setIsPolling(false);
      }

    } catch (error) {
      console.error('Failed to check resume status:', error);
      toast({
        title: "Error",
        description: "Failed to check resume processing status",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkStatus();
  }, [resumeId]);

  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (isPolling || (status && (status.status === 'pending' || status.status === 'processing'))) {
      interval = setInterval(checkStatus, 3000); // Poll every 3 seconds
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPolling, status?.status]);

  const getStatusIcon = (status: ProcessingStatus['status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'processing':
        return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: ProcessingStatus['status']) => {
    switch (status) {
      case 'pending':
        return <Badge variant="outline" className="gap-1">
          <Clock className="h-3 w-3" />
          Pending
        </Badge>;
      case 'processing':
        return <Badge variant="secondary" className="gap-1">
          <RefreshCw className="h-3 w-3 animate-spin" />
          Processing
        </Badge>;
      case 'completed':
        return <Badge variant="default" className="gap-1">
          <CheckCircle className="h-3 w-3" />
          Completed
        </Badge>;
      case 'failed':
        return <Badge variant="destructive" className="gap-1">
          <AlertCircle className="h-3 w-3" />
          Failed
        </Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const getStatusMessage = () => {
    if (!status) return 'Loading...';

    switch (status.status) {
      case 'pending':
        return 'Your resume is in the queue for processing. We\'ll start analyzing it shortly.';
      case 'processing':
        return status.currentStep || 'Analyzing your resume with AI...';
      case 'completed':
        return `Analysis complete! Your resume scored ${status.overall_score}/100.`;
      case 'failed':
        return status.error || 'Resume processing failed. Please try uploading again.';
      default:
        return 'Unknown status';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Checking status...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!status) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load resume status. Please refresh the page.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center gap-2">
            {getStatusIcon(status.status)}
            <span className="truncate">{filename}</span>
          </div>
          {getStatusBadge(status.status)}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status Message */}
        <p className="text-sm text-muted-foreground">
          {getStatusMessage()}
        </p>

        {/* Progress Bar for Processing */}
        {status.status === 'processing' && status.progress !== undefined && (
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span>Progress</span>
              <span>{status.progress}%</span>
            </div>
            <Progress value={status.progress} className="h-2" />
            {status.estimated_time && (
              <p className="text-xs text-muted-foreground">
                Estimated time remaining: {status.estimated_time} seconds
              </p>
            )}
          </div>
        )}

        {/* Score Display for Completed */}
        {status.status === 'completed' && status.overall_score && (
          <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-green-600" />
              <span className="text-sm font-medium text-green-800">Analysis Score</span>
            </div>
            <Badge 
              variant="default" 
              className={`${
                status.overall_score >= 80 
                  ? 'bg-green-100 text-green-800' 
                  : status.overall_score >= 60 
                  ? 'bg-yellow-100 text-yellow-800' 
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {status.overall_score}/100
            </Badge>
          </div>
        )}

        {/* Error Display */}
        {status.status === 'failed' && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {status.error || 'An error occurred during processing. Please try again.'}
            </AlertDescription>
          </Alert>
        )}

        {/* Action Buttons */}
        {showActions && (
          <div className="flex gap-2 pt-2">
            {status.status === 'completed' && (
              <>
                <Button size="sm" className="gap-1">
                  <Eye className="h-3 w-3" />
                  View Analysis
                </Button>
                <Button variant="outline" size="sm" className="gap-1">
                  <Download className="h-3 w-3" />
                  Download Report
                </Button>
              </>
            )}
            
            {status.status === 'failed' && (
              <Button variant="outline" size="sm" onClick={checkStatus}>
                <RefreshCw className="h-3 w-3 mr-1" />
                Retry
              </Button>
            )}

            {(status.status === 'pending' || status.status === 'processing') && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => {
                  setIsPolling(!isPolling);
                  if (!isPolling) checkStatus();
                }}
              >
                <RefreshCw className={`h-3 w-3 mr-1 ${isPolling ? 'animate-spin' : ''}`} />
                {isPolling ? 'Auto-refresh On' : 'Manual Refresh'}
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
