'use client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip, Legend } from "recharts";
import { Target, TrendingUp, Users, AlertTriangle } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import React, { useState, useEffect } from 'react';
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

// From your endpoints.md file for GET /api/admin/hot-leads
type HotLead = {
  user_id: string; // This would be the UUID
  email: string;
  lead_score: number;
  qualification_status: 'hot' | 'qualified' | 'new';
};

type PaymentTransaction = {
    razorpay_payment_id: string;
    user_id: string; // This is a UUID, might need a join to get email
    amount: number;
    status: string;
    processed_at: string;
};

const forecastData = [
  { name: 'Q3 \'23', actual: 1.2, forecast: 1.3 },
  { name: 'Q4 \'23', actual: 1.5, forecast: 1.45 },
  { name: 'Q1 \'24', actual: 1.8, forecast: 1.7 },
  { name: 'Q2 \'24', actual: 2.1, forecast: 2.0 },
  { name: 'Q3 \'24', forecast: 2.4 },
  { name: 'Q4 \'24', forecast: 2.7 },
];


export default function SalesIntelligencePage() {
    const [hotLeads, setHotLeads] = useState<HotLead[]>([]);
    const [paymentHistory, setPaymentHistory] = useState<PaymentTransaction[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchSalesData() {
            setIsLoading(true);
            setError(null);
            try {
                // Fetch admin sales intelligence data
                const [hotLeadsRes, salesAnalyticsRes] = await Promise.all([
                    fetch('/api/admin/hot-leads'),
                    fetch('/api/admin/sales-intelligence')
                ]);

                if (!hotLeadsRes.ok) {
                    const errorData = await hotLeadsRes.json();
                    throw new Error(errorData.message || 'Failed to fetch hot leads.');
                }
                 if (!salesAnalyticsRes.ok) {
                    const errorData = await salesAnalyticsRes.json();
                    throw new Error(errorData.message || 'Failed to fetch sales analytics.');
                }

                const hotLeadsData = await hotLeadsRes.json();
                const salesAnalyticsData = await salesAnalyticsRes.json();

                setHotLeads(hotLeadsData.qualified_leads || []);
                setPaymentHistory(salesAnalyticsData.payment_analytics || []);

            } catch (err: any) {
                setError(err.message);
                 // Set mock data on error for UI resilience
                setHotLeads([
                    { user_id: 'uuid-hl-1', email: 'lead1@example.com', lead_score: 92, qualification_status: 'hot' },
                    { user_id: 'uuid-hl-2', email: 'lead2@example.com', lead_score: 85, qualification_status: 'qualified' },
                ]);
                 setPaymentHistory([
                    { razorpay_payment_id: 'pay_1', user_id: 'user1@corp.com', amount: 30000, status: 'successful', processed_at: '2023-10-28' },
                    { razorpay_payment_id: 'pay_2', user_id: 'user2@enterprise.com', amount: 65000, status: 'successful', processed_at: '2023-10-27' },
                    { razorpay_payment_id: 'pay_3', user_id: 'user3@startup.com', amount: 4000, status: 'failed', processed_at: '2023-10-26' },
                    { razorpay_payment_id: 'pay_4', user_id: 'user4@firm.com', amount: 30000, status: 'successful', processed_at: '2023-10-25' },
                ]);
            } finally {
                setIsLoading(false);
            }
        }
        fetchSalesData();
    }, []);

  return (
    <div className="flex flex-col gap-6">
       {error && (
        <Alert variant="destructive">
          <AlertTitle>Could not load sales data</AlertTitle>
          <AlertDescription>{error} Displaying sample data instead.</AlertDescription>
        </Alert>
      )}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2">
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Target /> Hot Leads</CardTitle>
            <CardDescription>Users with high engagement or near trial exhaustion.</CardDescription>
          </CardHeader>
          <CardContent>
             <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>User</TableHead>
                        <TableHead>Lead Score</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Action</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {isLoading && Array.from({length: 2}).map((_, i) => (
                        <TableRow key={i}>
                            <TableCell><Skeleton className="h-5 w-32"/></TableCell>
                            <TableCell><Skeleton className="h-5 w-12"/></TableCell>
                            <TableCell><Skeleton className="h-6 w-20"/></TableCell>
                            <TableCell><Skeleton className="h-8 w-24"/></TableCell>
                        </TableRow>
                    ))}
                    {!isLoading && hotLeads.map(lead => (
                        <TableRow key={lead.user_id}>
                            <TableCell className="font-medium">{lead.email}</TableCell>
                            <TableCell className="font-mono">{lead.lead_score}</TableCell>
                            <TableCell><Badge variant={lead.qualification_status === 'hot' ? 'destructive' : 'default'}>{lead.qualification_status}</Badge></TableCell>
                            <TableCell><Button size="sm">Contact</Button></TableCell>
                        </TableRow>
                    ))}
                    {!isLoading && !hotLeads.length && !error && (
                        <TableRow>
                            <TableCell colSpan={4} className="text-center">No hot leads found.</TableCell>
                        </TableRow>
                    )}
                </TableBody>
             </Table>
          </CardContent>
        </Card>

        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><TrendingUp /> Revenue Analytics</CardTitle>
            <CardDescription>MRR forecast vs. actual (in Lakhs).</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={forecastData}>
                <XAxis dataKey="name" />
                <YAxis unit="L" />
                <Tooltip formatter={(value, name) => [`₹${value}L`, typeof name === 'string' ? name.charAt(0).toUpperCase() + name.slice(1) : String(name)]} />
                <Legend />
                <Bar dataKey="actual" fill="hsl(var(--primary))" name="Actual" />
                <Bar dataKey="forecast" fill="hsl(var(--secondary))" name="Forecast" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

      </div>

       <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Payment History</CardTitle>
            <CardDescription>A filterable log of all payment transactions on the platform.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Transaction ID</TableHead>
                        <TableHead>User ID</TableHead>
                        <TableHead>Amount (INR)</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Date</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {isLoading && Array.from({length: 4}).map((_, i) => (
                         <TableRow key={i}>
                            <TableCell><Skeleton className="h-5 w-24"/></TableCell>
                            <TableCell><Skeleton className="h-5 w-32"/></TableCell>
                            <TableCell><Skeleton className="h-5 w-16"/></TableCell>
                            <TableCell><Skeleton className="h-6 w-24"/></TableCell>
                            <TableCell><Skeleton className="h-5 w-20"/></TableCell>
                        </TableRow>
                    ))}
                    {!isLoading && paymentHistory.map(payment => (
                        <TableRow key={payment.razorpay_payment_id}>
                            <TableCell className="font-mono">{payment.razorpay_payment_id}</TableCell>
                            <TableCell className="text-sm text-muted-foreground">{payment.user_id}</TableCell>
                            <TableCell className="font-mono">{(payment.amount / 100).toLocaleString('en-IN')}</TableCell>
                            <TableCell><Badge variant={payment.status === 'successful' ? 'secondary' : 'destructive'}>{payment.status}</Badge></TableCell>
                            <TableCell>{new Date(payment.processed_at).toLocaleDateString()}</TableCell>
                        </TableRow>
                    ))}
                     {!isLoading && !paymentHistory.length && !error && (
                        <TableRow>
                            <TableCell colSpan={5} className="text-center">No payment history found.</TableCell>
                        </TableRow>
                    )}
                </TableBody>
            </Table>
          </CardContent>
        </Card>
    </div>
  );
}
