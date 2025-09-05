# 开发文档
## 后端环境配置与运行流程
conda create -n quizGame python=3.11
conda activate quizGame

pip install fastapi uvicorn
pip install uvicorn[standard]

进入APP文件夹
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

## 前端
