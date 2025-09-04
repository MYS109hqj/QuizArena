conda create -n quizGame python=3.11
conda activate quizGame

pip install fastapi uvicorn
pip install uvicorn[standard]

APP
uvicorn main:app --host 0.0.0.0 --port 8000 --reload