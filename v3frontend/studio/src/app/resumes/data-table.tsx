"use client";

import * as React from "react";
import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
  VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SlidersHorizontal, PlusCircle, X } from "lucide-react";
import { DataTableFacetedFilter } from "./faceted-filter";
import { Resume, ResumeStatus } from "@/types";
import { DateRangePicker } from "@/components/date-range-picker";
import { DateRange } from "react-day-picker";

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  updateDataAction: React.Dispatch<React.SetStateAction<TData[]>>
}

const statuses: { value: string, label: string }[] = [
    { value: "pending", label: "Pending" },
    { value: "processing", label: "Processing" },
    { value: "completed", label: "Completed" },
    { value: "failed", label: "Failed" },
    // Legacy statuses for backward compatibility
    { value: "Pending", label: "Pending" },
    { value: "In Review", label: "In Review" },
    { value: "Approved", label: "Approved" },
    { value: "Rejected", label: "Rejected" },
    { value: "Archived", label: "Archived" },
]

export function DataTable<TData extends Resume, TValue>({
  columns,
  data,
  updateDataAction
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    []
  );
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = React.useState({});
  const [globalFilter, setGlobalFilter] = React.useState('');

  // Memoize the table meta to prevent infinite loops
  const tableMeta = React.useMemo(() => ({
    removeRow: (rowIndex: number) => {
      updateDataAction(prev => prev.filter((_, index) => index !== rowIndex));
    },
    updateRowStatus: (rowIndex: number, status: ResumeStatus) => {
      updateDataAction(prev => prev.map((row, index) => 
          index === rowIndex ? { ...row, status } : row
      ))
    },
  }), [updateDataAction]);

  const table = useReactTable({
    data,
    columns,
    meta: tableMeta,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    onColumnFiltersChange: setColumnFilters,
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    onGlobalFilterChange: setGlobalFilter,
    globalFilterFn: 'auto',
    autoResetPageIndex: false, // Prevent auto page reset that causes infinite loops
    autoResetAll: false, // Prevent all auto resets
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
      globalFilter
    },
  });

  // Memoize the name column reference to prevent infinite loops
  const nameColumn = React.useMemo(() => table.getColumn('name'), [table]);

  React.useEffect(() => {
    // We are using a multi-column filter for the search input,
    // so we pass the value to the 'name' column's filter.
    if (nameColumn) {
      nameColumn.setFilterValue(globalFilter);
    }
  }, [globalFilter, nameColumn]); // Use memoized column reference

  const isFiltered = table.getState().columnFilters.length > 0 || globalFilter.length > 0;
  
  // Memoize the onDateChange callback to prevent infinite loops in DateRangePicker
  const onDateChange = React.useCallback((dateRange: DateRange | undefined) => {
    if (dateRange) {
      table.getColumn("date")?.setFilterValue([dateRange.from, dateRange.to]);
    } else {
      table.getColumn("date")?.setFilterValue(undefined);
    }
  }, [table]);

  const resetFilters = React.useCallback(() => {
    table.resetColumnFilters();
    setGlobalFilter('');
  }, [table]);

  return (
    <div className="rounded-lg border bg-card">
      <div className="flex items-center p-4 gap-2 flex-wrap">
        <Input
          placeholder="Filter by name, email, or keywords..."
          value={globalFilter}
          onChange={(event) => setGlobalFilter(event.target.value)}
          className="max-w-xs"
        />
        {table.getColumn("status") && (
          <DataTableFacetedFilter
            column={table.getColumn("status")}
            title="Status"
            options={statuses}
          />
        )}
        <DateRangePicker onChangeAction={onDateChange} />
         {isFiltered && (
          <Button
            variant="ghost"
            onClick={resetFilters}
            className="h-8 px-2 lg:px-3"
          >
            Reset
            <X className="ml-2 h-4 w-4" />
          </Button>
        )}
        <div className="flex-grow" />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="ml-auto">
              <SlidersHorizontal className="mr-2 h-4 w-4" />
              View
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {table
              .getAllColumns()
              .filter((column) => column.getCanHide())
              .map((column) => {
                return (
                  <DropdownMenuCheckboxItem
                    key={column.id}
                    className="capitalize"
                    checked={column.getIsVisible()}
                    onCheckedChange={(value) =>
                      column.toggleVisibility(!!value)
                    }
                  >
                    {column.id}
                  </DropdownMenuCheckboxItem>
                );
              })}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <Table className="data-table-enhanced">
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id} className="table-header-enhanced">
              {headerGroup.headers.map((header) => {
                return (
                  <TableHead key={header.id} className="h-12 px-4 text-left font-medium">
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </TableHead>
                );
              })}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows?.length ? (
            table.getRowModel().rows.map((row) => (
              <TableRow
                key={row.id}
                data-state={row.getIsSelected() && "selected"}
                className="table-row-enhanced"
              >
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id} className="px-4 py-3">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow className="table-row-enhanced">
              <TableCell colSpan={columns.length} className="h-24 text-center px-4 py-3">
                No results found.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
      <div className="flex items-center justify-end space-x-2 p-4">
        <div className="flex-1 text-sm text-muted-foreground">
          {table.getFilteredSelectedRowModel().rows.length} of{" "}
          {table.getFilteredRowModel().rows.length} row(s) selected.
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
