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
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { AdminService } from "@/services/admin.service";
import { useToast } from "@/hooks/use-toast";

interface CreateLegalQueryModalProps {
  open: boolean;
  onOpenChangeAction: (open: boolean) => void;
  onSuccessAction: () => void;
}

export function CreateLegalQueryModal({ 
  open, 
  onOpenChangeAction, 
  onSuccessAction 
}: CreateLegalQueryModalProps) {
  const [query, setQuery] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async () => {
    if (!query.trim()) {
      toast({
        title: "Query required",
        description: "Please enter a legal query.",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      await AdminService.createLegalQuery(query.trim());
      onSuccessAction();
      setQuery("");
    } catch (error) {
      toast({
        title: "Submission failed",
        description: error instanceof Error ? error.message : "Failed to submit legal query.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setQuery("");
      onOpenChangeAction(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Submit Legal Query</DialogTitle>
          <DialogDescription>
            Ask a question about HR legal compliance. Our AI will provide guidance based on current employment law.
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid gap-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="query">Legal Question</Label>
            <Textarea
              id="query"
              placeholder="Enter your HR legal compliance question here..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={6}
              className="resize-none"
            />
            <p className="text-xs text-muted-foreground">
              Be specific about your situation for more accurate guidance.
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!query.trim() || isSubmitting}>
            {isSubmitting ? "Submitting..." : "Submit Query"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
