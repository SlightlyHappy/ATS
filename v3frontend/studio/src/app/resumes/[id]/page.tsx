
"use client";

import { useEffect, useState } from "react";
import { fetchResumeById } from "@/services/api";
import { notFound } from "next/navigation";
import PageHeader from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import AiInsights from "./ai-insights";
import { Resume } from "@/types";
import { Skeleton } from "@/components/ui/skeleton";
import { format } from "date-fns";

export default function ResumeDetailPage({ params }: { params: { id: string } }) {
  const [resume, setResume] = useState<Resume | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadResume() {
      setIsLoading(true);
      try {
        const data = await fetchResumeById(params.id);
        if (data) {
          setResume(data);
        } else {
          notFound();
        }
      } catch (error) {
        console.error("Failed to fetch resume", error);
        // Handle error, maybe show a toast
      } finally {
        setIsLoading(false);
      }
    }
    loadResume();
  }, [params.id]);
  
  if (isLoading || !resume) {
    return (
       <div className="flex flex-col gap-8">
            <PageHeader
                title={<Skeleton className="h-8 w-48" />}
                description={<Skeleton className="h-4 w-32" />}
                actions={<Skeleton className="h-8 w-20" />}
            />
            <div className="grid gap-8 lg:grid-cols-3">
                <div className="lg:col-span-2 flex flex-col gap-8">
                    <Card>
                        <CardHeader>
                            <CardTitle>Resume</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <Skeleton className="h-4 w-full" />
                            <Skeleton className="h-4 w-full" />
                            <Skeleton className="h-4 w-3/4" />
                        </CardContent>
                    </Card>
                </div>
                <div className="lg:col-span-1">
                    <Skeleton className="h-96 w-full" />
                </div>
            </div>
       </div>
    )
  }

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title={resume.name}
        description={`Submitted on ${format(new Date(resume.date), "MM/dd/yyyy")}`}
        actions={<Badge className="text-base">{resume.status}</Badge>}
      />

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2 flex flex-col gap-8">
            <Card>
                <CardHeader>
                    <CardTitle>Resume</CardTitle>
                    <CardDescription>The full text of the candidate's resume.</CardDescription>
                </CardHeader>
                <CardContent>
                    <pre className="whitespace-pre-wrap font-sans text-sm">{resume.resumeText}</pre>
                </CardContent>
            </Card>
            <Card>
                <CardHeader>
                    <CardTitle>Job Description</CardTitle>
                     <CardDescription>The job description associated with this submission.</CardDescription>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground">{resume.jobDescription}</p>
                </CardContent>
            </Card>
        </div>
        <div className="lg:col-span-1">
            <AiInsights resume={resume} />
        </div>
      </div>
    </div>
  );
}
