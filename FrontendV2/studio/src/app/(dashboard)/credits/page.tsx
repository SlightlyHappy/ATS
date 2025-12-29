
'use client';
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Gift, Zap, IndianRupee, BarChart, AlertTriangle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { PaymentDialog } from './_components/payment-dialog';


const creditTiers = [
    { name: "Resume Analysis", credits: 1, description: "1 credit per standard resume analysis." },
    { name: "Batch Analysis", credits: 5, description: "5 credits per batch processing job." },
    { name: "Legal Query", credits: 1, description: "1 credit per HR legal consultation." },
];

type CreditStatus = {
    trial_credits: number;
    premium_credits: number;
    total_used: number;
    processing_tier: string;
    can_process: boolean;
};


export default function CreditsPage() {
    const [status, setStatus] = useState<CreditStatus | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isPaymentDialogOpen, setIsPaymentDialogOpen] = useState(false);
    const { toast } = useToast();
    
    async function fetchCreditStatus() {
        setIsLoading(true);
        setError(null);
        try {
            const token = localStorage.getItem('auth_token');
            if (!token) {
                throw new Error('Authentication token not found. Please log in.');
            }
            const response = await fetch('/api/credits/status', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) {
                const errorData = await response.json();
                 if (response.status === 401) {
                     throw new Error('Your session has expired. Please log in again.');
                 }
                throw new Error(errorData.message || 'Failed to fetch credit status.');
            }
            const data = await response.json();
            setStatus(data.credit_status);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        fetchCreditStatus();
    }, []);

    const onPaymentSuccess = () => {
        toast({
            title: "Payment Successful!",
            description: "Your credits have been added to your account.",
            variant: "default",
        });
        fetchCreditStatus(); // Re-fetch credits after successful payment
        setIsPaymentDialogOpen(false);
    };

    const onPaymentError = (errorMsg: string) => {
        toast({
            title: "Payment Failed",
            description: errorMsg || "An unknown error occurred.",
            variant: "destructive",
        });
        setIsPaymentDialogOpen(false);
    };

    const trialCredits = status?.trial_credits ?? 0;
    const premiumCredits = status?.premium_credits ?? 0;
    const totalCredits = trialCredits + premiumCredits;
    const trialCreditsPercentage = status ? (status.trial_credits / 100) * 100 : 0;


    return (
        <>
            <PaymentDialog 
                isOpen={isPaymentDialogOpen} 
                onOpenChange={setIsPaymentDialogOpen}
                onPaymentSuccess={onPaymentSuccess}
                onPaymentError={onPaymentError}
            />
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {error && (
                    <div className="lg:col-span-3">
                        <Alert variant="destructive">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertTitle>Could not load credit status</AlertTitle>
                            <AlertDescription>{error}</AlertDescription>
                        </Alert>
                    </div>
                )}
                <Card className="shadow-lg lg:col-span-1">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Gift className="text-secondary" />
                            Credit Balance
                        </CardTitle>
                        <CardDescription>Your available credits for resume analysis.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {isLoading ? (
                            <div className="space-y-6">
                                <Skeleton className="h-6 w-full" />
                                <Skeleton className="h-6 w-full" />
                                <div className="text-center pt-4">
                                    <Skeleton className="h-16 w-32 mx-auto" />
                                </div>
                                <Skeleton className="h-12 w-full" />
                            </div>
                        ) : (
                            <>
                                <div>
                                    <div className="flex justify-between mb-1">
                                        <span className="text-sm font-medium">Trial Credits</span>
                                        <span className="text-sm font-medium">{trialCredits} / 100</span>
                                    </div>
                                    <Progress value={trialCreditsPercentage} />
                                </div>
                                <div>
                                    <div className="flex justify-between mb-1">
                                        <span className="text-sm font-medium">Premium Credits</span>
                                        <span className="text-sm font-medium">{premiumCredits}</span>
                                    </div>
                                    <Progress value={premiumCredits > 0 ? 100: 0} className="[&>*]:bg-accent" />
                                </div>
                                <div className="text-center pt-4">
                                    <p className="text-sm text-muted-foreground">Total Available</p>
                                    <p className="text-5xl font-bold text-primary">{totalCredits}</p>
                                    <p className="text-xs text-muted-foreground">credits</p>
                                </div>
                                <Button onClick={() => setIsPaymentDialogOpen(true)} className="w-full bg-gradient-to-r from-amber-400 to-yellow-500 text-primary-foreground hover:from-amber-500 hover:to-yellow-600 shadow-lg">
                                    <IndianRupee className="mr-2 h-4 w-4" />
                                    Buy More Credits
                                </Button>
                            </>
                        )}
                    </CardContent>
                </Card>

                <div className="lg:col-span-2 grid gap-6">
                    <Card className="shadow-lg">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Zap className="text-primary" />
                                Credit Consumption
                            </CardTitle>
                            <CardDescription>Understand how your credits are used.</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {creditTiers.map(tier => (
                                <div key={tier.name} className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                                    <div>
                                        <p className="font-semibold">{tier.name}</p>
                                        <p className="text-xs text-muted-foreground">{tier.description}</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="font-bold text-lg text-primary">{tier.credits}</p>
                                        <p className="text-xs text-muted-foreground">credit{tier.credits !== 1 ? 's' : ''}</p>
                                    </div>
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                    <Card className="shadow-lg">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <BarChart className="text-primary" />
                                Usage Analytics
                            </CardTitle>
                            <CardDescription>Forecast your credit needs.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-center justify-center h-24 text-muted-foreground">
                                <p>Usage charts and forecasting coming soon.</p>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </>
    );
}
