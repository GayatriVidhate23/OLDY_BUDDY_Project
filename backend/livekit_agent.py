import logging
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession
from livekit.plugins import silero, sarvam

# Load .env from project root via absolute path
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("oldy-buddy-agent")

# Verify API keys without printing secrets
if not os.getenv("SARVAM_API_KEY"):
    raise RuntimeError("Missing SARVAM_API_KEY in .env file.")
if not os.getenv("LIVEKIT_API_KEY"):
    raise RuntimeError("Missing LIVEKIT_API_KEY in .env file.")


async def entrypoint(ctx: JobContext):
    logger.info(f"Connecting to room: {ctx.room.name}")
    await ctx.connect()

    # 1. VAD Tuning for elderly users (Less sensitive to prevent agent from stopping randomly)
    vad_plugin = silero.VAD.load(
        min_speech_duration=0.2,       # Require longer speech to trigger
        min_silence_duration=2.5,      # Wait longer before assuming user is done (prevents cutting off)
        prefix_padding_duration=0.5,
        activation_threshold=0.4,      # Less sensitive to background noise/breathing
    )

    # 2. STT Setup (Sarvam)
    stt_plugin = sarvam.STT(
        sample_rate=8000,
        model="saaras:v4",
        language="hi-IN",
        mode="transcribe",
        flush_signal=True,
    )

    # 3. LLM Setup (Sarvam) - Keeping architecture consistent
    llm_plugin = sarvam.LLM(
        model="sarvam-105b-conversations",
    )

    # 4. TTS Setup (Sarvam)
    tts_plugin = sarvam.TTS(
        target_language_code="hi-IN",
        model="bulbul:v3",
        speaker="shubh",
        output_audio_codec="mp3",
    )

    # 5. Initialize AgentSession (Standard LiveKit 1.8.x Voice Pipeline)
    session = AgentSession(
        stt=stt_plugin,
        llm=llm_plugin,
        tts=tts_plugin,
        vad=vad_plugin,
    )

    # Helper to extract text safely from events
    def extract_text(obj):
        if isinstance(obj, dict):
            return obj.get("lk.pii.user_transcript") or obj.get("lk.pii.text") or obj.get("text") or obj.get("transcript") or obj.get("raw_text_content") or str(obj)
        # Handle objects by checking common attributes
        return getattr(obj, "transcript", getattr(obj, "text", getattr(obj, "raw_text_content", str(obj))))

    # 6. Diagnostic Logging Hooks (Clear formatting)
    @session.on("user_state_changed")
    def on_user_state_changed(ev):
        state = ev.get("new_state") if isinstance(ev, dict) else getattr(ev, "new_state", "")
        if state == "speaking":
            print("\n🎙️  \033[93m[VAD] User is speaking...\033[0m")

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev):
        is_final = ev.get("is_final", True) if isinstance(ev, dict) else getattr(ev, "is_final", True)
        text = extract_text(ev)
        if is_final:
            print(f"\n🗣️  \033[92m[USER SAID]:\033[0m {text}")
        else:
            print(f"\r🗣️  [STT INTERIM]: {text[:80]}...", end="", flush=True)

    @session.on("agent_state_changed")
    def on_agent_state_changed(ev):
        state = ev.get("new_state") if isinstance(ev, dict) else getattr(ev, "new_state", "")
        if state == "speaking":
            print("\n🔊 \033[93m[TTS] Oldy Buddy is speaking...\033[0m")

    @session.on("conversation_item_added")
    def on_conversation_item_added(ev):
        item = ev.get("item") if isinstance(ev, dict) else getattr(ev, "item", ev)
        role = item.get("role") if isinstance(item, dict) else getattr(item, "role", "")
        if role == "assistant":
            text = extract_text(item)
            print(f"\n🤖 \033[96m[OLDY BUDDY SAID]:\033[0m {text}")

    @session.on("error")
    def on_error(err):
        print(f"\n❌ \033[91m[AGENT ERROR]: {err}\033[0m")

    # 7. Start Agent Session with System Prompt
    system_prompt = (
        "Aap Oldy Buddy hain, ek caring, polite aur elder-friendly companion app jo buzurgon ki madad karta hai.\n\n"
        "RULES FOR CONVERSATION:\n"
        "1. Responses hamesha chote, saaf, aasan aur shant bhasha mein hone chahiye. Ek asali insaan ki tarah naturally aur continuously baat karein.\n"
        "2. User jis bhasha mein bole (Hindi, Marathi, English), aap usi bhasha mein politely jawab dein.\n"
        "3. User ko kabhi zor se bolne ke liye mat kahein.\n"
        "4. Agar audio saf na sunai de ya unclear ho, toh politely kahein:\n"
        "   'Kshama kijiye, mujhe aapki aawaaz saf nahi sunai di. Kya aap dobara bolenge?'\n"
        "5. Complex technical words use mat karein. Dawaai, reminder aur daily help mein caring tareeke se madad karein."
    )

    await session.start(
        room=ctx.room,
        agent=Agent(instructions=system_prompt),
    )

    # 8. Initial Greeting
    await session.generate_reply(
        instructions=(
            "Say exactly this in Hindi/Hinglish: "
            "Namaste! Main Oldy Buddy hoon. Aaj main aapki kya madad kar sakta hoon?"
        )
    )

    # 9. Keep the session alive indefinitely so it doesn't stop
    print("\n✅ \033[92mOldy Buddy is ready and listening!\033[0m")
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        print("\n👋 \033[95m[SYSTEM] Session cancelled, closing agent.\033[0m")

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint
        )
    )
