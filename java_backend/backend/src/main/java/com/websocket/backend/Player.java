package com.websocket.backend;

import java.util.HashMap;
import java.util.Map;

public class Player {
    private String id;
    private String name;
    private String avatar;
    private Map<String, Object> content;
    private long lastActiveTimestamp;

    public Player(String id, String name, String avatar) {
        this.id = id;
        this.name = name;
        this.avatar = avatar;
        this.content = new HashMap<>();
        initializeContent(); // 初始化 scoring 和 survival
        this.lastActiveTimestamp = System.currentTimeMillis();
    }

    // 初始化 scoring 和 survival
    private void initializeContent() {
        System.out.println(this.content);
        this.content.put("scoring", new HashMap<String, Object>() {{
            put("score", 0);
            put("round_score", 0);
        }});
        this.content.put("survival", new HashMap<String, Object>() {{
            put("lives", 3);
            put("lost_lives_this_round", 0);
        }});
        this.content.put("judgement_correct", false);
    }

    // Getter 和 Setter 方法

    public String getId() { return id; }
    public String getName() { return name; }
    public String getAvatar() { return avatar; }

    public long getLastActiveTimestamp() { return lastActiveTimestamp; }
    public void setLastActiveTimestamp(long lastActiveTimestamp) {
        this.lastActiveTimestamp = lastActiveTimestamp;
    }

    // Scoring Getters and Setters
    public int getScore() {
        return (int) ((Map<String, Object>) content.get("scoring")).getOrDefault("score", 0);
    }

    public void setScore(int score) {
        ((Map<String, Object>) content.get("scoring")).put("score", score);
    }

    public int getRoundScore() {
        return (int) ((Map<String, Object>) content.get("scoring")).getOrDefault("round_score", 0);
    }

    public void setRoundScore(int roundScore) {
        ((Map<String, Object>) content.get("scoring")).put("round_score", roundScore);
    }

    // Survival Getters and Setters
    public int getLives() {
        return (int) ((Map<String, Object>) content.get("survival")).getOrDefault("lives", 3);
    }

    public void setLives(int lives) {
        ((Map<String, Object>) content.get("survival")).put("lives", lives);
    }

    public int getLostLivesThisRound() {
        return (int) ((Map<String, Object>) content.get("survival")).getOrDefault("lost_lives_this_round", 0);
    }

    public void setLostLivesThisRound(int lostLives) {
        ((Map<String, Object>) content.get("survival")).put("lost_lives_this_round", lostLives);
    }

    // Judgement correct setter and getter
    public boolean isJudgementCorrect() {
        return (boolean) content.getOrDefault("judgement_correct", false);
    }

    public void setJudgementCorrect(boolean correct) {
        content.put("judgement_correct", correct);
    }
}
