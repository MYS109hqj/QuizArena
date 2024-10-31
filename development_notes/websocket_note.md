# SpringBoot中WebSocket的连接 笔记

## 1. WebSocket前端调用

在我的 Vue3 Vite 前端中，WebSocket 的调用方式如下：

```javascript
socket.value = new WebSocket(`${import.meta.env.VITE_WEBSOCKET_URL}/${questionRoomId.value}`);
```

其中，涉及的环境变量的定义为：

```
VITE_WEBSOCKET_URL=ws://localhost:8080/ws
```

当前端执行 `new WebSocket(url)` 时，浏览器会尝试与指定的 WebSocket 服务器建立连接。

WebSocket 使用 HTTP 协议进行初始的握手过程。浏览器会发送一个 HTTP 请求，包含特定的头信息来请求建立 WebSocket 连接。服务器接收到这个请求后，会返回一个带有 HTTP 状态码 101（切换协议）的响应，表示同意建立 WebSocket 连接。一旦服务器确认了请求，连接就建立成功。此时，浏览器和服务器之间可以进行双向通信。

可以通过监听 WebSocket 的事件（如 `onopen`、`onmessage`、`onclose` 和 `onerror`）来处理连接的状态和数据。例如：

```javascript
socket.value.onopen = () => {
    console.log('WebSocket connection established');
};

socket.value.onmessage = (event) => {
    console.log('Message from server:', event.data);
};
```

## 2. 后端对WebSocket连接的处理

在 Spring Boot 的后端，`WebSocketConfig` 实现了 `WebSocketConfigurer` 接口，通过实现其方法 `registerWebSocketHandlers(WebSocketHandlerRegistry registry)` 来定义和注册 WebSocket 端点。此方法通过 `registry.addHandler()` 关联 WebSocket 端点 URL 和消息处理器，指定前端 WebSocket 请求的接入路径。Spring 会在应用启动时自动调用此方法，完成 WebSocket 端点的配置，使后端能够在前端请求时自动接收并处理 WebSocket 连接。

### 2.1 WebSocket端点的配置

对该方法中 `registry.addHandler(new WebSocketHandler(), "/ws/{roomId}").setAllowedOrigins("*");` 的实现逻辑进行分析：

- `registry.addHandler` 中的第一个参数 `new WebSocketHandler()` 表示自定义的 WebSocketHandler 实现类，包含处理 WebSocket 消息的逻辑，该类需要实现 `WebSocketHandler` 接口。

- 第二个参数 `"/ws/{roomId}"` 指定 WebSocket 端点的 URL 模式。前端可以通过这个 URL 与后端建立 WebSocket 连接。其中 `{roomId}` 是路径变量，允许在 URL 中动态指定。例如，`/ws/123` 会为房间 ID 为 123 的房间创建连接。

- `setAllowedOrigins("*")` 用于设置跨域请求的来源，允许哪些源可以访问该 WebSocket 端点。`"*"` 表示允许所有来源进行跨域连接。`setAllowedOrigins` 可指定多个具体的域名（如 `http://example.com`），以控制 WebSocket 的跨域访问权限。

```java
@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {
    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(new WebSocketHandler(), "/ws/{roomId}").setAllowedOrigins("*");
    }
}
```

## 3. WebSocket连接建立

在 WebSocket 连接建立时，Spring 框架会自动创建并传递 `session` 参数（Spring 框架创建了一个新的代表与特定客户端连接的 `WebSocketSession` 实例，并回调 `WebSocketHandler` 中的 `afterConnectionEstablished` 方法，将新创建的 `WebSocketSession` 作为参数传入）。接下来分析 `WebSocketHandler` 中的 `afterConnectionEstablished` 方法，我在项目中的实现如下。在我定义的方法中，我将 `roomId` 存储到了 `session` 的属性中。

### 3.1 WebSocketSession对象信息

`session` 是 `WebSocketSession` 对象，它本身包含的重要信息如下：

- **会话 ID**：通过 `getId()` 获取唯一标识每个连接的 ID。
- **URI 和路径**：
  - `getUri()`: 获取连接的 URI，用于解析请求来源和路径参数。
  - `getUri().getPath()`: 可提取动态路径变量（如 `{roomId}`）。
- **属性**：`getAttributes()` 返回一个 `Map<String, Object>`，用于存储与会话相关的任意数据（如我存储的房间 ID）。
- **连接状态**：`isOpen()` 检查连接是否有效。
- **消息处理**：使用 `sendMessage(TextMessage message)` 向客户端发送消息。
- **用户信息**：`getPrincipal()`（如有安全性设置）可获取代表连接用户的 Principal 对象。
- **连接时间**：可用于获取连接时间或最后活动时间（具体取决于实现）。

```java
@Override
public void afterConnectionEstablished(WebSocketSession session) throws Exception {
    String roomId = session.getUri().getPath().split("/")[2];
    session.getAttributes().put("roomId", roomId);  // 存储 roomId
    System.out.println("连接建立：房间 ID = " + roomId + ", 会话 ID = " + session.getId());
}
```

## 4. 消息处理与广播

在重写的 `handleTextMessage` 方法中，通过 `session` 获取了 `roomId`：

```java
(String) session.getAttributes().get("roomId");
```

另外，在 `ConnectionManager` 的 `broadcastToConnections(String roomId, Map<String, Object> message)` 方法（用于广播信息）中，利用 `session` 广播的信息。下面这个循环，对 `Room` 对象 `room` 中的 `private List<WebSocketSession> connections` 进行遍历，遍历房间中的所有 WebSocket 连接，若连接开放则发送文本格式消息到连接的客户端。

```java
for (WebSocketSession connection : room.getConnections()) {
    try {
        if (connection.isOpen()) {
            connection.sendMessage(new TextMessage(messageJson));
        }
    } catch (IOException e) {
        e.printStackTrace(); // 处理异常
    }
}
```

连接建立之后，当客户端通过 WebSocket 发送消息时，`handleTextMessage(WebSocketSession session, TextMessage message)` 方法被调用。默认情况下，`handleTextMessage` 方法会直接接收并处理 `TextMessage` 对象。这个对象包含了客户端发送的文本内容。但是默认实现不会执行任何操作，处理过程的异常也不会被传递给客户端，只会在控制台中捕获记录。

在我的 Vue3 前端中，创建的 WebSocket 对象存储在 `socket.value` 中，发送信息的形式如下：

```javascript
const getLatestAnswers = () => {
    const requestData = {
        type: 'get_latest_answers',
        questionerId: playerId.value
    };
    socket.value.send(JSON.stringify(requestData));
}
```

在我重写的 `handleTextMessage` 方法中，接收到的消息被解析并根据消息类型调用相应的逻辑。具体的类型定义与解析方法根据自己定义的信息结构实现。对于上面这个信息，依据逻辑会进入分支：

```java
case "get_latest_answers":
    manager.getLatestAnswers(roomId);
    break;
```

并在我实现的 `manager` 对象中实现相关逻辑。（`manager` 是我自定义的 `ConnectionManager` 对象实例，不涉及 WebSocket 相关接口的继承，用于处理信息）

## 5. WebSocket连接关闭

在 WebSocket 应用中，`afterConnectionClosed(WebSocketSession session, CloseStatus status)` 方法会在 WebSocket 连接被关闭时自动执行。具体来说，它会在以下几种情况下被调用：

- **正常关闭**：
  - 客户端或服务器通过调用 `session.close()` 显式关闭连接。

- **意外关闭**：
  - 连接由于网络问题、浏览器关闭、页面刷新等原因而意外关闭。

- **超时**：
  - 服务器端检测到某种超时条件（如未发送消息）后关闭连接。

对于项目来说，需要在连接关闭后妥善处理连接信息。在我的项目代码中，涉及到房间中存储 WebSocket 连接的 List 对象的相关删除操作，以及玩家信息的处理操作。