let socket = null;

export function connectQuizSocket(roomId, onMessage) {
  if (socket) socket.close();
  socket = new WebSocket(`${import.meta.env.VITE_WEBSOCKET_URL}/${roomId}/quiz`);
  socket.onopen = () => console.log('Quiz WebSocket connected');
  socket.onmessage = event => onMessage(JSON.parse(event.data));
  socket.onclose = () => console.log('Quiz WebSocket closed');
}

export function sendQuizMessage(message) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(message));
  }
}

export function closeQuizSocket() {
  if (socket) socket.close();
}