'use client';
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { UploadCloud, File, BrainCircuit, Bot, CheckCircle, Clock, Trophy, Wand2, Sparkles, ThumbsUp, ThumbsDown } from 'lucide-react';
import { Progress } from "@/components/ui/progress";
import { Separator } from '@/components/ui/separator';
import { analyzeResume, type AnalyzeResumeOutput } from '@/ai/flows/analyze-resume-flow';
import { summarizeResumeInsights, type SummarizeResumeInsightsOutput } from '@/ai/flows/summarize-resume-insights';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

const AgentAnalysis = ({ agentName, status, score }: { agentName: string, status: 'pending' | 'analyzing' | 'complete', score?: number }) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'pending':
        return <Clock className="h-5 w-5 text-muted-foreground" />;
      case 'analyzing':
        return <Bot className="h-5 w-5 text-secondary animate-pulse" />;
      case 'complete':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
    }
  };

  return (
    <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
      <div className="flex items-center gap-3">
        {getStatusIcon()}
        <span className="font-medium">{agentName}</span>
      </div>
      {status === 'complete' && score !== undefined && (
        <div className="font-bold text-lg text-primary">{score}/100</div>
      )}
    </div>
  );
};

export default function ResumeAnalysisPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalyzeResumeOutput | null>(null);
  const [insightsResult, setInsightsResult] = useState<SummarizeResumeInsightsOutput | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
      setAnalysisResult(null);
      setInsightsResult(null);
      setError(null);
    }
  };
  
  const fileToDataUri = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const handleAnalysis = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setAnalysisResult(null);
    setInsightsResult(null);
    setError(null);
    
    try {
      const resumeDataUri = await fileToDataUri(selectedFile);
      const result = await analyzeResume({ resumeDataUri });
      setAnalysisResult(result);
    } catch (err) {
        console.error(err);
        setError("An error occurred during analysis. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGetInsights = async () => {
      if (!analysisResult) return;
      
      setIsSummarizing(true);
      setError(null);
      try {
          // This is a conceptual mapping. In a real scenario, you'd have more structured data.
          // For now, we simulate extracting strengths and weaknesses from the summary.
          const strengths = analysisResult.summary.split('.').filter(s => s.toLowerCase().includes('strength') || s.toLowerCase().includes('strong'));
          const weaknesses = analysisResult.summary.split('.').filter(s => s.toLowerCase().includes('weakness') || s.toLowerCase().includes('limited'));

          const result = await summarizeResumeInsights({
              strengths: strengths.length ? strengths : ["No specific strengths listed in summary."],
              weaknesses: weaknesses.length ? weaknesses : ["No specific weaknesses listed in summary."]
          });
          setInsightsResult(result);

      } catch (err) {
          console.error(err);
          setError("An error occurred while generating insights.");
      } finally {
          setIsSummarizing(false);
      }
  }

  const getAgentStatus = (agentScore?: number) => {
    if (isAnalyzing || !analysisResult) {
      return 'pending';
    }
    return agentScore !== undefined ? 'complete' : 'pending';
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle>Upload Resume</CardTitle>
          <CardDescription>Upload a PDF or DOCX file to begin analysis.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-center w-full">
            <label htmlFor="dropzone-file" className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-lg cursor-pointer bg-muted/50 hover:bg-muted">
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <UploadCloud className="w-10 h-10 mb-4 text-muted-foreground" />
                <p className="mb-2 text-sm text-muted-foreground">
                  <span className="font-semibold">Click to upload</span> or drag and drop
                </p>
                <p className="text-xs text-muted-foreground">PDF or DOCX (MAX. 5MB)</p>
              </div>
              <Input id="dropzone-file" type="file" className="hidden" onChange={handleFileChange} accept=".pdf,.docx" />
            </label>
          </div>
          {selectedFile && (
            <div className="flex items-center p-3 text-sm border rounded-md bg-background">
              <File className="w-5 h-5 mr-3 shrink-0" />
              <span className="font-medium truncate">{selectedFile.name}</span>
            </div>
          )}
          <Button onClick={handleAnalysis} disabled={!selectedFile || isAnalyzing} className="w-full">
            {isAnalyzing ? 'Analyzing...' : <><BrainCircuit className="mr-2 h-4 w-4" /> Start Analysis</>}
          </Button>
        </CardContent>
      </Card>

      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle>Real-time Analysis</CardTitle>
          <CardDescription>Tracking progress from our 4-Agent AI system.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertTitle>Analysis Failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {isAnalyzing && (
            <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
              <BrainCircuit className="h-12 w-12 mb-4 animate-pulse text-primary" />
              <p className="font-semibold">AI agents are analyzing the resume...</p>
              <Progress value={undefined} className="w-full mt-4" />
            </div>
          )}

          {!isAnalyzing && analysisResult && (
            <>
              <Card className="bg-primary/10 border-primary/50">
                <CardHeader className="p-4">
                  <CardTitle className="flex items-center gap-2 text-primary"><Trophy /> Overall Score</CardTitle>
                </CardHeader>
                <CardContent className="p-4 pt-0 text-center">
                  <p className="text-6xl font-extrabold text-primary">{analysisResult.overallScore}</p>
                  <p className="text-sm text-primary/80">Consensus Score</p>
                </CardContent>
              </Card>
              <Separator />
              <div className="space-y-3">
                <AgentAnalysis agentName="Technical Skills" status={getAgentStatus(analysisResult.technicalScore)} score={analysisResult.technicalScore} />
                <AgentAnalysis agentName="Experience" status={getAgentStatus(analysisResult.experienceScore)} score={analysisResult.experienceScore} />
                <AgentAnalysis agentName="Cultural Fit" status={getAgentStatus(analysisResult.culturalFitScore)} score={analysisResult.culturalFitScore} />
                <AgentAnalysis agentName="Legal Compliance" status={getAgentStatus(analysisResult.legalComplianceScore)} score={analysisResult.legalComplianceScore} />
              </div>
               <Separator />
               <div>
                    <h3 className="font-semibold text-md">Analysis Summary</h3>
                    <p className="text-sm text-muted-foreground mt-1">{analysisResult.summary}</p>
                </div>
                 <Button onClick={handleGetInsights} disabled={isSummarizing || !analysisResult} className="w-full">
                    {isSummarizing ? 'Generating...' : <><Wand2 className="mr-2 h-4 w-4" /> Get Actionable Insights</>}
                </Button>
            </>
          )}

          {insightsResult && (
              <Card className="bg-secondary/10 border-secondary/50">
                <CardHeader className="p-4">
                  <CardTitle className="flex items-center gap-2 text-secondary"><Sparkles /> Actionable Insights</CardTitle>
                </CardHeader>
                <CardContent className="p-4 pt-0 text-sm space-y-3">
                   <div>
                        <h4 className="font-semibold flex items-center gap-1.5"><ThumbsUp className="h-4 w-4 text-green-500" /> Key Strengths</h4>
                        <p className="text-muted-foreground">{insightsResult.summary}</p>
                   </div>
                   <div>
                        <h4 className="font-semibold flex items-center gap-1.5"><ThumbsDown className="h-4 w-4 text-red-500" /> Areas for Discussion</h4>
                         <ul className="list-disc list-inside text-muted-foreground space-y-1 mt-1">
                            {insightsResult.recommendations.map((rec, i) => (
                                <li key={i}>{rec}</li>
                            ))}
                        </ul>
                   </div>
                </CardContent>
              </Card>
            )}

          {!isAnalyzing && !analysisResult && !error && (
            <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground pt-10">
              <BrainCircuit className="h-12 w-12 mb-4" />
              <p>Upload a resume to see the AI analysis results.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
