"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  FileText,
  User,
  Star,
  Clock,
  Brain,
  Download,
  Mail,
  Phone,
  MapPin,
  Briefcase,
  GraduationCap,
  Target,
  Award,
  Calendar,
  Timer,
  Zap,
  CheckCircle,
  XCircle,
  AlertCircle,
  Eye,
  ExternalLink
} from "lucide-react";
import { Resume } from "@/types";
import { format, formatDistanceToNow } from "date-fns";

interface ResumeDetailViewProps {
  resume: Resume;
  isOpen: boolean;
  onCloseAction: () => void;
  isAdmin?: boolean;
}

export function ResumeDetailView({ resume, isOpen, onCloseAction, isAdmin = false }: ResumeDetailViewProps) {
  const getStatusIcon = (status: string, isComplete?: boolean) => {
    if (isComplete) return <CheckCircle className="h-5 w-5 text-green-500" />;
    switch (status) {
      case 'completed': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'processing': return <Timer className="h-5 w-5 text-blue-500" />;
      case 'failed': return <XCircle className="h-5 w-5 text-red-500" />;
      case 'pending': return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      default: return <AlertCircle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getScoreColor = (score?: number) => {
    if (!score) return "text-gray-500";
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreLabel = (score?: number) => {
    if (!score) return "Not Analyzed";
    if (score >= 80) return "Excellent";
    if (score >= 60) return "Good";
    return "Needs Improvement";
  };

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onCloseAction()}>
      <SheetContent className="w-full sm:max-w-2xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Resume Analysis Details
          </SheetTitle>
          <SheetDescription>
            Comprehensive analysis and metadata for {resume.filename}
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Candidate Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Candidate Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-4">
                <Avatar className="h-16 w-16">
                  <AvatarFallback className="text-lg">
                    {resume.candidate_name 
                      ? resume.candidate_name.split(' ').map(n => n[0]).join('').toUpperCase()
                      : <User className="h-8 w-8" />
                    }
                  </AvatarFallback>
                </Avatar>
                <div className="space-y-1">
                  <h3 className="text-xl font-semibold">
                    {resume.candidate_name || 'Name not extracted'}
                  </h3>
                  {resume.candidate_email && (
                    <div className="flex items-center text-muted-foreground">
                      <Mail className="h-4 w-4 mr-2" />
                      {resume.candidate_email}
                    </div>
                  )}
                  {resume.candidate_phone && (
                    <div className="flex items-center text-muted-foreground">
                      <Phone className="h-4 w-4 mr-2" />
                      {resume.candidate_phone}
                    </div>
                  )}
                </div>
              </div>
              
              {resume.experience_years !== undefined && (
                <div className="flex items-center">
                  <Briefcase className="h-4 w-4 mr-2" />
                  <span>{resume.experience_years} years of experience</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Analysis Scores */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Star className="h-5 w-5" />
                Analysis Scores
              </CardTitle>
            </CardHeader>
            <CardContent>
              {resume.overall_score !== undefined ? (
                <div className="space-y-4">
                  {/* Overall Score */}
                  <div className="text-center">
                    <div className={`text-4xl font-bold ${getScoreColor(resume.overall_score)}`}>
                      {resume.overall_score}
                    </div>
                    <div className="text-lg text-muted-foreground">
                      {getScoreLabel(resume.overall_score)}
                    </div>
                    <Progress 
                      value={resume.overall_score} 
                      className="mt-2 h-2"
                    />
                  </div>

                  <Separator />

                  {/* Detailed Scores */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {resume.experience_score !== undefined && (
                      <div className="text-center">
                        <div className="text-2xl font-semibold text-blue-600">
                          {resume.experience_score}
                        </div>
                        <div className="text-sm text-muted-foreground">Experience</div>
                        <Progress value={resume.experience_score} className="mt-1 h-1" />
                      </div>
                    )}
                    
                    {resume.skills_score !== undefined && (
                      <div className="text-center">
                        <div className="text-2xl font-semibold text-purple-600">
                          {resume.skills_score}
                        </div>
                        <div className="text-sm text-muted-foreground">Skills</div>
                        <Progress value={resume.skills_score} className="mt-1 h-1" />
                      </div>
                    )}
                    
                    {resume.education_score !== undefined && (
                      <div className="text-center">
                        <div className="text-2xl font-semibold text-green-600">
                          {resume.education_score}
                        </div>
                        <div className="text-sm text-muted-foreground">Education</div>
                        <Progress value={resume.education_score} className="mt-1 h-1" />
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <AlertCircle className="h-12 w-12 mx-auto mb-4" />
                  <p>Resume analysis not yet completed</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Analysis Content */}
          <Tabs defaultValue="summary" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="summary">Summary</TabsTrigger>
              <TabsTrigger value="skills">Skills</TabsTrigger>
              <TabsTrigger value="education">Education</TabsTrigger>
              <TabsTrigger value="metadata">Metadata</TabsTrigger>
            </TabsList>

            <TabsContent value="summary" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>AI-Generated Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  {resume.summary ? (
                    <p className="text-sm leading-relaxed">{resume.summary}</p>
                  ) : (
                    <p className="text-muted-foreground">No summary available</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="skills" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Key Skills</CardTitle>
                </CardHeader>
                <CardContent>
                  {resume.key_skills && resume.key_skills.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {resume.key_skills.map((skill, index) => (
                        <Badge key={index} variant="secondary">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No skills extracted</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="education" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <GraduationCap className="h-5 w-5" />
                    Education
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {resume.education && resume.education.length > 0 ? (
                    <div className="space-y-3">
                      {resume.education.map((edu, index) => (
                        <div key={index} className="border-l-2 border-blue-200 pl-4">
                          <div className="font-medium">{edu.degree || 'Degree not specified'}</div>
                          <div className="text-sm text-muted-foreground">
                            {edu.institution || 'Institution not specified'}
                          </div>
                          {edu.year && (
                            <div className="text-xs text-muted-foreground">{edu.year}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No education information extracted</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="metadata" className="space-y-4">
              {/* File Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    File Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Filename:</span>
                      <p className="text-muted-foreground break-all">{resume.filename}</p>
                    </div>
                    <div>
                      <span className="font-medium">Upload Date:</span>
                      <p className="text-muted-foreground">
                        {format(new Date(resume.upload_date), 'PPpp')}
                      </p>
                    </div>
                    <div>
                      <span className="font-medium">Status:</span>
                      <div className="flex items-center gap-2 mt-1">
                        {getStatusIcon(resume.processing_status, resume.analysis_complete)}
                        <span className="text-muted-foreground">
                          {resume.analysis_complete ? 'Analysis Complete' : resume.processing_status}
                        </span>
                      </div>
                    </div>
                    {isAdmin && (
                      <div>
                        <span className="font-medium">User ID:</span>
                        <p className="text-muted-foreground font-mono text-xs">{resume.user_id}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Processing Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5" />
                    AI Processing Details
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    {resume.ai_provider_used && (
                      <div>
                        <span className="font-medium">AI Provider:</span>
                        <p className="text-muted-foreground">{resume.ai_provider_used}</p>
                      </div>
                    )}
                    {resume.ai_model_used && (
                      <div>
                        <span className="font-medium">AI Model:</span>
                        <p className="text-muted-foreground">{resume.ai_model_used}</p>
                      </div>
                    )}
                    {resume.ai_processing_time && (
                      <div>
                        <span className="font-medium">Processing Time:</span>
                        <p className="text-muted-foreground flex items-center">
                          <Timer className="h-3 w-3 mr-1" />
                          {resume.ai_processing_time}ms
                        </p>
                      </div>
                    )}
                    {resume.processing_completed_at && (
                      <div>
                        <span className="font-medium">Completed:</span>
                        <p className="text-muted-foreground">
                          {format(new Date(resume.processing_completed_at), 'PPpp')}
                        </p>
                      </div>
                    )}
                  </div>
                  
                  {resume.processing_error && (
                    <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
                      <span className="font-medium text-red-800">Error:</span>
                      <p className="text-red-700 text-sm mt-1">{resume.processing_error}</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Timestamps */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    Timeline
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Uploaded:</span>
                      <span className="text-muted-foreground">
                        {formatDistanceToNow(new Date(resume.upload_date))} ago
                      </span>
                    </div>
                    {resume.processing_completed_at && (
                      <div className="flex justify-between">
                        <span>Analyzed:</span>
                        <span className="text-muted-foreground">
                          {formatDistanceToNow(new Date(resume.processing_completed_at))} ago
                        </span>
                      </div>
                    )}
                    {resume.updated_at && (
                      <div className="flex justify-between">
                        <span>Last Updated:</span>
                        <span className="text-muted-foreground">
                          {formatDistanceToNow(new Date(resume.updated_at))} ago
                        </span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Action Buttons */}
          <div className="flex gap-2 pt-4">
            <Button 
              className="flex-1"
              onClick={() => window.open(resume.file_url, '_blank')}
            >
              <Download className="h-4 w-4 mr-2" />
              Download Resume
            </Button>
            <Button 
              variant="outline"
              onClick={() => window.open(resume.file_url, '_blank')}
            >
              <ExternalLink className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
