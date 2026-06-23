from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CollectionAgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    livekit_url: str = Field(default="", alias="LIVEKIT_URL")
    livekit_api_key: str = Field(default="", alias="LIVEKIT_API_KEY")
    livekit_api_secret: str = Field(default="", alias="LIVEKIT_API_SECRET")
    sarvam_api_key: str = Field(default="", alias="SARVAM_API_KEY")

    prompt_path: Path = Field(
        default=Path("collection_agent/prompts/collection_agent.md"),
        alias="COLLECTION_AGENT_PROMPT_PATH",
    )
    stt_language: str = Field(default="unknown", alias="COLLECTION_AGENT_STT_LANGUAGE")
    stt_model: str = Field(default="saaras:v3", alias="COLLECTION_AGENT_STT_MODEL")
    tts_language: str = Field(default="en-IN", alias="COLLECTION_AGENT_TTS_LANGUAGE")
    tts_model: str = Field(default="bulbul:v3", alias="COLLECTION_AGENT_TTS_MODEL")
    tts_speaker: str = Field(default="aditya", alias="COLLECTION_AGENT_TTS_SPEAKER")
    llm_model: str = Field(default="sarvam-105b", alias="COLLECTION_AGENT_LLM_MODEL")

    def missing_runtime_keys(self) -> list[str]:
        missing: list[str] = []
        for key, value in {
            "LIVEKIT_URL": self.livekit_url,
            "LIVEKIT_API_KEY": self.livekit_api_key,
            "LIVEKIT_API_SECRET": self.livekit_api_secret,
            "SARVAM_API_KEY": self.sarvam_api_key,
        }.items():
            if not value:
                missing.append(key)
        return missing


def get_collection_agent_settings() -> CollectionAgentSettings:
    return CollectionAgentSettings()
