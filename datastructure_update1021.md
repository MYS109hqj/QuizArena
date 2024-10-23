以下是更新后的 `DataStructure.md` 文件，包含了新的数据结构设计，能够支持不同模式下的玩家信息和其他必要字段：

```markdown
# 数据结构

## 类定义

### Player
- `id` (str): 玩家唯一标识符。
- `name` (str): 玩家姓名。
- `avatar` (str): 玩家头像的 URL 或路径。
- `content` (Dict[str, Dict]): 存储与模式相关的内容。
  - `scoring` (Dict): 计分模式下的信息。
    - `score` (int): 玩家总得分。
    - `round_score` (int): 玩家本轮得分。
  - `survival` (Dict): 生存模式下的信息。
    - `lives` (int): 玩家剩余生命。
    - `lost_lives_this_round` (int): 本轮失去的生命数。

### Room
- `connections` (List[WebSocket]): 连接到此房间的所有 WebSocket 实例。
- `players` (Dict[str, Player]): 当前房间内的玩家字典。
- `current_question` (Optional[Dict]): 当前问题的信息。
- `current_question_id` (Optional[str]): 当前问题的唯一标识符。
- `total_rounds` (Optional[int]): 总轮次数（计分模式下的特有字段）。
- `current_round` (Optional[int]): 当前轮次。

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
    - `score` (int): 玩家当前得分（计分模式下）。
    - `lives` (int): 玩家剩余生命（生存模式下）。

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
    - `timestamp` (float): 答案提交的时间戳，用于判断提交顺序。

## 向后端传递的数据

### 连接请求
```json
{
    "id": "user-unique-id",
    "type": "join",
    "name": "提问者",
    "avatar": "https://i0.hippopx.com/photos/490/240/938/connect-connection-cooperation-hands-thumb.jpg"
}
```

### 判题请求
```json
{
    "questionId": "question-unique-id",
    "correctAnswers": ["答案1", "答案2"],
    "submittedAnswers": [
        {
            "playerId": "player1",
            "answer": "提交的答案1"
        },
        {
            "playerId": "player2",
            "answer": "提交的答案2"
        }
    ]
}
```

### 更新得分请求
```json
{
    "playerScores": [
        {
            "playerId": "player1",
            "roundScore": 10,
            "totalScore": 50
        },
        {
            "playerId": "player2",
            "roundScore": 0,
            "totalScore": 40
        }
    ],
    "correctAnswer": "正确答案"
}
```
```

### 说明
- 在 `Player` 类中，通过 `content` 字典来存储与不同模式相关的字段，从而支持未来可能添加的其他模式。
- `Room` 类新增了 `total_rounds` 和 `current_round` 字段，以适应计分模式的需求。
- 答案信息中增加了 `timestamp` 字段，以便于判定答案的提交顺序。

这种数据结构设计不仅增强了扩展性，还确保了在不同模式下信息的有序管理。