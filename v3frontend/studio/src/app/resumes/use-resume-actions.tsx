"use client";

import { useToast } from "@/hooks/use-toast";
import { deleteResume, updateResumeStatus } from "@/services/api";
import { useAlertDialog } from "@/components/alert-dialog-provider";

interface ResumeActionCallbacks {
  onArchive: (id: string) => void;
  onDelete: (id: string) => void;
}

export function useResumeActions(callbacks: Partial<ResumeActionCallbacks> = {}) {
    const { toast } = useToast();
    const { showAlertDialog } = useAlertDialog();

    const handleArchive = (id: string) => {
        showAlertDialog({
            title: "Are you sure you want to archive this resume?",
            description: "This action will move the resume to the archived list.",
            onConfirm: async () => {
                 try {
                    await updateResumeStatus(id, "Archived");
                    toast({
                        title: "Success",
                        description: "Resume has been archived."
                    });
                    callbacks.onArchive?.(id);
                } catch (error) {
                    toast({
                        title: "Error",
                        description: "Failed to archive resume.",
                        variant: "destructive"
                    });
                }
            },
        });
    };

    const handleDelete = (id: string) => {
        showAlertDialog({
            title: "Are you sure you want to delete this resume?",
            description: "This action cannot be undone and will permanently delete the resume.",
            onConfirm: async () => {
                try {
                    await deleteResume(id);
                    toast({
                        title: "Success",
                        description: "Resume has been deleted."
                    });
                    callbacks.onDelete?.(id);
                } catch (error) {
                    toast({
                        title: "Error",
                        description: "Failed to delete resume.",
                        variant: "destructive"
                    });
                }
            },
        });
    };

    return { handleArchive, handleDelete };
}
