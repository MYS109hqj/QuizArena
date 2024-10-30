package com.websocket.backend;

public class Message {
    private String type;
    private Object content;

    public Message(String type, Object content) {
        this.type = type;
        this.content = content;
    }

    public String getType() { return type; }
    public Object getContent() { return content; }
}
