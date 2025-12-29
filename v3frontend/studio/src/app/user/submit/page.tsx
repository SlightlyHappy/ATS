"use client";

import { useState, useRef, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { 
  Upload, 
  FileText, 
  X, 
  AlertCircle, 
  CheckCircle,
  Clock,
  ArrowRight,
  File,
  Target,
  Lightbulb,
  Zap,
  Shield,
  ChevronRight
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { UserService } from "@/services/user.service";
import Link from "next/link";
import { CreditCheck } from "@/components/payment/credit-check";

interface UploadState {
  file: File | null;
  uploading: boolean;
  progress: number;
  status: 'idle' | 'uploading' | 'analyzing' | 'success' | 'error';
  error?: string;
  uploadId?: string;
  analysisResults?: any;
}

interface FileValidation {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

const ACCEPTED_FILE_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
];

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

const JOB_CATEGORIES = [
  'Software Engineering',
  'Data Science', 
  'Marketing',
  'Sales',
  'Human Resources',
  'Finance',
  'Operations',
  'Customer Support',
  'Design',
  'Project Management',
  'Other'
];

export default function UserSubmitPage() {
  const { user } = useAuth();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [jobDescription, setJobDescription] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [jobCategory, setJobCategory] = useState("");
  const [company, setCompany] = useState("");
  const [uploadState, setUploadState] = useState<UploadState>({
    file: null,
    uploading: false,
    progress: 0,
    status: 'idle',
  });
  const [hasCredits, setHasCredits] = useState<boolean>(true);
  const { toast } = useToast();

  const validateFile = useCallback((file: File): FileValidation => {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check file type
    if (!ACCEPTED_FILE_TYPES.includes(file.type)) {
      errors.push(`File type "${file.type}" is not supported. Please upload PDF, DOC, or DOCX files.`);
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      errors.push(`File size (${(file.size / 1024 / 1024).toFixed(1)}MB) exceeds the 5MB limit.`);
    }

    // Check file name
    if (file.name.length > 100) {
      warnings.push('File name is quite long. Consider using a shorter name.');
    }

    // Check for common issues
    if (file.name.toLowerCase().includes('template')) {
      warnings.push('Filename suggests this might be a template. Make sure it\'s your actual resume.');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }, []);

  const handleFileSelect = useCallback((file: File) => {
    const validation = validateFile(file);
    
    if (!validation.isValid) {
      setUploadState(prev => ({
        ...prev,
        status: 'error',
        error: validation.errors.join(' ')
      }));
      return;
    }

    setUploadState(prev => ({
      ...prev,
      file,
      status: 'idle',
      error: undefined
    }));

    // Show warnings if any
    if (validation.warnings.length > 0) {
      toast({
        title: "File Upload Note",
        description: validation.warnings.join(' '),
        variant: "default",
      });
    }
  }, [validateFile, toast]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  }, [handleFileSelect]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  }, [handleFileSelect]);

  const removeFile = useCallback(() => {
    setUploadState(prev => ({
      ...prev,
      file: null,
      status: 'idle',
      error: undefined
    }));
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const simulateProgress = (callback: () => void) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 15;
      if (progress > 90) {
        clearInterval(interval);
        setUploadState(prev => ({ ...prev, progress: 100 }));
        setTimeout(callback, 500);
      } else {
        setUploadState(prev => ({ ...prev, progress }));
      }
    }, 200);
  };

  const handleSubmit = async () => {
    if (!uploadState.file) {
      toast({
        title: "No file selected",
        description: "Please select a resume file to upload.",
        variant: "destructive",
      });
      return;
    }

    // Check credits before proceeding
    if (!hasCredits) {
      toast({
        title: "Insufficient credits",
        description: "You need at least 1 credit to analyze a resume. Please purchase more credits.",
        variant: "destructive",
      });
      return;
    }

    try {
      setUploadState(prev => ({ 
        ...prev, 
        uploading: true, 
        status: 'uploading',
        progress: 0 
      }));

      // Simulate upload progress
      simulateProgress(async () => {
        setUploadState(prev => ({ ...prev, status: 'analyzing' }));
        
        try {
          const response = await UserService.submitResume(uploadState.file!, jobDescription);
          
          if (response.success) {
            setUploadState(prev => ({
              ...prev,
              status: 'success',
              uploadId: response.data?.id,
              analysisResults: response.data
            }));

            toast({
              title: "Resume uploaded successfully!",
              description: "Your resume is being analyzed. You'll be redirected to view the results.",
            });

            // Redirect after a short delay
            setTimeout(() => {
              router.push('/user/my-resumes');
            }, 2000);
          } else {
            throw new Error(response.error || 'Upload failed');
          }
        } catch (error) {
          setUploadState(prev => ({
            ...prev,
            status: 'error',
            error: error instanceof Error ? error.message : 'Upload failed'
          }));
        } finally {
          setUploadState(prev => ({ ...prev, uploading: false }));
        }
      });
    } catch (error) {
      setUploadState(prev => ({
        ...prev,
        uploading: false,
        status: 'error',
        error: error instanceof Error ? error.message : 'An unexpected error occurred'
      }));
    }
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf':
        return <FileText className="h-8 w-8 text-red-500" />;
      case 'doc':
      case 'docx':
        return <File className="h-8 w-8 text-blue-500" />;
      default:
        return <FileText className="h-8 w-8 text-gray-500" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Upload Resume"
        description="Submit your resume for AI-powered analysis and optimization"
      />

      {/* Credit Check Component */}
      <CreditCheck 
        requiredCredits={1}
        onCreditCheckCompleteAction={setHasCredits}
        onTopUpAction={() => router.push('/user/billing')}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Upload Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* File Upload Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Resume Upload
              </CardTitle>
              <CardDescription>
                Upload your resume in PDF, DOC, or DOCX format (max 5MB)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!uploadState.file ? (
                <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    dragActive 
                      ? 'border-primary bg-primary/5' 
                      : 'border-muted-foreground/25 hover:border-muted-foreground/50'
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <div className="space-y-2">
                    <p className="text-lg font-medium">
                      Drop your resume here, or{" "}
                      <button
                        type="button"
                        className="text-primary hover:underline"
                        onClick={() => fileInputRef.current?.click()}
                      >
                        browse files
                      </button>
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Supports PDF, DOC, DOCX up to 5MB
                    </p>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    accept=".pdf,.doc,.docx"
                    onChange={handleFileInput}
                  />
                </div>
              ) : (
                <div className="border rounded-lg p-4">
                  <div className="flex items-center gap-3">
                    {getFileIcon(uploadState.file.name)}
                    <div className="flex-1">
                      <div className="font-medium">{uploadState.file.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {formatFileSize(uploadState.file.size)}
                      </div>
                    </div>
                    {uploadState.status === 'idle' && (
                      <Button variant="ghost" size="sm" onClick={removeFile}>
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                    {(uploadState.status === 'success') && (
                      <Badge className="bg-green-100 text-green-800">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Uploaded
                      </Badge>
                    )}
                  </div>
                  
                  {(uploadState.status === 'uploading' || uploadState.status === 'analyzing') && (
                    <div className="mt-3 space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span>
                          {uploadState.status === 'uploading' ? 'Uploading...' : 'Analyzing...'}
                        </span>
                        <span>{Math.round(uploadState.progress)}%</span>
                      </div>
                      <Progress value={uploadState.progress} />
                    </div>
                  )}
                </div>
              )}

              {uploadState.error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{uploadState.error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Job Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Job Information (Optional)
              </CardTitle>
              <CardDescription>
                Provide job details for more targeted analysis
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="jobTitle">Job Title</Label>
                  <Input
                    id="jobTitle"
                    placeholder="e.g. Senior Software Engineer"
                    value={jobTitle}
                    onChange={(e) => setJobTitle(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="company">Company</Label>
                  <Input
                    id="company"
                    placeholder="e.g. Google, Microsoft"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="jobCategory">Job Category</Label>
                <Select value={jobCategory} onValueChange={setJobCategory}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a category" />
                  </SelectTrigger>
                  <SelectContent>
                    {JOB_CATEGORIES.map((category) => (
                      <SelectItem key={category} value={category}>
                        {category}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="jobDescription">Job Description</Label>
                <Textarea
                  id="jobDescription"
                  placeholder="Paste the job description here for more accurate analysis..."
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  rows={6}
                />
                <p className="text-xs text-muted-foreground">
                  Including a job description helps our AI provide more targeted feedback
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Submit Button */}
          <div className="flex gap-3">
            <Button
              onClick={handleSubmit}
              disabled={!uploadState.file || uploadState.uploading || uploadState.status === 'success' || !hasCredits}
              className="flex-1 gap-2"
              size="lg"
            >
              {uploadState.uploading ? (
                <>
                  <Clock className="h-4 w-4 animate-spin" />
                  {uploadState.status === 'uploading' ? 'Uploading...' : 'Analyzing...'}
                </>
              ) : uploadState.status === 'success' ? (
                <>
                  <CheckCircle className="h-4 w-4" />
                  Upload Complete
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4" />
                  Analyze Resume
                </>
              )}
            </Button>
            
            {uploadState.status === 'success' && (
              <Button variant="outline" asChild>
                <Link href="/user/my-resumes" className="gap-2">
                  View Results
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            )}
          </div>
        </div>

        {/* Sidebar with Tips and Info */}
        <div className="space-y-6">
          {/* Tips Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="h-5 w-5 text-yellow-500" />
                Pro Tips
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-3 text-sm">
                <div className="flex gap-3">
                  <ChevronRight className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                  <div>
                    <p className="font-medium">Use a clean format</p>
                    <p className="text-muted-foreground">Avoid fancy graphics and unusual fonts</p>
                  </div>
                </div>
                
                <div className="flex gap-3">
                  <ChevronRight className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                  <div>
                    <p className="font-medium">Include keywords</p>
                    <p className="text-muted-foreground">Match skills and terms from the job description</p>
                  </div>
                </div>
                
                <div className="flex gap-3">
                  <ChevronRight className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                  <div>
                    <p className="font-medium">Quantify achievements</p>
                    <p className="text-muted-foreground">Use numbers and metrics to show impact</p>
                  </div>
                </div>
                
                <div className="flex gap-3">
                  <ChevronRight className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                  <div>
                    <p className="font-medium">Keep it concise</p>
                    <p className="text-muted-foreground">1-2 pages for most roles, 3+ for senior positions</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Privacy Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-green-500" />
                Privacy & Security
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                <p>Your resume is encrypted and securely stored</p>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                <p>Only you can access your uploaded documents</p>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                <p>Analysis is performed by AI, not humans</p>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                <p>You can delete your data anytime</p>
              </div>
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle>Need Help?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="outline" size="sm" className="w-full justify-start" asChild>
                <Link href="/user/my-resumes">
                  <FileText className="h-4 w-4 mr-2" />
                  View Past Analyses
                </Link>
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start" asChild>
                <Link href="/user/profile">
                  <Target className="h-4 w-4 mr-2" />
                  Account Settings
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
