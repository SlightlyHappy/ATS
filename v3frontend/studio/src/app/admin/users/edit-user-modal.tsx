"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AdminService } from "@/services/admin.service";
import { useToast } from "@/hooks/use-toast";
import type { User } from "@/types";

interface EditUserModalProps {
  open: boolean;
  user: User | null;
  onOpenChangeAction: (open: boolean) => void;
  onSuccessAction: () => void;
}

interface UserFormData {
  name: string;
  email: string;
  access_type: 'admin' | 'user';
  trial_resume_limit: number;
  trial_legal_limit: number;
}

interface FormErrors {
  name?: string;
  email?: string;
  access_type?: string;
  trial_resume_limit?: string;
  trial_legal_limit?: string;
}

export function EditUserModal({ open, user, onOpenChangeAction, onSuccessAction }: EditUserModalProps) {
  const [formData, setFormData] = useState<UserFormData>({
    name: "",
    email: "",
    access_type: "user",
    trial_resume_limit: 5,
    trial_legal_limit: 3,
  });
  const [isUpdating, setIsUpdating] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const { toast } = useToast();

  // Reset form when user changes or modal opens
  useEffect(() => {
    if (user && open) {
      setFormData({
        name: user.name || "",
        email: user.email || "",
        access_type: user.access_type || "user",
        trial_resume_limit: user.trial_info?.resume_limit || 5,
        trial_legal_limit: user.trial_info?.legal_limit || 3,
      });
      setErrors({});
    }
  }, [user, open]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = "Name is required";
    }

    if (!formData.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }

    if (!formData.access_type) {
      newErrors.access_type = "Access type is required";
    }

    if (formData.trial_resume_limit < 1 || formData.trial_resume_limit > 100) {
      newErrors.trial_resume_limit = "Trial resume limit must be between 1 and 100";
    }

    if (formData.trial_legal_limit < 1 || formData.trial_legal_limit > 100) {
      newErrors.trial_legal_limit = "Trial legal limit must be between 1 and 100";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm() || !user) {
      return;
    }

    try {
      setIsUpdating(true);
      
      const updateData = {
        name: formData.name,
        email: formData.email,
        access_type: formData.access_type,
        trial_resume_limit: formData.trial_resume_limit,
        trial_legal_limit: formData.trial_legal_limit,
      };

      await AdminService.updateUser(user.user_id || user.id, updateData);
      
      toast({
        title: "Success",
        description: "User updated successfully.",
      });
      
      onSuccessAction();
    } catch (error) {
      console.error('Update user error:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update user. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsUpdating(false);
    }
  };

  const handleInputChange = (field: keyof UserFormData, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const handleClose = () => {
    if (!isUpdating) {
      onOpenChangeAction(false);
      setFormData({
        name: "",
        email: "",
        access_type: "user",
        trial_resume_limit: 5,
        trial_legal_limit: 3,
      });
      setErrors({});
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit User</DialogTitle>
          <DialogDescription>
            Update user information and permissions. Changes will be saved immediately.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">Full Name</Label>
              <Input
                id="edit-name"
                type="text"
                placeholder="Enter user's full name"
                value={formData.name}
                onChange={(e) => handleInputChange("name", e.target.value)}
                disabled={isUpdating}
                className={errors.name ? "border-destructive" : ""}
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-email">Email Address</Label>
              <Input
                id="edit-email"
                type="email"
                placeholder="Enter user's email address"
                value={formData.email}
                onChange={(e) => handleInputChange("email", e.target.value)}
                disabled={isUpdating}
                className={errors.email ? "border-destructive" : ""}
              />
              {errors.email && (
                <p className="text-sm text-destructive">{errors.email}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="edit-access-type">Access Type</Label>
              <Select
                value={formData.access_type}
                onValueChange={(value: 'admin' | 'user') => handleInputChange("access_type", value)}
                disabled={isUpdating}
              >
                <SelectTrigger className={errors.access_type ? "border-destructive" : ""}>
                  <SelectValue placeholder="Select access type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="user">User</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
              {errors.access_type && (
                <p className="text-sm text-destructive">{errors.access_type}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit-resume-limit">Resume Limit</Label>
                <Input
                  id="edit-resume-limit"
                  type="number"
                  min="1"
                  max="100"
                  value={formData.trial_resume_limit}
                  onChange={(e) => handleInputChange("trial_resume_limit", parseInt(e.target.value) || 1)}
                  disabled={isUpdating}
                  className={errors.trial_resume_limit ? "border-destructive" : ""}
                />
                {errors.trial_resume_limit && (
                  <p className="text-sm text-destructive">{errors.trial_resume_limit}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit-legal-limit">Legal Limit</Label>
                <Input
                  id="edit-legal-limit"
                  type="number"
                  min="1"
                  max="100"
                  value={formData.trial_legal_limit}
                  onChange={(e) => handleInputChange("trial_legal_limit", parseInt(e.target.value) || 1)}
                  disabled={isUpdating}
                  className={errors.trial_legal_limit ? "border-destructive" : ""}
                />
                {errors.trial_legal_limit && (
                  <p className="text-sm text-destructive">{errors.trial_legal_limit}</p>
                )}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button 
              type="button" 
              variant="outline" 
              onClick={handleClose}
              disabled={isUpdating}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isUpdating}>
              {isUpdating ? "Updating..." : "Update User"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
