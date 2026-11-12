type ScanEventHandler = (event: string, data: any) => void;

class ScanWebSocketClient {
  private ws: WebSocket | null = null;
  private listeners: Set<ScanEventHandler> = new Set();
  private reconnectTimer: any = null;
  private isExplicitlyClosed = false;

  public connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isExplicitlyClosed = false;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/scan`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        // Send keep-alive ping periodically
      };

      this.ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          if (parsed.event) {
            this.notifyListeners(parsed.event, parsed.data);
          }
        } catch (e) {
          console.debug('Failed to parse WebSocket message:', e);
        }
      };

      this.ws.onclose = () => {
        if (!this.isExplicitlyClosed) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (err) => {
        console.debug('WebSocket error:', err);
        this.ws?.close();
      };
    } catch (e) {
      console.debug('WebSocket connection initialization error:', e);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, 3000);
  }

  public subscribe(handler: ScanEventHandler) {
    this.listeners.add(handler);
    return () => {
      this.listeners.delete(handler);
    };
  }

  private notifyListeners(event: string, data: any) {
    this.listeners.forEach((fn) => fn(event, data));
  }

  public disconnect() {
    this.isExplicitlyClosed = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const wsClient = new ScanWebSocketClient();
