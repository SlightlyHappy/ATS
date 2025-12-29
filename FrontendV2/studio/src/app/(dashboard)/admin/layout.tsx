'use client';
import React from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

const adminTabs = [
  { name: 'Overview', href: '/admin' },
  { name: 'User Management', href: '/admin/users' },
  { name: 'System Health', href: '/admin/system-health' },
  { name: 'Sales Intelligence', href: '/admin/sales-intelligence' },
  { name: 'Resume Database', href: '/admin/resumes' },
  { name: 'RAG Testing', href: '/admin/hr-legal-testing' },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();

  // Determine the base path for Tabs.Value
  const basePath = `/admin/${pathname.split('/')[2] || ''}`.replace(/\/$/, '');

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Admin Console</h1>
        <p className="text-muted-foreground">
          Central command for system management and business intelligence.
        </p>
      </div>
      <Tabs value={basePath} className="w-full">
        <TabsList className="grid w-full grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
          {adminTabs.map((tab) => (
            <TabsTrigger 
              key={tab.name} 
              value={tab.href}
              onClick={() => router.push(tab.href)}
              className="cursor-pointer"
            >
              {tab.name}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>
      <div className="mt-4">{children}</div>
    </div>
  );
}
