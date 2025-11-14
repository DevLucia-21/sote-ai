###########################################################
# 🐳 SOTE-AI 최적 Dockerfile (Render 대응 완벽 버전)
###########################################################

# 1) Base Image
FROM python:3.10-slim

# 2) System Dependencies (Whisper, MeCab, ffmpeg 지원)
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    curl \
    git \
    libmecab-dev \
    mecab \
    mecab-ipadic-utf8 \
    && rm -rf /var/lib/apt/lists/*

# 3) Set working directory
WORKDIR /app

# 4) Install Python Dependencies
COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 5) Copy application source
COPY . .

# 6) Render PORT 설정
ENV PORT=10000
EXPOSE 10000

# 7) Start FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
