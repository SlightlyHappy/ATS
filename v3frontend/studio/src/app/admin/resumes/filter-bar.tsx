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
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { 
  Search, 
  Filter, 
  X, 
  Calendar as CalendarIcon,
  RotateCcw 
} from "lucide-react";
import { format } from "date-fns";
import { cn } from "@/lib/utils";

export interface FilterState {
  search: string;
  status: string | null;
  startDate: Date | null;
  endDate: Date | null;
  minScore: number;
  maxScore: number;
}

interface FilterBarProps {
  filters: FilterState;
  onFiltersChangeAction: (filters: FilterState) => void;
  onClearFiltersAction: () => void;
  activeFilterCount: number;
}

export function FilterBar({
  filters,
  onFiltersChangeAction,
  onClearFiltersAction,
  activeFilterCount,
}: FilterBarProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const updateFilter = (key: keyof FilterState, value: any) => {
    onFiltersChangeAction({
      ...filters,
      [key]: value,
    });
  };

  const scoreRange = [filters.minScore, filters.maxScore];

  const handleScoreRangeChange = (values: number[]) => {
    onFiltersChangeAction({
      ...filters,
      minScore: values[0],
      maxScore: values[1],
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
              placeholder="Search by filename, user, or content..."
              value={filters.search}
              onChange={(e) => updateFilter("search", e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Quick Status Filter */}
          <Select
            value={filters.status || "all"}
            onValueChange={(value) => updateFilter("status", value === "all" ? null : value)}
          >
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="processing">Processing</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-4 border-t">
            {/* Date Range Filter */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Upload Date Range</Label>
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

            {/* Score Range Filter */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">Score Range</Label>
              <div className="px-2">
                <Slider
                  value={scoreRange}
                  onValueChange={handleScoreRangeChange}
                  max={100}
                  min={0}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>{filters.minScore}</span>
                  <span>{filters.maxScore}</span>
                </div>
              </div>
              <div className="text-xs text-center text-muted-foreground">
                Showing scores {filters.minScore} - {filters.maxScore}
              </div>
            </div>

            {/* File Type Filter (Future Enhancement) */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">File Type</Label>
              <Select defaultValue="all">
                <SelectTrigger>
                  <SelectValue placeholder="All Types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="pdf">PDF</SelectItem>
                  <SelectItem value="docx">DOCX</SelectItem>
                  <SelectItem value="doc">DOC</SelectItem>
                </SelectContent>
              </Select>
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
            
            {filters.status && (
              <Badge variant="secondary" className="gap-1">
                Status: {filters.status}
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => updateFilter("status", null)}
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
            
            {(filters.minScore > 0 || filters.maxScore < 100) && (
              <Badge variant="secondary" className="gap-1">
                Score: {filters.minScore}-{filters.maxScore}
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => {
                    updateFilter("minScore", 0);
                    updateFilter("maxScore", 100);
                  }}
                />
              </Badge>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
