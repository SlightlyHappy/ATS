'use client';

import dynamic from 'next/dynamic';

// Dynamic imports for recharts components with type assertions to avoid TypeScript conflicts
// Use @ts-ignore to suppress TypeScript errors for dynamic imports
// @ts-ignore
export const BarChart = dynamic(() => import('recharts').then(mod => mod.BarChart), { 
  ssr: false,
  loading: () => <div className="h-[300px] flex items-center justify-center text-muted-foreground">Loading chart...</div>
});

// @ts-ignore
export const Bar = dynamic(() => import('recharts').then(mod => mod.Bar), { ssr: false });
// @ts-ignore
export const XAxis = dynamic(() => import('recharts').then(mod => mod.XAxis), { ssr: false });
// @ts-ignore
export const YAxis = dynamic(() => import('recharts').then(mod => mod.YAxis), { ssr: false });
// @ts-ignore
export const CartesianGrid = dynamic(() => import('recharts').then(mod => mod.CartesianGrid), { ssr: false });
// @ts-ignore
export const Tooltip = dynamic(() => import('recharts').then(mod => mod.Tooltip), { ssr: false });
// @ts-ignore
export const ResponsiveContainer = dynamic(() => import('recharts').then(mod => mod.ResponsiveContainer), { ssr: false });
// @ts-ignore
export const LineChart = dynamic(() => import('recharts').then(mod => mod.LineChart), { 
  ssr: false,
  loading: () => <div className="h-[300px] flex items-center justify-center text-muted-foreground">Loading chart...</div>
});
// @ts-ignore
export const Line = dynamic(() => import('recharts').then(mod => mod.Line), { ssr: false });
// @ts-ignore
export const AreaChart = dynamic(() => import('recharts').then(mod => mod.AreaChart), { 
  ssr: false,
  loading: () => <div className="h-[300px] flex items-center justify-center text-muted-foreground">Loading chart...</div>
});
// @ts-ignore
export const Area = dynamic(() => import('recharts').then(mod => mod.Area), { ssr: false });
// @ts-ignore
export const PieChart = dynamic(() => import('recharts').then(mod => mod.PieChart), { 
  ssr: false,
  loading: () => <div className="h-[300px] flex items-center justify-center text-muted-foreground">Loading chart...</div>
});
// @ts-ignore
export const Pie = dynamic(() => import('recharts').then(mod => mod.Pie), { ssr: false });
// @ts-ignore
export const Cell = dynamic(() => import('recharts').then(mod => mod.Cell), { ssr: false });
// @ts-ignore
export const Legend = dynamic(() => import('recharts').then(mod => mod.Legend), { ssr: false });

// Additional chart components for analytics
// @ts-ignore
export const ComposedChart = dynamic(() => import('recharts').then(mod => mod.ComposedChart), { 
  ssr: false,
  loading: () => <div className="h-[300px] flex items-center justify-center text-muted-foreground">Loading chart...</div>
});

interface ChartWrapperProps {
  children: React.ReactNode;
  className?: string;
}

export function ChartWrapper({ children, className }: ChartWrapperProps) {
  return (
    <div className={className}>
      {children}
    </div>
  );
}
