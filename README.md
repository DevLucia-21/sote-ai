# S:ote AI Server - Dev Branch

> AI 기반 감정 분석을 활용한 개인 맞춤형 음악·챌린지 추천 일기 시스템      
> **S:ote**의 AI 서버 개발 및 기능 통합 브랜치입니다.

---

## Branch Purpose

이 브랜치는 S:ote AI 서버 개발 과정에서 사용한 개발 브랜치입니다.

감정 분석, 음악 추천, STT, OCR, Redis 기반 사용 제한, Spring Boot 백엔드 연동 등      
AI 서버의 주요 기능을 개발하고 통합하는 과정에서 사용되었습니다.

포트폴리오 최종 정리용 `main` 브랜치와 달리,      
본 브랜치는 기능 개발과 외부 API 연동 구조가 누적된 개발 기준 브랜치입니다.

---

## Branch Scope

본 브랜치에서는 다음 AI 서버 기능 흐름을 중심으로 작업했습니다.

* FastAPI 기반 AI 서버 구성
* OpenAI API 기반 감정 분석 및 음악 추천 로직
* Whisper 기반 STT 음성 변환 처리
* Google Cloud Vision 기반 OCR 이미지 텍스트 추출
* Redis 기반 STT/OCR 사용 제한 처리
* Spring Boot 백엔드 연동을 위한 응답 구조 구성
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

## Processing Flow

```text
1. 사용자가 텍스트, 음성, 이미지 중 하나의 방식으로 일기를 입력
2. 음성 또는 이미지 입력은 STT/OCR API를 통해 텍스트로 변환
3. 변환된 일기 텍스트를 감정 분석 API로 전달
4. 감정 라벨, 감정 점수, 분석 사유와 음악 추천 결과를 생성
5. 분석 결과를 Spring Boot 백엔드와 프론트엔드 흐름에서 활용
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
```

공개 저장소에는 실제 API Key, Google Cloud 인증 JSON, Redis 접속 정보 등 민감 정보를 포함하지 않습니다.      
OpenAI API Key, Google Cloud 인증 정보, Redis URL, Spring Boot 연동 URL 등은    
로컬 또는 서버 환경변수로 별도 관리합니다.

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

민감 정보는 공개 저장소에 포함하지 않으며,      
실제 실행 시 필요한 API Key와 인증 파일은 로컬 또는 서버 환경변수로 별도 관리합니다.
