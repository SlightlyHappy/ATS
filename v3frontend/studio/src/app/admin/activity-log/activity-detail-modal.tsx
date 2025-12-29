"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { 
  User, 
  Calendar, 
  MapPin, 
  Monitor, 
  Smartphone,
  Copy,
  ExternalLink
} from "lucide-react";
import { format } from "date-fns";
import { useToast } from "@/hooks/use-toast";

interface ActivityLogEntry {
  id: string;
  timestamp: string;
  user: {
    id: string;
    name: string;
    email: string;
    role: string;
  };
  action: string;
  resource: string;
  resourceId?: string;
  status: "success" | "failed" | "warning";
  details: string;
  metadata?: {
    ipAddress?: string;
    userAgent?: string;
    location?: string;
    duration?: number;
    errorCode?: string;
    additionalData?: Record<string, any>;
  };
}

interface ActivityDetailModalProps {
  isOpen: boolean;
  onCloseAction: () => void;
  activity: ActivityLogEntry | null;
}

export function ActivityDetailModal({
  isOpen,
  onCloseAction,
  activity,
}: ActivityDetailModalProps) {
  const { toast } = useToast();

  if (!activity) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case "success":
        return "bg-green-100 text-green-800 border-green-200";
      case "failed":
        return "bg-red-100 text-red-800 border-red-200";
      case "warning":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied to clipboard",
      description: `${label} has been copied to your clipboard.`,
    });
  };

  const getDeviceIcon = (userAgent?: string) => {
    if (!userAgent) return <Monitor className="h-4 w-4" />;
    if (userAgent.includes("Mobile") || userAgent.includes("Android") || userAgent.includes("iPhone")) {
      return <Smartphone className="h-4 w-4" />;
    }
    return <Monitor className="h-4 w-4" />;
  };

  return (
    <Dialog open={isOpen} onOpenChange={onCloseAction}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            Activity Details
            <Badge className={getStatusColor(activity.status)}>
              {activity.status}
            </Badge>
          </DialogTitle>
          <DialogDescription>
            Detailed information about this activity log entry
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    Timestamp
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm">
                      {format(new Date(activity.timestamp), "PPP 'at' p")}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(activity.timestamp, "Timestamp")}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="text-sm font-medium text-muted-foreground">Action</div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{activity.action}</Badge>
                    <span className="text-sm text-muted-foreground">on</span>
                    <Badge variant="secondary">{activity.resource}</Badge>
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <div className="text-sm font-medium text-muted-foreground">Details</div>
                <div className="bg-muted/50 p-3 rounded-lg">
                  <p className="text-sm">{activity.details}</p>
                </div>
              </div>

              {activity.resourceId && (
                <div className="space-y-2">
                  <div className="text-sm font-medium text-muted-foreground">Resource ID</div>
                  <div className="flex items-center gap-2">
                    <code className="bg-muted px-2 py-1 rounded text-sm font-mono">
                      {activity.resourceId}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(activity.resourceId!, "Resource ID")}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        // Navigate to resource (implement based on resource type)
                        toast({
                          title: "Navigation",
                          description: "Resource navigation would open here in a real implementation.",
                        });
                      }}
                    >
                      <ExternalLink className="h-3 w-3" />
                    </Button>
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
                  <div className="text-sm font-medium text-muted-foreground">Name</div>
                  <div>{activity.user.name}</div>
                </div>
                
                <div className="space-y-2">
                  <div className="text-sm font-medium text-muted-foreground">Email</div>
                  <div className="flex items-center gap-2">
                    <span>{activity.user.email}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(activity.user.email, "Email")}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="text-sm font-medium text-muted-foreground">Role</div>
                  <Badge variant="outline">{activity.user.role}</Badge>
                </div>
                
                <div className="space-y-2">
                  <div className="text-sm font-medium text-muted-foreground">User ID</div>
                  <div className="flex items-center gap-2">
                    <code className="bg-muted px-2 py-1 rounded text-sm font-mono">
                      {activity.user.id}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(activity.user.id, "User ID")}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Technical Metadata */}
          {activity.metadata && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Technical Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {activity.metadata.ipAddress && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                        <MapPin className="h-4 w-4" />
                        IP Address
                      </div>
                      <div className="flex items-center gap-2">
                        <code className="bg-muted px-2 py-1 rounded text-sm font-mono">
                          {activity.metadata.ipAddress}
                        </code>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(activity.metadata?.ipAddress || "", "IP Address")}
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>

                    {activity.metadata.location && (
                      <div className="space-y-2">
                        <div className="text-sm font-medium text-muted-foreground">Location</div>
                        <div>{activity.metadata.location}</div>
                      </div>
                    )}
                  </div>
                )}

                {activity.metadata.userAgent && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                      {getDeviceIcon(activity.metadata.userAgent)}
                      User Agent
                    </div>
                    <div className="bg-muted/50 p-3 rounded-lg">
                      <code className="text-xs break-all">{activity.metadata.userAgent}</code>
                    </div>
                  </div>
                )}

                {activity.metadata.duration && (
                  <div className="space-y-2">
                    <div className="text-sm font-medium text-muted-foreground">Duration</div>
                    <div>{activity.metadata.duration}ms</div>
                  </div>
                )}

                {activity.metadata.errorCode && (
                  <div className="space-y-2">
                    <div className="text-sm font-medium text-muted-foreground">Error Code</div>
                    <Badge variant="destructive">{activity.metadata.errorCode}</Badge>
                  </div>
                )}

                {activity.metadata.additionalData && (
                  <div className="space-y-2">
                    <div className="text-sm font-medium text-muted-foreground">Additional Data</div>
                    <div className="bg-muted/50 p-3 rounded-lg">
                      <pre className="text-xs overflow-x-auto">
                        {JSON.stringify(activity.metadata.additionalData, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
