"use client";

import { useEffect, useState } from "react";
import { fetchUsers } from "@/services/api";
import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { PlusCircle } from "lucide-react";
import { DataTable } from "./data-table";
import { columns } from "./columns";
import Link from "next/link";
import { User } from "@/types";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertDialogProvider } from "@/components/alert-dialog-provider";

export default function UsersPage() {
    const [data, setData] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const { toast } = useToast();

    useEffect(() => {
        async function loadUsers() {
            setIsLoading(true);
            try {
                const users = await fetchUsers();
                setData(users);
            } catch (error) {
                toast({
                    title: "Error fetching users",
                    description: error instanceof Error ? error.message : "Could not connect to the server.",
                    variant: "destructive",
                });
            } finally {
                setIsLoading(false);
            }
        }
        loadUsers();
    }, [toast]);

    if (isLoading) {
        return (
            <div className="flex flex-col gap-8">
                <PageHeader
                    title="User Management"
                    description="Manage team members, roles, and permissions."
                    actions={
                        <Button asChild>
                            <Link href="#">
                                <PlusCircle className="mr-2 h-4 w-4" />
                                Invite User
                            </Link>
                        </Button>
                    }
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
        <AlertDialogProvider>
            <div className="flex flex-col gap-8">
                <PageHeader
                    title="User Management"
                    description="Manage team members, roles, and permissions."
                    actions={
                        <Button asChild>
                            <Link href="#">
                                <PlusCircle className="mr-2 h-4 w-4" />
                                Invite User
                            </Link>
                        </Button>
                    }
                />
                <DataTable columns={columns} data={data} setData={setData} />
            </div>
        </AlertDialogProvider>
    );
}
