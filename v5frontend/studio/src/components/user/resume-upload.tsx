'use client';

import { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { 
  Upload, 
  FileText, 
  Archive, 
  CheckCircle, 
  XCircle, 
  Clock,
  AlertTriangle,
  Trash2,
  RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';
import { userApi } from '@/lib/user-api';

interface UploadProgress {
  current: number;
  total: number;
  filename: string;
  status: 'uploading' | 'completed' | 'error';
  error?: string;
}

interface UploadResult {
  filename: string;
  success: boolean;
  result?: any;
  error?: string;
}

export default function ResumeUpload() {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
  const [batchProgress, setBatchProgress] = useState<{
    totalFiles: number;
    completed: number;
    failed: number;
    results: UploadResult[];
  } | null>(null);
  const [recentUploads, setRecentUploads] = useState<any[]>([]);

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
      handleFiles(e.dataTransfer.files);
    }
  }, []);

  const handleFiles = async (files: FileList) => {
    const file = files[0];
    if (!file) return;

    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
      'text/plain',
      'application/zip'
    ];

    if (!allowedTypes.includes(file.type)) {
      toast.error('Invalid file type. Please upload PDF, DOCX, DOC, TXT, or ZIP files.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      toast.error('File size exceeds 10MB limit.');
      return;
    }

    try {
      setUploading(true);
      
      if (file.type === 'application/zip') {
        await handleZipUpload(file);
      } else {
        await handleSingleUpload(file);
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setUploading(false);
      setUploadProgress(null);
      setBatchProgress(null);
    }
  };

  const handleSingleUpload = async (file: File) => {
    try {
      setUploadProgress({
        current: 1,
        total: 1,
        filename: file.name,
        status: 'uploading'
      });

      const result = await userApi.uploadResume(file);
      
      setUploadProgress({
        current: 1,
        total: 1,
        filename: file.name,
        status: 'completed'
      });

      setRecentUploads(prev => [result, ...prev.slice(0, 4)]);
      toast.success(`Resume uploaded successfully: ${file.name}`);
      
    } catch (error) {
      setUploadProgress({
        current: 1,
        total: 1,
        filename: file.name,
        status: 'error',
        error: error instanceof Error ? error.message : 'Upload failed'
      });
      throw error;
    }
  };

  const handleZipUpload = async (file: File) => {
    try {
      // Show cache warning for ZIP files
      toast.info('Processing ZIP file: We will temporarily cache extracted files in your browser for processing.', {
        duration: 5000
      });

      const results = await userApi.handleZipUpload(file, (progress) => {
        setUploadProgress(progress);
      });

      setBatchProgress({
        totalFiles: results.totalFiles,
        completed: results.successful,
        failed: results.failed,
        results: results.results
      });
      
      if (results.successful > 0) {
        toast.success(`Successfully uploaded ${results.successful} out of ${results.totalFiles} resumes`);
      }
      
      if (results.failed > 0) {
        toast.warning(`${results.failed} files failed to upload`);
      }

      // Update recent uploads with successful uploads
      const successfulUploads = results.results
        .filter(r => r.success)
        .map(r => r.result)
        .slice(0, 5);
      
      setRecentUploads(prev => [...successfulUploads, ...prev].slice(0, 10));

    } catch (error) {
      console.error('ZIP upload error:', error);
      throw error;
    }
  };

  const clearResults = () => {
    setBatchProgress(null);
    setRecentUploads([]);
  };

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Upload className="h-5 w-5" />
            <span>Resume Upload</span>
          </CardTitle>
          <CardDescription>
            Upload individual resumes or ZIP files containing multiple resumes. Supported formats: PDF, DOCX, DOC, TXT, ZIP
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={`relative border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              dragActive 
                ? 'border-primary bg-primary/5' 
                : 'border-muted-foreground/25 hover:border-muted-foreground/50'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="file-upload"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              onChange={(e) => e.target.files && handleFiles(e.target.files)}
              accept=".pdf,.docx,.doc,.txt,.zip"
              disabled={uploading}
            />
            
            <div className="space-y-4">
              <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                {uploading ? (
                  <RefreshCw className="h-8 w-8 text-primary animate-spin" />
                ) : (
                  <Upload className="h-8 w-8 text-primary" />
                )}
              </div>
              
              <div>
                <p className="text-lg font-medium">
                  {uploading ? 'Processing files...' : 'Drop files here or click to upload'}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  Maximum file size: 10MB per file
                </p>
              </div>
              
              <Button disabled={uploading} variant="outline">
                Select Files
              </Button>
            </div>
          </div>

          {/* Upload Progress */}
          {uploadProgress && (
            <div className="mt-6 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Uploading: {uploadProgress.filename}</span>
                <Badge variant={
                  uploadProgress.status === 'completed' ? 'default' :
                  uploadProgress.status === 'error' ? 'destructive' : 'secondary'
                }>
                  {uploadProgress.status}
                </Badge>
              </div>
              
              <Progress 
                value={(uploadProgress.current / uploadProgress.total) * 100} 
                className="w-full"
              />
              
              <div className="text-sm text-muted-foreground">
                {uploadProgress.current} of {uploadProgress.total} files
              </div>
              
              {uploadProgress.error && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>{uploadProgress.error}</AlertDescription>
                </Alert>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* ZIP Processing Information */}
      <Alert>
        <Archive className="h-4 w-4" />
        <AlertDescription>
          <strong>ZIP File Processing:</strong> When you upload ZIP files, we extract and process each resume individually using your browser's resources. 
          Temporary files are cached locally during processing and automatically cleared afterward. This ensures better progress tracking and error handling per file.
        </AlertDescription>
      </Alert>

      {/* Batch Upload Results */}
      {batchProgress && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-base">Batch Upload Results</CardTitle>
            <Button variant="ghost" size="sm" onClick={clearResults}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{batchProgress.completed}</div>
                <div className="text-sm text-muted-foreground">Successful</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{batchProgress.failed}</div>
                <div className="text-sm text-muted-foreground">Failed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{batchProgress.totalFiles}</div>
                <div className="text-sm text-muted-foreground">Total Files</div>
              </div>
            </div>

            <div className="space-y-2 max-h-40 overflow-y-auto">
              {batchProgress.results.map((result, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-muted/50 rounded">
                  <div className="flex items-center space-x-2">
                    {result.success ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-600" />
                    )}
                    <span className="text-sm truncate">{result.filename}</span>
                  </div>
                  {result.error && (
                    <span className="text-xs text-red-600 truncate max-w-40">
                      {result.error}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Uploads */}
      {recentUploads.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Uploads</CardTitle>
            <CardDescription>
              Recently uploaded resumes and their analysis status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentUploads.map((upload, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">{upload.original_filename || upload.filename}</p>
                      <p className="text-xs text-muted-foreground">
                        Uploaded {new Date(upload.upload_timestamp).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={upload.is_analyzed ? 'default' : 'secondary'}>
                      {upload.is_analyzed ? 'Analyzed' : 'Processing'}
                    </Badge>
                    {upload.is_analyzed && upload.analysis_score && (
                      <Badge variant="outline">
                        Score: {upload.analysis_score.toFixed(1)}
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
