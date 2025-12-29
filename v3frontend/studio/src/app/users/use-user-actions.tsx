"use client";

import { useState } from "react";
import { useToast } from "@/hooks/use-toast";
import { AdminService } from "@/services/admin.service";
import { useAlertDialog } from "@/components/alert-dialog-provider";
import type { User } from "@/types";

interface UserActionCallbacks {
  onDelete: (id: string) => void;
  onEdit: (updatedUser: User) => void;
}

export function useUserActions(callbacks: Partial<UserActionCallbacks> = {}) {
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [creditsModalOpen, setCreditsModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const { toast } = useToast();
  const { showAlertDialog } = useAlertDialog();

  const handleDelete = (id: string) => {
    showAlertDialog({
      title: "Are you sure you want to deactivate this user?",
      description: "This will deactivate the user's account. They will no longer be able to access the system, but their data will be preserved.",
      confirmText: "Deactivate User",
      onConfirm: async () => {
        try {
          console.log("🗑️ Attempting to deactivate user:", id);
          const response = await AdminService.deleteUser(id);
          console.log("🗑️ Deactivate response:", response);
          
          // Check if the response indicates success
          // Handle different possible response formats
          const isSuccess = response?.success !== false && 
                           response?.error === undefined &&
                           !response?.message?.toLowerCase().includes('error') &&
                           !response?.message?.toLowerCase().includes('failed');
          
          if (isSuccess) {
            toast({
              title: "Success",
              description: response?.message || "User has been deactivated."
            });
            callbacks.onDelete?.(id);
          } else {
            console.error("🗑️ Deactivate operation indicated failure:", response);
            throw new Error(response?.message || response?.error || "Deactivate operation failed - backend returned error status");
          }
        } catch (error) {
          console.error("🗑️ Deactivate failed:", error);
          toast({
            title: "Error",
            description: error instanceof Error ? error.message : "Failed to deactivate user.",
            variant: "destructive"
          });
        }
      },
    });
  };

  const handleEdit = (user: User) => {
    setSelectedUser(user);
    setEditModalOpen(true);
  };

  const handleEditSuccess = () => {
    setEditModalOpen(false);
    if (selectedUser) {
      callbacks.onEdit?.(selectedUser);
    }
    setSelectedUser(null);
  };

  const handleViewCredits = (user: User) => {
    setSelectedUser(user);
    setCreditsModalOpen(true);
  };

  const handleResetTrial = (userId: string) => {
    showAlertDialog({
      title: "Reset trial limits?",
      description: "This will reset the user's trial usage counters to zero. They will be able to use their full trial limits again.",
      confirmText: "Reset Trial",
      onConfirm: async () => {
        try {
          await AdminService.resetUserTrial(userId);
          toast({
            title: "Success",
            description: "User trial limits have been reset."
          });
          // Optionally refresh the data here
        } catch (error) {
          toast({
            title: "Error",
            description: "Failed to reset trial limits.",
            variant: "destructive"
          });
        }
      },
    });
  };

  return { 
    handleDelete, 
    handleEdit,
    handleEditSuccess,
    handleViewCredits,
    handleResetTrial,
    editModalOpen,
    setEditModalOpen,
    creditsModalOpen,
    setCreditsModalOpen,
    selectedUser,
  };
}
