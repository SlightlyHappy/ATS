"use client";

import { useEffect, useState, useMemo } from "react";
import { AdminService } from "@/services/admin.service";
import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Plus, 
  RefreshCw, 
  Trash2, 
  Eye, 
  Search,
  Filter,
  Download,
  MessageSquare,
  Clock,
  CheckCircle,
  XCircle,
  MoreHorizontal
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { format, formatDistanceToNow } from "date-fns";
import { CreateLegalQueryModal } from "./create-legal-query-modal";
import { LegalQueryDetailModal } from "./legal-query-detail-modal";

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

export default function AdminLegalQueriesPage() {
  const [data, setData] = useState<LegalQuery[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedQuery, setSelectedQuery] = useState<LegalQuery | null>(null);
  const [deleteQueryId, setDeleteQueryId] = useState<string | null>(null);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [priorityFilter, setPriorityFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  
  const { toast } = useToast();

  // Filter and search queries
  const filteredQueries = useMemo(() => {
    let filtered = [...data];

    // Search filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (query) =>
          query.query.toLowerCase().includes(searchLower) ||
          query.response?.toLowerCase().includes(searchLower) ||
          query.user_name?.toLowerCase().includes(searchLower) ||
          query.user_email?.toLowerCase().includes(searchLower) ||
          query.category.toLowerCase().includes(searchLower) ||
          query.tags?.some(tag => tag.toLowerCase().includes(searchLower))
      );
    }

    // Status filter
    if (statusFilter !== "all") {
      filtered = filtered.filter((query) => query.status === statusFilter);
    }

    // Priority filter
    if (priorityFilter !== "all") {
      filtered = filtered.filter((query) => query.priority === priorityFilter);
    }

    // Category filter
    if (categoryFilter !== "all") {
      filtered = filtered.filter((query) => query.category === categoryFilter);
    }

    return filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  }, [data, searchTerm, statusFilter, priorityFilter, categoryFilter]);

  // Get unique categories for filter
  const categories = useMemo(() => {
    const uniqueCategories = [...new Set(data.map(query => query.category))];
    return uniqueCategories.filter(Boolean);
  }, [data]);

  const loadLegalQueries = async () => {
    try {
      setIsLoading(true);
      const response = await AdminService.getLegalQueries();
      
      // Handle API response properly
      if (response.success && response.data) {
        // Transform API data to match our interface if needed
        const responseData = response.data as any;
        const legalQueries: LegalQuery[] = Array.isArray(responseData) 
          ? responseData 
          : (responseData.queries || responseData.legal_queries || []);
        setData(legalQueries);
      } else {
        // Handle API error or no data scenario
        console.warn("Legal queries API returned no data or failed:", response);
        setData([]);
        
        // Show user-friendly message if it's not a connection error
        if (response.message && !response.message.includes('network') && !response.message.includes('connection')) {
          toast({
            title: "No Legal Queries",
            description: response.message || "No legal queries found.",
            variant: "default",
          });
        }
      }
    } catch (error) {
      console.error('Failed to load legal queries:', error);
      setData([]);
      toast({
        title: "Failed to Load Legal Queries",
        description: error instanceof Error ? error.message : "Could not connect to the server. Please try refreshing.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setIsRefreshing(true);
      await loadLegalQueries();
      toast({
        title: "Success",
        description: "Legal queries refreshed successfully.",
      });
    } catch (error) {
      toast({
        title: "Error refreshing data",
        description: error instanceof Error ? error.message : "Could not refresh data.",
        variant: "destructive",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleDelete = async (queryId: string) => {
    try {
      await AdminService.deleteLegalQuery(queryId);
      setData(prev => prev.filter(query => query.id !== queryId));
      toast({
        title: "Success",
        description: "Legal query deleted successfully.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete legal query. Please try again.",
        variant: "destructive",
      });
    } finally {
      setDeleteQueryId(null);
    }
  };

  const handleExport = () => {
    const csvContent = [
      ["ID", "Query", "Status", "Priority", "Category", "User", "Created", "Response"],
      ...filteredQueries.map((query) => [
        query.id,
        query.query.substring(0, 100) + "...",
        query.status,
        query.priority,
        query.category,
        `${query.user_name} (${query.user_email})`,
        format(new Date(query.created_at), "yyyy-MM-dd HH:mm"),
        query.response ? "Yes" : "No",
      ]),
    ]
      .map((row) => row.map((field) => `"${field}"`).join(","))
      .join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `legal-queries-${format(new Date(), "yyyy-MM-dd")}.csv`;
    a.click();
    URL.revokeObjectURL(url);

    toast({
      title: "Export Complete",
      description: `Exported ${filteredQueries.length} legal queries.`,
    });
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
        return <Clock className="h-4 w-4" />;
      case "pending":
        return <MessageSquare className="h-4 w-4" />;
      case "failed":
        return <XCircle className="h-4 w-4" />;
      default:
        return <MessageSquare className="h-4 w-4" />;
    }
  };

  useEffect(() => {
    loadLegalQueries();
  }, []);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-8">
        <PageHeader
          title="Legal Queries"
          description="Manage and track legal consultation requests"
        />
        <div className="space-y-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Legal Queries"
        description="Manage and track legal consultation requests from users"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleExport} className="gap-2">
              <Download className="h-4 w-4" />
              Export
            </Button>
            <Button
              variant="outline"
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button onClick={() => setShowCreateModal(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              New Query
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.length}</div>
            <p className="text-xs text-muted-foreground">
              {filteredQueries.length} after filters
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {data.filter(q => q.status === 'pending').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Need attention
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Progress</CardTitle>
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {data.filter(q => q.status === 'in_progress').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Being worked on
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {data.filter(q => q.status === 'completed').length}
            </div>
            <p className="text-xs text-muted-foreground">
              {data.length > 0 ? Math.round((data.filter(q => q.status === 'completed').length / data.length) * 100) : 0}% completion rate
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search queries..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All Statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>

            <Select value={priorityFilter} onValueChange={setPriorityFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All Priorities" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priorities</SelectItem>
                <SelectItem value="urgent">Urgent</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>

            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {categories.map((category) => (
                  <SelectItem key={category} value={category}>
                    {category}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button
              variant="outline"
              onClick={() => {
                setSearchTerm("");
                setStatusFilter("all");
                setPriorityFilter("all");
                setCategoryFilter("all");
              }}
              className="gap-2"
            >
              <Filter className="h-4 w-4" />
              Clear Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Legal Queries Table */}
      <Card>
        <CardHeader>
          <CardTitle>Legal Queries ({filteredQueries.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Query</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredQueries.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                    No legal queries found
                  </TableCell>
                </TableRow>
              ) : (
                filteredQueries.map((query) => (
                  <TableRow key={query.id} className="hover:bg-muted/50">
                    <TableCell>
                      <div className="max-w-md">
                        <div className="font-medium truncate">{query.query}</div>
                        {query.tags && query.tags.length > 0 && (
                          <div className="flex gap-1 mt-1">
                            {query.tags.slice(0, 2).map((tag) => (
                              <Badge key={tag} variant="outline" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                            {query.tags.length > 2 && (
                              <Badge variant="outline" className="text-xs">
                                +{query.tags.length - 2}
                              </Badge>
                            )}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="text-sm font-medium">{query.user_name}</div>
                        <div className="text-xs text-muted-foreground">{query.user_email}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(query.status)}
                        <Badge className={getStatusColor(query.status)}>
                          {query.status.replace('_', ' ')}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={getPriorityColor(query.priority)}>
                        {query.priority}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{query.category}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="text-sm">
                          {format(new Date(query.created_at), "MMM dd, yyyy")}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {formatDistanceToNow(new Date(query.created_at), { addSuffix: true })}
                        </div>
                      </div>
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
                            onClick={() => setSelectedQuery(query)}
                            className="gap-2"
                          >
                            <Eye className="h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => setDeleteQueryId(query.id)}
                            className="gap-2 text-red-600"
                          >
                            <Trash2 className="h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Modals */}
      <CreateLegalQueryModal
        open={showCreateModal}
        onOpenChangeAction={setShowCreateModal}
        onSuccessAction={loadLegalQueries}
      />

      <LegalQueryDetailModal
        isOpen={!!selectedQuery}
        onCloseAction={() => setSelectedQuery(null)}
        query={selectedQuery}
        onUpdateAction={loadLegalQueries}
      />

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteQueryId} onOpenChange={() => setDeleteQueryId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the legal query
              and remove it from our servers.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteQueryId && handleDelete(deleteQueryId)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
