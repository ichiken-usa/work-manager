FROM python:3.13-slim

WORKDIR /app

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# print出力をリアルタイムで表示するための設定
ENV PYTHONUNBUFFERED=1

CMD ["streamlit", "run", "input.py", "--server.port=8501", "--server.address=0.0.0.0"]