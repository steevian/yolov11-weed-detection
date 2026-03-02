import { io, Socket } from 'socket.io-client';

export class SocketService {
  private socket: Socket;

  constructor() {
    this.socket = io('/', {
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      transports: ['polling', 'websocket'],
    });

    this.setupListeners();
  }

  private setupListeners = () => {
    this.socket.on('connect', () => {
      console.log('Connected to Weed Detection WebSocket server!');
    });

    this.socket.on('disconnect', (reason: string) => {
      console.log('Socket disconnected:', reason);
    });

    this.socket.on('connect_error', (error: Error) => {
      console.error('Socket connection error:', error.message);
    });
  }

  // 添加 off 方法 - 解决 "socketService.off is not a function" 错误
  off(event: string, callback?: (data: any) => void): void {
    if (callback) {
      // 移除特定回调的监听器
      this.socket.off(event, callback);
    } else {
      // 移除该事件的所有监听器
      this.socket.off(event);
    }
  }

  on(event: string, callback: (data: any) => void): void {
    this.socket.on(event, callback);
  }

  emit(event: string, data: any): void {
    if (this.socket.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('Socket not connected, cannot emit event:', event);
      // 尝试重新连接
      this.socket.connect();
      // 延迟发送
      setTimeout(() => {
        if (this.socket.connected) {
          this.socket.emit(event, data);
        }
      }, 1000);
    }
  }

  connect(url?: string): void {
    if (url && url !== this.socket.io.uri) {
      this.socket.disconnect();
      this.socket.io.uri = url;
    }
    if (!this.socket.connected) {
      this.socket.connect();
    }
  }

  disconnect(): void {
    if (this.socket.connected) {
      this.socket.disconnect();
    }
  }

  close(): void {
    this.disconnect();
  }

  get isConnected(): boolean {
    return this.socket.connected;
  }

  // 新增：移除所有事件监听器
  removeAllListeners(): void {
    this.socket.removeAllListeners();
  }

  // 新增：获取连接状态详情
  get connectionState(): string {
    if (!this.socket) return 'not_initialized';
    return this.socket.connected ? 'connected' : this.socket.disconnected ? 'disconnected' : 'connecting';
  }

  // 新增：等待连接建立
  waitForConnection(timeout = 5000): Promise<boolean> {
    return new Promise((resolve) => {
      if (this.socket.connected) {
        resolve(true);
        return;
      }

      const timer = setTimeout(() => {
        this.socket.off('connect', onConnect);
        resolve(false);
      }, timeout);

      const onConnect = () => {
        clearTimeout(timer);
        resolve(true);
      };

      this.socket.once('connect', onConnect);
    });
  }
}

// 导出单例实例
export const socketService = new SocketService();

// 可选：创建全局Socket实例的方法
export const createSocketService = (url?: string): SocketService => {
  if (url) {
    return new SocketService(); // 注意：这里应该使用新的URL，但需要修改构造函数
  }
  return socketService;
};