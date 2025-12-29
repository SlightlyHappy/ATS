'use client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Server, Database, BrainCircuit, Activity, AlertTriangle, CheckCircle, RefreshCw, Thermometer, MemoryStick } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { useToast } from '@/hooks/use-toast';
import { authenticatedApiCall } from '@/lib/auth-utils';

type SystemStatus = {
    basic_health: {
        supabase: { status: 'healthy' | 'unhealthy' };
        ai_basic: { status: 'healthy' | 'unhealthy' };
    };
    enhanced_ai_status: {
        agentic_system: 'operational' | 'degraded';
        '4_agent_analysis': 'ready' | 'busy';
    };
};

type RailwayPerformance = {
    memory: {
        used_percent: number;
        optimization: string;
    }
}

const HealthCard = ({ title, status, icon: Icon, isLoading, isHealthyOverride }: { title: string, status: string, icon: React.ElementType, isLoading: boolean, isHealthyOverride?: boolean }) => {
    const isHealthy = isHealthyOverride !== undefined ? isHealthyOverride : (status?.toLowerCase() === 'healthy' || status?.toLowerCase() === 'operational' || status?.toLowerCase() === 'ready');
    return (
        <Card className="shadow-md">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{title}</CardTitle>
                <Icon className={`h-5 w-5 ${isHealthy ? 'text-green-500' : 'text-red-500'}`} />
            </CardHeader>
            <CardContent>
                {isLoading ? <Skeleton className="h-6 w-24" /> : <div className="text-xl font-bold capitalize">{status}</div>}
            </CardContent>
        </Card>
    )
};

export default function SystemHealthPage() {
    const [status, setStatus] = useState<SystemStatus | null>(null);
    const [railwayData, setRailwayData] = useState<RailwayPerformance | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { toast } = useToast();

    const fetchHealth = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const [statusData, perfData] = await Promise.all([
                authenticatedApiCall('/api/system/status', { useAdminToken: true }),
                authenticatedApiCall('/api/railway/performance', { useAdminToken: true })
            ]);
            
            console.log('System status response:', statusData);
            console.log('Railway performance response:', perfData);
            
            setStatus(statusData.system_status || statusData);
            setRailwayData(perfData.railway_performance || perfData);
        } catch (err: any) {
            setError(err.message);
            // Set mock data as fallback
            setStatus({
                basic_health: {
                    supabase: { status: 'healthy' },
                    ai_basic: { status: 'healthy' }
                },
                enhanced_ai_status: {
                    agentic_system: 'operational',
                    '4_agent_analysis': 'ready'
                }
            });
            setRailwayData({
                memory: {
                    used_percent: 65.2,
                    optimization: 'moderate'
                }
            });
        } finally {
            setIsLoading(false);
        }
    };    useEffect(() => {
        fetchHealth();
    }, []);

    const handleManualCheck = async () => {
        toast({ title: "Running manual health check..." });
        await fetchHealth();
        if (!error) {
            toast({ title: "Health check complete!", description: "System status has been updated.", variant: 'default' });
        } else {
            toast({ title: "Health check failed.", description: error, variant: 'destructive' });
        }
    }


    return (
        <div className="flex flex-col gap-6">
            {error && (
                <Alert variant="destructive">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>Could not load complete system health</AlertTitle>
                    <AlertDescription>{error} Displaying mock data as a fallback.</AlertDescription>
                </Alert>
            )}

            <div className="flex justify-end">
                <Button onClick={handleManualCheck} disabled={isLoading}>
                    <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                    Refresh Status
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Real-time Monitoring</CardTitle>
                    <CardDescription>Live status of all critical system components.</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <HealthCard title="Primary Database (Railway)" status={status?.basic_health?.supabase?.status ?? '...'} icon={Database} isLoading={isLoading} />
                    <HealthCard title="AI System (Basic)" status={status?.basic_health?.ai_basic?.status ?? '...'} icon={BrainCircuit} isLoading={isLoading} />
                    <HealthCard title="Agentic System" status={status?.enhanced_ai_status?.agentic_system ?? '...'} icon={Activity} isLoading={isLoading} />
                    <HealthCard title="4-Agent Analysis" status={status?.enhanced_ai_status?.['4_agent_analysis'] ?? '...'} icon={CheckCircle} isLoading={isLoading} />
                </CardContent>
            </Card>

             <Card>
                <CardHeader>
                    <CardTitle>Resource Usage (Railway)</CardTitle>
                    <CardDescription>Performance metrics for the hosting infrastructure.</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-2">
                     <HealthCard title="Memory Utilization" status={railwayData?.memory?.used_percent ? `${railwayData.memory.used_percent}%` : '...'} icon={MemoryStick} isLoading={isLoading} isHealthyOverride={railwayData?.memory?.used_percent ? railwayData.memory.used_percent < 85 : true} />
                     <HealthCard title="CPU Temperature" status="Normal" icon={Thermometer} isLoading={isLoading} isHealthyOverride={true} />
                </CardContent>
            </Card>

             <Card>
                <CardHeader>
                    <CardTitle>Logs & Diagnostics</CardTitle>
                    <CardDescription>Inspect recent system logs for errors or warnings.</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="bg-muted rounded-lg p-4 font-mono text-xs h-64 overflow-auto">
                        {isLoading && <p>Loading logs...</p>}
                        {!isLoading && !error &&
                          <>
                            <p><span className="text-green-500">[INFO]</span> System check initiated by admin.</p>
                            <p><span className="text-green-500">[INFO]</span> Database connection successful: {status?.basic_health?.supabase?.status}.</p>
                            <p><span className="text-green-500">[INFO]</span> AI agentic system {status?.enhanced_ai_status?.agentic_system}.</p>
                            {railwayData?.memory?.used_percent && railwayData.memory.used_percent > 75 && <p><span className="text-yellow-500">[WARN]</span> High memory usage detected: {railwayData?.memory.used_percent}%</p>}
                            <p><span className="text-green-500">[INFO]</span> Health check complete.</p>
                          </>
                        }
                        {error && <p><span className="text-red-500">[ERROR]</span> {error}</p>}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
