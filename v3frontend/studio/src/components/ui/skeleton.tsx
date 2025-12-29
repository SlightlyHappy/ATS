import { cn } from "@/lib/utils"

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted/50", className)}
      {...props}
    />
  )
}

// Specialized skeleton components for common UI patterns

function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {/* Table header */}
      <div className="flex space-x-4">
        <Skeleton className="h-4 w-[100px]" />
        <Skeleton className="h-4 w-[150px]" />
        <Skeleton className="h-4 w-[120px]" />
        <Skeleton className="h-4 w-[80px]" />
      </div>
      
      {/* Table rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex space-x-4">
          <Skeleton className="h-3 w-[100px]" />
          <Skeleton className="h-3 w-[150px]" />
          <Skeleton className="h-3 w-[120px]" />
          <Skeleton className="h-3 w-[80px]" />
        </div>
      ))}
    </div>
  )
}

function CardSkeleton() {
  return (
    <div className="border border-border rounded-lg p-6 space-y-4">
      <div className="flex items-center space-x-3">
        <Skeleton className="h-10 w-10 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-[200px]" />
          <Skeleton className="h-3 w-[150px]" />
        </div>
      </div>
      <Skeleton className="h-20 w-full" />
      <div className="flex space-x-2">
        <Skeleton className="h-8 w-16" />
        <Skeleton className="h-8 w-20" />
      </div>
    </div>
  )
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-[300px]" />
        <Skeleton className="h-4 w-[200px]" />
      </div>
      
      {/* Stats cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="border border-border rounded-lg p-6">
            <div className="flex items-center space-x-2">
              <Skeleton className="h-4 w-4" />
              <Skeleton className="h-4 w-[100px]" />
            </div>
            <Skeleton className="h-8 w-[80px] mt-3" />
            <Skeleton className="h-3 w-[60px] mt-2" />
          </div>
        ))}
      </div>
      
      {/* Chart area */}
      <div className="border border-border rounded-lg p-6">
        <div className="space-y-3">
          <Skeleton className="h-6 w-[200px]" />
          <Skeleton className="h-[300px] w-full" />
        </div>
      </div>
      
      {/* Table */}
      <div className="border border-border rounded-lg p-6">
        <Skeleton className="h-6 w-[150px] mb-4" />
        <TableSkeleton rows={8} />
      </div>
    </div>
  )
}

function FormSkeleton() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Skeleton className="h-4 w-[100px]" />
        <Skeleton className="h-10 w-full" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-4 w-[120px]" />
        <Skeleton className="h-10 w-full" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-4 w-[80px]" />
        <Skeleton className="h-20 w-full" />
      </div>
      <div className="flex space-x-4">
        <Skeleton className="h-10 w-[100px]" />
        <Skeleton className="h-10 w-[80px]" />
      </div>
    </div>
  )
}

function ProfileSkeleton() {
  return (
    <div className="space-y-6">
      {/* Profile header */}
      <div className="flex items-center space-x-6">
        <Skeleton className="h-24 w-24 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-6 w-[200px]" />
          <Skeleton className="h-4 w-[150px]" />
          <Skeleton className="h-4 w-[100px]" />
        </div>
      </div>
      
      {/* Form sections */}
      <div className="grid gap-6 md:grid-cols-2">
        <div className="space-y-4">
          <Skeleton className="h-5 w-[120px]" />
          <FormSkeleton />
        </div>
        <div className="space-y-4">
          <Skeleton className="h-5 w-[140px]" />
          <FormSkeleton />
        </div>
      </div>
    </div>
  )
}

function ResumeSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <Skeleton className="h-5 w-[200px]" />
          <Skeleton className="h-3 w-[150px]" />
        </div>
        <Skeleton className="h-6 w-16" />
      </div>
      
      <div className="border border-border rounded-lg p-4">
        <div className="grid gap-4 md:grid-cols-3">
          <div className="space-y-2">
            <Skeleton className="h-4 w-[80px]" />
            <Skeleton className="h-8 w-[60px]" />
          </div>
          <div className="space-y-2">
            <Skeleton className="h-4 w-[100px]" />
            <Skeleton className="h-8 w-[80px]" />
          </div>
          <div className="space-y-2">
            <Skeleton className="h-4 w-[90px]" />
            <Skeleton className="h-8 w-[70px]" />
          </div>
        </div>
        
        <div className="mt-4 space-y-2">
          <Skeleton className="h-4 w-[120px]" />
          <div className="space-y-1">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-[80%]" />
            <Skeleton className="h-3 w-[60%]" />
          </div>
        </div>
      </div>
    </div>
  )
}

export { 
  Skeleton, 
  TableSkeleton, 
  CardSkeleton, 
  DashboardSkeleton, 
  FormSkeleton, 
  ProfileSkeleton, 
  ResumeSkeleton 
}
