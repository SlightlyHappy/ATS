"use client"

import * as React from "react"
import { Bar, BarChart, CartesianGrid, XAxis, Pie, PieChart, Cell } from "recharts"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import type { ChartConfig } from "@/components/ui/chart"

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042"];

const chartConfig = {
  score: {
    label: "Score",
  },
  approved: {
    label: "Approved",
    color: "hsl(var(--chart-2))",
  },
  rejected: {
    label: "Rejected",
    color: "hsl(var(--chart-5))",
  },
  pending: {
    label: "Pending",
    color: "hsl(var(--chart-3))",
  },
  'in-review': {
    label: 'In Review',
    color: 'hsl(var(--chart-1))'
  }
} satisfies ChartConfig


export function DashboardCharts({ chartData }: { chartData: any }) {
  // Return empty state if no chart data is available
  if (!chartData || (!chartData.averageScores && !chartData.resumesByStatus)) {
    return (
      <Card className="lg:col-span-3 flex flex-col">
        <CardHeader>
          <CardTitle className="text-base md:text-lg">Resume Analytics</CardTitle>
          <CardDescription className="text-sm">Chart data will appear here when available.</CardDescription>
        </CardHeader>
        <CardContent className="flex-1 flex items-center justify-center">
          <div className="text-center text-muted-foreground">
            <p>No analytics data available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const safeChartData = {
    averageScores: chartData?.averageScores || [],
    resumesByStatus: chartData?.resumesByStatus || [],
  };

  return (
      <Card className="lg:col-span-3 flex flex-col chart-container">
        <CardHeader>
          <CardTitle className="text-lg md:text-xl font-semibold">Resume Analytics</CardTitle>
          <CardDescription className="text-sm text-muted-foreground">An overview of resume scores and statuses.</CardDescription>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col gap-6 md:gap-8">
            <div className="flex-1">
                <h3 className="text-sm font-medium mb-4 text-center text-foreground">Average AI Score by Category</h3>
                <ChartContainer config={chartConfig} className="w-full h-[140px] md:h-[180px]">
                    <BarChart accessibilityLayer data={safeChartData.averageScores} margin={{ top: 20, right: 20, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                        <XAxis
                        dataKey="name"
                        tickLine={false}
                        tickMargin={10}
                        axisLine={false}
                        fontSize={12}
                        />
                        <ChartTooltip
                        cursor={{ fill: 'hsl(var(--muted))' }}
                        content={<ChartTooltipContent indicator="dot" />}
                        />
                        <Bar dataKey="score" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                    </BarChart>
                </ChartContainer>
            </div>
            <div className="flex-1">
                <h3 className="text-sm font-medium mb-4 text-center text-foreground">Resumes by Status</h3>
                <ChartContainer config={chartConfig} className="w-full h-[140px] md:h-[180px]">
                     <PieChart accessibilityLayer>
                        <Pie
                            data={safeChartData.resumesByStatus}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            outerRadius={60}
                            innerRadius={20}
                            dataKey="value"
                            nameKey="name"
                        >
                            {safeChartData.resumesByStatus.map((entry: any, index: number) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <ChartTooltip cursor={false} content={<ChartTooltipContent hideLabel />} />
                    </PieChart>
                </ChartContainer>
            </div>
        </CardContent>
    </Card>
  )
}
