"use client";

import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import {
  FileText,
  User,
  Star,
  Clock,
  Brain,
  TrendingUp,
  Download,
  Eye,
  Search,
  Filter,
  Calendar,
  Users,
  Briefcase,
  GraduationCap,
  Phone,
  Mail,
  MapPin,
  Target,
  Zap,
  CheckCircle,
  XCircle,
  AlertCircle,
  Timer,
  Trash2,
  Play
} from "lucide-react";
import { Resume } from "@/types";
import { format, formatDistanceToNow } from "date-fns";

interface EnhancedResumeDashboardProps {
  resumes: Resume[];
  isAdmin?: boolean;
  onResumeSelect?: (resume: Resume) => void;
  onBulkAction?: (action: string, resumes: Resume[]) => void;
  onResumeDelete?: (resumeId: string) => void;
  onResumeAnalyze?: (resumeId: string) => void;
}

export function EnhancedResumeDashboard({ 
  resumes, 
  isAdmin = false, 
  onResumeSelect,
  onBulkAction,
  onResumeDelete,
  onResumeAnalyze
}: EnhancedResumeDashboardProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [scoreFilter, setScoreFilter] = useState<string>("all");
  const [selectedResumes, setSelectedResumes] = useState<Set<string>>(new Set());

  // Analytics calculations
  const analytics = useMemo(() => {
    const total = resumes.length;
    const completed = resumes.filter(r => r.analysis_complete).length;
    const pending = resumes.filter(r => r.processing_status === 'pending').length;
    const processing = resumes.filter(r => r.processing_status === 'processing').length;
    const failed = resumes.filter(r => r.processing_status === 'failed').length;
    
    const scores = resumes.filter(r => r.overall_score !== undefined).map(r => r.overall_score!);
    const avgScore = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
    const highScores = scores.filter(s => s >= 80).length;
    
    const avgProcessingTime = resumes
      .filter(r => r.ai_processing_time)
      .reduce((acc, r) => acc + (r.ai_processing_time || 0), 0) / 
      resumes.filter(r => r.ai_processing_time).length || 0;

    return {
      total,
      completed,
      pending,
      processing,
      failed,
      avgScore: Math.round(avgScore * 10) / 10,
      highScores,
      avgProcessingTime: Math.round(avgProcessingTime),
      completionRate: total > 0 ? Math.round((completed / total) * 100) : 0
    };
  }, [resumes]);

  // Filtered resumes
  const filteredResumes = useMemo(() => {
    return resumes.filter(resume => {
      const matchesSearch = searchTerm === "" || 
        resume.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
        resume.candidate_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        resume.candidate_email?.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStatus = statusFilter === "all" || resume.processing_status === statusFilter;
      
      const matchesScore = scoreFilter === "all" || (() => {
        const score = resume.overall_score || 0;
        switch (scoreFilter) {
          case "high": return score >= 80;
          case "medium": return score >= 60 && score < 80;
          case "low": return score < 60;
          default: return true;
        }
      })();

      return matchesSearch && matchesStatus && matchesScore;
    });
  }, [resumes, searchTerm, statusFilter, scoreFilter]);

  const getStatusIcon = (status: string, isComplete?: boolean) => {
    if (isComplete) return <CheckCircle className="h-4 w-4 text-green-500" />;
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'processing': return <Timer className="h-4 w-4 text-blue-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'pending': return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      default: return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string, isComplete?: boolean) => {
    if (isComplete) {
      return <Badge variant="default" className="bg-green-100 text-green-800">Analyzed</Badge>;
    }
    switch (status) {
      case 'completed':
        return <Badge variant="default" className="bg-green-100 text-green-800">Completed</Badge>;
      case 'processing':
        return <Badge variant="secondary" className="bg-blue-100 text-blue-800">Processing</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      case 'pending':
        return <Badge variant="outline" className="bg-yellow-100 text-yellow-800">Pending</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const getScoreColor = (score?: number) => {
    if (!score) return "text-gray-500";
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="space-y-6">
      {/* Analytics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Resumes</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.total}</div>
            <p className="text-xs text-muted-foreground">
              {analytics.completionRate}% analyzed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Score</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.avgScore}</div>
            <p className="text-xs text-muted-foreground">
              {analytics.highScores} high scores (80+)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processing Queue</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.pending + analytics.processing}</div>
            <p className="text-xs text-muted-foreground">
              {analytics.pending} pending, {analytics.processing} processing
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Processing Time</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.avgProcessingTime}ms</div>
            <p className="text-xs text-muted-foreground">
              {analytics.failed} failed analyses
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters & Search</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by filename, name, or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full md:w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="processing">Processing</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>

            <Select value={scoreFilter} onValueChange={setScoreFilter}>
              <SelectTrigger className="w-full md:w-48">
                <SelectValue placeholder="Filter by score" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Scores</SelectItem>
                <SelectItem value="high">High (80+)</SelectItem>
                <SelectItem value="medium">Medium (60-79)</SelectItem>
                <SelectItem value="low">Low (&lt;60)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Resume List */}
      <Card>
        <CardHeader>
          <CardTitle>Resume Details ({filteredResumes.length})</CardTitle>
          <CardDescription>
            Comprehensive view of all resume data and analysis results
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Candidate</TableHead>
                  <TableHead>File</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Scores</TableHead>
                  <TableHead>Experience</TableHead>
                  <TableHead>Analysis Details</TableHead>
                  <TableHead>Processing Info</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredResumes.map((resume) => (
                  <TableRow key={resume.id} className="hover:bg-muted/50">
                    {/* Candidate Info */}
                    <TableCell>
                      <div className="flex items-center space-x-3">
                        <Avatar className="h-8 w-8">
                          <AvatarFallback>
                            {resume.candidate_name 
                              ? resume.candidate_name.split(' ').map(n => n[0]).join('').toUpperCase()
                              : <User className="h-4 w-4" />
                            }
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="font-medium">
                            {resume.candidate_name || 'Unknown'}
                          </div>
                          {resume.candidate_email && (
                            <div className="flex items-center text-xs text-muted-foreground">
                              <Mail className="h-3 w-3 mr-1" />
                              {resume.candidate_email}
                            </div>
                          )}
                          {resume.candidate_phone && (
                            <div className="flex items-center text-xs text-muted-foreground">
                              <Phone className="h-3 w-3 mr-1" />
                              {resume.candidate_phone}
                            </div>
                          )}
                        </div>
                      </div>
                    </TableCell>

                    {/* File Info */}
                    <TableCell>
                      <div>
                        <div className="font-medium truncate max-w-32" title={resume.filename}>
                          {resume.filename}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {format(new Date(resume.upload_date), 'MMM dd, yyyy')}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {formatDistanceToNow(new Date(resume.upload_date))} ago
                        </div>
                      </div>
                    </TableCell>

                    {/* Status */}
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(resume.processing_status, resume.analysis_complete)}
                        {getStatusBadge(resume.processing_status, resume.analysis_complete)}
                      </div>
                      {resume.processing_error && (
                        <div className="text-xs text-red-600 mt-1">
                          Error: {resume.processing_error.substring(0, 50)}...
                        </div>
                      )}
                    </TableCell>

                    {/* Scores */}
                    <TableCell>
                      {resume.overall_score !== undefined ? (
                        <div className="space-y-1">
                          <div className={`font-bold ${getScoreColor(resume.overall_score)}`}>
                            Overall: {resume.overall_score}
                          </div>
                          {resume.experience_score !== undefined && (
                            <div className="text-xs">
                              <div>Exp: {resume.experience_score}</div>
                              <div>Skills: {resume.skills_score || 'N/A'}</div>
                              <div>Edu: {resume.education_score || 'N/A'}</div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-muted-foreground">Not analyzed</span>
                      )}
                    </TableCell>

                    {/* Experience */}
                    <TableCell>
                      <div className="space-y-1">
                        {resume.experience_years !== undefined && (
                          <div className="flex items-center text-sm">
                            <Briefcase className="h-3 w-3 mr-1" />
                            {resume.experience_years} years
                          </div>
                        )}
                        {resume.key_skills && resume.key_skills.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {resume.key_skills.slice(0, 3).map((skill, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {skill}
                              </Badge>
                            ))}
                            {resume.key_skills.length > 3 && (
                              <Badge variant="outline" className="text-xs">
                                +{resume.key_skills.length - 3}
                              </Badge>
                            )}
                          </div>
                        )}
                      </div>
                    </TableCell>

                    {/* Analysis Details */}
                    <TableCell>
                      <div className="space-y-1 text-xs">
                        {resume.ai_provider_used && (
                          <div>
                            <Brain className="h-3 w-3 inline mr-1" />
                            {resume.ai_provider_used}
                          </div>
                        )}
                        {resume.ai_model_used && (
                          <div className="text-muted-foreground">
                            Model: {resume.ai_model_used}
                          </div>
                        )}
                        {resume.processing_completed_at && (
                          <div className="text-muted-foreground">
                            Completed: {format(new Date(resume.processing_completed_at), 'MMM dd, HH:mm')}
                          </div>
                        )}
                      </div>
                    </TableCell>

                    {/* Processing Info */}
                    <TableCell>
                      <div className="space-y-1 text-xs">
                        {resume.ai_processing_time && (
                          <div>
                            <Timer className="h-3 w-3 inline mr-1" />
                            {resume.ai_processing_time}ms
                          </div>
                        )}
                        {isAdmin && (
                          <div className="text-muted-foreground">
                            User: {resume.user_id.substring(0, 8)}...
                          </div>
                        )}
                        {resume.updated_at && (
                          <div className="text-muted-foreground">
                            Updated: {formatDistanceToNow(new Date(resume.updated_at))} ago
                          </div>
                        )}
                      </div>
                    </TableCell>

                    {/* Actions */}
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onResumeSelect?.(resume)}
                          title="View details"
                        >
                          <Eye className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => window.open(resume.file_url, '_blank')}
                          title="Download resume"
                        >
                          <Download className="h-3 w-3" />
                        </Button>
                        {isAdmin && !resume.analysis_complete && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onResumeAnalyze?.(resume.id)}
                            title="Analyze resume"
                          >
                            <Play className="h-3 w-3" />
                          </Button>
                        )}
                        {isAdmin && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onResumeDelete?.(resume.id)}
                            title="Delete resume"
                            className="text-red-600 hover:text-red-800 hover:bg-red-50"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {filteredResumes.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              No resumes match the current filters.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
