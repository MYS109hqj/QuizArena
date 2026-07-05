import { ref } from 'vue';

let socket = null;
let isManualClose = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 3000;

const isConnected = ref(false);
const connectionError = ref(null);

function getWebSocketUrl(roomId, gameType) {
  return `${import.meta.env.VITE_WEBSOCKET_URL}/${roomId}/${gameType}`;
}

export function connectTemplateSocket(onMessage, roomId, player_info, gameType = 'o999Template') {
  if (!roomId) {
    const hasRestored = restoreConnection(onMessage);
    if (!hasRestored) {
      console.error('❌ 没有找到有效的roomId，无法建立连接');
    }
    return;
  }

  if (socket && socket.readyState === WebSocket.OPEN) {
    console.log('⚠️ 已存在活跃连接，先关闭旧连接');
    closeTemplateSocket();
  }

  const url = getWebSocketUrl(roomId, gameType);
  console.log(`🔗 正在连接 Template WebSocket: ${url}`);

  socket = new WebSocket(url);

  socket.onopen = () => {
    console.log('✅ Template WebSocket 连接成功');
    isConnected.value = true;
    connectionError.value = null;
    reconnectAttempts = 0;

    const joinMessage = JSON.stringify({
      id: player_info.player_id,
      name: player_info.player_name,
      avatar: player_info.avatarUrl
    });
    socket.send(joinMessage);
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (onMessage) {
        onMessage(data);
      }
    } catch (error) {
      console.error('❌ 解析消息失败:', error, event.data);
    }
  };

  socket.onerror = (error) => {
    console.error('❌ Template WebSocket 错误:', error);
    connectionError.value = error;
  };

  socket.onclose = (event) => {
    console.log(`🔌 Template WebSocket 关闭: ${event.code} - ${event.reason}`);
    isConnected.value = false;

    if (!isManualClose && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      reconnectAttempts++;
      console.log(`🔄 尝试重连... (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
      setTimeout(() => {
        connectTemplateSocket(onMessage, roomId, player_info, gameType);
      }, RECONNECT_DELAY * reconnectAttempts);
    } else if (!isManualClose) {
      console.error('❌ 重连失败，已达到最大尝试次数');
    }

    isManualClose = false;
  };
}

export function sendTemplateMessage(message) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    try {
      socket.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('❌ 发送消息失败:', error);
      return false;
    }
  } else {
    console.error('❌ WebSocket 未连接');
    return false;
  }
}

export function closeTemplateSocket(gameType = 'o999Template') {
  if (socket) {
    isManualClose = true;
    socket.close();
    socket = null;
  }
}

export function isWebSocketActive() {
  return socket && socket.readyState === WebSocket.OPEN;
}

export function hasPendingConnection(gameType = 'o999Template') {
  const sessionRouteChange = sessionStorage.getItem('TEMPLATE_ROUTE_CHANGING');
  if (sessionRouteChange) {
    sessionStorage.removeItem('TEMPLATE_ROUTE_CHANGING');
    return true;
  }
  return false;
}

export function restoreConnection(onMessage) {
  if (!socket) {
    console.log('❌ 没有可恢复的连接');
    return false;
  }

  console.log('🔄 恢复连接...');
  if (onMessage) {
    const originalOnMessage = socket.onmessage;
    socket.onmessage = (event) => {
      originalOnMessage(event);
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('❌ 解析恢复连接消息失败:', error);
      }
    };
  }
  return true;
}

export function setRouteChanging() {
  sessionStorage.setItem('TEMPLATE_ROUTE_CHANGING', 'true');
}

export { isConnected, connectionError };
