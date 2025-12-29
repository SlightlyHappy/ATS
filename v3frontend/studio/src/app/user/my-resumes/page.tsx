"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { UserService, Resume as UserResume } from "@/services/user.service";
import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  FileText, 
  Download, 
  Trash2, 
  Eye, 
  Search, 
  RefreshCw,
  Calendar,
  Star,
  AlertCircle,
  TrendingUp,
  Target,
  CheckCircle,
  Clock,
  Filter,
  Grid,
  List,
  BarChart3,
  Users,
  Award,
  BookOpen
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  PieChart,
  Pie,
  Cell
} from 'recharts';

interface Resume extends UserResume {
  user_id?: string;
  analysis_result?: {
    overall_assessment: string;
    agent_insights: any;
    skills_found?: string[];
    experience_level?: string;
    recommendations?: string[];
    strengths?: string[];
    weaknesses?: string[];
    keyword_matches?: number;
    ats_compatibility?: number;
    readability_score?: number;
    formatting_score?: number;
  };
}

interface ResumeStats {
  totalResumes: number;
  averageScore: number;
  topSkills: { skill: string; count: number }[];
  scoreDistribution: { range: string; count: number }[];
  recentActivity: { date: string; action: string; resume: string }[];
}

export default function EnhancedUserMyResumesPage() {
  const { user } = useAuth();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [scoreFilter, setScoreFilter] = useState<string>("all");
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('table');
  const [resumeStats, setResumeStats] = useState<ResumeStats | null>(null);
  const { toast } = useToast();

  const loadResumes = async () => {
    try {
      setIsLoading(true);
      const response = await UserService.getMyResumes();
      
      if (response.success && response.data) {
        setResumes(response.data.resumes);
        generateStats(response.data.resumes);
      } else {
        throw new Error(response.error || 'Failed to load resumes');
      }
    } catch (error) {
      console.error('Failed to load resumes:', error);
      toast({
        title: "Error loading resumes",
        description: error instanceof Error ? error.message : "Could not load your resumes. Please try again.",
        variant: "destructive",
      });
      setResumes([]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateStats = (resumeData: Resume[]) => {
    const stats: ResumeStats = {
      totalResumes: resumeData.length,
      averageScore: 0,
      topSkills: [],
      scoreDistribution: [],
      recentActivity: []
    };

    // Calculate average score
    const scoresWithValue = resumeData.filter(r => r.overall_score);
    if (scoresWithValue.length > 0) {
      stats.averageScore = Math.round(
        scoresWithValue.reduce((sum, r) => sum + (r.overall_score || 0), 0) / scoresWithValue.length
      );
    }

    // Aggregate skills
    const skillCounts: { [key: string]: number } = {};
    resumeData.forEach(resume => {
      resume.analysis_result?.skills_found?.forEach(skill => {
        skillCounts[skill] = (skillCounts[skill] || 0) + 1;
      });
    });
    stats.topSkills = Object.entries(skillCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10)
      .map(([skill, count]) => ({ skill, count }));

    // Score distribution
    const distribution = { '0-40': 0, '41-60': 0, '61-80': 0, '81-100': 0 };
    scoresWithValue.forEach(resume => {
      const score = resume.overall_score!;
      if (score <= 40) distribution['0-40']++;
      else if (score <= 60) distribution['41-60']++;
      else if (score <= 80) distribution['61-80']++;
      else distribution['81-100']++;
    });
    stats.scoreDistribution = Object.entries(distribution)
      .map(([range, count]) => ({ range, count }));

    // Recent activity (simulated)
    stats.recentActivity = resumeData
      .sort((a, b) => new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime())
      .slice(0, 5)
      .map(resume => ({
        date: resume.upload_date,
        action: 'Uploaded',
        resume: resume.filename
      }));

    setResumeStats(stats);
  };

  const handleDeleteResume = async (resumeId: string) => {
    try {
      const response = await UserService.deleteMyResume(resumeId);
      
      if (response.success) {
        const updatedResumes = resumes.filter(r => r.id !== resumeId);
        setResumes(updatedResumes);
        generateStats(updatedResumes);
        toast({
          title: "Resume deleted",
          description: "Your resume has been deleted successfully.",
        });
      } else {
        throw new Error(response.error || 'Failed to delete resume');
      }
    } catch (error) {
      console.error('Failed to delete resume:', error);
      toast({
        title: "Error deleting resume",
        description: error instanceof Error ? error.message : "Could not delete resume.",
        variant: "destructive",
      });
    }
  };

  const getStatusBadge = (status: Resume['processing_status']) => {
    switch (status) {
      case 'completed':
        return <Badge variant="default" className="gap-1"><CheckCircle className="h-3 w-3" />Completed</Badge>;
      case 'processing':
        return <Badge variant="secondary" className="gap-1"><Clock className="h-3 w-3" />Processing</Badge>;
      case 'pending':
        return <Badge variant="outline" className="gap-1"><Clock className="h-3 w-3" />Pending</Badge>;
      case 'failed':
        return <Badge variant="destructive" className="gap-1"><AlertCircle className="h-3 w-3" />Failed</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const getScoreBadge = (score?: number) => {
    if (!score) return null;
    
    let variant: "default" | "secondary" | "destructive" | "outline" = "outline";
    let icon = <BarChart3 className="h-3 w-3" />;
    
    if (score >= 80) {
      variant = "default";
      icon = <Award className="h-3 w-3" />;
    } else if (score >= 60) {
      variant = "secondary";
      icon = <TrendingUp className="h-3 w-3" />;
    } else {
      variant = "destructive";
      icon = <Target className="h-3 w-3" />;
    }
    
    return <Badge variant={variant} className="gap-1">{icon}{score}/100</Badge>;
  };

  const filteredResumes = resumes.filter(resume => {
    const matchesSearch = resume.filename.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || resume.processing_status === statusFilter;
    
    let matchesScore = true;
    if (scoreFilter !== "all" && resume.overall_score) {
      switch (scoreFilter) {
        case "high":
          matchesScore = resume.overall_score >= 80;
          break;
        case "medium":
          matchesScore = resume.overall_score >= 60 && resume.overall_score < 80;
          break;
        case "low":
          matchesScore = resume.overall_score < 60;
          break;
      }
    } else if (scoreFilter !== "all" && !resume.overall_score) {
      matchesScore = false;
    }
    
    return matchesSearch && matchesStatus && matchesScore;
  });

  useEffect(() => {
    loadResumes();
  }, []);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-8">
        <PageHeader
          title="My Resumes"
          description="View and manage your uploaded resumes and their AI analysis results."
        />
        
        {/* Stats Cards Loading */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-4 w-4" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16 mb-1" />
                <Skeleton className="h-3 w-24" />
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-64" />
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="My Resumes"
        description="View and manage your uploaded resumes with comprehensive AI analysis insights."
        actions={
          <div className="flex items-center gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2">
                  <Grid className="h-4 w-4" />
                  {viewMode === 'grid' ? 'Grid' : 'Table'}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>View Mode</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => setViewMode('table')}>
                  <List className="h-4 w-4 mr-2" />
                  Table View
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setViewMode('grid')}>
                  <Grid className="h-4 w-4 mr-2" />
                  Grid View
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            
            <Button
              variant="outline"
              onClick={loadResumes}
              className="gap-2"
              size="sm"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </div>
        }
      />

      {/* Stats Overview */}
      {resumeStats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Resumes</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{resumeStats.totalResumes}</div>
              <p className="text-xs text-muted-foreground">Uploaded documents</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Average Score</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{resumeStats.averageScore}/100</div>
              <p className="text-xs text-muted-foreground">AI analysis average</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Top Skills</CardTitle>
              <Award className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{resumeStats.topSkills.length}</div>
              <p className="text-xs text-muted-foreground">Unique skills identified</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {resumes.filter(r => r.processing_status === 'completed').length}
              </div>
              <p className="text-xs text-muted-foreground">Successfully analyzed</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Analytics Dashboard */}
      {resumeStats && resumeStats.totalResumes > 0 && (
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="skills">Skills Analysis</TabsTrigger>
            <TabsTrigger value="trends">Score Trends</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Score Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={resumeStats.scoreDistribution}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="range" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="count" fill="#8884d8" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Recent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {resumeStats.recentActivity.map((activity, index) => (
                      <div key={index} className="flex items-center gap-3 text-sm">
                        <div className="h-2 w-2 bg-blue-500 rounded-full" />
                        <div className="flex-1">
                          <span className="font-medium">{activity.action}</span>
                          <span className="text-muted-foreground"> {activity.resume}</span>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {new Date(activity.date).toLocaleDateString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="skills" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Top Skills Across Your Resumes</CardTitle>
                <CardDescription>Most frequently mentioned skills in your resume portfolio</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {resumeStats.topSkills.slice(0, 8).map((skill, index) => (
                    <div key={skill.skill} className="flex items-center gap-3">
                      <div className="w-8 text-xs text-muted-foreground">#{index + 1}</div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">{skill.skill}</span>
                          <span className="text-xs text-muted-foreground">{skill.count} resumes</span>
                        </div>
                        <Progress 
                          value={(skill.count / resumeStats.totalResumes) * 100} 
                          className="h-1 mt-1"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="trends" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Score Analysis</CardTitle>
                <CardDescription>Performance distribution across your resume portfolio</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={resumeStats.scoreDistribution}
                      dataKey="count"
                      nameKey="range"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      label={({ range, count }) => `${range}: ${count}`}
                    >
                      {resumeStats.scoreDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={['#ef4444', '#f97316', '#eab308', '#22c55e'][index]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {/* Resume Management */}
      <Card>
        <CardHeader>
          <CardTitle>Resume Collection</CardTitle>
          <CardDescription>
            Your uploaded resumes with comprehensive AI analysis and insights.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search resumes by filename..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8"
                />
              </div>
              
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-full sm:w-[180px]">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="processing">Processing</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={scoreFilter} onValueChange={setScoreFilter}>
                <SelectTrigger className="w-full sm:w-[180px]">
                  <SelectValue placeholder="Filter by score" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Scores</SelectItem>
                  <SelectItem value="high">High (80-100)</SelectItem>
                  <SelectItem value="medium">Medium (60-79)</SelectItem>
                  <SelectItem value="low">Low (0-59)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Results */}
            {filteredResumes.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-muted-foreground">
                  {searchQuery || statusFilter !== "all" || scoreFilter !== "all" 
                    ? 'No matching resumes found' 
                    : 'No resumes uploaded yet'
                  }
                </h3>
                <p className="text-sm text-muted-foreground mt-2">
                  {searchQuery || statusFilter !== "all" || scoreFilter !== "all"
                    ? 'Try adjusting your search terms or filters' 
                    : 'Upload your first resume to get started with AI analysis'
                  }
                </p>
                {(searchQuery || statusFilter !== "all" || scoreFilter !== "all") && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSearchQuery("");
                      setStatusFilter("all");
                      setScoreFilter("all");
                    }}
                    className="mt-4"
                  >
                    Clear Filters
                  </Button>
                )}
              </div>
            ) : viewMode === 'table' ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Resume</TableHead>
                    <TableHead>Upload Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>AI Score</TableHead>
                    <TableHead>Skills Found</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredResumes.map((resume) => (
                    <TableRow key={resume.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <div className="font-medium">{resume.filename}</div>
                            {resume.analysis_result?.experience_level && (
                              <div className="text-xs text-muted-foreground">
                                {resume.analysis_result.experience_level} Level
                              </div>
                            )}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Calendar className="h-3 w-3" />
                          {new Date(resume.upload_date).toLocaleDateString()}
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(resume.processing_status)}</TableCell>
                      <TableCell>
                        {resume.overall_score ? (
                          getScoreBadge(resume.overall_score)
                        ) : (
                          <span className="text-sm text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {resume.analysis_result?.skills_found ? (
                          <div className="flex items-center gap-1">
                            <BookOpen className="h-3 w-3 text-muted-foreground" />
                            <span className="text-sm">{resume.analysis_result.skills_found.length} skills</span>
                          </div>
                        ) : (
                          <span className="text-sm text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => window.open(resume.file_url, '_blank')}
                            title="Download"
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                          
                          {resume.processing_status === 'completed' && resume.analysis_result && (
                            <Sheet>
                              <SheetTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => setSelectedResume(resume)}
                                  title="View Analysis"
                                >
                                  <Eye className="h-4 w-4" />
                                </Button>
                              </SheetTrigger>
                              <SheetContent className="w-[700px] sm:w-[700px]">
                                <SheetHeader>
                                  <SheetTitle>Resume Analysis</SheetTitle>
                                  <SheetDescription>
                                    Comprehensive AI analysis for {selectedResume?.filename}
                                  </SheetDescription>
                                </SheetHeader>
                                
                                {selectedResume?.analysis_result && (
                                  <div className="mt-6 space-y-6 max-h-[calc(100vh-200px)] overflow-y-auto">
                                    {/* Score Overview */}
                                    <div className="grid grid-cols-2 gap-4">
                                      <div className="text-center p-4 bg-muted rounded-lg">
                                        <div className="text-3xl font-bold text-primary">
                                          {selectedResume.overall_score}/100
                                        </div>
                                        <p className="text-sm text-muted-foreground mt-1">
                                          Overall Score
                                        </p>
                                      </div>
                                      <div className="space-y-2">
                                        {selectedResume.analysis_result.ats_compatibility && (
                                          <div className="flex justify-between text-sm">
                                            <span>ATS Compatibility</span>
                                            <span className="font-medium">{selectedResume.analysis_result.ats_compatibility}/100</span>
                                          </div>
                                        )}
                                        {selectedResume.analysis_result.readability_score && (
                                          <div className="flex justify-between text-sm">
                                            <span>Readability</span>
                                            <span className="font-medium">{selectedResume.analysis_result.readability_score}/100</span>
                                          </div>
                                        )}
                                        {selectedResume.analysis_result.formatting_score && (
                                          <div className="flex justify-between text-sm">
                                            <span>Formatting</span>
                                            <span className="font-medium">{selectedResume.analysis_result.formatting_score}/100</span>
                                          </div>
                                        )}
                                      </div>
                                    </div>

                                    <Separator />

                                    {/* Assessment */}
                                    <div className="space-y-2">
                                      <h4 className="font-semibold flex items-center gap-2">
                                        <AlertCircle className="h-4 w-4" />
                                        Overall Assessment
                                      </h4>
                                      <p className="text-sm text-muted-foreground leading-relaxed">
                                        {selectedResume.analysis_result.overall_assessment}
                                      </p>
                                    </div>

                                    <Separator />

                                    {/* Strengths & Weaknesses */}
                                    <div className="grid md:grid-cols-2 gap-4">
                                      {selectedResume.analysis_result.strengths && selectedResume.analysis_result.strengths.length > 0 && (
                                        <div className="space-y-2">
                                          <h4 className="font-semibold text-green-600 flex items-center gap-2">
                                            <CheckCircle className="h-4 w-4" />
                                            Strengths
                                          </h4>
                                          <ul className="space-y-1">
                                            {selectedResume.analysis_result.strengths.map((strength, index) => (
                                              <li key={index} className="text-sm flex items-start gap-2">
                                                <div className="h-1.5 w-1.5 bg-green-500 rounded-full mt-2 shrink-0" />
                                                {strength}
                                              </li>
                                            ))}
                                          </ul>
                                        </div>
                                      )}

                                      {selectedResume.analysis_result.weaknesses && selectedResume.analysis_result.weaknesses.length > 0 && (
                                        <div className="space-y-2">
                                          <h4 className="font-semibold text-red-600 flex items-center gap-2">
                                            <AlertCircle className="h-4 w-4" />
                                            Areas for Improvement
                                          </h4>
                                          <ul className="space-y-1">
                                            {selectedResume.analysis_result.weaknesses.map((weakness, index) => (
                                              <li key={index} className="text-sm flex items-start gap-2">
                                                <div className="h-1.5 w-1.5 bg-red-500 rounded-full mt-2 shrink-0" />
                                                {weakness}
                                              </li>
                                            ))}
                                          </ul>
                                        </div>
                                      )}
                                    </div>

                                    <Separator />

                                    {/* Skills & Experience */}
                                    <div className="grid md:grid-cols-2 gap-4">
                                      {selectedResume.analysis_result.skills_found && selectedResume.analysis_result.skills_found.length > 0 && (
                                        <div className="space-y-2">
                                          <h4 className="font-semibold flex items-center gap-2">
                                            <BookOpen className="h-4 w-4" />
                                            Skills Identified ({selectedResume.analysis_result.skills_found.length})
                                          </h4>
                                          <div className="flex flex-wrap gap-1">
                                            {selectedResume.analysis_result.skills_found.map((skill, index) => (
                                              <Badge key={index} variant="outline" className="text-xs">
                                                {skill}
                                              </Badge>
                                            ))}
                                          </div>
                                        </div>
                                      )}

                                      {selectedResume.analysis_result.experience_level && (
                                        <div className="space-y-2">
                                          <h4 className="font-semibold flex items-center gap-2">
                                            <Users className="h-4 w-4" />
                                            Experience Level
                                          </h4>
                                          <Badge variant="secondary" className="text-sm">
                                            {selectedResume.analysis_result.experience_level}
                                          </Badge>
                                        </div>
                                      )}
                                    </div>

                                    <Separator />

                                    {/* Recommendations */}
                                    {selectedResume.analysis_result.recommendations && selectedResume.analysis_result.recommendations.length > 0 && (
                                      <div className="space-y-2">
                                        <h4 className="font-semibold flex items-center gap-2">
                                          <Target className="h-4 w-4" />
                                          AI Recommendations
                                        </h4>
                                        <ul className="space-y-2">
                                          {selectedResume.analysis_result.recommendations.map((rec, index) => (
                                            <li key={index} className="flex items-start gap-3 text-sm bg-blue-50 p-3 rounded-md">
                                              <div className="h-5 w-5 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-medium shrink-0 mt-0.5">
                                                {index + 1}
                                              </div>
                                              <span className="leading-relaxed">{rec}</span>
                                            </li>
                                          ))}
                                        </ul>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </SheetContent>
                            </Sheet>
                          )}

                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                title="Delete"
                                className="text-destructive hover:text-destructive"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Delete Resume</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Are you sure you want to delete "{resume.filename}"? 
                                  This action cannot be undone and will permanently remove 
                                  the resume and its analysis results.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => handleDeleteResume(resume.id)}
                                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                >
                                  Delete
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {filteredResumes.map((resume) => (
                  <Card key={resume.id} className="hover:shadow-md transition-shadow">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                          <CardTitle className="text-sm truncate">{resume.filename}</CardTitle>
                        </div>
                        {resume.overall_score && getScoreBadge(resume.overall_score)}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Calendar className="h-3 w-3" />
                        {new Date(resume.upload_date).toLocaleDateString()}
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Status</span>
                          {getStatusBadge(resume.processing_status)}
                        </div>
                        
                        {resume.analysis_result?.skills_found && (
                          <div>
                            <span className="text-sm font-medium">Skills Found</span>
                            <div className="text-xs text-muted-foreground mt-1">
                              {resume.analysis_result.skills_found.length} skills identified
                            </div>
                          </div>
                        )}
                        
                        {resume.analysis_result?.experience_level && (
                          <div>
                            <span className="text-sm font-medium">Experience</span>
                            <div className="text-xs text-muted-foreground mt-1">
                              {resume.analysis_result.experience_level} Level
                            </div>
                          </div>
                        )}

                        <div className="flex items-center gap-1 pt-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => window.open(resume.file_url, '_blank')}
                            className="flex-1"
                          >
                            <Download className="h-3 w-3 mr-1" />
                            Download
                          </Button>
                          
                          {resume.processing_status === 'completed' && resume.analysis_result && (
                            <Sheet>
                              <SheetTrigger asChild>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => setSelectedResume(resume)}
                                  className="flex-1"
                                >
                                  <Eye className="h-3 w-3 mr-1" />
                                  Analyze
                                </Button>
                              </SheetTrigger>
                              <SheetContent className="w-[700px] sm:w-[700px]">
                                {/* Same analysis content as table view */}
                              </SheetContent>
                            </Sheet>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
