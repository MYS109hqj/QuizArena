# 开发文档
## 后端环境配置与运行流程
conda create -n quizGame python=3.11
conda activate quizGame

pip install fastapi uvicorn
pip install uvicorn[standard]

进入APP文件夹
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

在backend文件夹：
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

## 前端
额外操作：
npm install pinia axios

<!-- npm install vue-cropperjs cropperjs -->
npm install vue-cropper@next
可以通过npm list vue-cropper判断是否安装了该包
cropperjs官方文档 https://github.com/fengyuanchen/cropperjs/blob/main/docs/zh/guide.md
踩坑：`npm install vue-cropperjs cropperjs`会有版本依赖问题，cropperjs的版本过新，文件结构相比vue-cropperjs预期的有所改变。只下载vue-cropperjs，让其自动下载依赖项，可以正常`import 'cropperjs/dist/cropper.css';`

npm install --save vue-cropperjs
官方文档：https://github.com/Agontuk/vue-cropperjs

- [ ] 考虑读<https://github.com/Agontuk/vue-cropperjs>的源码

每次都要创建两个cmd启动前后端，感觉很麻烦，有没有一键调试的方法？代价是什么？

---

前端要在游戏中断线重连，最优方案还是提供重进游戏的途径。
get_playing_games 获取player_id正在游玩的房间，可以快速进入游戏界面。
但这也对room获取game的player有所要求。理论上最好还是数据库。