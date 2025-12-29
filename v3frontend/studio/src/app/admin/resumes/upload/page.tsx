"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/services/api";
import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Upload, ArrowLeft } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import Link from "next/link";

export default function UploadResumePage() {
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const router = useRouter();
  const { toast } = useToast();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      // Validate file type
      const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      if (!allowedTypes.includes(selectedFile.type)) {
        toast({
          title: "Invalid file type",
          description: "Please upload a PDF or DOCX file.",
          variant: "destructive",
        });
        return;
      }
      setFile(selectedFile);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      toast({
        title: "No file selected",
        description: "Please select a resume file to upload.",
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);
    
    try {
      console.log('📤 Admin Resume Upload: Starting upload process...');
      
      // FIXED: Use real API call instead of simulation
      const response = await apiClient.uploadResume(file);
      
      console.log('📡 Admin Resume Upload: Response received:', {
        success: response.success,
        hasData: !!response.data,
        error: response.error
      });
      
      if (response.success) {
        console.log('✅ Admin Resume Upload: Upload successful');
        
        toast({
          title: "Resume uploaded successfully",
          description: "The resume has been uploaded and queued for analysis.",
        });
        
        router.push('/admin/resumes');
      } else {
        throw new Error(response.error || 'Upload failed');
      }
    } catch (error) {
      console.error('❌ Admin Resume Upload: Upload failed:', error);
      
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "Could not upload the resume.",
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Upload Resume"
        description="Upload a new resume for AI analysis."
        actions={
          <Button variant="outline" asChild>
            <Link href="/admin/resumes">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Resumes
            </Link>
          </Button>
        }
      />
      
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Resume Upload</CardTitle>
          <CardDescription>
            Upload a PDF or DOCX resume file for AI analysis and scoring.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="resume-file">Resume File *</Label>
              <Input
                id="resume-file"
                type="file"
                accept=".pdf,.docx"
                onChange={handleFileChange}
                disabled={isUploading}
                required
              />
              <p className="text-sm text-muted-foreground">
                Supported formats: PDF, DOCX (Max size: 10MB)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="job-description">Job Description (Optional)</Label>
              <Textarea
                id="job-description"
                placeholder="Enter the job description to provide context for the AI analysis..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                disabled={isUploading}
                rows={6}
              />
              <p className="text-sm text-muted-foreground">
                Providing a job description will help the AI analyze how well the resume matches the role.
              </p>
            </div>

            <div className="flex gap-4">
              <Button type="submit" disabled={!file || isUploading}>
                {isUploading ? (
                  <>
                    <Upload className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Resume
                  </>
                )}
              </Button>
              
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => router.push('/admin/resumes')}
                disabled={isUploading}
              >
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
