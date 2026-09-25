import { ref } from 'vue';

let socket = null;
let reconnectTimer = null;
let connectionArgs = null;
let manualClose = false;
let attempts = 0;

export const isConnected = ref(false);
export const connectionError = ref(null);

function getWsBaseUrl() {
  const envUrl = import.meta.env.VITE_WEBSOCKET_URL;
  if (envUrl) return envUrl;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws`;
}

function websocketUrl(roomId, gameType) {
  const base = getWsBaseUrl();
  return `${base}/${roomId}/${gameType}`;
}

export function connectFlip7Socket(onMessage, roomId, playerInfo, gameType = 'o4Flip7') {
  if (!roomId || !playerInfo) return false;
  closeFlip7Socket();
  manualClose = false;
  connectionArgs = { onMessage, roomId, playerInfo, gameType };
  const ws = new WebSocket(websocketUrl(roomId, gameType));
  socket = ws;
  ws.onopen = () => {
    if (socket !== ws || ws.readyState !== WebSocket.OPEN) return;
    attempts = 0;
    isConnected.value = true;
    connectionError.value = null;
  };
  ws.onmessage = event => {
    if (socket !== ws) return;
    try { onMessage?.(JSON.parse(event.data)); }
    catch (error) { console.error('Flip 7 消息解析失败', error); }
  };
  ws.onerror = error => { if (socket === ws) connectionError.value = error; };
  ws.onclose = () => {
    if (socket !== ws) return;
    isConnected.value = false;
    socket = null;
    if (!manualClose && connectionArgs && attempts < 5) {
      attempts += 1;
      reconnectTimer = setTimeout(() => connectFlip7Socket(
        connectionArgs.onMessage, connectionArgs.roomId, connectionArgs.playerInfo,
        connectionArgs.gameType), Math.min(15000, attempts * 2000));
    }
  };
  return true;
}

export function sendFlip7Message(message) {
  if (!socket || socket.readyState !== WebSocket.OPEN) return false;
  socket.send(JSON.stringify(message));
  return true;
}

export function closeFlip7Socket() {
  manualClose = true;
  if (reconnectTimer) clearTimeout(reconnectTimer);
  reconnectTimer = null;
  if (socket) socket.close();
  socket = null;
  isConnected.value = false;
}

export function isWebSocketActive() {
  return socket?.readyState === WebSocket.OPEN;
}

export function restoreConnection(onMessage) {
  if (!connectionArgs) return false;
  connectionArgs.onMessage = onMessage;
  if (!socket) connectFlip7Socket(onMessage, connectionArgs.roomId,
    connectionArgs.playerInfo, connectionArgs.gameType);
  return true;
}

export function hasPendingConnection() { return Boolean(connectionArgs); }
export function setRouteChanging() { }
