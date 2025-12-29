"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import { 
  Search, 
  Filter, 
  X, 
  Calendar as CalendarIcon,
  RotateCcw,
  Download 
} from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";

export interface ActivityLogFilterState {
  search: string;
  userFilter: string | null;
  actionFilter: string | null;
  resourceFilter: string | null;
  statusFilter: string | null;
  startDate: Date | null;
  endDate: Date | null;
}

interface ActivityLogFilterBarProps {
  filters: ActivityLogFilterState;
  onFiltersChangeAction: (filters: ActivityLogFilterState) => void;
  onClearFiltersAction: () => void;
  onExportAction: () => void;
  activeFilterCount: number;
}

export function ActivityLogFilterBar({
  filters,
  onFiltersChangeAction,
  onClearFiltersAction,
  onExportAction,
  activeFilterCount,
}: ActivityLogFilterBarProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const updateFilter = (key: keyof ActivityLogFilterState, value: any) => {
    onFiltersChangeAction({
      ...filters,
      [key]: value,
    });
  };

  return (
    <Card className="mb-6">
      <CardContent className="p-4 space-y-4">
        {/* Always visible: Search and quick filters */}
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
          {/* Search Input */}
          <div className="relative flex-1 min-w-[300px]">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by user, action, or details..."
              value={filters.search}
              onChange={(e) => updateFilter("search", e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Quick Status Filter */}
          <Select
            value={filters.statusFilter || "all"}
            onValueChange={(value) => updateFilter("statusFilter", value === "all" ? null : value)}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="success">Success</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="warning">Warning</SelectItem>
            </SelectContent>
          </Select>

          {/* Advanced Filters Toggle */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="gap-2"
            >
              <Filter className="h-4 w-4" />
              Advanced
              {activeFilterCount > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs">
                  {activeFilterCount}
                </Badge>
              )}
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={onExportAction}
              className="gap-2"
            >
              <Download className="h-4 w-4" />
              Export
            </Button>

            {activeFilterCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClearFiltersAction}
                className="gap-2 text-muted-foreground hover:text-foreground"
              >
                <RotateCcw className="h-4 w-4" />
                Clear
              </Button>
            )}
          </div>
        </div>

        {/* Expanded Advanced Filters */}
        {isExpanded && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t">
            {/* Action Type Filter */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Action Type</Label>
              <Select
                value={filters.actionFilter || "all"}
                onValueChange={(value) => updateFilter("actionFilter", value === "all" ? null : value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All Actions" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Actions</SelectItem>
                  <SelectItem value="login">Login</SelectItem>
                  <SelectItem value="logout">Logout</SelectItem>
                  <SelectItem value="upload">Upload Resume</SelectItem>
                  <SelectItem value="analyze">Analyze Resume</SelectItem>
                  <SelectItem value="delete">Delete</SelectItem>
                  <SelectItem value="update">Update</SelectItem>
                  <SelectItem value="create">Create</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Resource Type Filter */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Resource Type</Label>
              <Select
                value={filters.resourceFilter || "all"}
                onValueChange={(value) => updateFilter("resourceFilter", value === "all" ? null : value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All Resources" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Resources</SelectItem>
                  <SelectItem value="resume">Resume</SelectItem>
                  <SelectItem value="user">User</SelectItem>
                  <SelectItem value="legal_query">Legal Query</SelectItem>
                  <SelectItem value="system">System</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Date Range Filter */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Date Range</Label>
              <div className="grid grid-cols-2 gap-2">
                {/* Start Date */}
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        "justify-start text-left font-normal",
                        !filters.startDate && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {filters.startDate ? (
                        format(filters.startDate, "MMM dd")
                      ) : (
                        <span>From</span>
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={filters.startDate || undefined}
                      onSelect={(date) => updateFilter("startDate", date)}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>

                {/* End Date */}
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        "justify-start text-left font-normal",
                        !filters.endDate && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {filters.endDate ? (
                        format(filters.endDate, "MMM dd")
                      ) : (
                        <span>To</span>
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={filters.endDate || undefined}
                      onSelect={(date) => updateFilter("endDate", date)}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>
            </div>

            {/* User Filter */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">User Filter</Label>
              <Input
                placeholder="Filter by user..."
                value={filters.userFilter || ""}
                onChange={(e) => updateFilter("userFilter", e.target.value || null)}
              />
            </div>
          </div>
        )}

        {/* Active Filters Summary */}
        {activeFilterCount > 0 && (
          <div className="flex flex-wrap gap-2 pt-2 border-t">
            <span className="text-sm text-muted-foreground">Active filters:</span>
            
            {filters.search && (
              <Badge variant="secondary" className="gap-1">
                Search: "{filters.search.substring(0, 20)}..."
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => updateFilter("search", "")}
                />
              </Badge>
            )}
            
            {filters.statusFilter && (
              <Badge variant="secondary" className="gap-1">
                Status: {filters.statusFilter}
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => updateFilter("statusFilter", null)}
                />
              </Badge>
            )}
            
            {filters.actionFilter && (
              <Badge variant="secondary" className="gap-1">
                Action: {filters.actionFilter}
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => updateFilter("actionFilter", null)}
                />
              </Badge>
            )}
            
            {filters.resourceFilter && (
              <Badge variant="secondary" className="gap-1">
                Resource: {filters.resourceFilter}
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => updateFilter("resourceFilter", null)}
                />
              </Badge>
            )}
            
            {filters.startDate && (
              <Badge variant="secondary" className="gap-1">
                From: {format(filters.startDate, "MMM dd, yyyy")}
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => updateFilter("startDate", null)}
                />
              </Badge>
            )}
            
            {filters.endDate && (
              <Badge variant="secondary" className="gap-1">
                To: {format(filters.endDate, "MMM dd, yyyy")}
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => updateFilter("endDate", null)}
                />
              </Badge>
            )}
            
            {filters.userFilter && (
              <Badge variant="secondary" className="gap-1">
                User: {filters.userFilter}
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => updateFilter("userFilter", null)}
                />
              </Badge>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
