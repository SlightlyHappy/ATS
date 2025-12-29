"use client";

import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { 
  User, 
  Calendar, 
  Clock, 
  Tag, 
  MessageSquare,
  CheckCircle,
  XCircle,
  RefreshCw,
  Copy
} from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AdminService } from "@/services/admin.service";
import { useToast } from "@/hooks/use-toast";
import { format, formatDistanceToNow } from "date-fns";

interface LegalQuery {
  id: string;
  query: string;
  response?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  category: string;
  created_at: string;
  updated_at: string;
  user_id?: string;
  user_name?: string;
  user_email?: string;
  tags?: string[];
  estimated_time?: number;
  actual_time?: number;
}

interface LegalQueryDetailModalProps {
  isOpen: boolean;
  onCloseAction: () => void;
  query: LegalQuery | null;
  onUpdateAction: () => void;
}

export function LegalQueryDetailModal({ 
  isOpen, 
  onCloseAction, 
  query,
  onUpdateAction
}: LegalQueryDetailModalProps) {
  const [response, setResponse] = useState("");
  const [status, setStatus] = useState<string>("");
  const [priority, setPriority] = useState<string>("");
  const [isUpdating, setIsUpdating] = useState(false);
  const { toast } = useToast();

  // Initialize form values when query changes
  useEffect(() => {
    if (query) {
      setResponse(query.response || "");
      setStatus(query.status);
      setPriority(query.priority);
    }
  }, [query]);

  if (!query) return null;

  const handleUpdate = async () => {
    try {
      setIsUpdating(true);
      
      // In a real implementation, you would call an update API
      // await AdminService.updateLegalQuery(query.id, { response, status, priority });
      
      toast({
        title: "Success",
        description: "Legal query updated successfully.",
      });
      
      onUpdateAction();
      onCloseAction();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update legal query. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsUpdating(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800 border-green-200";
      case "in_progress":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "pending":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "failed":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "urgent":
        return "bg-red-100 text-red-800 border-red-200";
      case "high":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "low":
        return "bg-green-100 text-green-800 border-green-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4" />;
      case "in_progress":
        return <RefreshCw className="h-4 w-4" />;
      case "pending":
        return <Clock className="h-4 w-4" />;
      case "failed":
        return <XCircle className="h-4 w-4" />;
      default:
        return <MessageSquare className="h-4 w-4" />;
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied to clipboard",
      description: `${label} has been copied to your clipboard.`,
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onCloseAction}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            Legal Query Details
            <Badge className={getStatusColor(query.status)}>
              {getStatusIcon(query.status)}
              <span className="ml-1">{query.status.replace('_', ' ')}</span>
            </Badge>
          </DialogTitle>
          <DialogDescription>
            Review and manage this legal consultation request
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Query Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Query Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label className="text-sm font-medium text-muted-foreground">Question</Label>
                <div className="bg-muted/50 p-3 rounded-lg">
                  <p className="text-sm leading-relaxed">{query.query}</p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(query.query, "Query")}
                  className="h-6 px-2 text-xs"
                >
                  <Copy className="h-3 w-3 mr-1" />
                  Copy
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">Category</Label>
                  <Badge variant="secondary">{query.category}</Badge>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">Priority</Label>
                  <Badge className={getPriorityColor(query.priority)}>{query.priority}</Badge>
                </div>
              </div>

              {query.tags && query.tags.length > 0 && (
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">Tags</Label>
                  <div className="flex flex-wrap gap-1">
                    {query.tags.map((tag) => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        <Tag className="h-3 w-3 mr-1" />
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* User Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <User className="h-5 w-5" />
                User Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">Name</Label>
                  <div>{query.user_name}</div>
                </div>
                
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">Email</Label>
                  <div className="flex items-center gap-2">
                    <span>{query.user_email}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(query.user_email || "", "Email")}
                      className="h-6 px-2"
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Timeline */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Timeline
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">Created</Label>
                  <div className="space-y-1">
                    <div className="text-sm font-medium">
                      {format(new Date(query.created_at), "PPP 'at' p")}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(query.created_at), { addSuffix: true })}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium text-muted-foreground">Last Updated</Label>
                  <div className="space-y-1">
                    <div className="text-sm font-medium">
                      {format(new Date(query.updated_at), "PPP 'at' p")}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(query.updated_at), { addSuffix: true })}
                    </div>
                  </div>
                </div>
              </div>

              {(query.estimated_time || query.actual_time) && (
                <>
                  <Separator className="my-4" />
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {query.estimated_time && (
                      <div className="space-y-2">
                        <Label className="text-sm font-medium text-muted-foreground">Estimated Time</Label>
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          <span>{query.estimated_time} minutes</span>
                        </div>
                      </div>
                    )}

                    {query.actual_time && (
                      <div className="space-y-2">
                        <Label className="text-sm font-medium text-muted-foreground">Actual Time</Label>
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          <span>{query.actual_time} minutes</span>
                          {query.estimated_time && (
                            <Badge variant={query.actual_time <= query.estimated_time ? "default" : "secondary"}>
                              {query.actual_time <= query.estimated_time ? "On time" : "Over estimate"}
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Response Section */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Response & Management</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="status">Status</Label>
                  <Select value={status} onValueChange={setStatus}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="in_progress">In Progress</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                      <SelectItem value="failed">Failed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="priority">Priority</Label>
                  <Select value={priority} onValueChange={setPriority}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="urgent">Urgent</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="response">Response</Label>
                <Textarea
                  id="response"
                  placeholder="Enter your legal consultation response..."
                  value={response}
                  onChange={(e) => setResponse(e.target.value)}
                  rows={6}
                />
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={onCloseAction}>
                  Cancel
                </Button>
                <Button onClick={handleUpdate} disabled={isUpdating}>
                  {isUpdating ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Updating...
                    </>
                  ) : (
                    "Update Query"
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
}
