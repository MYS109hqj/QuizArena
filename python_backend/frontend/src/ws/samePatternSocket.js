let socket = null;
let reconnectAttempts = 0;
let isManualClose = false; // 标记是否为手动关闭
let isRouteChange = false; // 标记是否为路由切换
const MAX_RECONNECT_ATTEMPTS = 3;
const RECONNECT_DELAY = 3000;
const CONNECTION_TIMEOUT = 5000;

function getStorageKey(gameType) {
  return `${gameType}_LAST_CONNECTION`;
}

export function connectSPHSocket(onMessage, roomId, player_info, gameType = 'o3MB') {
  if (!roomId) {
    const hasRestored = restoreConnection(onMessage);
    if (hasRestored) {
      return;
    }
  }

  if (roomId) {
    localStorage.removeItem(getStorageKey(gameType));
  }

  isManualClose = false;
  isRouteChange = false;

  _connectWebSocket(onMessage, roomId, player_info, gameType);
}

export function setRouteChanging(value) {
  isRouteChange = value;
  if (value) {
    sessionStorage.setItem('SPH_ROUTE_CHANGING', 'true');
  } else {
    sessionStorage.removeItem('SPH_ROUTE_CHANGING');
  }
}

function _connectWebSocket(onMessage, roomId, player_info, gameType) {
  if (socket) {
    // 先移除旧的事件监听器，避免内存泄漏
    socket.onopen = null;
    socket.onmessage = null;
    socket.onclose = null;
    socket.onerror = null;
    socket.close();
  }

  console.log(`🔗 开始建立WebSocket连接: ${import.meta.env.VITE_WEBSOCKET_URL}/${roomId}/${gameType}`);
  const connectStartTime = Date.now();

  socket = new WebSocket(`${import.meta.env.VITE_WEBSOCKET_URL}/${roomId}/${gameType}`);

  // 设置连接超时
  const connectionTimeout = setTimeout(() => {
    if (socket.readyState === WebSocket.CONNECTING) {
      console.log(`⏱️ WebSocket连接超时 (${CONNECTION_TIMEOUT}ms)`);
      socket.close();
    }
  }, CONNECTION_TIMEOUT);

  socket.onopen = () => {
    clearTimeout(connectionTimeout);
    const connectTime = Date.now() - connectStartTime;
    console.log(`✅ SPH WebSocket连接成功，耗时: ${connectTime}ms`);
    reconnectAttempts = 0; // 重置重连计数
    sendSPHMessage({ "type": "player_info", ...player_info });
  };

  socket.onmessage = e => onMessage(JSON.parse(e.data));

  socket.onclose = (event) => {
    clearTimeout(connectionTimeout);
    console.log('SPH WebSocket closed', event.code, event.reason);

    // 检查是否是路由切换导致的正常关闭
    const sessionRouteChange = sessionStorage.getItem('SPH_ROUTE_CHANGING');

    // 只有在非手动关闭、非路由切换、需要重连时才尝试重连
    if (!isManualClose &&
      !isRouteChange &&
      !sessionRouteChange &&
      reconnectAttempts < MAX_RECONNECT_ATTEMPTS &&
      shouldReconnect(event)) {
      reconnectAttempts++;
      console.log(`Attempting to reconnect (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);

      // 保存连接信息用于重连，不保存onMessage回调函数
      const connectionInfo = { roomId, player_info, gameType };
      localStorage.setItem(getStorageKey(gameType), JSON.stringify(connectionInfo));

      setTimeout(() => {
        _connectWebSocket(onMessage, roomId, player_info, gameType);
      }, RECONNECT_DELAY);
    } else {
      localStorage.removeItem(getStorageKey(gameType));
      console.log('WebSocket connection closed permanently');

      if (sessionRouteChange) {
        sessionStorage.removeItem('SPH_ROUTE_CHANGING');
      }
    }
  };

  socket.onerror = (error) => {
    clearTimeout(connectionTimeout);
    console.error('WebSocket error:', error);
  };
}

// 判断是否需要重连的函数
function shouldReconnect(event) {
  // 这些是常见的正常关闭代码，不需要重连
  const normalCloseCodes = [1000, 1001, 1005, 1006];

  // 如果是正常关闭代码，不重连
  if (normalCloseCodes.includes(event.code)) {
    return false;
  }

  // 如果原因是正常关闭，不重连
  if (event.reason && event.reason.includes('Normal closure')) {
    return false;
  }

  // 其他情况尝试重连
  return true;
}

export function sendSPHMessage(msg) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(msg));
    console.log('Sent message:', msg);
  } else {
    console.error('WebSocket is not open. Ready state:', socket ? socket.readyState : 'No socket');
  }
}

export function closeSPHSocket(gameType = 'o3MB') {
  if (socket) {
    isManualClose = true;
    socket.close(1000, 'Normal closure');
    localStorage.removeItem(getStorageKey(gameType));
  }
}

export function hasPendingConnection(gameType = 'o3MB') {
  const sessionRouteChange = sessionStorage.getItem('SPH_ROUTE_CHANGING');
  if (sessionRouteChange) {
    return false;
  }
  return localStorage.getItem(getStorageKey(gameType)) !== null;
}

export function isWebSocketActive() {
  return socket && socket.readyState === WebSocket.OPEN;
}

export function restoreConnection(onMessage) {
  try {
    const gameTypes = ['o2SPH', 'o3MB'];
    for (const gameType of gameTypes) {
      const savedConnection = localStorage.getItem(getStorageKey(gameType));
      if (savedConnection) {
        const connectionInfo = JSON.parse(savedConnection);
        const { roomId, player_info, gameType: savedGameType } = connectionInfo;

        if (roomId && player_info && savedGameType) {
          console.log(`🔄 恢复连接: roomId=${roomId}, gameType=${savedGameType}`);
          connectSPHSocket(onMessage, roomId, player_info, savedGameType);

          sessionStorage.setItem('SPH_CONNECTION_RESTORED', 'true');

          return true;
        }
      }
    }
  } catch (error) {
    console.error('Failed to restore WebSocket connection:', error);
    localStorage.removeItem('SPH_LAST_CONNECTION');
  }
  return false;
}