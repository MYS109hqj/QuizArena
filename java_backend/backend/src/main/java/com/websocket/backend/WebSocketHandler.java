package com.websocket.backend;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.web.socket.*;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.util.Map;

public class WebSocketHandler extends TextWebSocketHandler {
    private final ConnectionManager manager = new ConnectionManager();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        String roomId = session.getUri().getPath().split("/")[2];
        session.getAttributes().put("roomId", roomId);  // 存储 roomId
        System.out.println("连接建立：房间 ID = " + roomId + ", 会话 ID = " + session.getId());

        // String initialData = (String) session.getAttributes().get("initialData");
        // System.out.println(1);
        // Map<String, Object> playerInfo = objectMapper.readValue(initialData, Map.class);
        // System.out.println(2);
        // manager.connect(roomId, session, playerInfo);  // 调用 ConnectionManager 连接逻辑
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String payload = message.getPayload();
        Map<String, Object> data = objectMapper.readValue(payload, Map.class);
        String roomId = (String) session.getAttributes().get("roomId");
        String type = (String) data.get("type");

        System.out.println("收到消息: 类型 = " + type + ", 内容 = " + payload + ", 房间 ID = " + roomId);

        switch (type) {
            case "join":
                manager.connect(roomId, session, data);
                break;
            case "mode_change":
                manager.updateMode(roomId, data);
                break;
            case "initialize_scores":
            case "initialize_lives":
                manager.initializePlayers(roomId, data);
                break;

            case "round_update":
                manager.updateRound(roomId, data);
                break;

            case "get_latest_answers":
                manager.getLatestAnswers(roomId);
                break;

            case "question":
                manager.setQuestion(roomId, data);
                break;

            case "answer":
                manager.submitAnswer(roomId, data, session);
                break;

            case "judgement":
                manager.judgeAnswers(roomId, data);
                break;

            default:
                System.out.println("未知消息类型: " + type);
                break;
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) throws Exception {
        String roomId = (String) session.getAttributes().get("roomId");
        String userId = (String) session.getAttributes().get("userId");
        System.out.println("连接关闭: 房间 ID = " + roomId + ", 用户 ID = " + userId + ", 状态 = " + status);
        manager.disconnect(roomId, session, userId);
    }
}
