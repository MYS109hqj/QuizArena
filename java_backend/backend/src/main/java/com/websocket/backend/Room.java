package com.websocket.backend;

import org.springframework.web.socket.WebSocketSession;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class Room {
    private List<WebSocketSession> connections; // WebSocket 连接
    private Map<String, Player> players; // 房间内的玩家
    private Map<String, Object> currentQuestion; // 当前问题
    private String mode; // 房间模式
    private int currentRound; // 当前轮次
    private int totalRounds; // 总轮次
    private boolean judgementPending; // 判题等待标志
    private Map<String, String> currentAnswers; // 当前玩家的答案
    private final long reconnectTimeout = 5  * 1000; // 5秒钟的超时设置
    private ScheduledExecutorService scheduler;
    private Map<String, Object> judgementResults;

    public Room() {
        this.connections = new ArrayList<>();
        this.players = new HashMap<>();
        this.mode = "none";
        this.currentRound = 0;
        this.totalRounds = 0;
        this.judgementPending = false;
        this.currentAnswers = new HashMap<>();
        this.scheduler = Executors.newScheduledThreadPool(1); // 创建定时任务调度器
    }

    public void checkExpiredPlayers() {
        long currentTime = System.currentTimeMillis();
        List<String> expiredPlayers = new ArrayList<>();

        for (Map.Entry<String, Player> entry : players.entrySet()) {
            String playerId = entry.getKey();
            Player player = entry.getValue();
            if (currentTime - player.getLastActiveTimestamp() >= reconnectTimeout) {
                expiredPlayers.add(playerId);
            }
        }

        for (String expiredPlayerId : expiredPlayers) {
            removeSession(null, expiredPlayerId); // 从连接和玩家列表中移除
        }
    }

    public void addPlayer(String playerId, WebSocketSession session, Map<String, Object> playerInfo) {
        Player player = new Player(playerId, (String) playerInfo.get("name"), (String) playerInfo.get("avatar"));
        players.put(playerId, player);
        connections.add(session);
        player.setLastActiveTimestamp(System.currentTimeMillis());
    }

    public void addPlayer(String playerId, Player player, WebSocketSession session) {
        players.put(playerId, player);
        connections.add(session);
        player.setLastActiveTimestamp(System.currentTimeMillis());
    }

    public void removeSession(WebSocketSession session, String userId) {
        connections.remove(session);
        if (players.containsKey(userId)) {
            Player player = players.get(userId);
            player.setLastActiveTimestamp(System.currentTimeMillis()); // 记录断开时间
            schedulePlayerExpirationCheck(userId); // 安排超时检查
        }
    }

    private void schedulePlayerExpirationCheck(String playerId) {
        scheduler.schedule(() -> checkExpiredPlayer(playerId), reconnectTimeout, TimeUnit.MILLISECONDS);
    }

    private void checkExpiredPlayer(String playerId) {
        Player player = players.get(playerId);
        if (player != null) {
            long currentTime = System.currentTimeMillis();
            // 判断是否超过重连时间
            if (currentTime - player.getLastActiveTimestamp() >= reconnectTimeout) {
                players.remove(playerId); // 超时，移除玩家数据
                System.out.println("玩家 " + playerId + " 超时未重连，已删除数据");
            }
        }
    }

    public boolean isEmpty() {
        return players.isEmpty();
    }

    public void setMode(String mode) {
        this.mode = mode;
    }

    public void setCurrentRound(int currentRound) {
        this.currentRound = currentRound;
    }

    public void setTotalRounds(int totalRounds) {
        this.totalRounds = totalRounds;
    }

    public void initializePlayers(String type, int value) {
        for (Player player : players.values()) {
            if ("scores".equals(type)) {
               player.setScore(value);
               System.out.println(1);
            } else if ("lives".equals(type)) {
                player.setLives(value);
                System.out.println(2);
            }
        }
    }

    public void setCurrentQuestion(Map<String, Object> question) {
        this.currentQuestion = question;
    }

    public void submitAnswer(String playerId, String answer) {
        currentAnswers.put(playerId, answer);
    }

    public void judgeAnswers(Map<String, Object> results) {
        Map<String, Object> updatedResults = new HashMap<>();

        for (Map.Entry<String, Object> entry : results.entrySet()) {
            String playerId = entry.getKey();
            Object resultObj = entry.getValue();

            // 确保 resultObj 是 Map 类型
            if (resultObj instanceof Map) {
                Map<String, Object> result = (Map<String, Object>) resultObj;
                Player player = players.get(playerId);

                if (player != null) {
                    if ("scoring".equals(mode)) {
                        int score = (int) result.getOrDefault("score", 0);
                        player.setRoundScore(score);
                        player.setScore(player.getScore() + score);
                    } else if ("survival".equals(mode)) {
                        int lostLives = (int) result.getOrDefault("lostLives", 0);
                        player.setLives(player.getLives() - lostLives);
                        player.setLostLivesThisRound(lostLives);
                    }

                    player.setJudgementCorrect((boolean) result.getOrDefault("correct", false));

                    Map<String, Object> playerResult = new HashMap<>();
                    playerResult.put("name", player.getName());
                    playerResult.put("avatar", player.getAvatar());
                    playerResult.put("correct", result.getOrDefault("correct", false));
                    playerResult.put("score", "scoring".equals(mode) ? (int) result.getOrDefault("score", 0) : null);
                    playerResult.put("lostLives", "survival".equals(mode) ? (int) result.getOrDefault("lostLives", 0) : null);

                    updatedResults.put(playerId, playerResult);
                }
            } else {
                System.out.println("错误：玩家数据格式不正确，无法处理判题结果");
            }
        }

        judgementPending = false;
        setJudgementResults(updatedResults);
    }
 
    public void setJudgementResults(Map<String, Object> results) {
        this.judgementResults = results;
    }
    
    public Map<String, Object> getJudgementResults() {
        return judgementResults; // 返回判题结果
    }

    public List<Map<String, Object>> getLatestAnswers() {
        // 返回最新答案
        List<Map<String, Object>> latestAnswers = new ArrayList<>();
        for (Map.Entry<String, Player> entry : players.entrySet()) {
            String playerId = entry.getKey();
            Player player = entry.getValue();
            latestAnswers.add(new HashMap<String, Object>() {{
                put("id", playerId);
                put("name", player.getName());
                put("avatar", player.getAvatar());
                put("submitted_answer", currentAnswers.get(playerId));
                // 可以添加时间戳等其他信息
            }});
        }
        return latestAnswers;
    }

    // Getter 和 Setter 方法
    public List<WebSocketSession> getConnections() {
        return connections;
    }

    public Map<String, Player> getPlayers() {
        return players;
    }

    public Map<String, Object> getCurrentQuestion() {
        return currentQuestion;
    }

    public String getMode() {
        return mode;
    }

    public int getCurrentRound() {
        return currentRound;
    }

    public int getTotalRounds() {
        return totalRounds;
    }

    public boolean isJudgementPending() {
        return judgementPending;
    }

    public void setJudgementPending(boolean state){
        judgementPending = state;
    }
}
