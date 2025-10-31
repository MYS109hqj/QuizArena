readme 文件结构：实现功能概述-更新日志-本机、服务器部署说明

## 实现功能：

### 提问端：

提出问题。
**可以设定输出题目类型**（**支持问答题、单选题、多提示题**；以及复制相应格式题目**自动填充**）
可以**收取各答题端回答的最新答案**，并进行**判题**
可以**设定并更新游戏的模式（无模式、计分模式、生存模式）**
可以**手动设定并更新游戏轮次**
可以**设置房间内回答是否对其它答题者可见**
可以主动在计分模式和生存模式下**显示结算界面（显示得分与排名）**

### 答题端：

可以**自定义名称**，从给定 url 中选择头像，或自己填写图片 url**设置头像**
可以**回答**（"回答"对所有人可见，但回答内容依据房间设置，在其它玩家处可能显示为[hidden]），可以手动清除答题记录（刷新页面自动清除）
提问端判题后，可以**查看判题结果**（刷新页面会清除）

在侧边栏显示玩家的状态；玩家若刷新可以立即重连，**超过 5 秒（房间设定的超时重连时间）被认为退出房间，删除玩家数据**。

注：使用 fastapi uvicorn(python 后端版本) 或 springboot(java 后端版本) + VUE3（Vite）的架构
websocket 调试时的 ip 地址设为本机，生产环境 ip 地址配置请参照后文部署流程。

## 更新日志：

### 25/10/31

新增“Same Pattern Hunt”寻找相同图案游戏，重构项目后端。
请注意，此版本为实验性版本，并不支持答题游戏。
已知 bug：

1. 答题游戏的 websocket 连接错误，并且不支持账号登录；
2. 个人信息板块，信息显示错误，包括但不限于： - 默认头像显示错误 - 姓名不可修改，但用输入框展示 - 游戏记录显示错误
   待优化：
3. 玩家游戏记录只能从首页查看

### 25/2/10 version1.7.1

1. 修复了玩家断开连接后， python 后端中`player_if - websocket`映射数据未被正确删除的问题
2. 在 EnterPage.vue 中添加了头像的预览功能（加载速度受网速影响）
3. 适当放大了答题端的提交答案和清空答案按钮；在未提交答案时显示“仍未提交答案”的文本。
4. 后端超时断开连接的 connect_timeout，现在实际为`connect_timeout - 0.1`。

### 25/2/8 version1.7

**功能更新清单**

- [x] 进行提问者与答题者的区分，在刷新页面、结算、判题等不出现“提问者”
- [x] 进行提问者与答题者的区分，在答题者刷新页面时，不影响提问端的题目
- [x] 填充题目时，若有 A.等前缀，在答题端时不再显示
- [x] enter_page 预览头像

**更新内容：**
**针对 python 后端的功能更新：**

1. 修复了`生存模式`下，剩余生命值显示为`NaN`的问题。现在生存模式也能正常显示结算界面
2. 在获取各玩家最新回答（注意会覆盖已收到的回答）、显示结算表格时，不再会显示"提问者"
3. 填充题目时，格式要求有`A. `等前缀，现在自动填充后会自动去除这个前缀，保证在答题端不会出现`A. A. `的错误显示
4. 提问端可以设置房间的“最大超时重连时间”，主持人可以依据游戏进程自行调整，输入后 0.8 秒后会应用。**（若要本地运行，从此版本开始，还需要安装`lodash`库，即需要`npm install lodash`）**
5. 现在答题端刷新页面，不会将广播的当前题目等推送至提问端并强制覆盖。但请注意，发送判题结果时会发送此时“答案”与“解析”中的内容，小心答案提前泄露。

### 25/1/31 version1.6

**针对 python 后端的功能更新：**

1. 支持三种题型（问答题、选择题、多提示题）在选定题型后，以指定格式输入到文本框种，自动填充到提问页面的题目中。具体格式附在本次更新日志末尾。
2. 在原有的题目的“题目-提示”基础结构上，新增可选项“答案”和“解析”，若填写“答案”和（或）“解析”，在提问端提交判题结果后，会将答案和解析一并呈现在判题结果中。
3. 新增“其它答题者能否看到答题者的回答”的选项。若设置为“是”，与此前版本一样，所有答题者的答案公开；若设置为“否”，除了答题者本人与提问者，其他人都只能看到该答题者提交了[hidden]的答案。
4. 新增答题者设置自定义头像的功能。在 enter 页面，可以像以往一样选择预设的 4 个图片 url，或者自行填写图片的 url 作为头像。使用自定义头像时请注意 url 能否正常访问。
5. 新增了计分模式下，显示结算界面的功能。界面显示由提问端主动按按钮触发。（已知 bug：生存模式下，结算界面中生命值全为 NaN）

version1.6 附录：题目形式示例和格式说明
注：请注意要使用中文的"："

##### 问答题（QA）

###### 示例：

什么是计算机的基本组成部分？
答案：计算机的基本组成部分包括输入设备、输出设备、存储器、中央处理器（CPU）。
解析：计算机的基本组成部分共同协作，实现信息处理功能。CPU 是核心组件，负责执行计算和控制指令。

###### 格式说明：

    • 第一行：题目内容
    • 答案（必须以答案：开头）
    • 解析（可选，必须以解析：开头）

##### 选择题（MCQ）

###### 示例：

以下哪项是计算机的存储设备？
A. 显示器
B. 键盘
C. 硬盘
D. 鼠标
答案：C
解析：硬盘是计算机用于长期存储数据的设备，而显示器、键盘和鼠标属于输入/输出设备。

###### 格式说明：

    • 第一行：题目内容
    • 选项（每行以 A. 、B. 、C. 、D. 开头）
    • 答案（必须以答案：开头，内容为正确选项字母 A~D）
    • 解析（可选，必须以解析：开头）

##### 多提示题（Hints）

###### 示例：

这个概念与计算机存储有关，它用于临时存储数据，以提高访问速度。
基本提示：它是一种高速存储器，位于 CPU 和主存之间。
追加提示 1：它通常比主存（RAM）更小但更快。
追加提示 2：它有 L1、L2、L3 等多个层级。
追加提示 3：它在计算机的处理器内部或附近。
追加提示 4：它能显著提高数据读取速度，减少 CPU 等待时间。
答案：缓存（Cache）
解析：这是解析

###### 格式说明：

    • 第一行：题目内容
    • 基本提示（必须以基本提示：开头）
    • 追加提示（可选，每个以 追加提示 1：、追加提示 2： 开头）

答案（必须以答案：开头）

### 25/1/4 version1.5

修复了 java 后端处理玩家状态错误的 bug。
没有进行额外的功能更新。

### 24/10/30 version1.4

正式根据 python 后端编写了 java 后端版本，前端相同。
使用.env 指定了端口，如果要修改，请注意修改.env 中的环境变量。生产环境需要修改.env.production。
另外，个人环境使用的 Vue3 基于 vite，如果使用 node.js 环境变量设置方法并不相同，需要修改。
（个人在另一个仓库上传的，作为网络应用开发作业的在线商城使用的是 node.js）

注：目前版本并未对服务器运行进行测试，没有构建实例，但是算是本地调试过后的稳定版本。

修复了添加“获取最新答案”后，无法对直接接收到的答案进行判题的 bug。

### 24/10/28 version1.3

拟添加功能：（不分先后）

1. 提问端获取最新答案
2. 答题端显示判题结果
3. 发布轮次更新后，在 answer 栏也加上“更新至第 n 轮”的形式
4. 重连时间 1 分钟，可以通过提问端设置

对于 4
使用 async 将 disconnect 改为异步操作。
在断开连接后，经过 last_active_timestamp（在 Room 中定义）事件后，调用 Room 类的异步方法 remove_player_if_expired，在非阻塞的延迟后，判断该玩家的最近连接时间（只有断开连接与重连操作，会记录 Player 的 last_active_timestamp）是否超过重连时间，超过则删除玩家信息。
websocket 只要断开链接就删除，每次刷新页面都会重新建立新的 websocket 链接。
目前的重连时间定义为 5 秒钟。

### 241024 version1.2 版本

完善判题逻辑
当前版本可以记总分
但是注意：刷新页面后用户信息会清除后再加入（已于 version1.3 解决该问题）

## 本机环境部署：

### 若使用 Python 后端

#### 依赖安装

- 使用`fastapi`与`uvicorn`作为后端框架和 ASGI 服务器。

```bash
pip install fastapi uvicorn
pip install uvicorn[standard]
```

#### 运行后端

安装好依赖后，在/backend/app 文件夹中运行以下命令

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 若使用 Java 后端

调试环境为 java22；本项目不提供额外 java 后端的调试相关说明

#### 构建与运行

1. 清理并构建项目：

```bash
mvn clean package
```

2. 运行 JAR 文件：

```bash
java -jar target/backend-0.0.1-SNAPSHOT.jar
```

### 前端 Vue3 (使用 Vite 构建)

#### 创建 Vue3 项目

```bash
npm init vue@latest
```

#### 安装依赖

- 安装`socket.io-client`以实现与后端的 WebSocket 通信。
- 安装`lodash`支持前端的防抖动功能。

```bash
npm install socket.io-client
npm install lodash
```

#### 运行前端

```bash
npm run dev
```

## java 后端版本的服务器部署流程

服务器环境：CentOS7 （linux 系统）

### 以使用 windows 的主机辅助为例

（提醒：本项目的前端是基于 Vite 的 Vue3，而非基于 cli，二者有一定差别）

在本机配置好 node.js 环境，在`/java_backend/frontend`目录中，创建`.env.production`文件，用于配置生产环境下的环境变量（本项目中用于设置服务器 IP 地址）。
在`.env.production`文件中输入以下内容。（将 server_ip_address 替换为服务器的 ip 地址）

```dotenv
VITE_WEBSOCKET_URL=ws://server_ip_address:8080/ws
```

之后，仍然在`/java_backend/frontend`目录，进入控制台（cmd），输入

```bash
npm run build
```

完成对前端项目的构建。生成我们需要的前端静态文件，所需的文件位于`dist`文件夹中。

对于后端，服务器只需要生成的 jar 文件。如果我有直接发送 jar 文件的话，可以直接使用。
在`/java_backend/frontend`目录，进入控制台，输入

```bash
mvn clean package
```

若构建成功，JAR 文件会生成在项目目录中的 target 文件夹中。文件名由`pox.xml`中的

```xml
	<artifactId>backend</artifactId>
	<version>0.0.1-SNAPSHOT</version>
```

参数决定。（如上述示例下，生成 jar 文件的文件名是`backend-0.0.1-SNAPSHOT`）

如果直接使用 git clone 克隆仓库，或者在 linux 系统操作，具体的运行命令可能会有差别，目标仍是在添加`.env.production`后生成 dist 中的前端静态文件以及后端的 JAR 文件。

在生成后，将 dist 文件夹以及 JAR 文件上传到服务器。记录好 dist 文件夹所在的文件路径。

在本示例中，使用到 nginx 作为反向代理。这里假设已经配置好了 nginx。

在 CentOS 中，Nginx 配置文件的默认路径为`/etc/nginx/nginx.conf`，站点配置文件路径在`/etc/nginx/conf.d/`下，在此文件中直接存储站点配置文件，如创建`quiz_Arena.conf`。
由于后端使用到了 websocket，在配置文件中需要做相应配置。示例配置文件如下：（请注意修改 server_name 与 location/{}中的 root）

```conf
server {
    # 监听端口 80（HTTP 默认端口）
    listen 80;
    # 将 'your_server_ip_or_domain' 替换为你的服务器 IP 或域名
    server_name your_server_ip_or_domain;

    # 静态文件服务
    location / {
        # 将 'your_dist_path' 替换为dist文件夹的的实际部署路径
        root your_dist_path;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://localhost:8080;  # WebSocket 服务监听的后端地址
        proxy_http_version 1.1;           # 确保使用 HTTP/1.1 以支持 Upgrade 机制
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 防止 WebSocket 超时
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # 防止静态文件和 WebSocket 路径冲突
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|otf|eot|ttc|map)$ {
        root /var/www/quiz_Arena/vue/dist;
        expires 1M;         # 设置浏览器缓存时间
        access_log off;     # 关闭日志记录（减少性能开销）
        try_files $uri =404;
    }
}
```

之后更新 nginx 的配置

```SHELL
sudo nginx -t  # 检查配置文件语法
sudo systemctl reload nginx  # 重新加载配置
```

在确认 nginx 拥有对 dist 文件夹的访问权限后，前端大概率可以正常运行。

对于后端，假设 JAR 文件的文件名为`backend-0.0.1-SNAPSHOT`。进入 JAR 文件所在目录，你可以输入以下指令，让后端在后台运行：

```SHELL
nohup java -jar backend-0.0.1-SNAPSHOT.jar > output.log 2>&1 &
```

后端的输出将会写入到同目录中的 output.log 文件。
查看 output.log，确认后端正常启动。

nginx 配置完毕，后端正常运行，项目在服务器上的部署也就完成了。祝你有良好的游戏体验！

如果你要关闭后端进程，可以使用

```SHELL
ps aux | grep java
kill <PID> # 将<PID>替换为你想要关闭的Java进程的进程ID
```

`ps aux | grep java`会列出所有包含"java"关键字的进程。输出中会包含进程 ID（PID），将输出的 PID 替换掉上述命令中的`<PID>`即可正常关闭进程。

如果在配置 nginx 的过程中遇到了错误，在 CentOS7 的环境下，可以输入以下指令查看日志：

```SHELL
tail -n 50 /var/log/nginx/error.log
```

## python 后端版本的服务器部署流程

前端部分同 java 部分
对于后端，需要 python 版本在 3.7 及以上。下面以 3.11 版本为例：

安装依赖：

```bash
pip install fastapi uvicorn
pip install uvicorn[standard]
```

将/backend/app 文件夹复制到服务器上，在 app 文件夹中执行

```bash
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > output.log 2>&1 &
```

即可让后端后台运行

nginx 配置部分，大体同 java，但是注意 python 后端的端口号是 8000，需要进行修改。
