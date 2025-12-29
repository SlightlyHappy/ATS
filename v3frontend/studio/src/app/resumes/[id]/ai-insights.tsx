"use client";

import { useState } from "react";
import { summarizeResume } from "@/ai/flows/summarize-resume";
import { generateCandidateQuestions } from "@/ai/flows/generate-candidate-questions";
import type { Resume } from "@/types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Wand2, BrainCircuit, Loader2 } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

export default function AiInsights({ resume }: { resume: Resume }) {
  const [summary, setSummary] = useState<string | undefined>(resume.summary);
  const [questions, setQuestions] = useState<string[] | undefined>(resume.questions);
  const [isSummaryLoading, setIsSummaryLoading] = useState(false);
  const [isQuestionsLoading, setIsQuestionsLoading] = useState(false);
  const { toast } = useToast();

  const handleSummarize = async () => {
    setIsSummaryLoading(true);
    try {
      const result = await summarizeResume({
        resumeText: resume.resumeText,
        jobDescription: resume.jobDescription,
      });
      setSummary(result.summary);
    } catch (error) {
      console.error(error);
      toast({
        title: "Error",
        description: "Failed to generate summary.",
        variant: "destructive",
      });
    } finally {
      setIsSummaryLoading(false);
    }
  };

  const handleGenerateQuestions = async () => {
    setIsQuestionsLoading(true);
    try {
      const result = await generateCandidateQuestions({
        resumeText: resume.resumeText,
        jobDescription: resume.jobDescription,
        numQuestions: 5,
      });
      setQuestions(result.questions);
    } catch (error) {
      console.error(error);
      toast({
        title: "Error",
        description: "Failed to generate questions.",
        variant: "destructive",
      });
    } finally {
      setIsQuestionsLoading(false);
    }
  };

  return (
    <Card className="sticky top-20">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BrainCircuit className="text-primary" />
          AI Insights
        </CardTitle>
        <CardDescription>
          Generate a summary and interview questions based on the resume.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <Accordion type="single" collapsible defaultValue="item-1" className="w-full">
            <AccordionItem value="item-1">
                <AccordionTrigger className="text-base font-semibold">Summary</AccordionTrigger>
                <AccordionContent>
                    {isSummaryLoading ? (
                        <div className="space-y-2 pt-2">
                            <Skeleton className="h-4 w-full" />
                            <Skeleton className="h-4 w-full" />
                            <Skeleton className="h-4 w-4/5" />
                        </div>
                    ) : summary ? (
                        <p className="text-sm text-muted-foreground pt-2">{summary}</p>
                    ) : (
                        <div className="text-sm text-muted-foreground pt-2 text-center py-4">
                            Click the button to generate an AI summary.
                        </div>
                    )}
                     <Button onClick={handleSummarize} disabled={isSummaryLoading} className="w-full mt-4">
                        {isSummaryLoading ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                            <Wand2 className="mr-2 h-4 w-4" />
                        )}
                        {summary ? "Regenerate Summary" : "Generate Summary"}
                    </Button>
                </AccordionContent>
            </AccordionItem>
            <AccordionItem value="item-2">
                <AccordionTrigger className="text-base font-semibold">Interview Questions</AccordionTrigger>
                <AccordionContent>
                {isQuestionsLoading ? (
                     <div className="space-y-3 pt-2">
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-full" />
                    </div>
                ) : questions && questions.length > 0 ? (
                    <ul className="space-y-2 text-sm text-muted-foreground list-decimal list-inside pt-2">
                        {questions.map((q, i) => (
                            <li key={i}>{q}</li>
                        ))}
                    </ul>
                ) : (
                    <div className="text-sm text-muted-foreground pt-2 text-center py-4">
                        Click the button to generate interview questions.
                    </div>
                )}
                 <Button onClick={handleGenerateQuestions} disabled={isQuestionsLoading} className="w-full mt-4">
                        {isQuestionsLoading ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                            <Wand2 className="mr-2 h-4 w-4" />
                        )}
                        {questions ? "Regenerate Questions" : "Generate Questions"}
                    </Button>
                </AccordionContent>
            </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  );
}
