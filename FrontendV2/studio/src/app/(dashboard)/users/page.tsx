
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
import { MoreHorizontal, Search, UserPlus, AlertTriangle } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

// As per your frontendguide.md
type User = {
  user_id: number;
  name: string;
  email: string;
  access_type: string; // 'trial', 'premium', 'enterprise'
  status: 'active' | 'inactive';
  created_at: string;
  trial_resumes_analyzed: number;
  trial_legal_queries: number;
};

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'active': return <Badge className="bg-green-100 text-green-800">Active</Badge>;
    case 'inactive': return <Badge variant="secondary">Inactive</Badge>;
    default: return <Badge variant="outline">{status}</Badge>;
  }
};

const getPlanBadge = (plan: string) => {
    switch (plan) {
        case 'trial': return <Badge variant="outline">Trial</Badge>;
        case 'premium': return <Badge variant="default">Premium</Badge>;
        case 'enterprise': return <Badge variant="secondary" className="bg-purple-100 text-purple-800">Enterprise</Badge>;
        default: return <Badge variant="outline">{plan}</Badge>;
    }
}


export default function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchUsers() {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch('/api/admin/users');
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
        const mockUsers: User[] = [
            { user_id: 1, name: 'John Doe (Mock)', email: 'john.doe@example.com', access_type: 'premium', status: 'active', created_at: '2023-01-15', trial_resumes_analyzed: 100, trial_legal_queries: 10 },
            { user_id: 2, name: 'Jane Smith (Mock)', email: 'jane.smith@example.com', access_type: 'trial', status: 'active', created_at: '2023-08-20', trial_resumes_analyzed: 50, trial_legal_queries: 5 },
        ];
        setUsers(mockUsers)
      } finally {
        setIsLoading(false);
      }
    }
    fetchUsers();
  }, []);


  const renderTableContent = () => {
    if (isLoading) {
      return Array.from({ length: 5 }).map((_, i) => (
        <TableRow key={i}>
          <TableCell>
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-4 w-32 mt-1" />
          </TableCell>
          <TableCell><Skeleton className="h-6 w-16" /></TableCell>
          <TableCell><Skeleton className="h-6 w-20" /></TableCell>
          <TableCell className="text-right"><Skeleton className="h-5 w-12 ml-auto" /></TableCell>
          <TableCell><Skeleton className="h-5 w-20" /></TableCell>
          <TableCell><Skeleton className="h-8 w-8" /></TableCell>
        </TableRow>
      ));
    }

    if (error && users.length === 0) {
        return (
            <TableRow>
                <TableCell colSpan={6}>
                    <Alert variant="destructive">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertTitle>Error</AlertTitle>
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                </TableCell>
            </TableRow>
        );
    }
    
    if (users.length === 0) {
        return (
             <TableRow>
                <TableCell colSpan={6} className="text-center h-24">
                    No users found.
                </TableCell>
            </TableRow>
        )
    }

    return users.map((user) => (
        <TableRow key={user.user_id}>
        <TableCell>
            <div className="font-medium">{user.name}</div>
            <div className="text-sm text-muted-foreground">{user.email}</div>
        </TableCell>
        <TableCell>{getStatusBadge(user.status)}</TableCell>
        <TableCell>{getPlanBadge(user.access_type)}</TableCell>
        <TableCell className="text-right font-mono">{user.trial_resumes_analyzed}/{user.trial_legal_queries}</TableCell>
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
                <DropdownMenuItem className="text-red-500">Suspend User</DropdownMenuItem>
            </DropdownMenuContent>
            </DropdownMenu>
        </TableCell>
        </TableRow>
    ));
  }

  return (
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
                <Button>
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
              <TableHead>Status</TableHead>
              <TableHead>Plan</TableHead>
              <TableHead className="text-right">Usage (Resumes/Legal)</TableHead>
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
  );
}

    
