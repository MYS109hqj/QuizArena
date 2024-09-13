文件结构
backend、frontend同级；文件结构如下：
    project-root/
    │
    ├── backend/
    │   ├── main.py               # FastAPI 后端入口文件
    │   ├── requirements.txt      # 后端依赖包
    │
    ├── frontend/
    │   ├── src/
    │   │   ├── components/
    │   │   │   ├── Questioner.vue  # 出题端组件
    │   │   │   ├── Responder.vue   # 答题端组件
    │   │   ├── App.vue            # 根组件
    │   │   ├── main.js            # Vue 入口文件
    │   ├── public/               # 静态资源
    │   ├── package.json          # 前端依赖包
    │
    ├── docker-compose.yml        # Docker Compose 配置文件（可选）
    └── README.md                 # 项目说明文件

后端依赖：（使用fastapi与uvicorn）
安装：
pip install fastapi uvicorn
运行：
uvicorn main:app --reload


前端Vue3
创建Vue3项目
npm init vue@latest
安装socket.io-client
npm install socket.io-client
运行：
npm run dev

