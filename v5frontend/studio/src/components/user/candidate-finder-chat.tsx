'use client';

import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { 
  Send, 
  MessageSquare, 
  User, 
  Bot, 
  Search,
  TrendingUp,
  Users,
  Award,
  Target,
  BarChart3,
  Filter,
  Star
} from 'lucide-react';
import { toast } from 'sonner';
import { userApi } from '@/lib/user-api';

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  candidates?: CandidateResult[];
  metrics?: SearchMetrics;
}

interface CandidateResult {
  id: number;
  name: string;
  score: number;
  skills: string[];
  experience_years: number;
  role: string;
  match_percentage: number;
  highlights: string[];
  peer_comparison: {
    percentile: number;
    avg_score: number;
    rank: number;
    total_candidates: number;
  };
}

interface SearchMetrics {
  total_candidates: number;
  avg_score: number;
  top_skills: { skill: string; count: number }[];
  experience_distribution: { range: string; count: number }[];
  score_distribution: { range: string; count: number }[];
}

export default function CandidateFinderChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Hello! I\'m your AI candidate finder. Ask me to search for candidates based on skills, experience, or any specific requirements. For example: "Find senior software engineers with Python experience" or "Show me candidates with project management skills scoring above 80".',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateResult | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Search candidates using the query
      const searchResults = await userApi.searchCandidates(inputValue) as {
        candidates?: CandidateResult[];
        metrics?: SearchMetrics;
      };
      
      // Create assistant response with results
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `Found ${searchResults.candidates?.length || 0} candidates matching your criteria. Here are the results:`,
        timestamp: new Date(),
        candidates: searchResults.candidates || [],
        metrics: searchResults.metrics
      };

      setMessages(prev => [...prev, assistantMessage]);
      
    } catch (error) {
      console.error('Search error:', error);
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'I apologize, but I encountered an error while searching for candidates. Please try again with a different query or check if the backend service is available.',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
      toast.error('Search failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 75) return 'text-blue-600 bg-blue-50 border-blue-200';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getPercentileColor = (percentile: number) => {
    if (percentile >= 90) return 'text-green-600';
    if (percentile >= 75) return 'text-blue-600';
    if (percentile >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
      {/* Chat Interface - Left Side */}
      <div className="lg:col-span-2">
        <Card className="h-full flex flex-col">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <MessageSquare className="h-5 w-5" />
              <span>AI Candidate Finder</span>
            </CardTitle>
            <CardDescription>
              Ask me to find candidates based on skills, experience, or any specific requirements
            </CardDescription>
          </CardHeader>
          
          <CardContent className="flex-1 flex flex-col space-y-4">
            {/* Messages Area */}
            <ScrollArea className="flex-1 h-96">
              <div className="space-y-4 p-4">
                {messages.map((message) => (
                  <div key={message.id} className="space-y-3">
                    <div className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`flex items-start space-x-2 max-w-3xl ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                          message.type === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'
                        }`}>
                          {message.type === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                        </div>
                        <div className={`px-4 py-2 rounded-lg ${
                          message.type === 'user' 
                            ? 'bg-primary text-primary-foreground' 
                            : 'bg-muted'
                        }`}>
                          <p className="text-sm">{message.content}</p>
                          <p className="text-xs opacity-70 mt-1">
                            {message.timestamp.toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Candidate Results */}
                    {message.candidates && message.candidates.length > 0 && (
                      <div className="space-y-3 ml-10">
                        {message.candidates.map((candidate) => (
                          <div 
                            key={candidate.id}
                            className="p-4 border rounded-lg hover:bg-accent cursor-pointer transition-colors"
                            onClick={() => setSelectedCandidate(candidate)}
                          >
                            <div className="flex items-start justify-between">
                              <div className="space-y-2">
                                <div className="flex items-center space-x-2">
                                  <h4 className="font-medium">{candidate.name}</h4>
                                  <Badge variant="outline">{candidate.role}</Badge>
                                  <Badge className={getScoreColor(candidate.score)}>
                                    Score: {candidate.score.toFixed(1)}
                                  </Badge>
                                </div>
                                
                                <div className="text-sm text-muted-foreground">
                                  {candidate.experience_years} years experience • {candidate.match_percentage}% match
                                </div>
                                
                                <div className="flex flex-wrap gap-1">
                                  {candidate.skills.slice(0, 5).map((skill, idx) => (
                                    <Badge key={idx} variant="secondary" className="text-xs">
                                      {skill}
                                    </Badge>
                                  ))}
                                  {candidate.skills.length > 5 && (
                                    <Badge variant="secondary" className="text-xs">
                                      +{candidate.skills.length - 5} more
                                    </Badge>
                                  )}
                                </div>

                                {candidate.highlights.length > 0 && (
                                  <div className="text-sm">
                                    <strong>Highlights:</strong>
                                    <ul className="list-disc list-inside mt-1 space-y-1">
                                      {candidate.highlights.slice(0, 2).map((highlight, idx) => (
                                        <li key={idx} className="text-muted-foreground">{highlight}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                              
                              <div className="text-right">
                                <div className={`text-sm font-medium ${getPercentileColor(candidate.peer_comparison.percentile)}`}>
                                  {candidate.peer_comparison.percentile}th percentile
                                </div>
                                <div className="text-xs text-muted-foreground">
                                  Rank #{candidate.peer_comparison.rank} of {candidate.peer_comparison.total_candidates}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="flex items-start space-x-2">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                        <Bot className="h-4 w-4" />
                      </div>
                      <div className="px-4 py-2 rounded-lg bg-muted">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
                          <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce delay-75" />
                          <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce delay-150" />
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Input Area */}
            <div className="flex space-x-2">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me to find candidates... (e.g., 'Find Python developers with 5+ years experience')"
                disabled={isLoading}
                className="flex-1"
              />
              <Button 
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                size="icon"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Metrics Dashboard - Right Side */}
      <div className="space-y-4">
        {/* Selected Candidate Details */}
        {selectedCandidate && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Candidate Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-medium">{selectedCandidate.name}</h4>
                <p className="text-sm text-muted-foreground">{selectedCandidate.role}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-2xl font-bold">{selectedCandidate.score.toFixed(1)}</div>
                  <div className="text-sm text-muted-foreground">Overall Score</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">{selectedCandidate.experience_years}</div>
                  <div className="text-sm text-muted-foreground">Years Exp.</div>
                </div>
              </div>

              <Separator />

              <div>
                <h5 className="font-medium mb-2">Peer Comparison</h5>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm">Percentile Rank</span>
                    <span className={`text-sm font-medium ${getPercentileColor(selectedCandidate.peer_comparison.percentile)}`}>
                      {selectedCandidate.peer_comparison.percentile}th
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Position</span>
                    <span className="text-sm">#{selectedCandidate.peer_comparison.rank} of {selectedCandidate.peer_comparison.total_candidates}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">vs. Average</span>
                    <span className="text-sm">
                      {selectedCandidate.score > selectedCandidate.peer_comparison.avg_score ? '+' : ''}
                      {(selectedCandidate.score - selectedCandidate.peer_comparison.avg_score).toFixed(1)}
                    </span>
                  </div>
                </div>
              </div>

              <Separator />

              <div>
                <h5 className="font-medium mb-2">Skills</h5>
                <div className="flex flex-wrap gap-1">
                  {selectedCandidate.skills.map((skill, idx) => (
                    <Badge key={idx} variant="secondary" className="text-xs">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>

              {selectedCandidate.highlights.length > 0 && (
                <>
                  <Separator />
                  <div>
                    <h5 className="font-medium mb-2">Key Highlights</h5>
                    <ul className="text-sm space-y-1">
                      {selectedCandidate.highlights.map((highlight, idx) => (
                        <li key={idx} className="flex items-start space-x-2">
                          <Star className="h-3 w-3 text-yellow-500 mt-0.5 flex-shrink-0" />
                          <span>{highlight}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        )}

        {/* Search Metrics */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span>Search Metrics</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {messages.length > 1 ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {messages[messages.length - 1]?.candidates?.length || 0}
                    </div>
                    <div className="text-sm text-muted-foreground">Results Found</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {messages[messages.length - 1]?.metrics?.avg_score?.toFixed(1) || '0'}
                    </div>
                    <div className="text-sm text-muted-foreground">Avg Score</div>
                  </div>
                </div>
                
                <div className="text-center text-sm text-muted-foreground">
                  Click on candidates to view detailed comparison metrics
                </div>
              </div>
            ) : (
              <div className="text-center text-sm text-muted-foreground">
                Start a search to see metrics
              </div>
            )}
          </CardContent>
        </Card>

        {/* Search Tips */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Search Tips</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div>
                <strong>Skills:</strong> "Find React developers"
              </div>
              <div>
                <strong>Experience:</strong> "Senior engineers with 5+ years"
              </div>
              <div>
                <strong>Score Range:</strong> "Candidates scoring above 80"
              </div>
              <div>
                <strong>Combined:</strong> "Python developers with ML experience and high scores"
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
