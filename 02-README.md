# 开发文档

## 后端环境配置与运行流程

conda create -n quizGame python=3.11
conda activate quizGame

pip install fastapi uvicorn
pip install uvicorn[standard]

进入 APP 文件夹
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

在 backend 文件夹：
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > output.log 2>&1 &

服务器上：
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > output.log 2>&1 &
[1] 3011320
[2] 3028333

## 前端

额外操作：
npm install pinia axios

<!-- npm install vue-cropperjs cropperjs -->

npm install vue-cropper@next
可以通过 npm list vue-cropper 判断是否安装了该包
cropperjs 官方文档 https://github.com/fengyuanchen/cropperjs/blob/main/docs/zh/guide.md
踩坑：`npm install vue-cropperjs cropperjs`会有版本依赖问题，cropperjs 的版本过新，文件结构相比 vue-cropperjs 预期的有所改变。只下载 vue-cropperjs，让其自动下载依赖项，可以正常`import 'cropperjs/dist/cropper.css';`

npm install --save vue-cropperjs
官方文档：https://github.com/Agontuk/vue-cropperjs

- [ ] 考虑读<https://github.com/Agontuk/vue-cropperjs>的源码

每次都要创建两个 cmd 启动前后端，感觉很麻烦，有没有一键调试的方法？代价是什么？

---

前端要在游戏中断线重连，最优方案还是提供重进游戏的途径。
get_playing_games 获取 player_id 正在游玩的房间，可以快速进入游戏界面。
但这也对 room 获取 game 的 player 有所要求。理论上最好还是数据库。

sudo dnf install python3.12 -y
可以输入`python3.12 --version`验证下载情况

sudo cat /var/log/nginx/static_error.log 查看 nginx 的报错日志

sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1 # 低优先级
sudo update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.12 2 # 高优先级

然后输入下面的命令，选择版本:
sudo update-alternatives --config python3

# 下载 get-pip.py 脚本

curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

# 用 Python 3.12 运行脚本安装 pip

python3.12 get-pip.py

# 验证安装

python3.12 -m pip --version # 应显示 pip 版本

# 便捷启动栏目

后端启动脚本

```
cd /home/lighthouse/quizArena/mainWebsite/backend/
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

之后更新 nginx 的配置

```SHELL
sudo nginx -t  # 检查配置文件语法
sudo systemctl reload nginx  # 重新加载配置
```
