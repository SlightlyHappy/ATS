"use client";

import { ColumnDef, Row, HeaderContext } from "@tanstack/react-table";
import { Resume, ResumeStatus } from "@/types";
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
import { MoreHorizontal, ArrowUpDown, Trash2, Archive, Eye } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import Link from "next/link";
import { useResumeActions } from "./use-resume-actions";
import { format } from "date-fns";
import React from "react";

const statusColors: Record<string, "default" | "secondary" | "destructive"> = {
    'Approved': 'default',
    'In Review': 'secondary',
    'Pending': 'secondary',
    'Rejected': 'destructive',
    'Archived': 'secondary',
    'pending': 'secondary',
    'processing': 'secondary', 
    'completed': 'default',
    'failed': 'destructive',
};

const dateFilterFn = (row: Row<Resume>, columnId: string, filterValue: [Date | undefined, Date | undefined]) => {
    const date = new Date(row.getValue(columnId));
    const [start, end] = filterValue;
    if (start && date < start) return false;
    if (end) {
        // Include the whole day
        const dayEnd = new Date(end);
        dayEnd.setDate(dayEnd.getDate() + 1);
        if (date >= dayEnd) return false;
    }
    return true;
};

const multiColumnFilterFn = (row: Row<Resume>, columnId: string, filterValue: string) => {
    const name: string = row.original.name || '';
    const email: string = row.original.email || '';
    const resumeText: string = row.original.resumeText || '';
    const search = filterValue.toLowerCase();

    // The columnId is 'name' but we are filtering on multiple columns
    return name.toLowerCase().includes(search) ||
           email.toLowerCase().includes(search) ||
           resumeText.toLowerCase().includes(search);
}

const SelectAllHeader = React.memo(({ table }: HeaderContext<Resume, unknown>) => {
    // Compute controlled checked state: true, false, or 'indeterminate'
    const allSelected = table.getIsAllPageRowsSelected();
    const someSelected = table.getIsSomePageRowsSelected();
    const checkedState: boolean | 'indeterminate' = allSelected ? true : someSelected ? 'indeterminate' : false;
    
    const handleCheckedChange = React.useCallback((value: boolean) => {
        table.toggleAllPageRowsSelected(value);
    }, [table]);
    
    return (
        <Checkbox
            checked={checkedState}
            onCheckedChange={handleCheckedChange}
            aria-label="Select all"
        />
    );
});

export const columns: ColumnDef<Resume>[] = [
  {
    id: "select",
    header: SelectAllHeader,
    cell: React.memo(({ row }) => {
      const handleCheckedChange = React.useCallback((value: boolean) => {
        row.toggleSelected(value);
      }, [row]);
      
      return (
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={handleCheckedChange}
          aria-label="Select row"
        />
      );
    }),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: "name",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Candidate
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    filterFn: multiColumnFilterFn,
  },
  {
    accessorKey: "status",
    header: ({column}) => {
       return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Status
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({ row }) => {
      // Handle both legacy 'status' field and new 'processing_status' field
      const status = (row.getValue("status") || row.original.processing_status || 'pending') as string;
      return (
        <Badge variant={statusColors[status] || 'secondary'} className="capitalize">
          {status}
        </Badge>
      );
    },
    filterFn: (row, id, value) => {
      return value.includes(row.getValue(id))
    },
  },
  {
    accessorKey: "aiScore",
    header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            AI Score
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
    cell: ({ row }) => {
      const amount = parseFloat(row.getValue("aiScore"));
      return <div className="font-medium text-center">{amount}%</div>;
    },
  },
  {
    accessorKey: "date",
    header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Date
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        );
      },
    cell: ({ row }) => {
        const date = new Date(row.getValue("date"));
        const formatted = format(date, "MM/dd/yyyy");
        return <div>{formatted}</div>
    },
    filterFn: dateFilterFn,
  },
  {
    id: "actions",
    cell: function Actions({ row, table }) {
      const resume = row.original;
       const { handleArchive, handleDelete } = useResumeActions({
        onArchive: (id) => {
          (table.options.meta as any)?.updateRowStatus(row.index, 'Archived');
        },
        onDelete: (id) => {
          (table.options.meta as any)?.removeRow(row.index);
        },
      });

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
            <DropdownMenuItem asChild>
              <Link href={`/resumes/${resume.id}`} className="flex items-center gap-2 cursor-pointer">
                <Eye className="h-4 w-4" />
                View & Analyze
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            {resume.status !== 'Archived' && (
              <DropdownMenuItem 
                className="flex items-center gap-2 cursor-pointer"
                onClick={() => handleArchive(resume.id)}
              >
                  <Archive className="h-4 w-4"/>
                  Archive
              </DropdownMenuItem>
            )}
            <DropdownMenuItem 
              className="flex items-center gap-2 text-destructive focus:text-destructive cursor-pointer"
              onClick={() => handleDelete(resume.id)}
            >
                <Trash2 className="h-4 w-4"/>
                Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        </div>
      );
    },
  },
];
