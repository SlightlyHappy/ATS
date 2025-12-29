"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AdminService } from "@/services/admin.service";
import { useToast } from "@/hooks/use-toast";
import { Upload, FileText } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface UploadResumeModalProps {
  open: boolean;
  onOpenChangeAction: (open: boolean) => void;
  onSuccessAction: () => void;
}

export function UploadResumeModal({ open, onOpenChangeAction, onSuccessAction }: UploadResumeModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [userId, setUserId] = useState<string>("");
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const { toast } = useToast();

  const handleFileSelect = (selectedFile: File) => {
    // Validate file type
    if (!selectedFile.type.includes('pdf') && !selectedFile.name.toLowerCase().endsWith('.docx')) {
      toast({
        title: "Invalid file type",
        description: "Please upload a PDF or DOCX file.",
        variant: "destructive",
      });
      return;
    }

    // Validate file size (10MB limit)
    if (selectedFile.size > 10 * 1024 * 1024) {
      toast({
        title: "File too large",
        description: "Please upload a file smaller than 10MB.",
        variant: "destructive",
      });
      return;
    }

    setFile(selectedFile);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const handleSubmit = async () => {
    if (!file) {
      toast({
        title: "No file selected",
        description: "Please select a file to upload.",
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);
    try {
      // Upload the resume
      const uploadResponse = await AdminService.uploadResume(file, userId || undefined);
      
      // If upload was successful and we have a resume ID, trigger analysis
      if (uploadResponse.success && uploadResponse.data?.id) {
        try {
          console.log('🧠 Auto-analyzing uploaded resume:', uploadResponse.data.id);
          await AdminService.analyzeResume(uploadResponse.data.id);
          toast({
            title: "Upload and analysis started",
            description: "Resume uploaded successfully and analysis has been queued.",
          });
        } catch (analysisError) {
          console.error('❌ Auto-analysis failed:', analysisError);
          toast({
            title: "Upload successful, analysis failed",
            description: "Resume uploaded but automatic analysis failed. You can manually analyze it later.",
          });
        }
      } else {
        toast({
          title: "Upload successful",
          description: "Resume uploaded successfully.",
        });
      }
      
      onSuccessAction();
      // Reset form
      setFile(null);
      setUserId("");
    } catch (error) {
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "Failed to upload resume.",
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleClose = () => {
    if (!isUploading) {
      setFile(null);
      setUserId("");
      onOpenChangeAction(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Upload Resume</DialogTitle>
          <DialogDescription>
            Upload a PDF or DOCX resume file. Analysis will be automatically triggered after upload. Optionally specify a user ID.
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid gap-4 py-4">
          {/* User ID Input */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="userId" className="text-right">
              User ID
            </Label>
            <Input
              id="userId"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="Optional"
              className="col-span-3"
            />
          </div>

          {/* File Upload Area */}
          <div className="grid grid-cols-1 gap-4">
            <Label>Resume File</Label>
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                isDragOver
                  ? "border-primary bg-primary/10"
                  : file
                  ? "border-green-500 bg-green-50"
                  : "border-gray-300 hover:border-gray-400"
              }`}
              onDrop={handleDrop}
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={() => setIsDragOver(false)}
              onClick={() => document.getElementById("file-input")?.click()}
            >
              {file ? (
                <div className="flex items-center justify-center gap-2">
                  <FileText className="h-6 w-6 text-green-600" />
                  <div>
                    <p className="font-medium text-green-800">{file.name}</p>
                    <p className="text-sm text-green-600">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <Upload className="h-8 w-8 text-gray-400" />
                  <div>
                    <p className="font-medium">Drop your resume here</p>
                    <p className="text-sm text-gray-500">
                      or click to browse files
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      PDF or DOCX, max 10MB
                    </p>
                  </div>
                </div>
              )}
            </div>
            <input
              id="file-input"
              type="file"
              accept=".pdf,.docx"
              className="hidden"
              onChange={handleFileInputChange}
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isUploading}
          >
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!file || isUploading}>
            {isUploading ? "Uploading..." : "Upload Resume"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
