"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { useRouter } from "next/navigation";
import { Loader2, Upload } from "lucide-react";
import { apiClient } from "@/services/api";
import { useState } from "react";
import { FileUploader } from "@/components/file-upload/file-uploader";

const formSchema = z.object({
  name: z.string().min(2, {
    message: "Name must be at least 2 characters.",
  }),
  email: z.string().email({
    message: "Please enter a valid email address.",
  }),
  jobDescription: z.string().optional(),
});

export default function ResumeForm() {
  const { toast } = useToast();
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      email: "",
      jobDescription: "",
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    console.log('📋 Resume Form: Starting submission process...', {
      formData: {
        name: values.name,
        email: values.email,
        hasJobDescription: !!values.jobDescription,
        jobDescriptionLength: values.jobDescription?.length || 0
      },
      selectedFile: selectedFile ? {
        name: selectedFile.name,
        size: selectedFile.size,
        type: selectedFile.type,
        lastModified: new Date(selectedFile.lastModified).toISOString()
      } : null
    });

    if (!selectedFile) {
      console.log('❌ Resume Form: No file selected');
      toast({
        title: "Error",
        description: "Please select a resume file to upload.",
        variant: "destructive",
      });
      return;
    }

    console.log('🔄 Resume Form: Setting submission state and starting upload...');
    setIsSubmitting(true);
    
    try {
      console.log('📤 Resume Form: Calling user-specific upload endpoint...');
      
      // FIXED: Use user-specific upload endpoint instead of admin endpoint
      const response = await apiClient.uploadMyResume(selectedFile, values.jobDescription);
      
      console.log('📡 Resume Form: Upload response received:', {
        success: response.success,
        hasData: !!response.data,
        error: response.error,
        message: response.message,
        endpoint: '/api/user/upload-resume'
      });
      
      if (response.success) {
        console.log('✅ Resume Form: Upload successful, showing success toast and redirecting...');
        
        toast({
          title: "Success!",
          description: `Resume file "${selectedFile.name}" has been uploaded successfully.`,
        });
        
        // Redirect to the appropriate page based on user role
        // For now, redirect to user's my-resumes page
        console.log('🔄 Resume Form: Redirecting to /user/my-resumes...');
        router.push("/user/my-resumes");
      } else {
        console.log('❌ Resume Form: Upload failed - response indicates failure');
        throw new Error(response.error || 'Upload failed');
      }
    } catch (error) {
      console.log('❌ Resume Form: Upload error caught:', error);
      
      toast({
        title: "Upload Failed",
        description: error instanceof Error ? error.message : "Failed to upload resume. Please try again.",
        variant: "destructive",
      });
    } finally {
      console.log('🔄 Resume Form: Resetting submission state...');
      setIsSubmitting(false);
    }
  }

  const handleFileSelect = (file: File | null) => {
    console.log('📁 Resume Form: File selection changed:', file ? {
      name: file.name,
      size: file.size,
      type: file.type,
      lastModified: new Date(file.lastModified).toISOString()
    } : 'No file selected');
    
    setSelectedFile(file);
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        {/* File Upload Section */}
        <div className="form-section">
          <div className="form-group">
            <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
              Resume File *
            </label>
            <p className="text-[0.8rem] text-muted-foreground">
              Upload your resume in PDF or Word format (max 10MB)
            </p>
          </div>
          <FileUploader
            onFileSelectAction={handleFileSelect}
            currentFile={selectedFile}
            acceptedFileTypes={['.pdf', '.docx', '.doc']}
            maxFileSize={10 * 1024 * 1024} // 10MB
            disabled={isSubmitting}
          />
        </div>

        {/* Personal Information Section */}
        <div className="form-section">
          <h3 className="text-lg font-semibold mb-4">Candidate Information</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem className="form-group">
                  <FormLabel className="text-sm font-medium">Candidate Name</FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="e.g., Jane Doe" 
                      className="transition-all duration-200 focus:ring-2 focus:ring-primary/20" 
                      {...field} 
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem className="form-group">
                  <FormLabel className="text-sm font-medium">Candidate Email</FormLabel>
                  <FormControl>
                    <Input 
                      placeholder="e.g., candidate@example.com" 
                      type="email"
                      className="transition-all duration-200 focus:ring-2 focus:ring-primary/20" 
                      {...field} 
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        </div>

        {/* Job Description Section */}
        <div className="form-section">
          <FormField
            control={form.control}
            name="jobDescription"
            render={({ field }) => (
              <FormItem className="form-group">
                <FormLabel className="text-sm font-medium">Job Description (Optional)</FormLabel>
                <FormControl>
                  <Textarea
                    placeholder="Paste the job description here to get more targeted analysis..."
                    className="min-h-[150px] transition-all duration-200 focus:ring-2 focus:ring-primary/20"
                    {...field}
                  />
                </FormControl>
                <FormDescription className="text-sm text-muted-foreground">
                  Providing a job description helps tailor the AI analysis to specific role requirements and improves matching accuracy.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
        
        <Button 
          type="submit" 
          disabled={isSubmitting || !selectedFile}
          className="w-full h-12 text-base font-medium btn-enhanced"
          size="lg"
        >
          {isSubmitting ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : <Upload className="mr-2 h-5 w-5" />}
          {isSubmitting ? "Analyzing Resume..." : "Upload & Analyze Resume"}
        </Button>
      </form>
    </Form>
  );
}
