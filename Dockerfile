###########################################################
#SOTE-AI Dockerfile (Render + Base64 JSON 완벽 지원)
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

###########################################################
# 7) Base64로 전달된 GOOGLE_CREDENTIALS_JSON을 
#    컨테이너 내 /app/config/gcp-ocr.json 으로 생성
#    → Google Cloud Vision OCR, GCS 업로드 사용
###########################################################
RUN mkdir -p /app/config

CMD sh -c "\
  echo \"===== Creating GCP Credentials File =====\" && \
  echo \"$GOOGLE_CREDENTIALS_JSON\" | base64 -d > /app/config/gcp-ocr.json && \
  export GOOGLE_APPLICATION_CREDENTIALS=/app/config/gcp-ocr.json && \
  echo \"===== Starting SOTE-AI =====\" && \
  uvicorn app.main:app --host 0.0.0.0 --port 10000 \
"
