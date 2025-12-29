
'use client';

import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { authenticatedApiCall } from '@/lib/auth-utils';
import { Badge } from '@/components/ui/badge';
import { MoreHorizontal, Search, RefreshCw, AlertTriangle } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';


type Resume = {
  id: string; // uuid
  filename: string;
  processing_status: 'completed' | 'pending' | 'failed';
  overall_score: number | null;
  user_id: string; // Assuming user email or id is available
  created_at: string;
};

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'completed': return <Badge className="bg-green-100 text-green-800">Success</Badge>;
    case 'pending': return <Badge className="bg-blue-100 text-blue-800 animate-pulse">Processing</Badge>;
    case 'failed': return <Badge variant="destructive">Failed</Badge>;
    default: return <Badge variant="outline">{status}</Badge>;
  }
};

export default function ResumeAdminPage() {
    const [resumes, setResumes] = useState<Resume[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { toast } = useToast();

    // Fetch all resumes for admin viewing with authentication
    async function fetchAdminResumes() {
        setIsLoading(true);
        setError(null);
        try {
            const data = await authenticatedApiCall('/api/admin/resumes', { useAdminToken: true });
            setResumes(data.resumes || []);
        } catch (err: any) {
            setError(err.message);
            const mockResumes: any[] = [
              { id: 'uuid-101', filename: 'resume_aarav_sharma.pdf', processing_status: 'completed', overall_score: 92, user_id: 'john.doe@example.com', created_at: '2023-10-26' },
              { id: 'uuid-102', filename: 'diya_patel_cv.docx', processing_status: 'completed', overall_score: 88, user_id: 'jane.smith@example.com', created_at: '2023-10-25' },
              { id: 'uuid-103', filename: 'project_manager_rohan.pdf', processing_status: 'completed', overall_score: 95, user_id: 'john.doe@example.com', created_at: '2023-10-24' },
              { id: 'uuid-104', filename: 'data_scientist_priya.pdf', processing_status: 'failed', overall_score: null, user_id: 'alice.j@example.com', created_at: '2023-10-23' },
              { id: 'uuid-105', filename: 'frontend_arjun_v.docx', processing_status: 'pending', overall_score: null, user_id: 'bob.brown@example.com', created_at: '2023-10-22' },
              { id: 'uuid-106', filename: 'Saanvi_Gupta_PM.pdf', processing_status: 'completed', overall_score: 91, user_id: 'jane.smith@example.com', created_at: '2023-10-21' },
            ];
            setResumes(mockResumes);
        } finally {
            setIsLoading(false);
        }
    }
    
    useEffect(() => {
        fetchAdminResumes();
    }, []);

    const handleRetryAnalysis = async (resumeId: string) => {
        toast({
            title: `Retrying analysis for resume ${resumeId}`,
            description: "Please wait...",
        });
        try {
            // As per docs, this endpoint retries analysis with admin authentication
            const data = await authenticatedApiCall(`/api/analyze/${resumeId}`, {
                method: 'POST',
                useAdminToken: true,
                body: JSON.stringify({}),
            });
            toast({
                title: "Analysis Retry Started",
                description: `The analysis for resume ${resumeId} has been queued.`,
                variant: 'default',
            });
            fetchAdminResumes();
        } catch (err: any) {
            toast({
                title: "Error",
                description: err.message,
                variant: "destructive",
            });
        }
    };


    const renderTableContent = () => {
        if (isLoading) {
            return Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                    <TableCell><Skeleton className="h-5 w-48" /></TableCell>
                    <TableCell><Skeleton className="h-5 w-32" /></TableCell>
                    <TableCell><Skeleton className="h-6 w-20" /></TableCell>
                    <TableCell className="text-right"><Skeleton className="h-5 w-12 ml-auto" /></TableCell>
                    <TableCell><Skeleton className="h-5 w-24" /></TableCell>
                    <TableCell><Skeleton className="h-8 w-8" /></TableCell>
                </TableRow>
            ));
        }

        if (error && resumes.length === 0) {
            return (
                <TableRow>
                    <TableCell colSpan={6}>
                        <Alert variant="destructive">
                            <AlertTitle>Error</AlertTitle>
                            <AlertDescription>{error} Using mock data instead.</AlertDescription>
                        </Alert>
                    </TableCell>
                </TableRow>
            );
        }

        if (resumes.length === 0) {
            return (
                <TableRow>
                    <TableCell colSpan={6} className="text-center h-24">
                        No resumes found in the system.
                    </TableCell>
                </TableRow>
            )
        }

        return resumes.map((resume) => (
            <TableRow key={resume.id}>
                <TableCell className="font-medium">{resume.filename}</TableCell>
                <TableCell className="text-sm text-muted-foreground">{resume.user_id}</TableCell>
                <TableCell>{getStatusBadge(resume.processing_status)}</TableCell>
                <TableCell className="text-right font-mono">{resume.overall_score ?? 'N/A'}</TableCell>
                <TableCell>{new Date(resume.created_at).toLocaleDateString()}</TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button aria-haspopup="true" size="icon" variant="ghost">
                        <MoreHorizontal className="h-4 w-4" />
                        <span className="sr-only">Toggle menu</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Actions</DropdownMenuLabel>
                      <DropdownMenuItem>View Analysis Details</DropdownMenuItem>
                      <DropdownMenuItem>View User Profile</DropdownMenuItem>
                      {resume.processing_status === 'failed' && (
                        <>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => handleRetryAnalysis(resume.id)}>
                                <RefreshCw className="mr-2 h-4 w-4" />
                                Retry Analysis
                            </DropdownMenuItem>
                        </>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
        ));
    };

  return (
    <Card className="shadow-lg">
      <CardHeader>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
                <CardTitle>Resume Database Administration</CardTitle>
                <CardDescription>System-wide view of all resumes and analysis jobs.</CardDescription>
            </div>
            <div className="flex gap-2 items-center">
                <div className="relative flex-1">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input placeholder="Search by filename or user..." className="pl-8" />
                </div>
            </div>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Filename</TableHead>
              <TableHead>Submitted by</TableHead>
              <TableHead>Analysis Status</TableHead>
              <TableHead className="text-right">AI Score</TableHead>
              <TableHead>Submitted On</TableHead>
              <TableHead><span className="sr-only">Actions</span></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {renderTableContent()}
          </TableBody>
        </Table>
        <div className="flex items-center justify-end space-x-2 py-4">
            <Button variant="outline" size="sm">Previous</Button>
            <Button variant="outline" size="sm">Next</Button>
        </div>
      </CardContent>
    </Card>
  );
}
