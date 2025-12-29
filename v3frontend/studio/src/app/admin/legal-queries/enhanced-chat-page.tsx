"use client";

import { useEffect, useState } from "react";
import { AdminService } from "@/services/admin.service";
import PageHeader from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Plus, RefreshCw, Trash2, Send, MessageCircle } from "lucide-react";
import { AlertDialogProvider } from "@/components/alert-dialog-provider";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CreateLegalQueryModal } from "./create-legal-query-modal";

interface LegalQuery {
  id: string;
  query: string;
  response?: string;
  status: 'pending' | 'completed' | 'failed';
  created_at: string;
  user_id?: string;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export default function EnhancedAdminLegalQueriesPage() {
  const [data, setData] = useState<LegalQuery[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [currentQuery, setCurrentQuery] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isSendingQuery, setIsSendingQuery] = useState(false);
  const { toast } = useToast();

  const loadLegalQueries = async () => {
    try {
      setIsLoading(true);
      const response = await AdminService.getLegalQueries();
      setData(response.data || []);
      console.log('⚖️ Legal queries loaded:', response.data?.length || 0);
    } catch (error) {
      console.error('❌ Failed to load legal queries:', error);
      toast({
        title: "Error",
        description: "Failed to load legal queries. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadLegalQueries();
    setIsRefreshing(false);
  };

  const handleDelete = async (queryId: string) => {
    try {
      await AdminService.deleteLegalQuery(queryId);
      toast({
        title: "Success",
        description: "Legal query deleted successfully.",
      });
      await loadLegalQueries();
    } catch (error) {
      console.error('❌ Failed to delete legal query:', error);
      toast({
        title: "Error",
        description: "Failed to delete legal query. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleCreateSuccess = () => {
    setShowCreateModal(false);
    loadLegalQueries();
    toast({
      title: "Success",
      description: "Legal query created successfully.",
    });
  };

  const handleSendChatQuery = async () => {
    if (!currentQuery.trim() || isSendingQuery) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: currentQuery,
      timestamp: new Date().toISOString(),
    };

    setChatMessages(prev => [...prev, userMessage]);
    const queryText = currentQuery;
    setCurrentQuery("");
    setIsSendingQuery(true);

    try {
      // Call the admin HR legal query endpoint
      const response = await AdminService.createHRLegalQuery(queryText, "admin");
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.data?.response || response.message || "Legal query processed successfully. Check the queries table above for details.",
        timestamp: new Date().toISOString(),
      };

      setChatMessages(prev => [...prev, assistantMessage]);
      
      // Refresh the queries table to show the new query
      await loadLegalQueries();

      toast({
        title: "Success",
        description: "Legal query submitted successfully.",
      });
    } catch (error) {
      console.error('❌ Failed to submit legal query:', error);
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to process legal query'}`,
        timestamp: new Date().toISOString(),
      };

      setChatMessages(prev => [...prev, errorMessage]);

      toast({
        title: "Error",
        description: "Failed to submit legal query. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSendingQuery(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendChatQuery();
    }
  };

  useEffect(() => {
    loadLegalQueries();
  }, []);

  return (
    <AlertDialogProvider>
      <div className="container mx-auto p-6 space-y-6">
        <PageHeader
          title="Legal Queries Management"
          description="Manage and track legal compliance queries and responses"
        />

        {/* Action Bar */}
        <div className="flex justify-between items-center">
          <div className="flex gap-2">
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Query
            </Button>
          </div>
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Queries Table */}
        <Card>
          <CardHeader>
            <CardTitle>Legal Queries</CardTitle>
            <CardDescription>
              View and manage all legal compliance queries
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Query</TableHead>
                    <TableHead className="hidden md:table-cell">Status</TableHead>
                    <TableHead className="hidden lg:table-cell">Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.map((query) => (
                    <TableRow key={query.id}>
                      <TableCell>
                        <div className="space-y-1">
                          <p className="font-medium truncate max-w-md">
                            {query.query}
                          </p>
                          {query.response && (
                            <p className="text-sm text-muted-foreground truncate max-w-md">
                              Response: {query.response}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="hidden md:table-cell">
                        <Badge
                          variant={
                            query.status === "completed"
                              ? "default"
                              : query.status === "pending"
                              ? "secondary"
                              : "destructive"
                          }
                        >
                          {query.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="hidden lg:table-cell">
                        {new Date(query.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(query.id)}
                          className="text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {data.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                        No legal queries found. Use the chat interface below to create your first query.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Chat Interface */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5" />
              Legal Assistant Chat
            </CardTitle>
            <CardDescription>
              Ask legal questions directly and get instant responses
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Chat Messages */}
            <ScrollArea className="h-80 w-full border rounded-lg p-4">
              <div className="space-y-4">
                {chatMessages.length === 0 ? (
                  <div className="text-center text-muted-foreground py-8">
                    <MessageCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Start a conversation by typing a legal question below.</p>
                    <p className="text-sm mt-2">Example: "What are the employment law requirements for remote work in India?"</p>
                  </div>
                ) : (
                  chatMessages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${
                        message.type === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      <div
                        className={`max-w-[80%] p-3 rounded-lg ${
                          message.type === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                        }`}
                      >
                        <p className="text-sm">{message.content}</p>
                        <p className={`text-xs mt-1 ${
                          message.type === 'user' 
                            ? 'text-primary-foreground/70' 
                            : 'text-muted-foreground'
                        }`}>
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))
                )}
                {isSendingQuery && (
                  <div className="flex justify-start">
                    <div className="bg-muted p-3 rounded-lg">
                      <p className="text-sm text-muted-foreground">Processing your legal query...</p>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            {/* Chat Input */}
            <div className="flex gap-2">
              <Textarea
                placeholder="Type your legal question here... (Press Enter to send, Shift+Enter for new line)"
                value={currentQuery}
                onChange={(e) => setCurrentQuery(e.target.value)}
                onKeyDown={handleKeyPress}
                className="min-h-[80px] resize-none"
                disabled={isSendingQuery}
              />
              <Button
                onClick={handleSendChatQuery}
                disabled={!currentQuery.trim() || isSendingQuery}
                className="px-6"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <CreateLegalQueryModal
        open={showCreateModal}
        onOpenChangeAction={setShowCreateModal}
        onSuccessAction={handleCreateSuccess}
      />
    </AlertDialogProvider>
  );
}
