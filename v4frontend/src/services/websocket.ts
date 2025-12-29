import { io, Socket } from 'socket.io-client'
import type { WebSocketMessage } from '../types'

class WebSocketService {
  private socket: Socket | null = null
  private callbacks: Map<string, Function[]> = new Map()

  connect(userId: string, userType: 'user' | 'admin' = 'user'): void {
    if (this.socket?.connected) {
      return
    }

    const wsUrl = import.meta.env.VITE_WS_URL || 'http://localhost:8000'
    
    this.socket = io(wsUrl, {
      transports: ['websocket'],
      timeout: 5000,
    })

    this.socket.on('connect', () => {
      console.log('WebSocket connected')
      this.socket?.emit('authenticate', { user_id: userId, user_type: userType })
    })

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected')
    })

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error)
    })

    // Handle incoming messages
    this.socket.on('queue_item_update', (data) => {
      this.triggerCallbacks('queue_item_update', data)
    })

    this.socket.on('analysis_completed', (data) => {
      this.triggerCallbacks('analysis_completed', data)
    })

    this.socket.on('notification', (data) => {
      this.triggerCallbacks('notification', data)
    })

    this.socket.on('system_alert', (data) => {
      this.triggerCallbacks('system_alert', data)
    })

    this.socket.on('dashboard_update', (data) => {
      this.triggerCallbacks('dashboard_update', data)
    })
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    this.callbacks.clear()
  }

  on(event: string, callback: Function): void {
    if (!this.callbacks.has(event)) {
      this.callbacks.set(event, [])
    }
    this.callbacks.get(event)?.push(callback)
  }

  off(event: string, callback: Function): void {
    const eventCallbacks = this.callbacks.get(event)
    if (eventCallbacks) {
      const index = eventCallbacks.indexOf(callback)
      if (index > -1) {
        eventCallbacks.splice(index, 1)
      }
    }
  }

  private triggerCallbacks(event: string, data: any): void {
    const eventCallbacks = this.callbacks.get(event)
    if (eventCallbacks) {
      eventCallbacks.forEach(callback => callback(data))
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false
  }

  emit(event: string, data: any): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data)
    }
  }
}

export const websocketService = new WebSocketService()
