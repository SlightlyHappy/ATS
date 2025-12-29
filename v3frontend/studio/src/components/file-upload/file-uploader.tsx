"use client";

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

export interface FileUploadProps {
  onFileSelectAction: (file: File | null) => void;
  acceptedFileTypes?: string[];
  maxFileSize?: number; // in bytes
  multiple?: boolean;
  className?: string;
  disabled?: boolean;
  currentFile?: File | null;
}

export function FileUploader({
  onFileSelectAction,
  acceptedFileTypes = ['.pdf', '.docx', '.doc'],
  maxFileSize = 10 * 1024 * 1024, // 10MB default
  multiple = false,
  className,
  disabled = false,
  currentFile = null,
}: FileUploadProps) {
  const [uploadError, setUploadError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    setUploadError(null);

    // Handle rejected files
    if (rejectedFiles.length > 0) {
      const rejectedFile = rejectedFiles[0];
      if (rejectedFile.errors?.some((e: any) => e.code === 'file-too-large')) {
        setUploadError(`File size must be less than ${Math.round(maxFileSize / 1024 / 1024)}MB`);
      } else if (rejectedFile.errors?.some((e: any) => e.code === 'file-invalid-type')) {
        setUploadError(`Please upload a file in one of these formats: ${acceptedFileTypes.join(', ')}`);
      } else {
        setUploadError('Invalid file. Please try again.');
      }
      return;
    }

    // Handle accepted files
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      onFileSelectAction(file);
    }
  }, [acceptedFileTypes, maxFileSize, onFileSelectAction]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedFileTypes.reduce((acc, type) => ({
      ...acc,
      [getAcceptMimeType(type)]: [type]
    }), {}),
    maxSize: maxFileSize,
    multiple,
    disabled,
  });

  const removeFile = () => {
    onFileSelectAction(null);
    setUploadError(null);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={cn('w-full', className)}>
      {!currentFile ? (
        <Card 
          {...getRootProps()} 
          className={cn(
            'border-2 border-dashed cursor-pointer transition-colors hover:border-primary/50',
            isDragActive && 'border-primary bg-primary/5',
            disabled && 'opacity-50 cursor-not-allowed',
            uploadError && 'border-destructive'
          )}
        >
          <CardContent className="flex flex-col items-center justify-center py-10 px-6">
            <input {...getInputProps()} />
            
            <Upload className={cn(
              'h-10 w-10 mb-4',
              isDragActive ? 'text-primary' : 'text-muted-foreground'
            )} />
            
            <div className="text-center space-y-2">
              <h3 className="text-lg font-semibold">
                {isDragActive ? 'Drop your file here' : 'Upload Resume'}
              </h3>
              <p className="text-sm text-muted-foreground">
                Drag and drop your resume file here, or click to browse
              </p>
              <p className="text-xs text-muted-foreground">
                Supports: {acceptedFileTypes.join(', ')} • Max {Math.round(maxFileSize / 1024 / 1024)}MB
              </p>
            </div>
            
            <Button 
              type="button" 
              variant="outline" 
              className="mt-4"
              disabled={disabled}
            >
              Choose File
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="flex items-center justify-between p-4">
            <div className="flex items-center space-x-3">
              <FileText className="h-8 w-8 text-primary" />
              <div>
                <p className="font-medium">{currentFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  {formatFileSize(currentFile.size)}
                </p>
              </div>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={removeFile}
              disabled={disabled}
            >
              <X className="h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      )}
      
      {uploadError && (
        <div className="mt-2 flex items-center space-x-2 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" />
          <span>{uploadError}</span>
        </div>
      )}
    </div>
  );
}

// Helper function to get MIME type from file extension
function getAcceptMimeType(extension: string): string {
  const mimeTypes: Record<string, string> = {
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  };
  
  return mimeTypes[extension] || 'application/octet-stream';
}
