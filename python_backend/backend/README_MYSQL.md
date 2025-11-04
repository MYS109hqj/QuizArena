# MySQL数据库配置与游戏记录功能说明

本文档详细介绍如何配置MySQL数据库以实现游戏记录功能，包括在对局结束后记录数据和查看历史游戏数据。

## 1. 前提条件

- 已安装MySQL服务器
- 已创建虚拟环境并激活
- 已安装项目依赖（见requirements.txt）

## 2. MySQL数据库配置

### 2.1 配置环境变量

项目使用.env文件存储MySQL连接信息。我们已经创建了.env文件，位于项目根目录（`python_backend/backend/.env`）。请根据您的MySQL配置修改以下内容：

```env
# MySQL数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password  # 请修改为实际密码
MYSQL_DATABASE=quizarena

# JWT配置
SECRET_KEY=your-secret-key-keep-it-safe-and-long-enough-for-production-use
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
```

### 2.2 初始化MySQL数据库

我们提供了一个初始化脚本`init_mysql.sql`，用于创建游戏所需的表结构和存储过程。

执行以下命令初始化数据库：

```bash
# 方法1：使用MySQL命令行工具
mysql -u root -p < init_mysql.sql

# 方法2：进入MySQL命令行后执行
mysql -u root -p
# 输入密码后，执行
USE quizarena;
SOURCE init_mysql.sql;
```

初始化脚本会创建以下表结构：
- `users`: 用户信息表
- `game_sessions`: 游戏会话记录表
- `game_rounds`: 游戏回合记录表
- `player_stats`: 玩家统计信息表

以及以下存储过程和视图：
- `UpdatePlayerStats`: 更新玩家统计信息的存储过程
- `user_game_history`: 查看用户游戏历史的视图

## 3. 游戏记录功能实现

### 3.1 对局结束数据记录流程

游戏结束时的数据记录流程如下：

1. 游戏前端在对局结束时收集游戏数据（得分、准确率、回合数等）
2. 前端调用`PUT /game-records/sessions/{session_id}` API更新游戏会话记录
3. 后端API接收数据后，更新`game_sessions`表中的记录
4. 自动调用`update_player_stats`函数更新玩家统计信息

### 3.2 核心代码实现

项目已实现以下核心功能：

- **GameRecordService** 类：提供游戏记录的业务逻辑处理
  - `create_game_session`: 创建新的游戏会话
  - `update_game_session`: 更新游戏会话信息（对局结束时调用）
  - `create_game_round`: 创建游戏回合记录
  - `update_player_stats`: 更新玩家统计信息
  - `get_user_game_sessions`: 获取用户的游戏会话记录
  - `get_player_stats`: 获取玩家统计信息
  - `get_session_rounds`: 获取游戏会话的回合记录

- **游戏记录API路由**：提供HTTP接口
  - `POST /game-records/sessions`: 创建游戏会话
  - `PUT /game-records/sessions/{session_id}`: 更新游戏会话（对局结束时调用）
  - `POST /game-records/rounds`: 添加游戏回合记录
  - `GET /game-records/sessions`: 获取用户游戏记录
  - `GET /game-records/stats`: 获取玩家统计信息

### 3.3 游戏结束时的数据处理

在`quiz_game.py`文件中，游戏结束时会调用`_handle_congratulations`方法广播结算信息：

```python
async def _handle_congratulations(self) -> None:
    await self.broadcast({
        "type": "congratulations_complete",
        "results": [
            {
                "id": p.id,
                "name": p.name,
                "avatar": p.avatar,
                "score": p.content["scoring"]["score"],
                "lives": p.content["survival"]["lives"]
            }
            for p in self.players.values()
            if not p.id.startswith("questioner-")  # 排除提问者
        ]
    })
```

前端接收到此消息后，应调用游戏记录API保存数据。

## 4. 查看历史游戏数据

### 4.1 使用API接口查看

前端可以通过调用以下API接口获取历史游戏数据：

- **获取用户游戏记录**
  ```
  GET /game-records/sessions?game_type={game_type}&limit={limit}&offset={offset}
  ```
  参数说明：
  - `game_type`: 可选，游戏类型过滤
  - `limit`: 可选，每页记录数（默认20）
  - `offset`: 可选，偏移量（默认0）
  
- **获取玩家统计信息**
  ```
  GET /game-records/stats?game_type={game_type}
  ```
  参数说明：
  - `game_type`: 可选，游戏类型过滤

### 4.2 直接查询MySQL数据库

您也可以直接在MySQL数据库中查询历史游戏数据，推荐使用我们创建的视图：

```sql
-- 查看所有用户的游戏历史
SELECT * FROM user_game_history LIMIT 100;

-- 查看特定用户的游戏历史
SELECT * FROM user_game_history WHERE username = 'your_username';

-- 查看特定游戏类型的历史记录
SELECT * FROM user_game_history WHERE game_type = 'quiz';

-- 查看玩家统计信息
SELECT * FROM player_stats;
```

## 5. 部署与启动说明

### 5.1 安装依赖

确保已安装所有必要的依赖包：

```bash
pip install -r requirements.txt
```

### 5.2 启动后端服务

使用项目提供的启动脚本：

```bash
# Windows系统
start-debug.bat

# 或手动启动
cd python_backend/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动时，系统会自动尝试连接到MySQL数据库，并在控制台输出连接状态信息。

## 6. 常见问题排查

### 6.1 数据库连接失败

如果启动时出现以下错误：
```
❌ 无法连接到MySQL数据库: [错误信息]
⚠️ 请确保MySQL服务已启动，且.env文件中的配置正确
```

请检查：
- MySQL服务是否已启动
- .env文件中的连接信息是否正确
- MySQL用户是否有足够的权限
- 防火墙设置是否允许连接

### 6.2 表结构不存在

如果出现表不存在的错误，请确保已运行`init_mysql.sql`脚本初始化数据库。

### 6.3 游戏记录未保存

如果游戏结束后记录未保存，请检查：
- 用户是否已登录（需要JWT令牌）
- 前端是否正确调用了游戏记录API
- 数据库权限是否正确

## 7. 数据模型说明

### 7.1 游戏会话表 (game_sessions)

存储完整游戏会话的信息：
- `id`: 会话ID
- `user_id`: 用户ID
- `game_type`: 游戏类型
- `room_id`: 房间ID
- `start_time`: 开始时间
- `end_time`: 结束时间
- `duration_seconds`: 游戏时长（秒）
- `score`: 得分
- `accuracy`: 准确率
- `rounds_played`: 完成的回合数
- `rounds_total`: 总回合数
- `status`: 游戏状态
- `created_at`: 创建时间

### 7.2 游戏回合表 (game_rounds)

存储每个游戏回合的详细信息：
- `id`: 回合ID
- `session_id`: 所属会话ID
- `round_number`: 回合序号
- `target_pattern`: 目标图案
- `user_pattern`: 用户选择
- `is_correct`: 是否正确
- `response_time_ms`: 响应时间（毫秒）
- `round_score`: 回合得分
- `created_at`: 创建时间

### 7.3 玩家统计表 (player_stats)

存储玩家的游戏统计信息：
- `user_id`: 用户ID
- `game_type`: 游戏类型
- `total_games`: 总游戏次数
- `total_score`: 总得分
- `average_score`: 平均得分
- `best_score`: 最高得分
- `average_accuracy`: 平均准确率
- `total_play_time_seconds`: 总游戏时长
- `last_played`: 最后游戏时间
- `updated_at`: 更新时间