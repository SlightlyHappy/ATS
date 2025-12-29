'use client';

import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MoreHorizontal, Search, UserPlus, AlertTriangle, Trash2 } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

// As per your `endpoints.md` for GET /api/admin/users
type User = {
  id: string; // uuid
  email: string;
  full_name: string;
  access_type: string; // 'trial', 'full', 'enterprise'
  trial_usage: number;
  created_at: string;
};

const getPlanBadge = (plan: string) => {
    switch (plan) {
        case 'trial': return <Badge variant="outline">Trial</Badge>;
        case 'full': return <Badge variant="default">Full</Badge>;
        case 'enterprise': return <Badge variant="secondary" className="bg-purple-100 text-purple-800">Enterprise</Badge>;
        default: return <Badge variant="outline">{plan}</Badge>;
    }
}


export default function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddUserDialogOpen, setIsAddUserDialogOpen] = useState(false);
  const { toast } = useToast();

  async function fetchUsers() {
    setIsLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('admin_auth_token');
      if (!token) throw new Error('Admin authentication token not found.');
      const response = await fetch('https://hrtoolsbackend-production.up.railway.app/api/admin/users', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to fetch users.');
      }
      const data = await response.json();
      setUsers(data.users || []);
    } catch (err: any) {
      setError(err.message);
      console.error(err);
      // Fallback to mock data on error for UI resilience
      setUsers([
        { id: 'uuid-1', email: 'john.doe@example.com', full_name: 'John Doe', access_type: 'trial', trial_usage: 25, created_at: '2023-10-26' },
        { id: 'uuid-2', email: 'jane.smith@example.com', full_name: 'Jane Smith', access_type: 'full', trial_usage: 100, created_at: '2023-10-25' },
        { id: 'uuid-3', email: 'enterprise@corp.com', full_name: 'Enterprise Corp', access_type: 'enterprise', trial_usage: 0, created_at: '2023-10-24' },
      ]);
    } finally {
      setIsLoading(false);
    }
  }
  
  useEffect(() => {
    fetchUsers();
  }, []);

  const handleDeleteUser = async (userId: string) => {
    try {
        const token = localStorage.getItem('admin_auth_token');
        if (!token) throw new Error("Admin token not found");

        const response = await fetch(`https://hrtoolsbackend-production.up.railway.app/api/admin/users/${userId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        if(!response.ok || !data.success) {
            throw new Error(data.message || 'Failed to delete user.');
        }
        toast({ title: "Success", description: "User deleted successfully." });
        fetchUsers(); // Refresh list
    } catch (err: any) {
        toast({ title: "Error", description: err.message, variant: "destructive" });
    }
  };


  const renderTableContent = () => {
    if (isLoading) {
      return Array.from({ length: 5 }).map((_, i) => (
        <TableRow key={i}>
          <TableCell>
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-4 w-32 mt-1" />
          </TableCell>
          <TableCell><Skeleton className="h-6 w-20" /></TableCell>
          <TableCell className="text-right"><Skeleton className="h-5 w-12 ml-auto" /></TableCell>
          <TableCell><Skeleton className="h-5 w-24" /></TableCell>
          <TableCell><Skeleton className="h-8 w-8" /></TableCell>
        </TableRow>
      ));
    }

    if (error) {
        return (
            <TableRow>
                <TableCell colSpan={5}>
                    <Alert variant="destructive">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertTitle>Error</AlertTitle>
                        <AlertDescription>{error} Using mock data instead.</AlertDescription>
                    </Alert>
                </TableCell>
            </TableRow>
        );
    }
    
    if (users.length === 0) {
        return (
             <TableRow>
                <TableCell colSpan={5} className="text-center h-24">
                    No users found.
                </TableCell>
            </TableRow>
        )
    }

    return users.map((user) => (
        <TableRow key={user.id}>
        <TableCell>
            <div className="font-medium">{user.full_name}</div>
            <div className="text-sm text-muted-foreground">{user.email}</div>
        </TableCell>
        <TableCell>{getPlanBadge(user.access_type)}</TableCell>
        <TableCell className="text-right font-mono">{user.trial_usage}</TableCell>
        <TableCell>{new Date(user.created_at).toLocaleDateString()}</TableCell>
        <TableCell>
            <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button aria-haspopup="true" size="icon" variant="ghost">
                <MoreHorizontal className="h-4 w-4" />
                <span className="sr-only">Toggle menu</span>
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
                <DropdownMenuLabel>Actions</DropdownMenuLabel>
                <DropdownMenuItem>Edit User</DropdownMenuItem>
                <DropdownMenuItem>Manage Credits</DropdownMenuItem>
                <DropdownMenuItem>View Analytics</DropdownMenuItem>
                <DropdownMenuSeparator />
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <DropdownMenuItem
                      className="text-red-500"
                      onSelect={(e) => e.preventDefault()}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete User
                    </DropdownMenuItem>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                      <AlertDialogDescription>
                        This action cannot be undone. This will permanently delete the user and all their associated data.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction onClick={() => handleDeleteUser(user.id)}>
                        Continue
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
            </DropdownMenuContent>
            </DropdownMenu>
        </TableCell>
        </TableRow>
    ));
  }

  return (
    <>
    <AddUserDialog 
        isOpen={isAddUserDialogOpen} 
        onOpenChange={setIsAddUserDialogOpen} 
        onUserAdded={() => {
            setIsAddUserDialogOpen(false);
            fetchUsers();
        }}
    />
    <Card className="shadow-lg">
      <CardHeader>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
                <CardTitle>User Management Hub</CardTitle>
                <CardDescription>Manage users, credits, and permissions.</CardDescription>
            </div>
            <div className="flex gap-2 items-center">
                <div className="relative flex-1">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input placeholder="Search users by name or email..." className="pl-8" />
                </div>
                <Button onClick={() => setIsAddUserDialogOpen(true)}>
                    <UserPlus className="h-4 w-4 mr-2" />
                    Add User
                </Button>
            </div>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User</TableHead>
              <TableHead>Plan</TableHead>
              <TableHead className="text-right">Trial Usage</TableHead>
              <TableHead>Joined</TableHead>
              <TableHead><span className="sr-only">Actions</span></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {renderTableContent()}
          </TableBody>
        </Table>
        <div className="flex items-center justify-end space-x-2 py-4">
            <Button variant="outline" size="sm">Previous</Button>
            <Button variant="outline" size="sm">Next</Button>
        </div>
      </CardContent>
    </Card>
    </>
  );
}


function AddUserDialog({ isOpen, onOpenChange, onUserAdded }: { isOpen: boolean, onOpenChange: (open: boolean) => void, onUserAdded: () => void }) {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string|null>(null);
    const { toast } = useToast();

    const handleCreateUser = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        const formData = new FormData(e.currentTarget);
        const userData = {
          email: formData.get('email'),
          name: formData.get('name'),
          password: formData.get('password'),
          // These fields are from frontendguide.md for user creation
          access_type: 'trial', 
          trial_resume_limit: 100,
          trial_legal_limit: 50,
        };

        try {
            const token = localStorage.getItem('admin_auth_token');
            if (!token) throw new Error("Admin token not found");

            // The docs are slightly inconsistent, but both point to an admin user creation endpoint.
            // Using /api/auth/create-user as it's more specific.
            const response = await fetch('https://hrtoolsbackend-production.up.railway.app/api/auth/create-user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(userData),
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Failed to create user.');
            }
            toast({ title: 'User Created', description: `User ${userData.email} has been created successfully.` });
            onUserAdded();
        } catch(err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onOpenChange}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Create a New User</DialogTitle>
                    <DialogDescription>
                        This will create a new user account and initialize their trial credits.
                    </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateUser} className="space-y-4">
                    {error && <Alert variant="destructive"><AlertTriangle className="h-4 w-4"/><AlertTitle>Error</AlertTitle><AlertDescription>{error}</AlertDescription></Alert>}
                    <div className="space-y-2">
                        <Label htmlFor="name">Full Name</Label>
                        <Input id="name" name="name" required disabled={isLoading} />
                    </div>
                     <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input id="email" name="email" type="email" required disabled={isLoading} />
                    </div>
                     <div className="space-y-2">
                        <Label htmlFor="password">Password</Label>
                        <Input id="password" name="password" type="password" required disabled={isLoading} />
                    </div>
                    <DialogFooter>
                        <DialogClose asChild>
                            <Button type="button" variant="outline" disabled={isLoading}>Cancel</Button>
                        </DialogClose>
                        <Button type="submit" disabled={isLoading}>{isLoading ? "Creating..." : "Create User"}</Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}
