import { cn } from "@/lib/utils";

type PageHeaderProps = {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
  badge?: React.ReactNode;
};

export default function PageHeader({
  title,
  description,
  actions,
  className,
  badge,
}: PageHeaderProps) {
  return (
    <div className={cn("pb-6 border-b mb-6", className)}>
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
              {title}
            </h1>
            {badge && badge}
          </div>
          {description && (
            <p className="text-muted-foreground text-base leading-relaxed max-w-3xl">
              {description}
            </p>
          )}
        </div>
        {actions && (
          <div className="flex items-center gap-2 mt-1">
            {actions}
          </div>
        )}
      </div>
    </div>
  );
}
