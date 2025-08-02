import { useState, useEffect, useCallback, useRef } from 'react';
import { AnalyticsMetrics, RealTimeUpdate, SystemHealth } from '../../types/analytics';

interface UseRealTimeMetricsOptions {
  enabled?: boolean;
  reconnectInterval?: number; // in milliseconds
  maxReconnectAttempts?: number;
}

interface UseRealTimeMetricsReturn {
  metrics: AnalyticsMetrics | null;
  systemHealth: SystemHealth | null;
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastUpdate: Date | null;
  connect: () => void;
  disconnect: () => void;
  sendHeartbeat: () => void;
}

export const useRealTimeMetrics = (
  options: UseRealTimeMetricsOptions = {}
): UseRealTimeMetricsReturn => {
  const {
    enabled = true,
    reconnectInterval = 5000, // 5 seconds
    maxReconnectAttempts = 10
  } = options;

  const [metrics, setMetrics] = useState<AnalyticsMetrics | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const heartbeatIntervalRef = useRef<number | null>(null);

  const getWebSocketUrl = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/api/ws/analytics`;
  };

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const update: RealTimeUpdate = JSON.parse(event.data);
      
      switch (update.type) {
        case 'metric_update':
          if (update.data.metrics) {
            setMetrics(update.data.metrics);
          }
          if (update.data.systemHealth) {
            setSystemHealth(update.data.systemHealth);
          }
          setLastUpdate(new Date(update.timestamp));
          break;
          
        case 'system_status':
          setSystemHealth(update.data);
          setLastUpdate(new Date(update.timestamp));
          break;
          
        case 'alert':
          // Handle alerts - could trigger notifications
          console.log('Real-time alert:', update.data);
          break;
          
        default:
          console.log('Unknown update type:', update.type);
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }, []);

  const handleOpen = useCallback(() => {
    console.log('WebSocket connected');
    setIsConnected(true);
    setConnectionStatus('connected');
    reconnectAttemptsRef.current = 0;
    
    // Start heartbeat
    heartbeatIntervalRef.current = setInterval(() => {
      sendHeartbeat();
    }, 30000); // Send heartbeat every 30 seconds
  }, []);

  const handleClose = useCallback((event: CloseEvent) => {
    console.log('WebSocket disconnected:', event.code, event.reason);
    setIsConnected(false);
    
    // Clear heartbeat interval
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
    
    if (event.code !== 1000 && enabled && reconnectAttemptsRef.current < maxReconnectAttempts) {
      // Abnormal closure, attempt to reconnect
      setConnectionStatus('connecting');
      reconnectAttemptsRef.current += 1;
      
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, reconnectInterval);
    } else {
      setConnectionStatus('disconnected');
    }
  }, [enabled, maxReconnectAttempts, reconnectInterval]);

  const handleError = useCallback((error: Event) => {
    console.error('WebSocket error:', error);
    setConnectionStatus('error');
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    if (wsRef.current) {
      wsRef.current.close();
    }

    try {
      setConnectionStatus('connecting');
      wsRef.current = new WebSocket(getWebSocketUrl());
      
      wsRef.current.onopen = handleOpen;
      wsRef.current.onmessage = handleMessage;
      wsRef.current.onclose = handleClose;
      wsRef.current.onerror = handleError;
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus('error');
    }
  }, [handleOpen, handleMessage, handleClose, handleError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'User requested disconnect');
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  const sendHeartbeat = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'heartbeat',
        timestamp: new Date().toISOString()
      }));
    }
  }, []);

  // Auto-connect when enabled
  useEffect(() => {
    if (enabled) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // Handle page visibility change to manage connection
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page is hidden, can reduce update frequency or pause connection
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }
      } else {
        // Page is visible, resume normal operation
        if (isConnected && !heartbeatIntervalRef.current) {
          heartbeatIntervalRef.current = setInterval(() => {
            sendHeartbeat();
          }, 30000);
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isConnected, sendHeartbeat]);

  return {
    metrics,
    systemHealth,
    isConnected,
    connectionStatus,
    lastUpdate,
    connect,
    disconnect,
    sendHeartbeat
  };
};