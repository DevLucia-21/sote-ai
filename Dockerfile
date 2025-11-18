###########################################################
# SOTE-AI Dockerfile (Render + Base64 GCP JSON 안정 적용)
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

# 🚨 핵심: pip hash-check 비활성화 + build isolation 제거
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
        --no-build-isolation \
        --disable-pip-version-check \
        -r requirements.txt

# 5) Copy application source
COPY . .

# 6) Render PORT 설정
ENV PORT=10000
EXPOSE 10000

###########################################################
# 7) Base64로 전달된 GCP OCR Credential JSON 복원
#    - 환경변수명: GCP_OCR_JSON_BASE64
#    - 줄바꿈 제거(tr -d '\n')
#    - /app/config/gcp-ocr.json 생성
###########################################################
RUN mkdir -p /app/config

CMD sh -c "\
  echo \"===== Creating GCP Credentials File =====\" && \
  echo \"$GCP_OCR_JSON_BASE64\" | tr -d '\n' | base64 -d > /app/config/gcp-ocr.json && \
  echo \"===== Starting SOTE-AI =====\" && \
  uvicorn app.main:app --host 0.0.0.0 --port 10000 \
"
