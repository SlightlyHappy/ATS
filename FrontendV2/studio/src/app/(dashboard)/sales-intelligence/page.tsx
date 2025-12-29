'use client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip, Legend } from "recharts";
import { Target, TrendingUp, Users, AlertTriangle } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";

type ConversionPrediction = {
    name: string; // e.g., month 'Jan'
    rate: number;
}
type RevenueForecast = {
    name: string; // e.g., quarter 'Q3 '23'
    actual: number | null;
    forecast: number;
}
type CustomerLifecycle = {
    name: string;
    value: number;
}

export default function SalesIntelligencePage() {
    const [conversionData, setConversionData] = useState<ConversionPrediction[]>([]);
    const [forecastData, setForecastData] = useState<RevenueForecast[]>([]);
    const [lifecycleData, setLifecycleData] = useState<CustomerLifecycle[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchSalesData() {
            setIsLoading(true);
            setError(null);
            try {
                // Fetch all data in parallel
                // Note: Using placeholder URLs based on docs. Replace with actual URLs.
                const [convRes, forecastRes, lifecycleRes] = await Promise.all([
                    fetch('/api/admin/conversion-predictions'), // Endpoint mentioned in docs
                    fetch('/api/admin/revenue-forecast'), // This endpoint is not in docs, but implied by the page.
                    fetch('/api/admin/sales-intelligence')  // This endpoint can provide lifecycle data
                ]);

                if (!convRes.ok || !forecastRes.ok || !lifecycleRes.ok) {
                    throw new Error('Failed to fetch some sales intelligence data.');
                }

                const convData = await convRes.json();
                const forecastData = await forecastRes.json();
                const salesIntelData = await lifecycleRes.json();

                setConversionData(convData.predictions || []);
                setForecastData(forecastData.forecasts || []);
                setLifecycleData(salesIntelData.lifecycle_distribution || []);

            } catch (err: any) {
                setError(err.message);
                // Set mock data on error so the page doesn't look broken
                setConversionData([
                  { name: 'Jan', rate: 2.5 }, { name: 'Feb', rate: 2.8 }, { name: 'Mar', rate: 3.5 },
                  { name: 'Apr', rate: 3.2 }, { name: 'May', rate: 4.1 }, { name: 'Jun', rate: 4.5 },
                ]);
                setForecastData([
                  { name: 'Q3 \'23', actual: 1.2, forecast: 1.3 },
                  { name: 'Q4 \'23', actual: 1.5, forecast: 1.45 },
                  { name: 'Q1 \'24', actual: 1.8, forecast: 1.7 },
                  { name: 'Q2 \'24', actual: 2.1, forecast: 2.0 },
                  { name: 'Q3 \'24', actual: null, forecast: 2.4 },
                  { name: 'Q4 \'24', actual: null, forecast: 2.7 },
                ]);
                setLifecycleData([
                  { name: 'New Trials', value: 400 },
                  { name: 'Active Subscribers', value: 850 },
                  { name: 'Upgraded', value: 150 },
                  { name: 'Churned', value: 50 },
                ]);
            } finally {
                setIsLoading(false);
            }
        }
        fetchSalesData();
    }, []);

    const COLORS = ['#3B82F6', '#10B981', '#FFD700', '#EF4444'];
    const renderChart = (chart: 'conversion' | 'forecast' | 'lifecycle') => {
        if (isLoading) return <Skeleton className="h-[200px] w-full" />;
        
        switch (chart) {
            case 'conversion':
                return (
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={conversionData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                        <XAxis dataKey="name" />
                        <YAxis unit="%" />
                        <Tooltip formatter={(value) => [`${value}%`, "Conversion Rate"]} />
                        <Legend />
                        <Line type="monotone" dataKey="rate" stroke="hsl(var(--primary))" strokeWidth={2} activeDot={{ r: 8 }} />
                      </LineChart>
                    </ResponsiveContainer>
                );
            case 'forecast':
                 return (
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={forecastData}>
                        <XAxis dataKey="name" />
                        <YAxis unit="M" />
                        <Tooltip formatter={(value, name) => [`₹${value}M`, name.charAt(0).toUpperCase() + name.slice(1)]} />
                        <Legend />
                        <Bar dataKey="actual" fill="hsl(var(--primary))" name="Actual" />
                        <Bar dataKey="forecast" fill="hsl(var(--secondary))" name="Forecast" />
                      </BarChart>
                    </ResponsiveContainer>
                 );
            case 'lifecycle':
                return (
                    <ResponsiveContainer width="100%" height={200}>
                        <PieChart>
                            <Pie data={lifecycleData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                                {lifecycleData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip formatter={(value, name) => [value, name]}/>
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                );
        }
    }


  return (
    <div className="flex flex-col gap-6">
       {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Could not load sales data</AlertTitle>
          <AlertDescription>{error} Displaying sample data instead.</AlertDescription>
        </Alert>
      )}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Target /> Lead Conversion</CardTitle>
            <CardDescription>Trial to premium conversion rate.</CardDescription>
          </CardHeader>
          <CardContent>
            {renderChart('conversion')}
          </CardContent>
        </Card>

        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><TrendingUp /> Revenue Forecast</CardTitle>
            <CardDescription>MRR forecast vs. actual (in millions).</CardDescription>
          </CardHeader>
          <CardContent>
            {renderChart('forecast')}
          </CardContent>
        </Card>

        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Users /> Customer Lifecycle</CardTitle>
            <CardDescription>Current customer distribution.</CardDescription>
          </CardHeader>
          <CardContent>
            {renderChart('lifecycle')}
          </CardContent>
        </Card>
      </div>

       <Card className="shadow-lg">
          <CardHeader>
            <CardTitle>Pricing Optimization</CardTitle>
            <CardDescription>AI-powered recommendations to optimize pricing tiers.</CardDescription>
          </CardHeader>
          <CardContent>
              <div className="flex items-center justify-center h-24 text-muted-foreground">
                  <p>Pricing recommendations coming soon.</p>
              </div>
          </CardContent>
        </Card>
    </div>
  );
}
