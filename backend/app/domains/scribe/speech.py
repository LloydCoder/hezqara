from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class TranscriptSegment:
    speaker: str
    start_ms: int
    end_ms: int
    text: str

@dataclass(frozen=True)
class TranscriptionResult:
    provider_name: str
    model_version: str
    transcript_text: str
    segments: list[TranscriptSegment]
    language_code: str|None = None
    provider_request_id: str|None = None
    provenance: dict|None = None

class SpeechProvider(Protocol):
    async def transcribe(self, audio_ref: str, *, language_code: str|None=None, medical_mode: bool=True) -> TranscriptionResult: ...

class UnconfiguredSpeechProvider:
    async def transcribe(self, audio_ref: str, *, language_code: str|None=None, medical_mode: bool=True) -> TranscriptionResult:
        raise RuntimeError("no approved speech provider is configured for this environment")

def provider_contract() -> dict:
    return {
        "interface":"speech-provider.v1",
        "required":["transcribe"],
        "capabilities":["streaming","batch","speaker_diarization","timestamps","medical_terminology"],
        "provider_is_replaceable":True,
        "canonical_state_owner":"hezqara",
    }
