import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Trash2, User, Bot } from 'lucide-react';
import Card from './Card';
import Button from './Button';
import LoadingSpinner from './LoadingSpinner';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const LegalChat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Generate conversation ID on component mount
    setConversationId(generateConversationId());
    
    // Add welcome message
    setMessages([{
      id: 'welcome',
      type: 'system',
      content: 'Welcome to the HR Legal Assistant! I can help you with employment law, compliance questions, policy guidance, and more. How can I assist you today?',
      timestamp: new Date()
    }]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const generateConversationId = () => {
    return 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/legal/chat`, {
        message: userMessage.content,
        conversation_id: conversationId
      });

      if (response.data.success) {
        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: response.data.response.content,
          metadata: response.data.response.metadata,
          citations: response.data.response.citations,
          followUpQuestions: response.data.response.follow_up_questions,
          timestamp: new Date()
        };

        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error(response.data.error || 'Unknown error occurred');
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: `Error: ${error.response?.data?.error || error.message || 'Failed to get response'}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleFollowUpClick = (question) => {
    setInputMessage(question);
  };

  const clearConversation = () => {
    setMessages([{
      id: 'welcome',
      type: 'system',
      content: 'Conversation cleared. How can I help you today?',
      timestamp: new Date()
    }]);
    setConversationId(generateConversationId());
  };

  const cleanMarkdownContent = (content) => {
    // Clean up the markdown formatting that comes from the API
    return content
      .replace(/^###\s*/gm, '### ') // Ensure proper spacing after ###
      .replace(/^####\s*/gm, '#### ') // Ensure proper spacing after ####
      .replace(/^\d+\./gm, '\n$&') // Add line break before numbered items
      .trim();
  };

  return (
    <Card className="h-full flex flex-col">
      {/* Chat Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Bot size={20} className="text-primary" />
          <h3 className="font-semibold text-primary">Legal Chat Assistant</h3>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={clearConversation}
          icon={Trash2}
          className="text-secondary hover:text-danger"
        >
          Clear Chat
        </Button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[400px] max-h-[600px]">
        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] ${
              message.type === 'user' 
                ? 'bg-primary text-primary-foreground' 
                : message.type === 'system'
                ? 'bg-info-light text-info border border-info'
                : 'bg-surface border border-border'
            } rounded-lg p-4 shadow-sm`}>
              
              {/* Message Header */}
              <div className="flex items-center gap-2 mb-2">
                {message.type === 'user' ? (
                  <User size={16} />
                ) : (
                  <Bot size={16} className="text-primary" />
                )}
                <span className="text-sm font-medium">
                  {message.type === 'user' ? 'You' : 'Legal Assistant'}
                </span>
                <span className="text-xs opacity-60 ml-auto">
                  {message.timestamp.toLocaleTimeString()}
                </span>
              </div>

              {/* Message Content */}
              <div className="prose prose-sm max-w-none">
                {message.type === 'user' ? (
                  <p className="m-0">{message.content}</p>
                ) : (
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      h3: ({children}) => <h3 className="text-lg font-semibold mt-4 mb-2 text-primary">{children}</h3>,
                      h4: ({children}) => <h4 className="text-base font-medium mt-3 mb-2 text-primary">{children}</h4>,
                      p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
                      ul: ({children}) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                      ol: ({children}) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                      li: ({children}) => <li className="mb-1">{children}</li>,
                      strong: ({children}) => <strong className="font-semibold text-primary">{children}</strong>,
                      em: ({children}) => <em className="italic">{children}</em>,
                      code: ({children}) => <code className="bg-surface px-1 py-0.5 rounded text-sm font-mono">{children}</code>,
                      pre: ({children}) => <pre className="bg-surface p-3 rounded overflow-x-auto text-sm">{children}</pre>
                    }}
                  >
                    {cleanMarkdownContent(message.content)}
                  </ReactMarkdown>
                )}
              </div>

              {/* Metadata */}
              {message.metadata && (
                <div className="mt-3 pt-2 border-t border-border">
                  <div className="text-xs text-secondary">
                    Confidence: {(message.metadata.confidence_score * 100).toFixed(1)}% • 
                    Sources: {message.metadata.sources_used || 0}
                  </div>
                </div>
              )}

              {/* Citations */}
              {message.citations && message.citations.length > 0 && (
                <div className="mt-3 pt-2 border-t border-border">
                  <div className="text-xs font-medium text-secondary mb-1">Sources:</div>
                  <div className="space-y-1">
                    {message.citations.map((citation, index) => (
                      <div key={index} className="text-xs text-tertiary">
                        • {citation.title} ({(citation.relevance_score * 100).toFixed(1)}% relevance)
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Follow-up Questions */}
              {message.followUpQuestions && message.followUpQuestions.length > 0 && (
                <div className="mt-3 pt-2 border-t border-border">
                  <div className="text-xs font-medium text-secondary mb-2">Suggested follow-up questions:</div>
                  <div className="space-y-1">
                    {message.followUpQuestions.map((question, index) => (
                      <button
                        key={index}
                        className="block w-full text-left text-xs p-2 rounded bg-surface hover:bg-surface-hover transition-colors"
                        onClick={() => handleFollowUpClick(question)}
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-surface border border-border rounded-lg p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <Bot size={16} className="text-primary" />
                <span className="text-sm font-medium">Legal Assistant</span>
              </div>
              <div className="flex items-center gap-2">
                <LoadingSpinner size="small" />
                <span className="text-sm text-secondary">Analyzing your question...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-border p-4 space-y-3">
        {/* Quick Actions */}
        <div className="flex flex-wrap gap-2">
          {[
            'What are the key compliance requirements for hiring in India?',
            'What should be included in an employment contract?',
            'What are the legal requirements for employee termination?',
            'What are mandatory employee benefits in India?'
          ].map((question, index) => (
            <button
              key={index}
              className="text-xs px-3 py-1 rounded-full bg-surface hover:bg-surface-hover border border-border transition-colors"
              onClick={() => setInputMessage(question)}
            >
              {question.split('?')[0]}?
            </button>
          ))}
        </div>

        {/* Input Field */}
        <div className="flex gap-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about employment law, HR policies, compliance requirements..."
            className="flex-1 min-h-[80px] p-3 border border-border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            disabled={loading}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || loading}
            variant="primary"
            size="lg"
            icon={Send}
            className="self-end"
          >
            Send
          </Button>
        </div>
      </div>
    </Card>
  );
};

export default LegalChat;
