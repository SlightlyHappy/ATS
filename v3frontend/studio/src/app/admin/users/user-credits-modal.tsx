"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { enhancedAdminService } from "@/services/enhanced-admin.service";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import { CreditCard, RefreshCw, UserIcon, AlertCircle } from "lucide-react";
import type { User } from "@/types";

interface UserCreditsModalProps {
  open: boolean;
  user: User | null;
  onOpenChangeAction: (open: boolean) => void;
}

interface UserCreditsData {
  credits: number;
  usage_stats?: {
    resumes_analyzed: number;
    legal_queries: number;
    remaining_resume_limit: number;
    remaining_legal_limit: number;
  };
}

export function UserCreditsModal({ open, user, onOpenChangeAction }: UserCreditsModalProps) {
  const [creditsData, setCreditsData] = useState<UserCreditsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [creditAmount, setCreditAmount] = useState<string>("");
  const [adjustmentReason, setAdjustmentReason] = useState<string>("");
  const { toast } = useToast();

  const loadUserCredits = async () => {
    if (!user) return;
    
    try {
      setIsLoading(true);
      const response = await enhancedAdminService.getUserCredits(user.user_id || user.id);
      if (response.data) {
        setCreditsData(response.data);
      }
    } catch (error) {
      console.error('Failed to load user credits:', error);
      toast({
        title: "Error",
        description: "Failed to load user credits. Please try again.",
        variant: "destructive",
      });
      setCreditsData(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (!user) return;
    
    try {
      setIsRefreshing(true);
      const response = await enhancedAdminService.getUserCredits(user.user_id || user.id);
      if (response.data) {
        setCreditsData(response.data);
      }
      toast({
        title: "Success",
        description: "User credits refreshed successfully.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to refresh user credits.",
        variant: "destructive",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleUpdateCredits = async () => {
    if (!user || !creditAmount) return;
    
    const amount = parseInt(creditAmount);
    if (isNaN(amount)) {
      toast({
        title: "Error",
        description: "Please enter a valid credit amount.",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsUpdating(true);
      const response = await enhancedAdminService.updateUserCredits(
        user.user_id || user.id, 
        amount, 
        adjustmentReason || "Admin adjustment"
      );
      
      if (response.success) {
        toast({
          title: "Success",
          description: `Credits ${amount > 0 ? 'added' : 'removed'} successfully.`,
        });
        
        // Refresh credits data
        await loadUserCredits();
        
        // Reset form
        setCreditAmount("");
        setAdjustmentReason("");
      } else {
        throw new Error(response.error || "Failed to update credits");
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update user credits.",
        variant: "destructive",
      });
    } finally {
      setIsUpdating(false);
    }
  };

  useEffect(() => {
    if (open && user) {
      loadUserCredits();
    }
  }, [open, user]);

  const handleClose = () => {
    onOpenChangeAction(false);
    setCreditsData(null);
  };

  if (!user) return null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserIcon className="h-5 w-5" />
            User Credits & Usage
          </DialogTitle>
          <DialogDescription>
            View credit balance and usage statistics for {user.name}
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-6">
          {/* User Info */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">User Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Name:</span>
                <span className="font-medium">{user.name}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Email:</span>
                <span className="font-medium">{user.email}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Account Type:</span>
                <Badge variant={user.access_type === 'admin' ? 'default' : 'secondary'}>
                  {user.access_type === 'admin' ? 'Admin' : 'User'}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Trial Status:</span>
                <Badge variant={user.is_trial ? 'outline' : 'default'}>
                  {user.is_trial ? 'Trial User' : 'Paid User'}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Credits and Usage */}
          {isLoading ? (
            <Card>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-4 w-48" />
              </CardHeader>
              <CardContent className="space-y-3">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </CardContent>
            </Card>
          ) : creditsData ? (
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <CreditCard className="h-4 w-4" />
                    Credits & Usage
                  </CardTitle>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleRefresh}
                    disabled={isRefreshing}
                    className="gap-2"
                  >
                    <RefreshCw className={`h-3 w-3 ${isRefreshing ? 'animate-spin' : ''}`} />
                    Refresh
                  </Button>
                </div>
                <CardDescription>
                  Current balance and usage statistics
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-muted rounded-lg">
                  <span className="font-medium">Available Credits:</span>
                  <Badge variant="default" className="text-sm px-2 py-1">
                    {creditsData.credits}
                  </Badge>
                </div>

                {creditsData.usage_stats && (
                  <div className="space-y-3">
                    <h4 className="font-medium text-sm">Usage Statistics</h4>
                    
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Resumes Analyzed:</span>
                          <span className="font-medium">{creditsData.usage_stats.resumes_analyzed}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Remaining Resume Limit:</span>
                          <Badge variant={creditsData.usage_stats.remaining_resume_limit > 0 ? 'default' : 'destructive'}>
                            {creditsData.usage_stats.remaining_resume_limit}
                          </Badge>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Legal Queries:</span>
                          <span className="font-medium">{creditsData.usage_stats.legal_queries}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Remaining Legal Limit:</span>
                          <Badge variant={creditsData.usage_stats.remaining_legal_limit > 0 ? 'default' : 'destructive'}>
                            {creditsData.usage_stats.remaining_legal_limit}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="flex flex-col items-center justify-center p-8 text-center space-y-4">
              <AlertCircle className="h-12 w-12 text-muted-foreground" />
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">Unable to Load Credits</h3>
                <p className="text-muted-foreground max-w-md">
                  Failed to retrieve user credits and usage information.
                </p>
              </div>
              <Button 
                onClick={handleRefresh} 
                disabled={isRefreshing}
                className="gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                Try Again
              </Button>
            </div>
          )}

          {/* Credit Adjustment Section */}
          {creditsData && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Adjust Credits</CardTitle>
                <CardDescription>
                  Add or remove credits for this user
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="creditAmount">Credit Amount</Label>
                    <Input
                      id="creditAmount"
                      type="number"
                      placeholder="Enter amount (+ to add, - to remove)"
                      value={creditAmount}
                      onChange={(e) => setCreditAmount(e.target.value)}
                      disabled={isUpdating}
                    />
                    <p className="text-xs text-muted-foreground">
                      Use positive numbers to add credits, negative to remove
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="adjustmentReason">Reason (Optional)</Label>
                    <Input
                      id="adjustmentReason"
                      placeholder="Reason for adjustment"
                      value={adjustmentReason}
                      onChange={(e) => setAdjustmentReason(e.target.value)}
                      disabled={isUpdating}
                    />
                  </div>
                </div>
                
                <Separator />
                
                <div className="flex justify-between items-center">
                  <div className="text-sm text-muted-foreground">
                    {creditAmount && !isNaN(parseInt(creditAmount)) && (
                      <span>
                        New balance will be: <strong>
                          {creditsData.credits + parseInt(creditAmount)}
                        </strong> credits
                      </span>
                    )}
                  </div>
                  <Button 
                    onClick={handleUpdateCredits}
                    disabled={!creditAmount || isUpdating}
                    className="gap-2"
                  >
                    {isUpdating ? (
                      <>
                        <RefreshCw className="h-4 w-4 animate-spin" />
                        Updating...
                      </>
                    ) : (
                      <>
                        <CreditCard className="h-4 w-4" />
                        Update Credits
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
        
        <div className="flex justify-end">
          <Button variant="outline" onClick={handleClose}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
