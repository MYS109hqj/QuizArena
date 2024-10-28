24/10/28
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

