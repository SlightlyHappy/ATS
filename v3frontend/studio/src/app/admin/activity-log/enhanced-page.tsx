"use client";

import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { 
  RefreshCw, 
  Eye, 
  User, 
  Calendar,
  Activity as ActivityIcon,
  Clock,
  MoreHorizontal
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import PageHeader from "@/components/page-header";
import { AdminService } from "@/services/admin.service";
import { useToast } from "@/hooks/use-toast";
import { format, formatDistanceToNow } from "date-fns";
import { 
  ActivityLogFilterBar, 
  type ActivityLogFilterState 
} from "./activity-log-filter-bar";
import { ActivityDetailModal } from "./activity-detail-modal";

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

export default function ActivityLogPage() {
  const [activityLogs, setActivityLogs] = useState<ActivityLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedActivity, setSelectedActivity] = useState<ActivityLogEntry | null>(null);
  const [filters, setFilters] = useState<ActivityLogFilterState>({
    search: "",
    userFilter: null,
    actionFilter: null,
    resourceFilter: null,
    statusFilter: null,
    startDate: null,
    endDate: null,
  });
  const { toast } = useToast();

  // Calculate active filter count
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.search) count++;
    if (filters.userFilter) count++;
    if (filters.actionFilter) count++;
    if (filters.resourceFilter) count++;
    if (filters.statusFilter) count++;
    if (filters.startDate) count++;
    if (filters.endDate) count++;
    return count;
  }, [filters]);

  // Filter activity logs based on current filters
  const filteredActivityLogs = useMemo(() => {
    let filtered = [...activityLogs];

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(
        (log) =>
          log.user.name.toLowerCase().includes(searchLower) ||
          log.user.email.toLowerCase().includes(searchLower) ||
          log.action.toLowerCase().includes(searchLower) ||
          log.details.toLowerCase().includes(searchLower) ||
          log.resource.toLowerCase().includes(searchLower)
      );
    }

    // User filter
    if (filters.userFilter) {
      const userLower = filters.userFilter.toLowerCase();
      filtered = filtered.filter(
        (log) =>
          log.user.name.toLowerCase().includes(userLower) ||
          log.user.email.toLowerCase().includes(userLower)
      );
    }

    // Action filter
    if (filters.actionFilter) {
      filtered = filtered.filter((log) => log.action === filters.actionFilter);
    }

    // Resource filter
    if (filters.resourceFilter) {
      filtered = filtered.filter((log) => log.resource === filters.resourceFilter);
    }

    // Status filter
    if (filters.statusFilter) {
      filtered = filtered.filter((log) => log.status === filters.statusFilter);
    }

    // Date range filters
    if (filters.startDate) {
      filtered = filtered.filter(
        (log) => new Date(log.timestamp) >= filters.startDate!
      );
    }
    if (filters.endDate) {
      const endOfDay = new Date(filters.endDate);
      endOfDay.setHours(23, 59, 59, 999);
      filtered = filtered.filter(
        (log) => new Date(log.timestamp) <= endOfDay
      );
    }

    return filtered.sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }, [activityLogs, filters]);

  const fetchActivityLogs = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      // Build query parameters from filters
      const params: Record<string, any> = {};
      if (filters.userFilter) params.user = filters.userFilter;
      if (filters.actionFilter) params.action = filters.actionFilter;
      if (filters.resourceFilter) params.resource = filters.resourceFilter;
      if (filters.statusFilter) params.status = filters.statusFilter;
      if (filters.startDate) params.startDate = filters.startDate.toISOString();
      if (filters.endDate) params.endDate = filters.endDate.toISOString();

      console.log('📊 Activity Log: Fetching activity logs...', { params, isRefresh });

      const response = await AdminService.getActivityLog(params);
      
      console.log('📊 Activity Log: API response:', {
        success: response.success,
        hasData: !!response.data,
        dataType: typeof response.data,
        error: response.error
      });

      if (response.success && response.data) {
        // Transform API response to expected format if needed
        let activityData = response.data;
        
        // If the response contains activity_logs array, use that
        if (response.data && typeof response.data === 'object' && 'activity_logs' in response.data) {
          activityData = (response.data as any).activity_logs;
        } else if (Array.isArray(response.data)) {
          activityData = response.data;
        }

        console.log('✅ Activity Log: Real data loaded successfully:', {
          count: Array.isArray(activityData) ? activityData.length : 0,
          endpoint: 'AdminService.getActivityLog'
        });

        setActivityLogs(Array.isArray(activityData) ? activityData : []);
      } else {
        console.warn('⚠️ Activity Log: API failed or returned no data, using empty array');
        setActivityLogs([]);
        
        toast({
          title: "Warning", 
          description: "Could not load activity logs. " + (response.error || "Please try again later."),
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("❌ Activity Log: Error fetching activity logs:", error);
      setActivityLogs([]);
      toast({
        title: "Error",
        description: "Failed to fetch activity logs. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchActivityLogs();
  }, []);

  const handleRefresh = () => {
    fetchActivityLogs(true);
  };

  const handleClearFilters = () => {
    setFilters({
      search: "",
      userFilter: null,
      actionFilter: null,
      resourceFilter: null,
      statusFilter: null,
      startDate: null,
      endDate: null,
    });
  };

  const handleExport = () => {
    // Export filtered data as CSV
    const csvContent = [
      ["Timestamp", "User", "Action", "Resource", "Status", "Details"],
      ...filteredActivityLogs.map((log) => [
        log.timestamp,
        `${log.user.name} (${log.user.email})`,
        log.action,
        log.resource,
        log.status,
        log.details,
      ]),
    ]
      .map((row) => row.map((field) => `"${field}"`).join(","))
      .join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `activity-log-${format(new Date(), "yyyy-MM-dd")}.csv`;
    a.click();
    URL.revokeObjectURL(url);

    toast({
      title: "Export Complete",
      description: `Exported ${filteredActivityLogs.length} activity log entries.`,
    });
  };

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

  const getActionIcon = (action: string) => {
    switch (action) {
      case "login":
      case "logout":
        return <User className="h-4 w-4" />;
      case "upload":
      case "analyze":
      case "create":
      case "update":
      case "delete":
        return <ActivityIcon className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Activity Log"
        description="Monitor and track all system activities and user actions"
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Activities</CardTitle>
            <ActivityIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{filteredActivityLogs.length}</div>
            <p className="text-xs text-muted-foreground">
              {activeFilterCount > 0 ? "Filtered results" : "All activities"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <Badge className="bg-green-100 text-green-800">
              {filteredActivityLogs.length > 0
                ? Math.round(
                    (filteredActivityLogs.filter((log) => log.status === "success").length /
                      filteredActivityLogs.length) *
                      100
                  )
                : 0}
              %
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {filteredActivityLogs.filter((log) => log.status === "success").length}
            </div>
            <p className="text-xs text-muted-foreground">Successful actions</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed Actions</CardTitle>
            <Badge className="bg-red-100 text-red-800">
              {filteredActivityLogs.filter((log) => log.status === "failed").length}
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {filteredActivityLogs.filter((log) => log.status === "failed").length}
            </div>
            <p className="text-xs text-muted-foreground">Need attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <User className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {new Set(filteredActivityLogs.map((log) => log.user.id)).size}
            </div>
            <p className="text-xs text-muted-foreground">Unique users</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <ActivityLogFilterBar
        filters={filters}
        onFiltersChangeAction={setFilters}
        onClearFiltersAction={handleClearFilters}
        onExportAction={handleExport}
        activeFilterCount={activeFilterCount}
      />

      {/* Activity Log Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Activity History</CardTitle>
            <Button
              onClick={handleRefresh}
              disabled={refreshing}
              variant="outline"
              size="sm"
              className="gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin" />
              <span className="ml-2">Loading activity logs...</span>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Resource</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Details</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredActivityLogs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      {activeFilterCount > 0
                        ? "No activities match your current filters"
                        : "No activity logs found"}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredActivityLogs.map((log) => (
                    <TableRow key={log.id} className="hover:bg-muted/50">
                      <TableCell>
                        <div className="space-y-1">
                          <div className="text-sm font-medium">
                            {format(new Date(log.timestamp), "MMM dd, HH:mm")}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {formatDistanceToNow(new Date(log.timestamp), { addSuffix: true })}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="text-sm font-medium">{log.user.name}</div>
                          <div className="text-xs text-muted-foreground">{log.user.email}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getActionIcon(log.action)}
                          <Badge variant="outline">{log.action}</Badge>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{log.resource}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(log.status)}>{log.status}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="max-w-xs truncate text-sm">{log.details}</div>
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={() => setSelectedActivity(log)}
                              className="gap-2"
                            >
                              <Eye className="h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Activity Detail Modal */}
      <ActivityDetailModal
        isOpen={!!selectedActivity}
        onCloseAction={() => setSelectedActivity(null)}
        activity={selectedActivity}
      />
    </div>
  );
}
