package com.websocket.backend;

import org.springframework.web.socket.WebSocketSession;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.web.socket.TextMessage;

import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class ConnectionManager {
    private final Map<String, Room> rooms = new HashMap<>();

    public void connect(String roomId, WebSocketSession session, Map<String, Object> playerInfo) {
        Room room = rooms.computeIfAbsent(roomId, k -> new Room());
        String playerId = (String) playerInfo.get("id");

        // 检查玩家是否在最近的时间内重连
        if (room.getPlayers().containsKey(playerId)) {
            Player player = room.getPlayers().get(playerId);
            player.setLastActiveTimestamp(System.currentTimeMillis()); // 更新活动时间
            room.getConnections().add(session);
            System.out.println("玩家 " + player.getName() + " 在最近的时间内重连，恢复连接");
        } else {
            // 新玩家加入
            Player player = new Player(playerId, (String) playerInfo.get("name"), (String) playerInfo.get("avatar"));
            // 修改了
            room.addPlayer(playerId, player, session);
            System.out.println("新玩家加入: " + playerInfo);
        }

        // 广播玩家加入
        broadcastPlayerJoinNotification(roomId, playerInfo);

        // 广播当前问题（如果存在）
        if (room.getCurrentQuestion() != null) {
            broadcastQuestion(roomId, room.getCurrentQuestion());
        }

        // 广播模式和当前轮次
        broadcastModeChange(roomId, room.getMode());
        broadcastRoundUpdate(roomId, room);
        broadcastPlayerList(roomId); // 更新玩家列表
    }

    public void disconnect(String roomId, WebSocketSession session, String userId) {
        Room room = rooms.get(roomId);
        if (room != null) {
            System.out.println("玩家 " + userId + " 断开连接");
            room.removeSession(session, userId);
            if (room.isEmpty()) {
                rooms.remove(roomId);
                System.out.println("房间 " + roomId + " 已空，删除房间");
            } else {
                broadcastPlayerList(roomId); // 更新玩家列表
            }
        }
    }
    
    public Room getRoom(String roomId){
        return rooms.get(roomId);
    }

    public void updateMode(String roomId, Map<String, Object> data) {
        Room room = rooms.get(roomId);
        if (room != null) {
            room.setMode((String) data.get("mode"));
            System.out.println("房间 " + roomId + " 模式更改为 " + room.getMode());
            broadcastModeChange(roomId, room.getMode());
        }
    }

    public void initializePlayers(String roomId, Map<String, Object> data) {
        Room room = rooms.get(roomId);
        if (room != null) {
            int value = 0;
            String type = (String) data.get("type");
            System.out.println("初始化房间 " + roomId + " 的玩家，类型: " + type);
            if ("initialize_scores".equals(type)){
                value = (int) data.get("score");
                room.initializePlayers("scores", value);
                System.out.println(1);
            }else if ("initialize_lives".equals(type)){
                value = (int) data.get("lives");
                room.initializePlayers("lives", value);
                System.out.println(2);
            }
            
            broadcastPlayerList(roomId); // 更新玩家列表
        }
    }

    public void updateRound(String roomId, Map<String, Object> data) {
        Room room = rooms.get(roomId);
        if (room != null) {
            room.setCurrentRound((int) data.get("currentRound"));
            room.setTotalRounds((int) data.get("totalRounds"));
            System.out.println("房间 " + roomId + " 的当前轮次更新为: " + room.getCurrentRound() + ", 总轮次: " + room.getTotalRounds());
            broadcastRoundUpdate(roomId, room);
        }
    }

    public void getLatestAnswers(String roomId) {
        Room room = rooms.get(roomId);
        if (room != null) {
            System.out.println("获取房间 " + roomId + " 的最新答案");
            broadcastLatestAnswers(roomId, room.getLatestAnswers());
        }
    }

    public void setQuestion(String roomId, Map<String, Object> data) {
        Room room = rooms.get(roomId);
        if (room != null) {
            room.setCurrentQuestion(data);
            System.out.println("房间 " + roomId + " 的问题设置为: " + data);
            broadcastQuestion(roomId, data);
        }
    }

    public void submitAnswer(String roomId, Map<String, Object> data, WebSocketSession session) {
        Room room = rooms.get(roomId);
        if (room != null) {
            String playerId = (String) data.get("playerId");
            String answer = (String) data.get("text");
            System.out.println("玩家 " + playerId + " 在房间 " + roomId + " 提交答案: " + answer);
            room.submitAnswer(playerId, answer);
            broadcastToConnections(roomId, data);
        }
    }

    public void judgeAnswers(String roomId, Map<String, Object> data) {
        Room room = rooms.get(roomId);
        if (room != null) {
            System.out.println("开始判题，房间 " + roomId);
            Map<String, Object> results = (Map<String, Object>) data.get("results");
            room.judgeAnswers(results);
            int round = room.getCurrentRound();
            broadcastJudgementResults(roomId, room.getJudgementResults(), round);
            broadcastPlayerList(roomId); // 更新玩家列表
        }
    }

    // 广播相关的方法
    public void broadcastPlayerList(String roomId) {
        Room room = rooms.get(roomId);
        if (room != null) {
            Map<String, Object> message = new HashMap<>();
            message.put("type", "player_list");
    
            // 遍历房间内的所有玩家，使用 getter 方法获取信息
            List<Map<String, Object>> playersList = room.getPlayers().values().stream()
                .map(player -> {
                    Map<String, Object> playerData = new HashMap<>();
                    playerData.put("id", player.getId());
                    playerData.put("name", player.getName());
                    playerData.put("avatar", player.getAvatar());
                    playerData.put("score", player.getScore());
                    playerData.put("lives", player.getLives());
                    return playerData;
                })
                .toList();
    
            message.put("players", playersList);
    
            // 广播该消息
            broadcastToConnections(roomId, message);
        }
    }
    
    private void broadcastPlayerJoinNotification(String roomId, Map<String, Object> playerInfo) {
        Map<String, Object> message = new HashMap<>();
        message.put("type", "notification");
        message.put("message", playerInfo.get("name") + " 已加入房间。");
        broadcastToConnections(roomId, message);
    }

    private void broadcastModeChange(String roomId, String mode) {
        Map<String, Object> message = new HashMap<>();
        message.put("type", "mode_change");
        message.put("currentMode", mode);
        broadcastToConnections(roomId, message);
    }

    private void broadcastRoundUpdate(String roomId, Room room) {
        Map<String, Object> message = new HashMap<>();
        message.put("type", "round");
        message.put("totalRounds", room.getTotalRounds());
        message.put("currentRound", room.getCurrentRound());
        broadcastToConnections(roomId, message);
    }

    private void broadcastLatestAnswers(String roomId, List<Map<String, Object>> latestAnswers) {
        Map<String, Object> message = new HashMap<>();
        message.put("type", "latest_answers");
        message.put("latest_answers", latestAnswers);
        broadcastToConnections(roomId, message);
    }

    private void broadcastQuestion(String roomId, Map<String, Object> question) {
        broadcastToConnections(roomId, question);
    }

    private void broadcastJudgementResults(String roomId, Map<String, Object> judgementResults, int round) {
        Map<String, Object> message = new HashMap<>();
        message.put("type", "judgement_complete");
        message.put("results", judgementResults);
        message.put("round", round); // 可选：传递当前轮次信息
        broadcastToConnections(roomId, message);
    }
    

    public void broadcastToConnections(String roomId, Map<String, Object> message) {
        Room room = rooms.get(roomId);
        if (room != null) {
            String messageJson;
            try {
                messageJson = new ObjectMapper().writeValueAsString(message);
            } catch (Exception e) {
                e.printStackTrace();
                return; // 转换失败时返回
            }
            System.out.println(messageJson);
            for (WebSocketSession connection : room.getConnections()) {
                try {
                    if (connection.isOpen()) {
                        connection.sendMessage(new TextMessage(messageJson));
                    }
                } catch (IOException e) {
                    e.printStackTrace(); // 处理异常
                }
            }
        }
    }
}
