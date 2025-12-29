
"use client";

import { ColumnDef, HeaderContext } from "@tanstack/react-table";
import { User } from "@/types";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { MoreHorizontal, Trash2, Edit, CreditCard, RotateCcw } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useUserActions } from "./use-user-actions";
import React from "react";

const SelectAllHeader = ({ table }: HeaderContext<User, unknown>) => {
    const handleCheckedChange = React.useCallback((value: boolean | 'indeterminate') => {
        table.toggleAllPageRowsSelected(!!value);
    }, [table]);

    return (
        <Checkbox
            checked={
                table.getIsAllPageRowsSelected() ||
                (table.getIsSomePageRowsSelected() && "indeterminate")
            }
            onCheckedChange={handleCheckedChange}
            aria-label="Select all"
        />
    );
};

export const columns = (userActions: ReturnType<typeof useUserActions>): ColumnDef<User>[] => [
  {
    id: "select",
    header: SelectAllHeader,
    cell: ({ row }) => {
       const handleCheckedChange = React.useCallback((value: boolean | 'indeterminate') => {
            row.toggleSelected(!!value)
        },[row]);

      return (
          <Checkbox
            checked={row.getIsSelected()}
            onCheckedChange={handleCheckedChange}
            aria-label="Select row"
          />
      )
    },
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => {
        const user = row.original;
        return (
            <div className="flex items-center gap-3">
                <Avatar>
                    <AvatarImage 
                        src={`https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(user.name)}&backgroundColor=c0392b,e74c3c,9b59b6,8e44ad,2980b9,3498db,1abc9c,16a085,27ae60,2ecc71,f1c40f,f39c12,e67e22,d35400,95a5a6,7f8c8d`}
                        alt={`Avatar for ${user.name}`}
                        onError={(e) => {
                            // Fallback to initials if external service fails
                            e.currentTarget.style.display = 'none';
                        }}
                    />
                    <AvatarFallback className="bg-primary/10 text-primary font-medium">
                        {user.name.charAt(0).toUpperCase()}
                    </AvatarFallback>
                </Avatar>
                <div>
                    <div className="font-medium">{user.name}</div>
                    <div className="text-sm text-muted-foreground">{user.email}</div>
                </div>
            </div>
        )
    }
  },
  {
    accessorKey: "role",
    header: "Role",
    cell: ({ row }) => {
        const role = row.getValue("role") as string;
        return <Badge variant="outline">{role}</Badge>
    }
  },
  {
    accessorKey: "access_type",
    header: "Access Type",
    cell: ({ row }) => {
        const accessType = row.original.access_type || 'user';
        return (
          <Badge variant={accessType === 'admin' ? 'default' : 'secondary'}>
            {accessType === 'admin' ? 'Admin' : 'User'}
          </Badge>
        );
    }
  },
  {
    accessorKey: "is_trial",
    header: "Status",
    cell: ({ row }) => {
        const isTrial = row.original.is_trial;
        return (
          <Badge variant={isTrial ? 'outline' : 'default'}>
            {isTrial ? 'Trial' : 'Paid'}
          </Badge>
        );
    }
  },
  {
    accessorKey: "trial_info",
    header: "Usage",
    cell: ({ row }) => {
        const trialInfo = row.original.trial_info;
        if (!trialInfo) return <span className="text-muted-foreground">-</span>;
        
        return (
          <div className="text-sm">
            <div>Resumes: {trialInfo.used_resumes}/{trialInfo.resume_limit}</div>
            <div>Legal: {trialInfo.used_legal}/{trialInfo.legal_limit}</div>
          </div>
        );
    }
  },
  {
    accessorKey: "plan",
    header: "Plan",
  },
  {
    accessorKey: "lastSeen",
    header: "Last Seen",
  },
  {
    accessorKey: "status",
    header: "User Status",
    cell: ({ row }) => {
        const user = row.original;
        // Check multiple possible status fields from backend
        const status = user.status || (user.active === false ? 'inactive' : 'active') || (user.is_active === false ? 'inactive' : 'active') || 'active';
        
        const isActive = status === 'active';
        return (
          <Badge variant={isActive ? 'default' : 'destructive'}>
            {isActive ? 'Active' : 'Deactivated'}
          </Badge>
        );
    }
  },
  {
    id: "actions",
    cell: function Actions({ row, table }) {
      const user = row.original;
      const isTrialUser = user.is_trial;

      return (
        <div className="text-right">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuItem 
              className="flex items-center gap-2 cursor-pointer"
              onClick={() => userActions.handleEdit(user)}
            >
                <Edit className="h-4 w-4" />
                Edit User
            </DropdownMenuItem>
            <DropdownMenuItem 
              className="flex items-center gap-2 cursor-pointer"
              onClick={() => userActions.handleViewCredits(user)}
            >
                <CreditCard className="h-4 w-4" />
                View Credits
            </DropdownMenuItem>
            {isTrialUser && (
              <DropdownMenuItem 
                className="flex items-center gap-2 cursor-pointer"
                onClick={() => userActions.handleResetTrial(user.user_id || user.id)}
              >
                  <RotateCcw className="h-4 w-4" />
                  Reset Trial
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem 
              className="flex items-center gap-2 text-destructive focus:text-destructive cursor-pointer"
              onClick={() => userActions.handleDelete(user.user_id || user.id)}
            >
                <Trash2 className="h-4 w-4"/>
                Deactivate User
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        </div>
      );
    },
  },
];
