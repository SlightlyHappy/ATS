"use client";

import { useEffect, useState } from "react";
import { AdminService } from "@/services/admin.service";
import { columns } from "@/app/users/columns";
import { DataTable } from "@/app/users/data-table";
import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { UserPlus, RefreshCw, Users, AlertCircle } from "lucide-react";
import type { User } from "@/types";
import { AlertDialogProvider } from "@/components/alert-dialog-provider";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import { CreateUserModal } from "./create-user-modal";
import { EditUserModal } from "./edit-user-modal";
import { UserCreditsModal } from "./user-credits-modal";
import { useUserActions } from "@/app/users/use-user-actions";

export default function AdminUsersPage() {
  return (
    <AlertDialogProvider>
      <AdminUsersPageContent />
    </AlertDialogProvider>
  );
}

function AdminUsersPageContent() {
  const [data, setData] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [hasError, setHasError] = useState(false);
  const { toast } = useToast();

  const userActions = useUserActions({
    onDelete: (id: string) => {
      // Remove from local state immediately for better UX
      setData(prev => prev.filter(user => user.id !== id));
      
      // Also refresh from server to ensure consistency
      setTimeout(() => {
        console.log("🔄 Refreshing user data after delete to verify backend consistency");
        handleRefresh();
      }, 1000); // Small delay to allow backend to process
    },
    onEdit: (updatedUser: User) => {
      setData(prev => prev.map(user => 
        user.id === updatedUser.id ? updatedUser : user
      ));
    }
  });

  const loadUsers = async () => {
    try {
      setIsLoading(true);
      setHasError(false);
      const response = await AdminService.getUsers();
      setData(response.users as User[]);
      setRetryCount(0);
    } catch (error) {
      console.error('Users loading failed:', error);
      setData([]);
      setHasError(true);
      
      // Automatic retry logic (max 3 attempts)
      if (retryCount < 3) {
        const retryDelay = Math.pow(2, retryCount) * 1000; // Exponential backoff
        setTimeout(() => {
          setRetryCount(prev => prev + 1);
          loadUsers();
        }, retryDelay);
        
        toast({
          title: "Connection Issue",
          description: `Retrying in ${retryDelay / 1000} seconds... (Attempt ${retryCount + 1}/3)`,
          variant: "destructive",
        });
      } else {
        toast({
          title: "Failed to Load Users",
          description: error instanceof Error ? error.message : "Could not connect to the server. Please check your connection and try refreshing.",
          variant: "destructive",
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setIsRefreshing(true);
      setRetryCount(0); // Reset retry count on manual refresh
      const response = await AdminService.getUsers();
      setData(response.users as User[]);
      setHasError(false);
      toast({
        title: "Success",
        description: "User data refreshed successfully.",
      });
    } catch (error) {
      setHasError(true);
      toast({
        title: "Error refreshing data",
        description: error instanceof Error ? error.message : "Could not refresh data.",
        variant: "destructive",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleCreateSuccess = () => {
    setShowCreateModal(false);
    loadUsers(); // Refresh the list
    toast({
      title: "Success",
      description: "User created successfully.",
    });
  };

  useEffect(() => {
    loadUsers();
  }, []);

  if (isLoading) {
    return (
       <div className="flex flex-col gap-8">
        <PageHeader
          title="User Management"
          description="View, create, and manage all system users."
        />
        <div className="rounded-lg border bg-card p-4 space-y-4">
            <Skeleton className="h-10 w-1/3" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
        </div>
       </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="User Management"
        description="View, create, and manage all system users and their permissions."
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button onClick={() => setShowCreateModal(true)} className="gap-2">
              <UserPlus className="h-4 w-4" />
              Create User
            </Button>
          </div>
        }
      />
      {data.length === 0 && hasError ? (
        <div className="flex flex-col items-center justify-center p-8 text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-muted-foreground" />
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Failed to Load Users</h3>
            <p className="text-muted-foreground max-w-md">
              Unable to connect to the server. Please check your connection and try again.
            </p>
          </div>
          <Button onClick={handleRefresh} disabled={isRefreshing} className="gap-2">
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Try Again
          </Button>
        </div>
      ) : data.length === 0 && !isLoading ? (
        <div className="flex flex-col items-center justify-center p-8 text-center space-y-4">
          <Users className="h-12 w-12 text-muted-foreground" />
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">No Users Found</h3>
            <p className="text-muted-foreground max-w-md">
              There are no users in the system yet. Create your first user to get started.
            </p>
          </div>
          <Button onClick={() => setShowCreateModal(true)} className="gap-2">
            <UserPlus className="h-4 w-4" />
            Create First User
          </Button>
        </div>
      ) : (
        <DataTable columns={columns(userActions)} data={data} setData={setData} />
      )}

      <CreateUserModal
        open={showCreateModal}
        onOpenChangeAction={setShowCreateModal}
        onSuccessAction={handleCreateSuccess}
      />

      <EditUserModal
        open={userActions.editModalOpen}
        onOpenChangeAction={userActions.setEditModalOpen}
        user={userActions.selectedUser}
        onSuccessAction={userActions.handleEditSuccess}
      />

      <UserCreditsModal
        open={userActions.creditsModalOpen}
        onOpenChangeAction={userActions.setCreditsModalOpen}
        user={userActions.selectedUser}
      />
    </div>
  );
} 
