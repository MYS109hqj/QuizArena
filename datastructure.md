# 数据结构

## 类定义

### Player
- `id` (str): 玩家唯一标识符。
- `name` (str): 玩家姓名。
- `avatar` (str): 玩家头像的 URL 或路径。

### Room
- `connections` (List[WebSocket]): 连接到此房间的所有 WebSocket 实例。
- `players` (Dict[str, Player]): 当前房间内的玩家字典。
- `current_question` (Optional[Dict]): 当前问题的信息。
- `current_question_id` (Optional[str]): 当前问题的唯一标识符。

### ConnectionManager
- `rooms` (Dict[str, Room]): 存储所有房间的信息。

## 前端数据结构

### 连接状态
- `isConnected` (Boolean): WebSocket 连接状态。

### 玩家信息
- `onlinePlayers` (Array): 在线玩家数组。
  - 每个玩家对象：
    - `id` (String): 玩家唯一标识符。
    - `name` (String): 玩家姓名。
    - `avatar` (String): 玩家头像的 URL。

### 题目信息
- `question` (String): 当前提问的内容。
- `questionRoomId` (String): 当前房间的 ID。
- `questionType` (String): 题目类型。
- `options` (Array[String]): 选择题选项。
- `basicHint` (String): 基本提示。
- `additionalHints` (Array[String]): 追加提示。

### 答案信息
- `answers` (Array): 收到的答案列表。
  - 每个答案对象：
    - `name` (String): 提交答案的玩家姓名。
    - `avatar` (String): 提交答案的玩家头像 URL。
    - `text` (String): 玩家提交的答案文本。

## 向后端传递的数据

### 连接请求
```json
{
    "id": "user-unique-id",
    "type": "join",
    "name": "提问者",
    "avatar": "https://i0.hippopx.com/photos/490/240/938/connect-connection-cooperation-hands-thumb.jpg"
}
