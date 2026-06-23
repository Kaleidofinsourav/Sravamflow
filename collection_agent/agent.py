import logging

from collection_agent.config import get_collection_agent_settings
from collection_agent.prompts import load_prompt

logger = logging.getLogger("collection-agent")
logging.basicConfig(level=logging.INFO)


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv()


def _runtime_imports():
    try:
        from livekit.agents import JobContext, WorkerOptions, cli
        from livekit.agents.voice import Agent, AgentSession
        from livekit.plugins import sarvam
    except ImportError as exc:
        raise RuntimeError(
            'Voice dependencies are not installed. Run: python3 -m pip install -e ".[voice]"'
        ) from exc

    return JobContext, WorkerOptions, cli, Agent, AgentSession, sarvam


def build_collection_agent_class():
    _load_dotenv_if_available()
    settings = get_collection_agent_settings()
    prompt = load_prompt(settings.prompt_path)
    missing_keys = settings.missing_runtime_keys()
    if missing_keys:
        raise RuntimeError(
            "Missing required environment variables for collection agent: "
            + ", ".join(missing_keys)
            + ". Copy .env.example to .env and fill in the real keys."
        )

    _, _, _, Agent, _, sarvam = _runtime_imports()

    class CollectionAgent(Agent):
        def __init__(self) -> None:
            super().__init__(
                instructions=prompt,
                stt=sarvam.STT(
                    language=settings.stt_language,
                    model=settings.stt_model,
                    mode="transcribe",
                ),
                llm=sarvam.LLM(model=settings.llm_model),
                tts=sarvam.TTS(
                    target_language_code=settings.tts_language,
                    model=settings.tts_model,
                    speaker=settings.tts_speaker,
                ),
            )

        async def on_enter(self) -> None:
            self.session.generate_reply()

    return CollectionAgent


async def entrypoint(ctx) -> None:
    JobContext, _, _, _, AgentSession, _ = _runtime_imports()
    if not isinstance(ctx, JobContext):
        logger.warning("entrypoint_received_unexpected_context_type", extra={"context_type": type(ctx).__name__})

    CollectionAgent = build_collection_agent_class()
    logger.info("collection_agent_user_connected", extra={"room": ctx.room.name})

    session = AgentSession()
    await session.start(agent=CollectionAgent(), room=ctx.room)


def main() -> None:
    _load_dotenv_if_available()
    _, WorkerOptions, cli, _, _, _ = _runtime_imports()
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


if __name__ == "__main__":
    main()
