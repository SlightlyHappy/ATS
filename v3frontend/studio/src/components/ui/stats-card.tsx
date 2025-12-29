"use client";

import { Card } from "@/components/ui/card";
import { TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: {
    value: number;
    trend: 'up' | 'down' | 'neutral';
  };
  icon: React.ReactNode;
  description?: string;
  className?: string;
}

export function StatsCard({ 
  title, 
  value, 
  change, 
  icon, 
  description, 
  className 
}: StatsCardProps) {
  return (
    <Card className={cn("stat-card", className)}>
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-3xl font-bold tracking-tight">{value}</p>
          {change && (
            <div className="flex items-center gap-1 text-xs">
              {change.trend === 'up' && <TrendingUp className="h-3 w-3 text-green-500" />}
              {change.trend === 'down' && <TrendingDown className="h-3 w-3 text-red-500" />}
              <span className={cn(
                "font-medium",
                change.trend === 'up' && "text-green-500",
                change.trend === 'down' && "text-red-500",
                change.trend === 'neutral' && "text-muted-foreground"
              )}>
                {change.value > 0 ? '+' : ''}{change.value}%
              </span>
              <span className="text-muted-foreground">from last month</span>
            </div>
          )}
          {description && (
            <p className="text-xs text-muted-foreground">{description}</p>
          )}
        </div>
        <div className="p-3 bg-primary/10 rounded-full">
          {icon}
        </div>
      </div>
    </Card>
  );
}
