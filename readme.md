## 实现功能：
提问端：提出问题。
    可以设定输出题目类型（目前demo只支持问答题）
    可以收取各答题端回答的答案

答题端：
    可以自定义头像url和名称
    根据问题类型，有不同的答题窗口
    
注：使用fastapi uvicorn + VUE3的架构
websocket的ip地址设为本机

## 环境部署：
### Python后端

#### 依赖安装
- 使用`fastapi`与`uvicorn`作为后端框架和ASGI服务器。

```bash
pip install fastapi uvicorn
```

#### 运行后端
```bash
uvicorn main:app --reload
```

### Java后端

调试环境为java22；本项目不提供额外java后端的调试相关说明
#### 构建与运行
1. 清理并构建项目：
```bash
mvn clean package
```

2. 运行JAR文件：
```bash
java -jar target/backend-0.0.1-SNAPSHOT.jar
```

### 前端Vue3

#### 创建Vue3项目
```bash
npm init vue@latest
```

#### 安装依赖
- 安装`socket.io-client`以实现与后端的WebSocket通信。

```bash
npm install socket.io-client
```

#### 运行前端
```bash
npm run dev
```



## 更新日志：

### 25/1/4 version1.5
修复了java后端处理玩家状态错误的bug。
没有进行额外的功能更新。

### 24/10/30 version1.4
正式根据python后端编写了java后端版本，前端相同。个人作为课程作业使用。请勿胡乱复制用作作业。
使用.env指定了端口，如果要修改，请注意修改.env中的环境变量。生产环境需要修改.env.production。
另外，个人环境使用的Vue3基于vite，如果使用node.js环境变量设置方法并不相同，需要修改。
（个人在另一个仓库上传的，作为网络应用开发作业的在线商城使用的是node.js）

注：目前版本并未对服务器运行进行测试，没有构建实例，但是算是本地调试过后的稳定版本。

修复了添加“获取最新答案”后，无法对直接接收到的答案进行判题的bug。


### 24/10/28 version1.3
拟添加功能：（不分先后）
1. 提问端获取最新答案
2. 答题端显示判题结果
3. 发布轮次更新后，在answer栏也加上“更新至第n轮”的形式
4. 重连时间1分钟，可以通过提问端设置

对于4
使用async将disconnect改为异步操作。
在断开连接后，经过last_active_timestamp（在Room中定义）事件后，调用Room类的异步方法remove_player_if_expired，在非阻塞的延迟后，判断该玩家的最近连接时间（只有断开连接与重连操作，会记录Player的last_active_timestamp）是否超过重连时间，超过则删除玩家信息。
websocket只要断开链接就删除，每次刷新页面都会重新建立新的websocket链接。
目前的重连时间定义为5秒钟。


### 241024 version1.2版本
完善判题逻辑
当前版本可以记总分
但是注意：刷新页面后用户信息会清除后再加入（已于version1.3解决该问题）
