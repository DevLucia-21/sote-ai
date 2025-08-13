import uuid
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import logging
import concurrent.futures
import os
import re

from faster_whisper import WhisperModel  # 경량화된 Whisper 구현

# 선택적 라이브러리
try:
    from pydub import AudioSegment, silence
    PYDUB_AVAILABLE = True
except Exception:
    PYDUB_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except Exception:
    PSUTIL_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False

# 한국어 문장 분리기(kss) 옵션
try:
    import kss
    KSS_AVAILABLE = True
except Exception:
    KSS_AVAILABLE = False

from app.core.config import settings

logger = logging.getLogger("sote.stt")
MODEL_CACHE: Dict[str, Any] = {}  # 모델 캐싱


# -------------------- 시스템 환경 판단 --------------------
def _has_enough_ram_gb(threshold_gb: int) -> bool:
    """사용 가능한 RAM이 threshold_gb 이상인지 확인"""
    if not PSUTIL_AVAILABLE:
        return True
    try:
        return psutil.virtual_memory().available / (1024 ** 3) >= threshold_gb
    except Exception:
        return True


def _cuda_available() -> bool:
    """CUDA 사용 가능 여부 확인"""
    if not TORCH_AVAILABLE:
        return False
    try:
        return torch.cuda.is_available()
    except Exception:
        return False


def pick_default_model() -> str:
    print("[TEST] pick_default_model called")
    """환경에 따라 기본 Whisper 모델 크기 선택"""

    env_model = getattr(settings, "WHISPER_MODEL", None)
    if env_model and str(env_model).lower() != "auto":
        model = str(env_model)
        deploy_target = "env only"
    else:
        deploy_target = (getattr(settings, "DEPLOY_TARGET", None) or os.getenv("DEPLOY_TARGET", "auto")).lower()

        if deploy_target == "mobile":
            model = "base"
        elif deploy_target == "desktop":
            model = "small" if _has_enough_ram_gb(settings.MIN_RAM_FOR_SMALL_GB) else "base"
        elif deploy_target == "server":
            model = "small" if _cuda_available() else "base"
        else:
            model = "small" if _cuda_available() else "base"

    print(f"[WHISPER] Deploy target: {deploy_target}, Selected model: {model}")
    return model


def _pick_compute_type(device: str, ram_ok: bool) -> str:
    """디바이스/RAM 상태에 따라 faster-whisper compute_type 결정"""
    cfg = getattr(settings, "WHISPER_COMPUTE_TYPE", None) or os.getenv("WHISPER_COMPUTE_TYPE")
    if cfg:
        return str(cfg)
    if device == "cuda":
        return "float16"
    return "int8" if not ram_ok else "int8_float16"


# -------------------- 모델 로드 --------------------
def load_model(name: Optional[str]):
    """faster-whisper 모델 로드 (캐싱 사용)"""
    if not name or name.lower() == "auto":
        name = pick_default_model()

    device = "cuda" if _cuda_available() else "cpu"
    ram_ok = _has_enough_ram_gb(settings.MIN_RAM_FOR_SMALL_GB)
    compute_type = _pick_compute_type(device, ram_ok)
    key = f"{name}|{device}|{compute_type}"

    if key in MODEL_CACHE:
        return MODEL_CACHE[key]

    logger.info(f"[STT] 모델 로드: {name} (device={device}, compute_type={compute_type})")
    model = WhisperModel(name, device=device, compute_type=compute_type)
    MODEL_CACHE[key] = model
    return model


# -------------------- 오디오 전처리 --------------------
def _convert_to_wav_mono_16k(src_path: str, dst_path: str):
    """모노 16kHz WAV로 변환"""
    if not PYDUB_AVAILABLE:
        raise RuntimeError("pydub 필요")
    audio = AudioSegment.from_file(src_path)
    audio.set_channels(1).set_frame_rate(16000).set_sample_width(2).export(dst_path, format="wav")


def _remove_silence_simple(wav_path: str, min_silence_len: int = 200, silence_thresh: int = -40) -> str:
    """무음 구간 제거"""
    if not PYDUB_AVAILABLE:
        return wav_path
    audio = AudioSegment.from_wav(wav_path)
    non_silents = silence.detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    if not non_silents:
        return wav_path
    out = AudioSegment.empty()
    for start_ms, end_ms in non_silents:
        out += audio[start_ms:end_ms]
    out_path = Path(tempfile.gettempdir()) / f"trimmed_{uuid.uuid4().hex}.wav"
    out.export(str(out_path), format="wav")
    return str(out_path)


def _clean_text(s: str) -> str:
    """텍스트 최소 정리: 공백/구두점 앞 공백"""
    if not isinstance(s, str):
        return ""
    s = " ".join(s.split())
    return re.sub(r'\s([,\.!?:;])', r'\1', s).strip()


def _should_preprocess_for(model_name: str) -> bool:
    """
    모델별 전처리 수행 여부:
    - small 계열: 스킵 (속도 우선)
    - 나머지: 수행 (안정성/정확도 우선)
    """
    name = (model_name or "").lower()
    return name not in {"small", "small.en"}

def _beam_for(model_name: str) -> int:
    """모델별 beam size: small=3, 그 외=5"""
    return 3 if (model_name or "").lower().startswith("small") else 5


# -------------------- 한국어 후처리(문장/마침표) --------------------
def _heuristic_sentence_split_ko(text: str) -> List[str]:
    """kss가 없을 때 쓰는 간단 문장 분리 휴리스틱"""
    if not text:
        return []
    t = text

    # 붙은 접속부 분리: '다그래서' → '다. 그래서'
    t = re.sub(r'(다|요)(그래서|그리고|그러나|하지만)', r'\1. \2', t)
    # 문장 말투 뒤 마침표 보정
    t = re.sub(r'(다|요|죠|네|까)(?=[^\.!?])', r'\1.', t)
    t = " ".join(t.split())

    parts = [p.strip() for p in re.split(r'(?<=[\.!?])\s+', t) if p.strip()]

    # 너무 짧게 잘린 조각 합치기
    merged: List[str] = []
    buf = ""
    for p in parts:
        if not buf:
            buf = p
            continue
        if len(buf) < 8:
            buf = (buf + " " + p).strip()
        else:
            merged.append(buf)
            buf = p
    if buf:
        merged.append(buf)
    return merged


def _post_process_korean(text: str, segments: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    한국어 후처리:
      1) kss 있으면 문장 분리, 없으면 휴리스틱
      2) 세그먼트 간 긴 정적 구간(>0.6s)에서 문장 경계 보정
      3) 문장 끝 마침표/공백 정리
    """
    raw = (text or "").strip()
    if not raw:
        return ""

    # 1) 1차 문장 분리
    if KSS_AVAILABLE:
        sents = [s.strip() for s in kss.split_sentences(raw) if s.strip()]
    else:
        sents = _heuristic_sentence_split_ko(raw)

    # 2) 세그먼트 기반 경계 보정
    if segments:
        try:
            enriched = []
            prev_end = None
            for seg in segments:
                seg_text = (seg.get("text") or "").strip()
                if not seg_text:
                    continue
                # 문장 말투면 마침표 보정
                if not re.search(r'[\.!?]$', seg_text) and re.search(r'(다|요|죠|네|까)$', seg_text):
                    seg_text += "."
                if prev_end is not None:
                    gap = float(seg.get("start", 0.0)) - prev_end
                    if gap > 0.6 and enriched and not re.search(r'[\.!?]$', enriched[-1]):
                        enriched[-1] = enriched[-1].rstrip() + "."
                prev_end = float(seg.get("end", 0.0))
                enriched.append(seg_text)
            # 지나치게 괴리 없으면 세그먼트 기반 문장으로 교체
            if enriched and abs(len(" ".join(enriched)) - len(raw)) < max(20, int(len(raw) * 0.3)):
                sents = [s.strip() for s in " ".join(enriched).split(".") if s.strip()]
                sents = [s + "." for s in sents]
        except Exception:
            pass

    # 3) 마침표/공백 정리
    cleaned = []
    for s in sents:
        s = s.strip()
        if not re.search(r'[\.!?]$', s):
            s += "."
        s = re.sub(r'\s+([,\.!?])', r'\1', s)
        cleaned.append(s)

    return " ".join(cleaned)


# -------------------- 모델 호출 --------------------
def _fw_transcribe(model: WhisperModel, audio_path: str, beam_size: int, do_vad: bool) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """faster-whisper로 STT 실행"""
    segments, info = model.transcribe(audio_path, beam_size=beam_size, vad_filter=do_vad)
    seg_list = [{
        "start": float(getattr(seg, "start", 0.0)),
        "end": float(getattr(seg, "end", 0.0)),
        "text": (getattr(seg, "text", "") or "").strip(),
        "avg_logprob": getattr(seg, "avg_logprob", None),
        "no_speech_prob": getattr(seg, "no_speech_prob", None),
    } for seg in segments]
    return seg_list, {"language": getattr(info, "language", None), "duration": getattr(info, "duration", None)}


# -------------------- 저신뢰 구간 재추론 --------------------
def _retranscribe_low_confidence_segments(
    file_path: str,
    segments: List[Dict[str, Any]],
    fallback_model_name: str,
    margin_seconds: float = 0.2,
    use_vad_inside: bool = False
) -> Optional[str]:
    print(f"[DEBUG] 재추론 시작 - fallback_model_name = {fallback_model_name}")

    """avg_logprob 낮은 구간만 지정 모델로 재추론"""
    if not PYDUB_AVAILABLE:
        return None
    low_conf = [s for s in segments if s.get("avg_logprob") is not None and s.get("avg_logprob") < -1.0]
    if not low_conf:
        return None

    try:
        audio = AudioSegment.from_file(file_path)
    except Exception:
        return None

    fb_model = load_model(fallback_model_name)
    tmp_dir = Path(tempfile.gettempdir())

    for seg in low_conf:
        start_s = max(0.0, seg.get("start", 0.0) - margin_seconds)
        end_s = seg.get("end", start_s + 1.0) + margin_seconds
        start_ms, end_ms = int(start_s * 1000), int(end_s * 1000)
        if end_ms <= start_ms:
            end_ms = start_ms + 1000
        chunk_path = tmp_dir / f"seg_{uuid.uuid4().hex}.wav"
        audio[start_ms:end_ms].export(str(chunk_path), format="wav")
        try:
            segs, _ = _fw_transcribe(fb_model, str(chunk_path), do_vad=use_vad_inside)
            new_text = "".join(s.get("text", "") for s in segs).strip()
            if new_text:
                seg["text"] = _clean_text(new_text)
        finally:
            Path(chunk_path).unlink(missing_ok=True)

    combined = " ".join(s.get("text", "") for s in sorted(segments, key=lambda x: x.get("start", 0.0)))
    return _post_process_korean(combined, segments)


# -------------------- 메인 전사 함수 --------------------
def transcribe_audio(
    file_path: str,
    model_name: Optional[str] = None,
    do_vad: bool = False,
    low_conf_retranscribe: bool = True,
    low_conf_threshold: float = -1.0,  # 현재 휴리스틱은 -1.0 고정 사용
    timeout_seconds: Optional[float] = 30.0,
    prefer_first: bool = True
) -> str:
    """
    오디오 파일을 텍스트로 변환(STT)
    - prefer_first=True: small 모델 우선 → 실패 시 base 모델
    - prefer_first=False: 지정 모델 우선 → 저신뢰 구간만 small 재추론
    """
    tmp_files: List[str] = []
    try:
        src = Path(file_path)
        if not src.exists():
            raise FileNotFoundError(f"파일 없음: {file_path}")

                # 모델 결정
        chosen = model_name or getattr(settings, "WHISPER_MODEL", None) or pick_default_model()
        if str(chosen).lower() == "auto":
            chosen = pick_default_model()

        # prefer/fallback 및 전처리/beam 정책 결정
        if prefer_first:
            prefer_model = chosen if chosen != "base" else "small"
            fallback_model = "base" if prefer_model != "base" else "tiny"
            preprocess_enabled = _should_preprocess_for(prefer_model)
            prefer_beam = _beam_for(prefer_model)
        else:
            prefer_model = None
            fallback_model = "small"  # 재추론용
            preprocess_enabled = _should_preprocess_for(chosen)
            prefer_beam = _beam_for(chosen)

        # ---- WAV 변환 (전처리 스킵이면 생략) ----
        processed_path = str(src)
        if preprocess_enabled and PYDUB_AVAILABLE:
            try:
                converted = Path(tempfile.gettempdir()) / f"conv_{uuid.uuid4().hex}.wav"
                _convert_to_wav_mono_16k(str(src), str(converted))
                processed_path = str(converted)
                tmp_files.append(str(converted))
            except Exception:
                pass

        # ---- 무음 제거 (전처리 스킵이면 생략) ----
        effective_do_vad = (do_vad and preprocess_enabled)
        if effective_do_vad and PYDUB_AVAILABLE:
            try:
                trimmed = _remove_silence_simple(processed_path)
                if trimmed != processed_path:
                    tmp_files.append(trimmed)
                    processed_path = trimmed
            except Exception:
                pass

        def _call_model(name_local: str, beam: int):
            m = load_model(name_local)
            # 전처리 스킵 시에는 vad_filter=False로 고정
            return _fw_transcribe(m, processed_path, beam_size=beam, do_vad=effective_do_vad)

        if prefer_first:
            try_prefer = not (
                prefer_model == "small"
                and not _cuda_available()
                and not _has_enough_ram_gb(settings.MIN_RAM_FOR_SMALL_GB)
            )
            if try_prefer:
                try:
                    if timeout_seconds is None:
                        segs, _ = _call_model(prefer_model, beam=prefer_beam)
                    else:
                        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                            segs, _ = ex.submit(_call_model, prefer_model, prefer_beam).result(timeout=timeout_seconds)
                    text = "".join(s["text"] for s in segs)
                    return _post_process_korean(text, segs)
                except Exception:
                    pass

            # fallback 실행 (base 쪽은 전처리 수행/beam=5)
            segs, _ = _call_model(fallback_model, beam=_beam_for(fallback_model))
            if low_conf_retranscribe:
                recomposed = _retranscribe_low_confidence_segments(
                    processed_path, segs, fallback_model_name=prefer_model
                )
                if recomposed:
                    return recomposed
            text = "".join(s["text"] for s in segs)
            return _post_process_korean(text, segs)

        else:
            segs, _ = _call_model(chosen, beam=prefer_beam)
            if low_conf_retranscribe:
                recomposed = _retranscribe_low_confidence_segments(
                    processed_path, segs, fallback_model_name="small"
                )
                if recomposed:
                    return recomposed
            text = "".join(s["text"] for s in segs)
            return _post_process_korean(text, segs)
        
    finally:
        for p in tmp_files:
            Path(p).unlink(missing_ok=True)
