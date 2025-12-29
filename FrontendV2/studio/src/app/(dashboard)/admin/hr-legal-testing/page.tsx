'use client';
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { TestTube2, BrainCircuit, Bot, Check, Zap, Wand2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Label } from '@/components/ui/label';
import { authenticatedApiCall } from '@/lib/auth-utils';

// Define the types locally since we removed the AI flows
type HrLegalQueryOutput = {
  answer: string;
  confidenceScore: number;
  sources: string[];
};

export default function RAGTestingPage() {
    const [query, setQuery] = useState('');
    const [promptStrategy, setPromptStrategy] = useState('A');
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<HrLegalQueryOutput | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setIsLoading(true);
        setResult(null);
        setError(null);

        try {
            // Call the Admin HR Legal API endpoint for unlimited queries with authentication
            const response = await authenticatedApiCall('/api/admin/hr-legal/query', {
                method: 'POST',
                useAdminToken: true,
                body: JSON.stringify({ 
                    query_text: query, 
                    query_category: 'testing',
                    promptStrategy 
                }),
            });

            const data = response;
            
            if (data.success && data.legal_response) {
                setResult({
                    answer: data.legal_response.legal_analysis,
                    confidenceScore: data.legal_response.confidence_score || 0,
                    sources: data.legal_response.relevant_laws || []
                });
            } else {
                throw new Error(data.message || 'Failed to get response from RAG system');
            }
        } catch (err) {
            setError('An error occurred while testing the RAG system. Please try again.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="grid gap-6 lg:grid-cols-3">
            <Card className="shadow-lg lg:col-span-1">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2"><TestTube2 /> RAG System Testing</CardTitle>
                    <CardDescription>Test and optimize the HR Legal RAG model.</CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <Label htmlFor="query-textarea">Query</Label>
                            <Textarea
                                id="query-textarea"
                                placeholder="Enter a legal query to test..."
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                rows={6}
                                disabled={isLoading}
                            />
                        </div>
                        <div>
                            <Label>Prompt Strategy (A/B Test)</Label>
                            <Select value={promptStrategy} onValueChange={setPromptStrategy} disabled={isLoading}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select a strategy" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="A">Strategy A</SelectItem>
                                    <SelectItem value="B">Strategy B</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <Button type="submit" className="w-full" disabled={isLoading || !query.trim()}>
                            {isLoading ? 'Executing...' : <><BrainCircuit className="mr-2 h-4 w-4" /> Run Test</>}
                        </Button>
                    </form>
                </CardContent>
            </Card>

            <div className="lg:col-span-2">
                <Card className="shadow-lg min-h-[400px]">
                    <CardHeader>
                        <CardTitle>Test Results</CardTitle>
                        <CardDescription>Output from the RAG model will appear here.</CardDescription>
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
                                <div>
                                    <h3 className="font-semibold text-lg text-primary flex items-center"><Bot className="mr-2 h-5 w-5"/> Answer</h3>
                                    <Badge>
                                        <Wand2 className="mr-1 h-3 w-3" />
                                        Strategy: {promptStrategy}
                                    </Badge>
                                </div>
                                <p className="text-foreground/90 whitespace-pre-wrap">{result.answer}</p>
                                
                                <div className="flex items-center gap-2">
                                    <Badge variant={result.confidenceScore > 0.8 ? "default" : "secondary"} className={result.confidenceScore > 0.8 ? "bg-green-500" : ""}>
                                        <Zap className="mr-1 h-3 w-3" />
                                        Confidence: {(result.confidenceScore * 100).toFixed(0)}%
                                    </Badge>
                                </div>

                                <div>
                                    <h4 className="font-semibold text-md flex items-center"><Check className="mr-2 h-4 w-4 text-green-500" /> Sources</h4>
                                    <ul className="list-disc list-inside text-sm text-muted-foreground mt-1 space-y-1">
                                    {result.sources.map((source, index) => (
                                        <li key={index}>{source}</li>
                                    ))}
                                    </ul>
                                </div>
                            </div>
                        )}
                         {!isLoading && !result && !error && (
                            <div className="text-center text-muted-foreground pt-10">
                                <TestTube2 className="mx-auto h-12 w-12 mb-4" />
                                <p>Enter a query to begin testing the RAG model.</p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
