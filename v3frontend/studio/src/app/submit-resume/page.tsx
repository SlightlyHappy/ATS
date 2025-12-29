import PageHeader from "@/components/page-header";
import ResumeForm from "./resume-form";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function SubmitResumePage() {
  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Submit a new Resume"
        description="Upload a resume and optional job description for AI analysis."
      />
      <Card>
        <CardHeader>
            <CardTitle>Candidate Details</CardTitle>
            <CardDescription>Fill out the form below to submit a new resume to the system.</CardDescription>
        </CardHeader>
        <CardContent>
            <ResumeForm />
        </CardContent>
      </Card>
    </div>
  );
}
