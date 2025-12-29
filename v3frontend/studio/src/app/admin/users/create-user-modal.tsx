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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AdminService } from "@/services/admin.service";
import { useToast } from "@/hooks/use-toast";

interface CreateUserModalProps {
  open: boolean;
  onOpenChangeAction: (open: boolean) => void;
  onSuccessAction: () => void;
}

interface UserFormData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
  access_type: 'admin' | 'user';
  trial_resume_limit: number;
  trial_legal_limit: number;
}

export function CreateUserModal({ open, onOpenChangeAction, onSuccessAction }: CreateUserModalProps) {
  const [formData, setFormData] = useState<UserFormData>({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    access_type: "user",
    trial_resume_limit: 5,
    trial_legal_limit: 3,
  });
  const [isCreating, setIsCreating] = useState(false);
  const [errors, setErrors] = useState<Partial<UserFormData>>({});
  const { toast } = useToast();

  const validateForm = (): boolean => {
    const newErrors: Partial<UserFormData> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Name is required";
    }

    if (!formData.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Email is invalid";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setIsCreating(true);
    try {
      await AdminService.createUser({
        name: formData.name,
        email: formData.email,
        password: formData.password,
        access_type: formData.access_type,
        trial_resume_limit: formData.trial_resume_limit,
        trial_legal_limit: formData.trial_legal_limit,
      });
      
      onSuccessAction();
      // Reset form
      setFormData({
        name: "",
        email: "",
        password: "",
        confirmPassword: "",
        access_type: "user",
        trial_resume_limit: 5,
        trial_legal_limit: 3,
      });
      setErrors({});
    } catch (error) {
      toast({
        title: "User creation failed",
        description: error instanceof Error ? error.message : "Failed to create user.",
        variant: "destructive",
      });
    } finally {
      setIsCreating(false);
    }
  };

  const handleClose = () => {
    if (!isCreating) {
      setFormData({
        name: "",
        email: "",
        password: "",
        confirmPassword: "",
        access_type: "user",
        trial_resume_limit: 5,
        trial_legal_limit: 3,
      });
      setErrors({});
      onOpenChangeAction(false);
    }
  };

  const updateFormData = (field: keyof UserFormData, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create New User</DialogTitle>
          <DialogDescription>
            Create a new user account with specified access level and trial limits.
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid gap-4 py-4">
          {/* Name */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="name" className="text-right">
              Name
            </Label>
            <div className="col-span-3">
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => updateFormData("name", e.target.value)}
                placeholder="Full name"
              />
              {errors.name && (
                <p className="text-sm text-red-500 mt-1">{errors.name}</p>
              )}
            </div>
          </div>

          {/* Email */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="email" className="text-right">
              Email
            </Label>
            <div className="col-span-3">
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => updateFormData("email", e.target.value)}
                placeholder="email@example.com"
              />
              {errors.email && (
                <p className="text-sm text-red-500 mt-1">{errors.email}</p>
              )}
            </div>
          </div>

          {/* Password */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="password" className="text-right">
              Password
            </Label>
            <div className="col-span-3">
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => updateFormData("password", e.target.value)}
                placeholder="Minimum 8 characters"
              />
              {errors.password && (
                <p className="text-sm text-red-500 mt-1">{errors.password}</p>
              )}
            </div>
          </div>

          {/* Confirm Password */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="confirmPassword" className="text-right">
              Confirm
            </Label>
            <div className="col-span-3">
              <Input
                id="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={(e) => updateFormData("confirmPassword", e.target.value)}
                placeholder="Repeat password"
              />
              {errors.confirmPassword && (
                <p className="text-sm text-red-500 mt-1">{errors.confirmPassword}</p>
              )}
            </div>
          </div>

          {/* Access Type */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="accessType" className="text-right">
              Access Type
            </Label>
            <Select
              value={formData.access_type}
              onValueChange={(value: 'admin' | 'user') => updateFormData("access_type", value)}
            >
              <SelectTrigger className="col-span-3">
                <SelectValue placeholder="Select access type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="user">User</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Trial Limits */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="resumeLimit" className="text-right">
              Resume Limit
            </Label>
            <Input
              id="resumeLimit"
              type="number"
              min="0"
              value={formData.trial_resume_limit}
              onChange={(e) => updateFormData("trial_resume_limit", parseInt(e.target.value) || 0)}
              className="col-span-3"
            />
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="legalLimit" className="text-right">
              Legal Limit
            </Label>
            <Input
              id="legalLimit"
              type="number"
              min="0"
              value={formData.trial_legal_limit}
              onChange={(e) => updateFormData("trial_legal_limit", parseInt(e.target.value) || 0)}
              className="col-span-3"
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isCreating}
          >
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isCreating}>
            {isCreating ? "Creating..." : "Create User"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
