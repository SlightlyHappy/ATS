'use client';
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Gavel, Bot, User, Check, Zap, Star } from 'lucide-react';
import { legalQueryIndianLaborLaw, type LegalQueryIndianLaborLawOutput } from '@/ai/flows/legal-query-indian-labor-law';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

export default function HrLegalPage() {
    const [query, setQuery] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<LegalQueryIndianLaborLawOutput | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setIsLoading(true);
        setResult(null);
        setError(null);

        try {
            const response = await legalQueryIndianLaborLaw({ query });
            setResult(response);
        } catch (err) {
            setError('An error occurred while fetching the legal recommendation. Please try again.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="grid gap-6 lg:grid-cols-3">
            <Card className="shadow-lg lg:col-span-1">
                <CardHeader>
                    <CardTitle>HR Legal Consultation</CardTitle>
                    <CardDescription>Get AI-powered guidance on Indian labor law.</CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <Textarea
                            placeholder="e.g., What are the rules for maternity leave in Maharashtra?"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            rows={6}
                            disabled={isLoading}
                        />
                        <Button type="submit" className="w-full" disabled={isLoading || !query.trim()}>
                            {isLoading ? 'Consulting AI...' : <><Gavel className="mr-2 h-4 w-4" /> Get Recommendation</>}
                        </Button>
                    </form>
                </CardContent>
            </Card>

            <div className="lg:col-span-2">
                <Card className="shadow-lg min-h-[400px]">
                    <CardHeader>
                        <CardTitle>AI Legal Assistant's Response</CardTitle>
                        <CardDescription>Results will appear below.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {isLoading && (
                            <div className="space-y-4">
                                <Skeleton className="h-6 w-3/4" />
                                <Skeleton className="h-4 w-1/2" />
                                <Skeleton className="h-20 w-full" />
                                <Skeleton className="h-4 w-1/4" />
                            </div>
                        )}
                        {error && <p className="text-destructive">{error}</p>}
                        {result && (
                            <div className="space-y-6">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <h3 className="font-semibold text-lg text-primary flex items-center"><Bot className="mr-2 h-5 w-5"/> Recommendation</h3>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Badge variant={result.confidenceScore > 0.8 ? "default" : "secondary"} className={result.confidenceScore > 0.8 ? "bg-green-500" : ""}>
                                            <Zap className="mr-1 h-3 w-3" />
                                            Confidence: {(result.confidenceScore * 100).toFixed(0)}%
                                        </Badge>
                                        <Button variant="ghost" size="icon"><Star className="h-4 w-4" /></Button>
                                    </div>
                                </div>

                                <p className="text-foreground/90 whitespace-pre-wrap">{result.recommendation}</p>

                                <div>
                                    <h4 className="font-semibold text-md flex items-center"><Check className="mr-2 h-4 w-4 text-green-500" /> Source Attribution</h4>
                                    <p className="text-sm text-muted-foreground italic mt-1">{result.sourceAttribution}</p>
                                </div>
                            </div>
                        )}
                         {!isLoading && !result && !error && (
                            <div className="text-center text-muted-foreground pt-10">
                                <Gavel className="mx-auto h-12 w-12 mb-4" />
                                <p>Your legal query results will be displayed here.</p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
