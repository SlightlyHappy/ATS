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
import { Badge } from '@/components/ui/badge';
import { MoreHorizontal, Search, FileDown, AlertTriangle, Trash2 } from 'lucide-react';
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

// Based on the data structure in your API docs for GET /api/resumes
type Resume = {
  id: string; // uuid
  filename: string;
  upload_date: string;
  overall_score: number | null;
  processing_status: 'completed' | 'pending' | 'failed' | 'reviewed' | 'shortlisted' | 'hired' | 'rejected';
};


const getStatusBadge = (status: Resume['processing_status']) => {
  switch (status) {
    case 'completed': return <Badge variant="secondary">Completed</Badge>;
    case 'pending': return <Badge className="bg-blue-100 text-blue-800 animate-pulse">Pending</Badge>;
    case 'failed': return <Badge variant="destructive">Failed</Badge>;
    case 'reviewed': return <Badge variant="secondary">Reviewed</Badge>;
    case 'shortlisted': return <Badge variant="default" className="bg-blue-500 hover:bg-blue-600">Shortlisted</Badge>;
    case 'hired': return <Badge variant="default" className="bg-green-500 hover:bg-green-600">Hired</Badge>;
    case 'rejected': return <Badge variant="destructive">Rejected</Badge>;
    default: return <Badge variant="outline">{status}</Badge>;
  }
};

export default function ResumeDatabasePage() {
    const [resumes, setResumes] = useState<Resume[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { toast } = useToast();

    async function fetchResumes() {
        setIsLoading(true);
        setError(null);
        try {
            const token = localStorage.getItem('auth_token');
            if (!token) {
                throw new Error('Authentication token not found. Please log in.');
            }
            const response = await fetch('https://hrtoolsbackend-production.up.railway.app/api/resumes', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to fetch resumes.');
            }
            const data = await response.json();
            setResumes(data.resumes || []);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    }

    const handleDeleteResume = async (resumeId: string) => {
        try {
            const token = localStorage.getItem('auth_token');
            if (!token) {
                toast({ title: "Authentication Error", description: "Please log in again.", variant: "destructive" });
                return;
            }
            const response = await fetch(`https://hrtoolsbackend-production.up.railway.app/api/resumes/${resumeId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` },
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Failed to delete resume.');
            }
            toast({
                title: "Success",
                description: "Resume deleted successfully.",
            });
            // Refresh the list
            fetchResumes();
        } catch (err: any) {
            toast({
                title: "Error",
                description: err.message,
                variant: "destructive",
            });
        }
    };
    
    useEffect(() => {
        fetchResumes();
    }, []);

    const renderTableContent = () => {
        if (isLoading) {
            return Array.from({ length: 6 }).map((_, i) => (
                <TableRow key={i}>
                    <TableCell><Skeleton className="h-5 w-48" /></TableCell>
                    <TableCell><Skeleton className="h-6 w-20" /></TableCell>
                    <TableCell className="text-right"><Skeleton className="h-5 w-12 ml-auto" /></TableCell>
                    <TableCell><Skeleton className="h-5 w-24" /></TableCell>
                    <TableCell><Skeleton className="h-8 w-8" /></TableCell>
                </TableRow>
            ));
        }

        if (error) {
             return (
                <TableRow>
                    <TableCell colSpan={5}>
                        <Alert variant="destructive">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertTitle>Error</AlertTitle>
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    </TableCell>
                </TableRow>
            );
        }

        if (resumes.length === 0) {
            return (
                 <TableRow>
                    <TableCell colSpan={5} className="text-center h-24">
                        You haven't analyzed any resumes yet.
                    </TableCell>
                </TableRow>
            );
        }

        return resumes.map((resume) => (
              <TableRow key={resume.id}>
                <TableCell className="font-medium">{resume.filename}</TableCell>
                <TableCell>
                  <div className="font-bold text-lg">{resume.overall_score ?? 'N/A'}</div>
                </TableCell>
                <TableCell>{getStatusBadge(resume.processing_status)}</TableCell>
                <TableCell>{new Date(resume.upload_date).toLocaleDateString()}</TableCell>
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
                      <DropdownMenuItem>View Analysis</DropdownMenuItem>
                      <DropdownMenuItem>Download Report</DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem className="text-red-500" onClick={() => handleDeleteResume(resume.id)}>
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
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
                <CardTitle>Resume Database</CardTitle>
                <CardDescription>Search and manage all your processed resumes.</CardDescription>
            </div>
            <div className="flex gap-2 items-center">
                <div className="relative flex-1">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input placeholder="Search resumes..." className="pl-8" />
                </div>
                <Button variant="outline">
                    <FileDown className="h-4 w-4 mr-2" />
                    Export
                </Button>
            </div>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Filename</TableHead>
              <TableHead>AI Score</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Date Analyzed</TableHead>
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
