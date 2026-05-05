# S:ote AI Server - Dev Branch

> AI 기반 감정 분석을 활용한 개인 맞춤형 음악·챌린지 추천 일기 시스템      
> **S:ote**의 AI 서버 개발 및 기능 통합 브랜치입니다.

---

## Branch Purpose

이 브랜치는 S:ote AI 서버 개발 과정에서 사용한 개발 브랜치입니다.

감정 분석, 음악 추천, STT, OCR, Redis 기반 사용 제한, Spring Boot 백엔드 연동 등      
AI 서버의 주요 기능을 구현하고 통합하는 과정에서 사용되었습니다.

포트폴리오 최종 정리용 `main` 브랜치와 달리,     
본 브랜치는 기능 개발과 실험, 외부 API 연동 구조가 누적된 개발 기준 브랜치입니다.

---

## Development Scope

본 브랜치에서는 다음 AI 서버 기능 개발을 중심으로 작업했습니다.

* FastAPI 기반 AI 서버 구성
* 일기 텍스트 기반 감정 분석 API
* OpenAI API 기반 감정 분석 및 음악 추천 로직
* 사용자 출생연도와 선호 장르를 반영한 추천 결과 생성
* 감정 라벨, 감정 점수, 추천 사유, 음악 후보 응답 구조 설계
* Whisper 기반 STT 음성 변환 API
* FFmpeg 기반 오디오 포맷 변환 처리
* Google Cloud Vision 기반 OCR 이미지 텍스트 추출
* Redis 기반 STT/OCR 하루 1회 사용 제한 처리
* STT/OCR 결과의 Spring Boot 백엔드 전송 옵션 구성
* 환경변수 기반 외부 API Key 및 인증 정보 관리

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

## Main API Scope

| Method   | Endpoint               | Description             |
| -------- | ---------------------- | ----------------------- |
| `GET`    | `/`                    | AI 서버 헬스체크              |
| `POST`   | `/api/analysis/result` | 일기 텍스트 기반 감정 분석 및 음악 추천 |
| `POST`   | `/ai/stt/transcribe`   | 음성 파일 기반 STT 변환         |
| `POST`   | `/ocr/preview`         | 이미지 기반 OCR 미리보기         |
| `DELETE` | `/ocr/delete`          | OCR 이미지 삭제              |

---

## AI Processing Flow

```text
1. 사용자가 텍스트, 음성, 이미지 중 하나의 방식으로 일기를 입력
2. 음성 입력은 STT API를 통해 텍스트로 변환
3. 이미지 입력은 OCR API를 통해 텍스트로 변환
4. 변환된 일기 텍스트를 감정 분석 API로 전달
5. 감정 라벨, 감정 점수, 분석 사유를 생성
6. 감정과 상황 맥락, 사용자 선호 장르를 바탕으로 음악 후보를 추천
7. 분석 결과를 Spring Boot 백엔드와 프론트엔드 흐름에서 활용
```

---

## Running the Project

```bash
uvicorn app.main:app --reload
```

Windows PowerShell 환경에서는 가상환경을 활성화한 뒤 실행합니다.

```powershell
.venv\Scripts\activate
uvicorn app.main:app --reload
```

실행을 위해서는 로컬 환경에서 별도의 환경변수 파일이 필요합니다.

```text
.env
.env.production
.env.local
```

공개 저장소에는 실제 API Key, Google Cloud 인증 JSON, Redis 접속 정보 등 민감 정보를 포함하지 않습니다.      
OpenAI API Key, Google Cloud 인증 정보, Redis URL, Spring Boot 연동 URL 등은 로컬 환경변수로 관리합니다.

---

## Environment Variables

주요 환경변수는 다음과 같습니다.

| Name                             | Description                     |
| -------------------------------- | ------------------------------- |
| `ENVIRONMENT`                    | 실행 환경 구분                        |
| `OPENAI_API_KEY`                 | OpenAI API Key                  |
| `ENABLE_OPENAI`                  | OpenAI API 사용 여부                |
| `WHISPER_MODEL`                  | Whisper 모델 설정                   |
| `WHISPER_DEVICE`                 | Whisper 실행 디바이스 설정              |
| `WHISPER_COMPUTE_TYPE`           | Whisper 연산 타입 설정                |
| `FFMPEG_BIN`                     | FFmpeg 실행 파일 경로                 |
| `SPRING_STT_URL`                 | STT 결과를 전송할 Spring Boot API URL |
| `SPRING_OCR_URL`                 | OCR 결과를 전송할 Spring Boot API URL |
| `SEND_STT_TO_SPRING`             | STT 결과 Spring 전송 여부             |
| `SEND_OCR_TO_SPRING`             | OCR 결과 Spring 전송 여부             |
| `GOOGLE_APPLICATION_CREDENTIALS` | Google Cloud 인증 파일 경로           |
| `REDIS_URL`                      | Redis 접속 URL                    |

---

## Project Structure

```text
sote-ai/
├── app/
│   ├── api/
│   │   ├── analysis.py         # 감정 분석 API
│   │   ├── stt.py              # STT API
│   │   └── ocr.py              # OCR API
│   ├── core/
│   │   └── config.py           # 환경변수 및 설정 관리
│   ├── schemas/
│   │   ├── analysis.py         # 감정 분석 요청/응답 스키마
│   │   └── stt.py              # STT 응답 스키마
│   ├── services/
│   │   ├── analysis_service.py # 감정 분석 및 음악 추천 로직
│   │   ├── stt_service.py      # STT 변환 로직
│   │   └── ocr_service.py      # OCR 처리 로직
│   └── main.py                 # FastAPI 애플리케이션 진입점
├── requirements.txt
├── render.yaml
├── runtime.txt
└── README.md
```

---

## Branch Guide

| Branch | Description          |
| ------ | -------------------- |
| `main` | 포트폴리오용 최종 정리 브랜치     |
| `dev`  | AI 서버 개발 및 기능 통합 브랜치 |

---

## Note

본 브랜치는 S:ote AI 서버의 기능 개발과 통합 과정이 누적된 개발 브랜치입니다.

최신 포트폴리오 정리본은 `main` 브랜치를 기준으로 확인하는 것을 권장합니다.     
`dev` 브랜치에는 개발 과정의 구조와 실험성 코드가 일부 남아 있을 수 있습니다.

민감 정보는 공개 저장소에 포함하지 않으며, 실제 실행 시 필요한 API Key와 인증 파일은 로컬 또는 서버 환경변수로 별도 관리합니다.
