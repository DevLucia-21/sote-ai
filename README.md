# S:ote AI Server

> AI 기반 감정 분석을 활용한 개인 맞춤형 음악·챌린지 추천 일기 시스템      
> **S:ote**의 FastAPI 기반 AI 서버 리포지토리입니다.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?style=flat-square&logo=gunicorn&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat-square&logo=openai&logoColor=white)
![Whisper](https://img.shields.io/badge/Whisper-000000?style=flat-square&logo=openai&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google%20Cloud-4285F4?style=flat-square&logo=googlecloud&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=flat-square&logo=render&logoColor=black)

---

## Project Overview

**S:ote**는 사용자가 작성한 일기를 기반으로 감정을 분석하고,     
감정에 맞는 음악과 챌린지를 추천하는 감정 기반 일기 서비스입니다.

사용자는 텍스트, 음성, 손글씨 기반으로 일기를 작성할 수 있으며,    
입력된 일기는 AI 서버를 통해 감정 분석 결과와 음악 추천 결과로 변환됩니다.

본 AI 서버는 S:ote 서비스에서 감정 분석, 음악 추천, STT, OCR 처리를 담당합니다.     
Spring Boot 백엔드와 분리된 FastAPI 서버로 구성하여, AI 처리 로직과 서비스 도메인 로직의 책임을 분리했습니다.

본 저장소는 Fluxion 팀 캡스톤 프로젝트 **S:ote**의 AI 서버 코드를 개인 포트폴리오용으로 정리한 리포지토리입니다.

| Item                     | Description                                                             |
| ------------------------ | ----------------------------------------------------------------------- |
| Project                  | S:ote                                                                   |
| Team                     | Fluxion                                                                 |
| Period                   | 2025 Capstone Design                                                    |
| Award                    | 2025 캡스톤 경진대회 아리상                                                       |
| Repository Type          | Portfolio-maintained AI server repository                               |
| Original Team Repository | [fluxion-capstone/sote-ai](https://github.com/fluxion-capstone/sote-ai) |
| Personal Repository      | [DevLucia-21/sote-ai](https://github.com/DevLucia-21/sote-ai)           |
| Main Role                | AI Server / Backend / Frontend                                          |

---

## Service Concept

일기 서비스는 사용자의 감정을 기록할 수는 있지만,      
기록 이후의 감정 해석과 회복 행동까지 자연스럽게 연결하는 경우는 많지 않습니다.

S:ote는 단순히 일기를 저장하는 데 그치지 않고,      
사용자가 작성한 일기를 분석하여 감정 상태를 이해하고 음악 추천과 감정 회복 챌린지로 이어질 수 있도록 설계했습니다.

AI 서버는 이 흐름에서 사용자의 입력을 분석 가능한 텍스트로 변환하고,      
감정 분석 결과와 음악 추천 후보를 생성하는 역할을 담당합니다.

```text
텍스트 / 음성 / 손글씨 일기 입력
        ↓
STT / OCR 텍스트 변환
        ↓
일기 텍스트 전처리
        ↓
감정 분석 프롬프트 구성
        ↓
OpenAI API 기반 감정 분석 및 음악 추천
        ↓
응답 후처리 및 검증
        ↓
Spring Boot 백엔드와 프론트엔드 흐름에서 활용
```

---

## Branch Guide

| Branch                                                     | Description          |
| ---------------------------------------------------------- | -------------------- |
| [`main`](https://github.com/DevLucia-21/sote-ai/tree/main) | 포트폴리오용 최종 정리 브랜치     |
| [`dev`](https://github.com/DevLucia-21/sote-ai/tree/dev)   | AI 서버 개발 및 기능 통합 브랜치 |

---

## AI Server Role

S:ote AI 서버는 서비스의 AI 처리 영역을 담당합니다.

Spring Boot 백엔드는 사용자, 일기, 챌린지, LP 보상, 통계와 같은 도메인 데이터 저장 및 상태 관리를 담당하고,      
FastAPI AI 서버는 입력 변환과 감정 분석, 추천 결과 생성을 담당합니다.

| Area                 | Responsibility                   |
| -------------------- | -------------------------------- |
| Emotion Analysis     | 일기 텍스트 기반 감정 라벨, 감정 점수, 분석 사유 생성 |
| Music Recommendation | 감정, 상황 맥락, 사용자 선호 장르 기반 음악 후보 추천 |
| Prompt Engineering   | 감정 분석과 추천 품질을 높이기 위한 프롬프트 규칙 설계  |
| Preprocessing        | 일기 텍스트, 사용자 정보, 선호 장르, 컨텍스트 정리   |
| Postprocessing       | 감정 라벨 정규화, 추천 사유 보정, 음악 후보 검증    |
| STT                  | 음성 기반 일기 입력을 텍스트로 변환             |
| OCR                  | 손글씨 또는 이미지 기반 일기 입력을 텍스트로 변환     |
| Backend Integration  | Spring Boot 백엔드와 연동 가능한 응답 구조 제공 |

---

## Core Features

### 1. Emotion Analysis

사용자의 일기 텍스트를 기반으로 감정을 분석합니다.

감정 라벨은 서비스에서 사용하는 감정 범위에 맞추어 정규화하며,      
프론트엔드에서 감정 시각화와 추천 결과를 표현할 수 있도록 감정 점수와 분석 사유를 함께 반환합니다.

주요 감정 라벨은 다음과 같습니다.

```text
기쁨
슬픔
화남
무기력
예민
```

관련 파일:

```text
app/api/analysis.py
app/services/analysis_service.py
app/schemas/analysis.py
```

---

### 2. Music Recommendation

감정 분석 결과와 일기 문맥을 바탕으로 음악 후보를 추천합니다.

단순히 감정 라벨만 기준으로 추천하지 않고,      
일기 속 상황 맥락, 사용자 출생연도, 선호 장르를 함께 고려하여 사용자에게 더 자연스럽게 느껴지는 추천 결과를 생성하도록 설계했습니다.

추천 결과에는 다음 정보가 포함됩니다.

```text
음악 제목
아티스트
앨범
장르
템포
분위기
추천 사유
```

관련 파일:

```text
app/services/analysis_service.py
```

---

### 3. Prompt Engineering

감정 분석과 음악 추천 품질을 높이기 위해 프롬프트 작성에 많은 비중을 두었습니다.

감정 분석은 별도 로컬 모델을 직접 학습시키기보다,      
OpenAI API를 활용하되 서비스 목적에 맞는 프롬프트와 응답 구조를 설계하는 방식으로 구현했습니다.

프롬프트에서는 다음 요소를 명확히 제어했습니다.

```text
감정 라벨 범위
감정 점수 기준
사용자 나이대 반영
선호 장르 반영
일기 문맥 기반 추천
연애/실연 등 특정 테마 오추천 방지
공부/집중 상황에서 고에너지 음악 추천 제한
응답 형식 JSON 고정
```

이를 통해 모델 응답이 프론트엔드와 백엔드에서 바로 사용할 수 있는 일관된 구조로 반환되도록 했습니다.

---

### 4. Preprocessing & Context Detection

일기 본문을 그대로 모델에 전달하지 않고, 추천 품질에 영향을 주는 정보를 먼저 정리했습니다.

일기 속 키워드를 기반으로 공부, 휴식, 스트레스, 비, 새벽, 여행, 가족 등       
여러 상황 컨텍스트를 감지하고, 감정 분석 및 음악 추천 프롬프트에 반영했습니다.

예시 컨텍스트:

```text
study
calm
energy
stress
rain
late-night
family
travel
work
celebration
```

이 과정을 통해 같은 감정이라도 상황에 맞는 추천 결과가 나오도록 구성했습니다.

관련 파일:

```text
app/services/analysis_service.py
```

---

### 5. Postprocessing & Response Validation

OpenAI API 응답은 그대로 사용하지 않고, 서비스에서 사용할 수 있도록 후처리 과정을 거쳤습니다.

후처리에서는 감정 라벨을 서비스 기준으로 정규화하고,     
분석 사유와 음악 추천 사유가 지나치게 딱딱하거나 내부 규칙을 노출하지 않도록 보정했습니다.

또한 추천 곡이 같은 아티스트, 같은 앨범, 같은 소분류 장르에 몰리지 않도록 후보 다양성을 보정하는 로직을 구성했습니다.

관련 파일:

```text
app/services/analysis_service.py
```

---

### 6. STT

음성 기반 일기 입력을 지원하기 위해 STT 기능을 구성했습니다.

초기에는 로컬 음성 인식 모델을 직접 구성하고 모델 설정을 조정하는 방향으로 구현을 진행했습니다.     
이후 배포 환경의 서버 리소스, 모델 용량, 처리 속도, 운영 안정성을 고려하여     
API 기반 처리 구조로 전환하는 방향을 검토하고 연동 흐름을 정리했습니다.

사용자가 음성으로 입력한 일기를 텍스트로 변환하고,     
변환된 텍스트가 이후 일기 작성 및 감정 분석 흐름에 연결될 수 있도록 설계했습니다.

관련 파일:

```text
app/api/stt.py
app/services/stt_service.py
app/schemas/stt.py
```

---

### 7. OCR

손글씨 또는 이미지 기반 일기 입력을 지원하기 위해 OCR 기능이 AI 서버에 포함되어 있습니다.


본 리포지토리에서는 OCR 결과가 일기 작성 및 감정 분석 흐름과 연결될 수 있도록 AI 서버 구조 안에서 함께 관리됩니다.

관련 파일:

```text
app/api/ocr.py
app/services/ocr_service.py
```

---

## Main API Scope

| Method   | Endpoint               | Description             |
| -------- | ---------------------- | ----------------------- |
| `GET`    | `/`                    | AI 서버 헬스체크              |
| `GET`    | `/health`              | AI 서버 상태 확인             |
| `POST`   | `/api/analysis/result` | 일기 텍스트 기반 감정 분석 및 음악 추천 |
| `POST`   | `/ai/stt/transcribe`   | 음성 파일 기반 STT 변환         |
| `POST`   | `/ocr/preview`         | 이미지 기반 OCR 미리보기         |
| `DELETE` | `/ocr/delete`          | OCR 이미지 삭제              |

---

## AI Processing Flow

```text
1. 사용자가 텍스트, 음성, 손글씨 중 하나의 방식으로 일기를 입력
2. 음성 입력은 STT API를 통해 텍스트로 변환
3. 이미지 입력은 OCR API를 통해 텍스트로 변환
4. 정리된 일기 텍스트와 사용자 정보를 감정 분석 API로 전달
5. 일기 내용에서 감정 단서와 상황 컨텍스트를 추출
6. 사용자 출생연도와 선호 장르를 프롬프트에 반영
7. OpenAI API를 통해 감정 분석 및 음악 후보 추천
8. 모델 응답을 서비스 기준으로 후처리
9. 감정 라벨, 감정 점수, 추천 음악 후보를 백엔드 흐름에서 활용
```

---

## Project Structure

```text
sote-ai/
├── app/
│   ├── api/
│   │   ├── analysis.py         # 감정 분석 API
│   │   ├── ocr.py              # OCR API
│   │   └── stt.py              # STT API
│   ├── core/
│   │   └── config.py           # 환경변수 및 설정 관리
│   ├── schemas/
│   │   ├── analysis.py         # 감정 분석 요청/응답 스키마
│   │   └── stt.py              # STT 응답 스키마
│   ├── services/
│   │   ├── analysis_service.py # 감정 분석 및 음악 추천 로직
│   │   ├── ocr_service.py      # OCR 처리 로직
│   │   └── stt_service.py      # STT 변환 로직
│   └── main.py                 # FastAPI 애플리케이션 진입점
├── requirements.txt
├── render.yaml
├── runtime.txt
└── README.md
```

---

## Technical Challenges

### 1. STT 로컬 모델 기반 구현에서 API 연동 구조로 전환

초기에는 음성 일기 입력을 처리하기 위해 로컬 음성 인식 모델을 직접 구성하고,     
모델 설정과 오디오 변환 흐름을 조정하는 방식으로 STT 기능을 구현했습니다.

하지만 실제 서비스 형태로 배포하기 위해서는 모델 용량, 추론 속도, 서버 리소스,     
배포 환경에서의 안정성을 함께 고려해야 했습니다.

이 과정에서 STT 기능은 로컬 모델을 직접 운영하는 방식만으로는 부담이 크다고 판단했고,     
API 기반 처리 구조로 전환하는 방향을 검토하며 백엔드와 연동 가능한 흐름을 정리했습니다.

이를 통해 AI 서버는 음성 입력을 서비스 흐름에서 사용할 수 있는 텍스트로 변환하고,     
변환 결과가 일기 작성 및 감정 분석 흐름으로 이어질 수 있도록 구성했습니다.

---

### 2. 감정 분석 프롬프트 품질 개선

감정 분석은 단순히 긍정/부정을 분류하는 기능이 아니라,     
사용자가 작성한 일기의 분위기와 상황을 자연스럽게 읽어내야 하는 기능이었습니다.

따라서 프롬프트에는 감정 라벨 범위, 감정 점수 기준, 말투, 금지 표현,    
추천 음악 응답 형식, 사용자 선호 장르 반영 기준 등을 구체적으로 작성했습니다.

특히 모델이 내부 분석 규칙을 그대로 드러내거나,     
사용자의 일기를 기계적으로 평가하는 표현을 하지 않도록 응답 톤과 출력 형식을 세밀하게 조정했습니다.

---

### 3. 일기 문맥 기반 음악 추천 로직 설계

같은 감정이라도 사용자의 상황에 따라 어울리는 음악은 달라질 수 있습니다.

예를 들어 예민한 감정이라도 공부 중인지, 새벽인지, 비가 오는 날인지,     
스트레스가 높은 상황인지에 따라 추천해야 할 음악의 분위기가 달라집니다.

이를 위해 일기 속 키워드를 기반으로 상황 컨텍스트를 감지하고,     
감정 라벨뿐 아니라 사용자의 상황과 선호 장르를 함께 반영하도록 추천 로직을 구성했습니다.

또한 특정 상황에서 맞지 않는 추천이 나오지 않도록     
연애/실연 테마, 고BPM 음악, 고에너지 장르 등에 대한 제한 규칙도 추가했습니다.

---

### 4. 전처리와 후처리를 통한 응답 안정화

LLM 응답은 항상 동일한 형식과 품질을 보장하지 않기 때문에,      
서비스에서 안정적으로 사용하기 위한 전처리와 후처리가 필요했습니다.

전처리 단계에서는 사용자 출생연도, 선호 장르, 일기 컨텍스트를 정리하여 프롬프트에 반영했습니다.

후처리 단계에서는 감정 라벨을 서비스 기준으로 정규화하고,     
추천 사유에서 불필요한 분석 말투나 내부 규칙이 드러나는 표현을 제거했습니다.

또한 음악 추천 후보가 특정 아티스트나 장르에 과도하게 몰리지 않도록 후보 다양성을 보정했습니다.

---

### 5. Spring Boot 백엔드와의 책임 분리

S:ote는 Spring Boot 백엔드와 FastAPI AI 서버가 분리된 구조입니다.

AI 서버는 감정 분석과 입력 변환, 추천 결과 생성을 담당하고,     
백엔드는 사용자 인증, 일기 저장, 분석 결과 저장, 챌린지 상태, LP 보상, 통계 흐름을 담당합니다.

이 구조를 통해 AI 처리 로직과 서비스 도메인 로직이 섞이지 않도록 했고,     
각 서버가 자신의 책임에 집중할 수 있도록 분리했습니다.

---

### 6. Render 환경변수와 공개 리포지토리 보안 설정 정리

포트폴리오 공개 리포지토리로 전환하면서     
OpenAI API Key, Google Cloud 인증 정보, Redis URL 등 민감 정보를 저장소에서 제외했습니다.

특히 Google Cloud와 같이 인증 정보가 JSON 파일 형태로 제공되는 경우,     
로컬에서는 파일 경로를 기준으로 인증 정보를 읽을 수 있지만    
Render와 같은 PaaS 환경에서는 동일한 방식으로 파일을 직접 관리하기 어렵다는 문제가 있었습니다.

이를 해결하기 위해 인증 JSON을 그대로 저장소에 포함하지 않고,    
base64 형태로 인코딩한 값을 환경변수로 등록한 뒤     
서버 실행 시 필요한 인증 정보를 복원하는 방식으로 정리했습니다.

이 과정에서 로컬 실행 환경과 배포 환경의 인증 처리 방식이 달라 발생하는 문제를 확인했고,    
외부 API 인증 정보는 코드나 파일에 직접 의존하기보다 환경변수 기반으로 관리해야 한다는 점을 경험했습니다.

또한 서비스 계정 JSON과 `.env` 파일이 커밋되지 않도록 `.gitignore`를 정리하고,     
공개 리포지토리에 노출될 수 있는 디버그성 코드와 불필요한 파일을 함께 점검했습니다.

---

## My Contribution

본 프로젝트에서는 AI 서버의 감정 분석과 STT 기능, 그리고 Spring Boot 백엔드와의 연동 흐름을 주로 담당했습니다.

감정 분석에서는 OpenAI API 기반 분석 구조를 사용하되,     
서비스에 맞는 감정 라벨과 추천 결과가 안정적으로 생성되도록     
프롬프트 설계, 일기 컨텍스트 전처리, 응답 후처리 로직을 구현했습니다.

STT 기능에서는 초기 로컬 음성 인식 모델 기반 구현을 진행하고,    
배포 환경을 고려하여 API 기반 처리 구조로 전환하는 방향을 검토했습니다.

프로젝트 종료 이후에는 포트폴리오 공개를 위해     
민감 정보 제거, 환경변수 정리, 불필요한 코드 정리, README 작성까지 진행했습니다.

| Area                 | Contribution                          |
| -------------------- | ------------------------------------- |
| AI Server            | FastAPI 기반 AI 서버 구조 설계 및 구현           |
| Emotion Analysis     | 일기 텍스트 기반 감정 분석 API 구현                |
| Prompt Engineering   | 감정 라벨, 감정 점수, 추천 결과 생성을 위한 프롬프트 설계    |
| Preprocessing        | 사용자 정보, 선호 장르, 일기 컨텍스트 정리             |
| Postprocessing       | 감정 라벨 정규화, 추천 사유 보정, 음악 후보 다양성 검증     |
| Music Recommendation | 감정과 상황 맥락 기반 음악 후보 추천 로직 구성           |
| STT                  | 음성 일기 입력을 위한 STT 처리 흐름 구현 및 API 전환 검토 |
| Backend Integration  | Spring Boot 백엔드와 연동 가능한 API 응답 구조 설계  |
| Portfolio Cleanup    | 공개 리포지토리 전환을 위한 민감 정보 제거 및 문서 정리      |

---

## Tech Stack

| Category         | Stack                            |
| ---------------- | -------------------------------- |
| Language         | Python                           |
| Framework        | FastAPI                          |
| Server           | Uvicorn                          |
| AI / LLM         | OpenAI API                       |
| STT              | Whisper, faster-whisper          |
| Audio Processing | FFmpeg, pydub                    |
| OCR              | Google Cloud Vision              |
| Cache / Limit    | Redis                            |
| HTTP Client      | requests, httpx                  |
| Config           | python-dotenv, pydantic-settings |

---

## Environment Variables

프로젝트 실행을 위해 로컬 환경에서 `.env` 파일을 생성하고 필요한 값을 설정해야 합니다.

공개 저장소에는 실제 API Key, Google Cloud 인증 JSON, Redis 접속 정보 등 민감 정보를 포함하지 않습니다.

주요 설정 항목은 다음과 같습니다.

```text
ENVIRONMENT

OPENAI_API_KEY
ENABLE_OPENAI

WHISPER_MODEL
WHISPER_DEVICE
WHISPER_COMPUTE_TYPE
FFMPEG_BIN

GOOGLE_APPLICATION_CREDENTIALS
GCP_OCR_JSON_BASE64

REDIS_URL

SPRING_STT_URL
SPRING_OCR_URL
SEND_STT_TO_SPRING
SEND_OCR_TO_SPRING
```

---

## Running the Project

```bash
git clone https://github.com/DevLucia-21/sote-ai.git
cd sote-ai
```

가상환경을 생성하고 활성화합니다.

```bash
python -m venv .venv
```

Windows PowerShell 환경에서는 다음 명령어를 사용할 수 있습니다.

```powershell
.venv\Scripts\activate
```

의존성을 설치합니다.

```bash
pip install -r requirements.txt
```

로컬 실행을 위해 `.env` 파일을 생성하고 필요한 환경변수를 설정합니다.

```text
.env
```

실행 명령어는 다음과 같습니다.

```bash
uvicorn app.main:app --reload
```

서버 실행 후 다음 주소에서 상태를 확인할 수 있습니다.

```text
http://localhost:8000/health
```

---

## Related Repositories

| Repository                                                              | Description              |
| ----------------------------------------------------------------------- | ------------------------ |
| [sote-fe](https://github.com/DevLucia-21/sote-fe)                       | S:ote 프론트엔드 리포지토리        |
| [sote-be](https://github.com/DevLucia-21/sote-be)                       | Spring Boot 기반 백엔드 리포지토리 |
| [sote-ai](https://github.com/DevLucia-21/sote-ai)                       | FastAPI 기반 AI 서버 리포지토리   |
| [fluxion-capstone/sote-ai](https://github.com/fluxion-capstone/sote-ai) | S:ote 원본 팀 AI 서버 리포지토리   |

---

## Note

본 저장소는 Fluxion 팀 캡스톤 프로젝트의 AI 서버 코드를 개인 포트폴리오용으로 정리한 리포지토리입니다.

실제 운영 환경에서 사용한 민감 설정값은 포함하지 않으며,     
로컬 실행을 위해서는 별도의 환경 변수 및 외부 서비스 설정이 필요합니다.

원본 팀 리포지토리는 팀 프로젝트 진행 당시 사용한 저장소이며, 현재 접근 권한 또는 공개 여부가 변경되었을 수 있습니다.

---

## Author

**Yeeun Park**

* GitHub: [DevLucia-21](https://github.com/DevLucia-21)
