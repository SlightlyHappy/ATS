/**
 * @file WebSocket service for real-time updates
 * Implements backend v1.3 WebSocket capabilities
 */

import React from 'react';

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

interface ResumeProcessingUpdate {
  resume_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  analysis_result?: any;
  error?: string;
}

interface NotificationUpdate {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
}

class WebSocketServiceClass {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: { [key: string]: Function[] } = {};
  private isDisabled = false;

  constructor() {
    // Check if WebSocket should be disabled
    if (typeof window !== 'undefined') {
      const disableWS = localStorage.getItem('disable_websocket') === 'true';
      if (disableWS) {
        console.log('🔌 WebSocket: Disabled via localStorage');
        this.isDisabled = true;
        return;
      }
    }
    this.connect();
  }

  /**
   * Connect to WebSocket server
   */
  private connect() {
    if (this.isDisabled) {
      console.log('🔌 WebSocket: Connection disabled');
      return;
    }

    try {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'wss://hrtoolsbackend-production.up.railway.app/ws';
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      
      console.log('🔌 WebSocket: Attempting connection to', wsUrl);
    } catch (error) {
      console.warn('⚠️ WebSocket: Connection failed, continuing without real-time updates', error);
      this.isDisabled = true;
      // Don't schedule reconnect on initial failure
    }
  }

  /**
   * Handle WebSocket open
   */
  private handleOpen(event: Event) {
    console.log('✅ WebSocket: Connected successfully');
    this.reconnectAttempts = 0;
    
    // Send authentication if needed
    this.sendAuth();
  }

  /**
   * Handle WebSocket message
   */
  private handleMessage(event: MessageEvent) {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      console.log('📨 WebSocket: Message received', message.type, message.data);
      
      // Emit to specific listeners
      this.emit(message.type, message.data);
      
      // Handle specific message types
      switch (message.type) {
        case 'resume_processing_update':
          this.handleResumeUpdate(message.data);
          break;
        case 'notification':
          this.handleNotification(message.data);
          break;
        case 'system_alert':
          this.handleSystemAlert(message.data);
          break;
        default:
          console.log('📨 WebSocket: Unknown message type', message.type);
      }
    } catch (error) {
      console.error('❌ WebSocket: Failed to parse message', error);
    }
  }

  /**
   * Handle WebSocket close
   */
  private handleClose(event: CloseEvent) {
    console.log('🔌 WebSocket: Connection closed', event.code, event.reason);
    this.ws = null;
    
    // Attempt reconnection if not intentional close
    if (event.code !== 1000) {
      this.scheduleReconnect();
    }
  }

  /**
   * Handle WebSocket error
   */
  private handleError(event: Event) {
    console.warn('⚠️ WebSocket: Connection error, will disable WebSocket for this session', event);
    this.isDisabled = true;
    if (typeof window !== 'undefined') {
      localStorage.setItem('disable_websocket', 'true');
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect() {
    if (this.isDisabled) {
      console.log('🔌 WebSocket: Reconnection disabled');
      return;
    }

    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      console.log(`🔄 WebSocket: Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      
      setTimeout(() => {
        this.connect();
      }, delay);
    } else {
      console.warn('⚠️ WebSocket: Max reconnection attempts reached, disabling WebSocket for this session');
      this.isDisabled = true;
      if (typeof window !== 'undefined') {
        localStorage.setItem('disable_websocket', 'true');
      }
    }
  }

  /**
   * Send authentication token
   */
  private sendAuth() {
    if (typeof window !== 'undefined') {
      const adminToken = document.cookie.split('; ').find(row => row.startsWith('admin_session_token='))?.split('=')[1];
      const userToken = document.cookie.split('; ').find(row => row.startsWith('user_session_token='))?.split('=')[1];
      
      const token = adminToken || userToken;
      if (token && this.ws?.readyState === WebSocket.OPEN) {
        this.send('auth', { token });
      }
    }
  }

  /**
   * Send message to WebSocket server
   */
  send(type: string, data: any) {
    if (this.isDisabled) {
      // Silently ignore if WebSocket is disabled
      return;
    }

    if (this.ws?.readyState === WebSocket.OPEN) {
      const message: WebSocketMessage = {
        type,
        data,
        timestamp: new Date().toISOString()
      };
      
      this.ws.send(JSON.stringify(message));
      console.log('📤 WebSocket: Message sent', type, data);
    } else {
      // Only log warning if not disabled
      if (!this.isDisabled) {
        console.warn('⚠️ WebSocket: Cannot send message - connection not open');
      }
    }
  }

  /**
   * Subscribe to WebSocket events
   */
  on(event: string, callback: Function) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  /**
   * Unsubscribe from WebSocket events
   */
  off(event: string, callback: Function) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  /**
   * Emit event to listeners
   */
  private emit(event: string, data: any) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('❌ WebSocket: Listener error', error);
        }
      });
    }
  }

  /**
   * Handle resume processing updates
   */
  private handleResumeUpdate(data: ResumeProcessingUpdate) {
    console.log('📄 WebSocket: Resume processing update', data);
    
    // Update local state or trigger UI updates
    this.emit('resume_update', data);
  }

  /**
   * Handle notification updates
   */
  private handleNotification(data: NotificationUpdate) {
    console.log('🔔 WebSocket: Notification received', data);
    
    // Show toast notification or update notification center
    this.emit('notification', data);
  }

  /**
   * Handle system alerts
   */
  private handleSystemAlert(data: any) {
    console.log('🚨 WebSocket: System alert', data);
    
    // Handle system-wide alerts
    this.emit('system_alert', data);
  }

  /**
   * Subscribe to resume processing updates
   */
  subscribeToResumeUpdates(resumeIds: string[]) {
    this.send('subscribe_resume_updates', { resume_ids: resumeIds });
  }

  /**
   * Unsubscribe from resume processing updates
   */
  unsubscribeFromResumeUpdates(resumeIds: string[]) {
    this.send('unsubscribe_resume_updates', { resume_ids: resumeIds });
  }

  /**
   * Subscribe to user notifications
   */
  subscribeToNotifications() {
    this.send('subscribe_notifications', {});
  }

  /**
   * Mark notification as read
   */
  markNotificationAsRead(notificationId: string) {
    this.send('mark_notification_read', { notification_id: notificationId });
  }

  /**
   * Get connection status
   */
  isConnected(): boolean {
    return !this.isDisabled && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Close WebSocket connection
   */
  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }
}

// React hook for WebSocket integration
export function useWebSocket() {
  const [connected, setConnected] = React.useState(WebSocketService.isConnected());
  
  React.useEffect(() => {
    const handleConnection = () => setConnected(true);
    const handleDisconnection = () => setConnected(false);
    
    WebSocketService.on('open', handleConnection);
    WebSocketService.on('close', handleDisconnection);
    
    return () => {
      WebSocketService.off('open', handleConnection);
      WebSocketService.off('close', handleDisconnection);
    };
  }, []);
  
  return {
    connected,
    send: WebSocketService.send.bind(WebSocketService),
    on: WebSocketService.on.bind(WebSocketService),
    off: WebSocketService.off.bind(WebSocketService),
    subscribeToResumeUpdates: WebSocketService.subscribeToResumeUpdates.bind(WebSocketService),
    subscribeToNotifications: WebSocketService.subscribeToNotifications.bind(WebSocketService)
  };
}

// React hook for resume processing updates
export function useResumeUpdates(resumeIds: string[]) {
  const [updates, setUpdates] = React.useState<{ [key: string]: ResumeProcessingUpdate }>({});
  
  React.useEffect(() => {
    const handleUpdate = (data: ResumeProcessingUpdate) => {
      setUpdates(prev => ({
        ...prev,
        [data.resume_id]: data
      }));
    };
    
    WebSocketService.on('resume_update', handleUpdate);
    WebSocketService.subscribeToResumeUpdates(resumeIds);
    
    return () => {
      WebSocketService.off('resume_update', handleUpdate);
      WebSocketService.unsubscribeFromResumeUpdates(resumeIds);
    };
  }, [resumeIds]);
  
  return updates;
}

// Export singleton instance
export const WebSocketService = new WebSocketServiceClass();
export type { WebSocketMessage, ResumeProcessingUpdate, NotificationUpdate };
