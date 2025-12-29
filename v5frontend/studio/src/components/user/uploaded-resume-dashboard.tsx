'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { 
  FileText, 
  TrendingUp, 
  Award, 
  Target,
  BarChart3,
  Download,
  Eye,
  Star,
  Users,
  Calendar,
  MapPin,
  Mail,
  Phone,
  ExternalLink,
  AlertCircle,
  CheckCircle,
  Clock,
  RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';
import { userApi } from '@/lib/user-api';

interface EnterpriseAnalytics {
  candidate_analytics: {
    metrics: {
      technical_depth_score: number;
      leadership_potential_score: number;
      innovation_indicator: number;
      communication_excellence: number;
      market_readiness_index: number;
      role_category: string;
      experience_band: string;
    };
    skill_proficiency_map: {
      [skill: string]: {
        proficiency_level: number;
        market_demand_score: number;
        years_experience: number;
      };
    };
  };
  peer_group_analytics: {
    role_category: string;
    experience_band: string;
    overall_percentile: number;
    technical_percentile: number;
  };
  generated_at: string;
}

interface UploadedResume {
  id: number;
  filename: string;
  upload_date: string;
  file_size: number;
  analysis_status: 'pending' | 'processing' | 'completed' | 'failed';
  candidate_data?: CandidateData;
  analysis_results?: AnalysisResults;
  enterprise_analytics?: EnterpriseAnalytics; // NEW for v1.76
}

interface CandidateData {
  name: string;
  email?: string;
  phone?: string;
  location?: string;
  summary?: string;
  experience_years: number;
  skills: string[];
  education: EducationItem[];
  experience: ExperienceItem[];
  certifications: string[];
}

interface EducationItem {
  degree: string;
  institution: string;
  year?: string;
  gpa?: string;
}

interface ExperienceItem {
  title: string;
  company: string;
  duration: string;
  description: string;
  technologies?: string[];
}

interface AnalysisResults {
  overall_score: number;
  category_scores: {
    technical_skills: number;
    experience_relevance: number;
    education_quality: number;
    presentation_quality: number;
    keyword_matching: number;
  };
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  fit_assessment: {
    roles: { role: string; match_percentage: number }[];
    salary_estimate: { min: number; max: number; currency: string };
    market_competitiveness: number;
  };
  comparison_metrics: {
    percentile_rank: number;
    peer_comparison: string;
    industry_standing: string;
  };
}

export default function UploadedResumeDashboard() {
  const [resumes, setResumes] = useState<UploadedResume[]>([]);
  const [selectedResume, setSelectedResume] = useState<UploadedResume | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  useEffect(() => {
    loadUploadedResumes();
  }, []);

  const loadUploadedResumes = async () => {
    try {
      const uploadedResumes = await userApi.getUploadedResumes() as UploadedResume[];
      setResumes(uploadedResumes);
      if (uploadedResumes.length > 0) {
        setSelectedResume(uploadedResumes[0]);
      }
    } catch (error) {
      console.error('Failed to load resumes:', error);
      toast.error('Failed to load uploaded resumes');
    } finally {
      setIsLoading(false);
    }
  };

  const loadEnterpriseAnalytics = async (resumeId: number) => {
    try {
      const analytics = await userApi.getEnterpriseAnalytics(resumeId) as EnterpriseAnalytics;
      
      // Update the selected resume with enterprise analytics
      setResumes(prev => prev.map(resume => 
        resume.id === resumeId 
          ? { ...resume, enterprise_analytics: analytics }
          : resume
      ));
      
      if (selectedResume?.id === resumeId) {
        setSelectedResume(prev => prev ? { ...prev, enterprise_analytics: analytics } : null);
      }
      
    } catch (error) {
      console.error('Failed to load enterprise analytics:', error);
      toast.error('Failed to load enterprise analytics');
    }
  };

  const triggerAnalysis = async (resumeId: number) => {
    setIsAnalyzing(true);
    try {
      await userApi.triggerResumeAnalysis(resumeId);
      toast.success('Analysis started. Results will appear shortly.');
      // Refresh the data after a short delay
      setTimeout(loadUploadedResumes, 2000);
    } catch (error) {
      console.error('Failed to trigger analysis:', error);
      toast.error('Failed to start analysis');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const downloadResume = async (resumeId: number, filename: string) => {
    try {
      const blob = await userApi.downloadResume(resumeId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Resume downloaded successfully');
    } catch (error) {
      console.error('Download failed:', error);
      toast.error('Failed to download resume');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'processing':
        return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'processing':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'failed':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading resumes...</span>
      </div>
    );
  }

  if (resumes.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-medium mb-2">No Resumes Uploaded</h3>
        <p className="text-muted-foreground mb-4">
          Upload your first resume using the Resume Upload tab to see detailed analysis and insights.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
      {/* Resume List - Left Sidebar */}
      <div className="lg:col-span-1">
        <Card className="h-fit">
          <CardHeader>
            <CardTitle className="text-base">Uploaded Resumes</CardTitle>
            <CardDescription>
              {resumes.length} resume{resumes.length !== 1 ? 's' : ''} uploaded
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-96">
              <div className="space-y-3">
                {resumes.map((resume) => (
                  <div
                    key={resume.id}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedResume?.id === resume.id ? 'bg-accent border-primary' : 'hover:bg-accent'
                    }`}
                    onClick={() => setSelectedResume(resume)}
                  >
                    <div className="space-y-2">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-sm truncate">{resume.filename}</h4>
                          {resume.candidate_data?.name && (
                            <p className="text-xs text-muted-foreground truncate">
                              {resume.candidate_data.name}
                            </p>
                          )}
                        </div>
                        {getStatusIcon(resume.analysis_status)}
                      </div>
                      
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{formatFileSize(resume.file_size)}</span>
                        <span>{new Date(resume.upload_date).toLocaleDateString()}</span>
                      </div>
                      
                      <Badge className={getStatusColor(resume.analysis_status)} variant="outline">
                        {resume.analysis_status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Resume Details - Main Content */}
      <div className="lg:col-span-3">
        {selectedResume ? (
          <Tabs defaultValue="overview" className="space-y-4">
            <div className="flex items-center justify-between">
              <TabsList>
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="analysis">Analysis</TabsTrigger>
                <TabsTrigger value="enterprise">Enterprise Analytics</TabsTrigger>
                <TabsTrigger value="candidate">Candidate Profile</TabsTrigger>
                <TabsTrigger value="comparison">Market Comparison</TabsTrigger>
              </TabsList>
              
              <div className="flex space-x-2">
                {selectedResume.analysis_status !== 'completed' && (
                  <Button
                    onClick={() => triggerAnalysis(selectedResume.id)}
                    disabled={isAnalyzing}
                    size="sm"
                    variant="outline"
                  >
                    {isAnalyzing ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <BarChart3 className="h-4 w-4 mr-2" />
                        Analyze Resume
                      </>
                    )}
                  </Button>
                )}
                {selectedResume.analysis_status === 'completed' && !selectedResume.enterprise_analytics && (
                  <Button
                    onClick={() => loadEnterpriseAnalytics(selectedResume.id)}
                    size="sm"
                    variant="outline"
                  >
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Load Enterprise Analytics
                  </Button>
                )}
                <Button
                  onClick={() => downloadResume(selectedResume.id, selectedResume.filename)}
                  size="sm"
                  variant="outline"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </Button>
              </div>
            </div>

            <TabsContent value="overview" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>{selectedResume.filename}</CardTitle>
                  <CardDescription>
                    Uploaded on {new Date(selectedResume.upload_date).toLocaleDateString()} • {formatFileSize(selectedResume.file_size)}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {selectedResume.analysis_results ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="text-center">
                        <div className={`text-3xl font-bold ${getScoreColor(selectedResume.analysis_results.overall_score)}`}>
                          {selectedResume.analysis_results.overall_score.toFixed(1)}
                        </div>
                        <div className="text-sm text-muted-foreground">Overall Score</div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-3xl font-bold text-blue-600">
                          {selectedResume.analysis_results.comparison_metrics.percentile_rank}th
                        </div>
                        <div className="text-sm text-muted-foreground">Percentile Rank</div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-3xl font-bold text-green-600">
                          {selectedResume.analysis_results.fit_assessment.market_competitiveness}%
                        </div>
                        <div className="text-sm text-muted-foreground">Market Competitive</div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                      <h3 className="text-lg font-medium mb-2">Analysis {selectedResume.analysis_status}</h3>
                      <p className="text-muted-foreground">
                        {selectedResume.analysis_status === 'pending' && 'Resume analysis is queued for processing.'}
                        {selectedResume.analysis_status === 'processing' && 'Resume is currently being analyzed.'}
                        {selectedResume.analysis_status === 'failed' && 'Analysis failed. Please try again.'}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="analysis" className="space-y-4">
              {selectedResume.analysis_results ? (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle>Score Breakdown</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {Object.entries(selectedResume.analysis_results.category_scores).map(([category, score]) => (
                          <div key={category}>
                            <div className="flex justify-between mb-2">
                              <span className="text-sm font-medium capitalize">
                                {category.replace('_', ' ')}
                              </span>
                              <span className="text-sm">{score.toFixed(1)}</span>
                            </div>
                            <Progress value={score} className="h-2" />
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base text-green-600">Strengths</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-2">
                          {selectedResume.analysis_results.strengths.map((strength, idx) => (
                            <li key={idx} className="flex items-start space-x-2 text-sm">
                              <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                              <span>{strength}</span>
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base text-yellow-600">Areas for Improvement</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-2">
                          {selectedResume.analysis_results.weaknesses.map((weakness, idx) => (
                            <li key={idx} className="flex items-start space-x-2 text-sm">
                              <AlertCircle className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                              <span>{weakness}</span>
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Recommendations</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {selectedResume.analysis_results.recommendations.map((rec, idx) => (
                          <li key={idx} className="flex items-start space-x-2 text-sm">
                            <Star className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <Card>
                  <CardContent className="text-center py-8">
                    <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium mb-2">No Analysis Available</h3>
                    <p className="text-muted-foreground">
                      Analysis is required to view detailed breakdown and recommendations.
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="enterprise" className="space-y-4">
              {selectedResume.enterprise_analytics ? (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">AI-Enhanced Enterprise Metrics</CardTitle>
                      <CardDescription>CHRO-level comprehensive candidate assessment</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-6 text-center">
                        <div>
                          <div className="text-2xl font-bold text-blue-600">
                            {selectedResume.enterprise_analytics.candidate_analytics.metrics.technical_depth_score.toFixed(1)}
                          </div>
                          <div className="text-sm text-muted-foreground">Technical Depth</div>
                        </div>
                        
                        <div>
                          <div className="text-2xl font-bold text-green-600">
                            {selectedResume.enterprise_analytics.candidate_analytics.metrics.leadership_potential_score.toFixed(1)}
                          </div>
                          <div className="text-sm text-muted-foreground">Leadership Potential</div>
                        </div>
                        
                        <div>
                          <div className="text-2xl font-bold text-purple-600">
                            {selectedResume.enterprise_analytics.candidate_analytics.metrics.innovation_indicator.toFixed(1)}
                          </div>
                          <div className="text-sm text-muted-foreground">Innovation Indicator</div>
                        </div>
                        
                        <div>
                          <div className="text-2xl font-bold text-orange-600">
                            {selectedResume.enterprise_analytics.candidate_analytics.metrics.communication_excellence.toFixed(1)}
                          </div>
                          <div className="text-sm text-muted-foreground">Communication</div>
                        </div>
                        
                        <div>
                          <div className="text-2xl font-bold text-red-600">
                            {selectedResume.enterprise_analytics.candidate_analytics.metrics.market_readiness_index.toFixed(1)}
                          </div>
                          <div className="text-sm text-muted-foreground">Market Readiness</div>
                        </div>
                        
                        <div>
                          <div className="text-xl font-bold text-gray-600">
                            {selectedResume.enterprise_analytics.candidate_analytics.metrics.experience_band}
                          </div>
                          <div className="text-sm text-muted-foreground">Experience Band</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Skill Proficiency Map</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {Object.entries(selectedResume.enterprise_analytics.candidate_analytics.skill_proficiency_map)
                            .slice(0, 5).map(([skill, data]) => (
                            <div key={skill} className="space-y-2">
                              <div className="flex justify-between text-sm">
                                <span className="capitalize">{skill}</span>
                                <span className="text-muted-foreground">Level {data.proficiency_level}/5</span>
                              </div>
                              <div className="flex justify-between text-xs text-muted-foreground">
                                <span>Market Demand: {data.market_demand_score}%</span>
                                <span>Experience: {data.years_experience} years</span>
                              </div>
                              <Progress value={data.proficiency_level * 20} className="h-2" />
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Peer Group Analytics</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div className="text-center p-4 bg-muted rounded-lg">
                            <div className="text-3xl font-bold text-blue-600">
                              {selectedResume.enterprise_analytics.peer_group_analytics.overall_percentile}th
                            </div>
                            <div className="text-sm text-muted-foreground">Overall Percentile</div>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 text-center">
                            <div>
                              <div className="text-xl font-bold">
                                {selectedResume.enterprise_analytics.peer_group_analytics.technical_percentile}th
                              </div>
                              <div className="text-xs text-muted-foreground">Technical Rank</div>
                            </div>
                            <div>
                              <div className="text-sm font-medium">
                                {selectedResume.enterprise_analytics.peer_group_analytics.role_category.replace('_', ' ')}
                              </div>
                              <div className="text-xs text-muted-foreground">Role Category</div>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </>
              ) : (
                <Card>
                  <CardContent className="text-center py-8">
                    <TrendingUp className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium mb-2">Enterprise Analytics Unavailable</h3>
                    <p className="text-muted-foreground">
                      Advanced enterprise analytics are not available for this resume. Try triggering a new analysis.
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="candidate" className="space-y-4">
              {selectedResume.candidate_data ? (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle>{selectedResume.candidate_data.name}</CardTitle>
                      <CardDescription>
                        {selectedResume.candidate_data.experience_years} years of experience
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-4">
                          {selectedResume.candidate_data.email && (
                            <div className="flex items-center space-x-2">
                              <Mail className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm">{selectedResume.candidate_data.email}</span>
                            </div>
                          )}
                          {selectedResume.candidate_data.phone && (
                            <div className="flex items-center space-x-2">
                              <Phone className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm">{selectedResume.candidate_data.phone}</span>
                            </div>
                          )}
                          {selectedResume.candidate_data.location && (
                            <div className="flex items-center space-x-2">
                              <MapPin className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm">{selectedResume.candidate_data.location}</span>
                            </div>
                          )}
                        </div>

                        <div>
                          <h4 className="font-medium mb-2">Skills</h4>
                          <div className="flex flex-wrap gap-1">
                            {selectedResume.candidate_data.skills.map((skill, idx) => (
                              <Badge key={idx} variant="secondary" className="text-xs">
                                {skill}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>

                      {selectedResume.candidate_data.summary && (
                        <div className="mt-6">
                          <h4 className="font-medium mb-2">Professional Summary</h4>
                          <p className="text-sm text-muted-foreground">
                            {selectedResume.candidate_data.summary}
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {selectedResume.candidate_data.experience.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Work Experience</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {selectedResume.candidate_data.experience.map((exp, idx) => (
                            <div key={idx} className="border-l-2 border-muted pl-4">
                              <div className="flex items-start justify-between">
                                <div>
                                  <h5 className="font-medium">{exp.title}</h5>
                                  <p className="text-sm text-muted-foreground">{exp.company}</p>
                                </div>
                                <Badge variant="outline">{exp.duration}</Badge>
                              </div>
                              <p className="text-sm mt-2">{exp.description}</p>
                              {exp.technologies && (
                                <div className="flex flex-wrap gap-1 mt-2">
                                  {exp.technologies.map((tech, techIdx) => (
                                    <Badge key={techIdx} variant="secondary" className="text-xs">
                                      {tech}
                                    </Badge>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </>
              ) : (
                <Card>
                  <CardContent className="text-center py-8">
                    <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium mb-2">No Candidate Data</h3>
                    <p className="text-muted-foreground">
                      Resume parsing is required to extract candidate information.
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="comparison" className="space-y-4">
              {selectedResume.analysis_results ? (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Market Position</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
                        <div>
                          <div className="text-2xl font-bold text-blue-600">
                            {selectedResume.analysis_results.comparison_metrics.percentile_rank}th
                          </div>
                          <div className="text-sm text-muted-foreground">Percentile</div>
                          <p className="text-xs mt-1">
                            {selectedResume.analysis_results.comparison_metrics.peer_comparison}
                          </p>
                        </div>
                        
                        <div>
                          <div className="text-2xl font-bold text-green-600">
                            {selectedResume.analysis_results.fit_assessment.market_competitiveness}%
                          </div>
                          <div className="text-sm text-muted-foreground">Competitive</div>
                          <p className="text-xs mt-1">Market readiness score</p>
                        </div>
                        
                        <div>
                          <div className="text-2xl font-bold text-purple-600">
                            ${selectedResume.analysis_results.fit_assessment.salary_estimate.min}k-${selectedResume.analysis_results.fit_assessment.salary_estimate.max}k
                          </div>
                          <div className="text-sm text-muted-foreground">Salary Range</div>
                          <p className="text-xs mt-1">Market estimate</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Role Fit Assessment</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {selectedResume.analysis_results.fit_assessment.roles.map((role, idx) => (
                          <div key={idx} className="flex items-center justify-between">
                            <div>
                              <h5 className="font-medium">{role.role}</h5>
                              <div className="text-sm text-muted-foreground">
                                {role.match_percentage}% match
                              </div>
                            </div>
                            <Progress value={role.match_percentage} className="w-32" />
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Industry Standing</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm">
                        {selectedResume.analysis_results.comparison_metrics.industry_standing}
                      </p>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <Card>
                  <CardContent className="text-center py-8">
                    <TrendingUp className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium mb-2">No Comparison Data</h3>
                    <p className="text-muted-foreground">
                      Analysis is required to compare with market standards.
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        ) : (
          <Card>
            <CardContent className="text-center py-12">
              <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">Select a Resume</h3>
              <p className="text-muted-foreground">
                Choose a resume from the list to view detailed analysis and insights.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
